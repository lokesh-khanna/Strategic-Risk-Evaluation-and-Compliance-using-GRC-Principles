"""
Audit Trail routes - PaySecure Technologies GRC Platform
ISO 27001:2022 A.8.15 · PCI-DSS Req 10 · 7-year retention
Python 3.8+ safe (no backslashes inside f-string expressions).
"""
import csv
import io
import json
import traceback

from flask import (Blueprint, render_template, request,
                   Response, session, flash, redirect, url_for)

from app.auth.utils import login_required, any_role_required
from app.db import db
from . import audit_bp


def _write_log(action, entity_type, entity_id, details_dict):
    """Persist an audit event."""
    try:
        db.execute_query(
            """INSERT INTO audit_logs
               (user_id, action, entity_type, entity_id, details, ip_address)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                session.get('user_id'), action, entity_type, entity_id,
                json.dumps(details_dict), request.remote_addr,
            ),
        )
    except Exception as exc:
        print("Audit log write error: {}".format(exc))


# ── Audit Trail View ─────────────────────────────────────────────────────────

@audit_bp.route('/audit')
@any_role_required('admin', 'auditor')
def trail():
    """Audit trail with user / action / date filters."""
    try:
        days_str = request.args.get('date', '7')
        user_id  = request.args.get('user_id', 'all')
        action   = request.args.get('action', 'all')

        try:
            days = int(days_str)
        except (TypeError, ValueError):
            days = 7

        conditions = ["al.created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)"]
        params: list = [days]

        if user_id != 'all':
            conditions.append("al.user_id = %s")
            params.append(user_id)

        if action != 'all':
            conditions.append("al.action = %s")
            params.append(action)

        where = "WHERE " + " AND ".join(conditions)

        logs = db.execute_query(
            """SELECT al.log_id, al.action, al.entity_type, al.entity_id,
                      al.details, al.ip_address, al.created_at,
                      u.full_name, u.username, u.job_title
               FROM audit_logs al
               LEFT JOIN users u ON al.user_id = u.user_id
               {where}
               ORDER BY al.created_at DESC
               LIMIT 500""".format(where=where),
            tuple(params),
            fetch=True,
        )

        users = db.execute_query(
            "SELECT DISTINCT user_id, full_name FROM users "
            "WHERE is_active=TRUE ORDER BY full_name",
            fetch=True,
        )

        actions = db.execute_query(
            "SELECT DISTINCT action FROM audit_logs ORDER BY action",
            fetch=True,
        )

        stats_row = db.execute_query(
            """SELECT COUNT(*)                 AS total_logs,
                      COUNT(DISTINCT al.user_id) AS unique_users,
                      COUNT(DISTINCT al.action)  AS unique_actions,
                      MAX(al.created_at)         AS last_activity
               FROM audit_logs al
               {where}""".format(where=where),
            tuple(params),
            fetch=True,
        )[0]

        username = session.get('username', 'unknown')
        _write_log('AUDIT_TRAIL_VIEWED', 'audit_logs', None, {
            'viewed_by':    username,
            'filter_days':  days,
            'filter_user':  user_id,
            'filter_action': action,
        })

        return render_template(
            'audit/trail.html',
            logs=logs,
            users=users,
            actions=actions,
            stats=stats_row,
            filters={'date': str(days), 'user_id': user_id, 'action': action},
        )

    except Exception:
        print(traceback.format_exc())
        flash('Error loading audit trail.', 'danger')
        return render_template(
            'audit/trail.html',
            logs=[], users=[], actions=[],
            stats={
                'total_logs': 0, 'unique_users': 0,
                'unique_actions': 0, 'last_activity': None,
            },
            filters={},
        )


# ── CSV Export ───────────────────────────────────────────────────────────────

@audit_bp.route('/audit/export')
@any_role_required('admin')
def export():
    """Export audit logs as CSV (admin only)."""
    try:
        days_str = request.args.get('date', '30')
        try:
            days = int(days_str)
        except (TypeError, ValueError):
            days = 30

        logs = db.execute_query(
            """SELECT al.log_id, al.action, al.entity_type, al.entity_id,
                      al.details, al.ip_address, al.created_at,
                      u.full_name, u.username, u.job_title
               FROM audit_logs al
               LEFT JOIN users u ON al.user_id = u.user_id
               WHERE al.created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
               ORDER BY al.created_at DESC""",
            (days,),
            fetch=True,
        )

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Log ID', 'Action', 'Entity Type', 'Entity ID',
            'Details', 'IP Address', 'Timestamp',
            'User Name', 'Username', 'Job Title',
        ])
        for log in logs:
            writer.writerow([
                log['log_id'], log['action'],
                log['entity_type'], log['entity_id'],
                log['details'], log['ip_address'],
                log['created_at'].isoformat() if log['created_at'] else '',
                log['full_name'], log['username'], log['job_title'],
            ])

        username = session.get('username', 'unknown')
        _write_log('AUDIT_LOG_EXPORTED', 'audit_logs', None, {
            'exported_by':   username,
            'record_count':  len(logs),
            'last_n_days':   days,
        })

        filename = 'paysecure_audit_log_{}d.csv'.format(days)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment;filename=' + filename},
        )

    except Exception as exc:
        flash('Export error: {}'.format(exc), 'danger')
        return redirect(url_for('audit.trail'))