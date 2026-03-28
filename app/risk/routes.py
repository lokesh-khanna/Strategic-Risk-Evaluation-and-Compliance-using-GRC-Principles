"""
Risk Management routes - PaySecure Technologies GRC Platform
Handles risk register CRUD, heat-map data, and status lifecycle transitions.
Compatible with Python 3.8+ (no backslashes inside f-string expressions).
"""
import json
import traceback

from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, jsonify, session)

from app.auth.utils import login_required, any_role_required
from app.db import db
from . import risk_bp

# Valid lifecycle transitions
RISK_LIFECYCLE = [
    'Identified', 'Assessed', 'Treatment Planned',
    'Mitigating', 'Accepted', 'Closed'
]


def _log(action, entity_type, entity_id, details_dict):
    """Write a JSON-serialised audit record."""
    try:
        db.execute_query(
            """INSERT INTO audit_logs
               (user_id, action, entity_type, entity_id, details, ip_address)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                session.get('user_id'),
                action,
                entity_type,
                entity_id,
                json.dumps(details_dict),
                request.remote_addr,
            ),
        )
    except Exception as exc:
        print(f"Audit log error: {exc}")


# ── Risk Register ────────────────────────────────────────────────────────────

@risk_bp.route('/register')
@login_required
def register():
    """Risk register – full list with server-side heatmap data."""
    try:
        risks = db.execute_query(
            """
            SELECT r.risk_id, r.risk_code, r.risk_title, r.risk_description,
                   r.probability, r.impact, r.risk_score, r.risk_level,
                   r.status, r.treatment_type, r.business_impact,
                   r.review_date, r.created_at, r.updated_at,
                   rc.category_name, rc.nist_csf_domain,
                   u.full_name  AS owner_name,
                   u.job_title  AS owner_title,
                   u.department AS owner_dept
            FROM risks r
            INNER JOIN risk_categories rc ON r.category_id = rc.category_id
            INNER JOIN users u            ON r.risk_owner_id = u.user_id
            ORDER BY r.risk_score DESC, r.created_at DESC
            """,
            fetch=True,
        )

        categories = db.execute_query(
            "SELECT category_id, category_name, nist_csf_domain "
            "FROM risk_categories ORDER BY category_name",
            fetch=True,
        )
        users = db.execute_query(
            "SELECT user_id, full_name, job_title "
            "FROM users WHERE is_active = TRUE ORDER BY full_name",
            fetch=True,
        )

        counts = {'High': 0, 'Medium': 0, 'Low': 0}
        for r in risks:
            counts[r['risk_level']] = counts.get(r['risk_level'], 0) + 1

        return render_template(
            'risk/register.html',
            risks=risks,
            categories=categories,
            users=users,
            counts=counts,
            lifecycle=RISK_LIFECYCLE,
        )

    except Exception:
        print(traceback.format_exc())
        flash('Error loading risk register.', 'danger')
        return render_template(
            'risk/register.html',
            risks=[], categories=[], users=[],
            counts={'High': 0, 'Medium': 0, 'Low': 0},
            lifecycle=RISK_LIFECYCLE,
        )


# ── Create Risk ──────────────────────────────────────────────────────────────

@risk_bp.route('/create', methods=['POST'])
@any_role_required('admin', 'risk_manager')
def create():
    """Create a new risk entry."""
    try:
        risk_title       = request.form.get('risk_title', '').strip()
        risk_description = request.form.get('risk_description', '').strip()
        category_id      = request.form.get('category_id')
        risk_owner_id    = request.form.get('risk_owner_id')
        probability      = request.form.get('probability')
        impact           = request.form.get('impact')
        mitigation_plan  = request.form.get('mitigation_plan', '').strip()
        business_impact  = request.form.get('business_impact', '').strip()
        treatment_type   = request.form.get('treatment_type', 'Mitigate')
        review_date      = request.form.get('review_date') or None

        if not risk_title or len(risk_title) < 5:
            flash('Risk title must be at least 5 characters.', 'danger')
            return redirect(url_for('risk.register'))

        if not category_id or not risk_owner_id:
            flash('Category and Risk Owner are required.', 'danger')
            return redirect(url_for('risk.register'))

        try:
            probability = int(probability)
            impact = int(impact)
            if not (1 <= probability <= 5) or not (1 <= impact <= 5):
                raise ValueError
        except (TypeError, ValueError):
            flash('Probability and Impact must be integers between 1 and 5.', 'danger')
            return redirect(url_for('risk.register'))

        # Generate risk_code
        max_id = (
            db.execute_query("SELECT MAX(risk_id) AS m FROM risks", fetch=True)[0]['m']
            or 0
        )
        risk_code = "RISK-2025-{:03d}".format(max_id + 1)

        risk_id = db.execute_query(
            """INSERT INTO risks
               (risk_code, risk_title, risk_description, category_id, risk_owner_id,
                probability, impact, status, treatment_type, mitigation_plan,
                business_impact, review_date, created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,'Identified',%s,%s,%s,%s,%s)""",
            (
                risk_code, risk_title, risk_description, category_id, risk_owner_id,
                probability, impact, treatment_type, mitigation_plan,
                business_impact, review_date, session.get('user_id'),
            ),
        )

        score = probability * impact
        level = 'High' if score >= 16 else ('Medium' if score >= 6 else 'Low')
        username = session.get('username', 'unknown')

        _log('RISK_CREATED', 'risks', risk_id, {
            'risk_code':   risk_code,
            'risk_title':  risk_title,
            'risk_level':  level,
            'probability': probability,
            'impact':      impact,
            'score':       score,
            'created_by':  username,
        })

        flash(
            'Risk {} created successfully! Risk Score: {} ({})'.format(
                risk_code, score, level),
            'success',
        )
        return redirect(url_for('risk.register'))

    except Exception as exc:
        flash('Error creating risk: {}'.format(exc), 'danger')
        return redirect(url_for('risk.register'))


# ── Update Status ────────────────────────────────────────────────────────────

@risk_bp.route('/update-status/<int:risk_id>', methods=['POST'])
@any_role_required('admin', 'risk_manager')
def update_status(risk_id):
    """Advance or revert a risk through its lifecycle."""
    try:
        new_status = request.form.get('status')
        if new_status not in RISK_LIFECYCLE:
            flash('Invalid status value.', 'danger')
            return redirect(url_for('risk.register'))

        risk = db.execute_query(
            "SELECT risk_code, risk_title, status FROM risks WHERE risk_id = %s",
            (risk_id,),
            fetch=True,
        )
        if not risk:
            flash('Risk not found.', 'danger')
            return redirect(url_for('risk.register'))

        old_status = risk[0]['status']
        risk_code  = risk[0]['risk_code']
        risk_title = risk[0]['risk_title']

        db.execute_query(
            "UPDATE risks SET status = %s, updated_at = NOW() WHERE risk_id = %s",
            (new_status, risk_id),
        )

        _log('RISK_STATUS_UPDATED', 'risks', risk_id, {
            'risk_code':       risk_code,
            'risk_title':      risk_title,
            'previous_status': old_status,
            'new_status':      new_status,
            'updated_by':      session.get('username', 'unknown'),
        })

        flash(
            'Risk {} status updated: {} → {}'.format(risk_code, old_status, new_status),
            'success',
        )
        return redirect(url_for('risk.register'))

    except Exception as exc:
        flash('Error updating risk status: {}'.format(exc), 'danger')
        return redirect(url_for('risk.register'))


# ── Delete Risk ──────────────────────────────────────────────────────────────

@risk_bp.route('/delete/<int:risk_id>', methods=['POST'])
@any_role_required('admin')
def delete(risk_id):
    """Hard-delete a risk and its mappings (admin only)."""
    try:
        risk = db.execute_query(
            "SELECT risk_code, risk_title FROM risks WHERE risk_id = %s",
            (risk_id,),
            fetch=True,
        )
        if not risk:
            flash('Risk not found.', 'danger')
            return redirect(url_for('risk.register'))

        risk_code  = risk[0]['risk_code']
        risk_title = risk[0]['risk_title']

        db.execute_query(
            "DELETE FROM risk_compliance_mapping WHERE risk_id = %s", (risk_id,)
        )
        db.execute_query("DELETE FROM risks WHERE risk_id = %s", (risk_id,))

        _log('RISK_DELETED', 'risks', risk_id, {
            'risk_code':  risk_code,
            'risk_title': risk_title,
            'deleted_by': session.get('username', 'unknown'),
        })

        flash('Risk {} deleted.'.format(risk_code), 'info')
        return redirect(url_for('risk.register'))

    except Exception as exc:
        flash('Error deleting risk: {}'.format(exc), 'danger')
        return redirect(url_for('risk.register'))


# ── Heatmap JSON API ─────────────────────────────────────────────────────────

@risk_bp.route('/heatmap-data')
@login_required
def heatmap_data():
    """Return 5×5 heatmap matrix as JSON for dynamic chart rendering."""
    try:
        risks = db.execute_query(
            "SELECT probability, impact, risk_level, risk_title, risk_code, risk_id "
            "FROM risks",
            fetch=True,
        )

        # matrix[impact_idx 0-4][prob_idx 0-4]  (0-indexed)
        matrix = [[[] for _ in range(5)] for _ in range(5)]
        level_counts = {'Low': 0, 'Medium': 0, 'High': 0}

        for risk in risks:
            p = risk['probability'] - 1
            i = risk['impact'] - 1
            matrix[i][p].append({
                'id':    risk['risk_id'],
                'code':  risk['risk_code'],
                'title': risk['risk_title'],
                'level': risk['risk_level'],
            })
            level_counts[risk['risk_level']] = (
                level_counts.get(risk['risk_level'], 0) + 1
            )

        return jsonify({
            'matrix':       matrix,
            'level_counts': level_counts,
            'total_risks':  len(risks),
        })

    except Exception as exc:
        return jsonify({'error': str(exc)}), 500