"""
Compliance routes - PaySecure Technologies GRC Platform
Manages PCI-DSS v4.0, GDPR, ISO 27001:2022, and RBI PA/PG controls.
Python 3.8+ safe (no backslashes inside f-string expressions).
"""
import json
import traceback

from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, session)

from app.auth.utils import login_required, any_role_required
from app.db import db
from . import compliance_bp


def _log(action, entity_type, entity_id, details_dict):
    """Write an audit record."""
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
        print("Audit log error: {}".format(exc))


# ── Compliance Controls List ─────────────────────────────────────────────────

@compliance_bp.route('/controls')
@login_required
def controls():
    """Main compliance controls view – all frameworks."""
    try:
        ctrl_list = db.execute_query(
            """SELECT control_id, control_code, control_name, control_description,
                      regulation, control_category, implementation_status,
                      last_tested, is_mandatory, is_active
               FROM compliance_controls
               WHERE is_active = TRUE
               ORDER BY regulation, control_code""",
            fetch=True,
        )

        stats = db.execute_query(
            """SELECT regulation,
                      COUNT(*) AS total_controls,
                      SUM(CASE WHEN implementation_status = 'Implemented' THEN 1 ELSE 0 END) AS active_controls
               FROM compliance_controls
               WHERE is_active = TRUE
               GROUP BY regulation
               ORDER BY regulation""",
            fetch=True,
        )

        mapping_rows = db.execute_query(
            "SELECT control_id, COUNT(risk_id) AS cnt "
            "FROM risk_compliance_mapping GROUP BY control_id",
            fetch=True,
        )
        mapping_dict = {r['control_id']: r['cnt'] for r in mapping_rows}

        _log('COMPLIANCE_CONTROLS_VIEWED', 'compliance_controls', None, {
            'viewed_by':     session.get('username', 'unknown'),
            'control_count': len(ctrl_list),
        })

        return render_template(
            'compliance/controls.html',
            controls=ctrl_list,
            stats=stats,
            mapping_dict=mapping_dict,
        )

    except Exception:
        print(traceback.format_exc())
        flash('Error loading compliance controls.', 'danger')
        return render_template(
            'compliance/controls.html',
            controls=[], stats=[], mapping_dict={},
        )


# ── Map Risk to Control ──────────────────────────────────────────────────────

@compliance_bp.route('/map-risk/<int:risk_id>', methods=['GET', 'POST'])
@any_role_required('admin', 'risk_manager', 'compliance_officer')
def map_risk(risk_id):
    """Map / un-map a risk to one or more compliance controls."""
    try:
        risk_rows = db.execute_query(
            """SELECT r.risk_id, r.risk_code, r.risk_title, r.risk_level,
                      rc.category_name
               FROM risks r
               JOIN risk_categories rc ON r.category_id = rc.category_id
               WHERE r.risk_id = %s""",
            (risk_id,),
            fetch=True,
        )
        if not risk_rows:
            flash('Risk not found.', 'danger')
            return redirect(url_for('compliance.controls'))
        risk = risk_rows[0]

        if request.method == 'POST':
            control_id   = request.form.get('control_id')
            mapping_type = request.form.get('mapping_type', 'Mitigating')
            action_type  = request.form.get('action', 'add')

            if not control_id:
                flash('Control ID is required.', 'danger')
                return redirect(url_for('compliance.map_risk', risk_id=risk_id))

            risk_code  = risk['risk_code']
            username   = session.get('username', 'unknown')

            if action_type == 'add':
                exists = db.execute_query(
                    "SELECT mapping_id FROM risk_compliance_mapping "
                    "WHERE risk_id=%s AND control_id=%s",
                    (risk_id, control_id),
                    fetch=True,
                )
                if exists:
                    flash('This risk-control mapping already exists.', 'warning')
                else:
                    db.execute_query(
                        """INSERT INTO risk_compliance_mapping
                           (risk_id, control_id, mapping_type, mapped_by)
                           VALUES (%s, %s, %s, %s)""",
                        (risk_id, control_id, mapping_type, session.get('user_id')),
                    )
                    ctrl = db.execute_query(
                        "SELECT control_code FROM compliance_controls "
                        "WHERE control_id=%s",
                        (control_id,),
                        fetch=True,
                    )
                    ctrl_code = ctrl[0]['control_code'] if ctrl else str(control_id)
                    _log('RISK_CONTROL_MAPPED', 'risk_compliance_mapping', risk_id, {
                        'risk_code':    risk_code,
                        'control':      ctrl_code,
                        'mapping_type': mapping_type,
                        'mapped_by':    username,
                    })
                    flash(
                        'Risk {} mapped to control {}.'.format(risk_code, ctrl_code),
                        'success',
                    )

            elif action_type == 'remove':
                mapping_id = request.form.get('mapping_id')
                if mapping_id:
                    db.execute_query(
                        "DELETE FROM risk_compliance_mapping "
                        "WHERE mapping_id = %s AND risk_id = %s",
                        (mapping_id, risk_id),
                    )
                    _log('RISK_CONTROL_UNMAPPED', 'risk_compliance_mapping', risk_id, {
                        'risk_code':  risk_code,
                        'mapping_id': mapping_id,
                        'removed_by': username,
                    })
                    flash('Mapping removed.', 'info')

            return redirect(url_for('compliance.map_risk', risk_id=risk_id))

        # GET – fetch controls and existing mappings
        all_controls = db.execute_query(
            """SELECT control_id, control_code, control_name,
                      regulation, implementation_status
               FROM compliance_controls
               WHERE is_active = TRUE
               ORDER BY regulation, control_code""",
            fetch=True,
        )

        existing_mappings = db.execute_query(
            """SELECT rcm.mapping_id, rcm.mapping_type, rcm.mapped_at,
                      cc.control_id, cc.control_code, cc.control_name, cc.regulation
               FROM risk_compliance_mapping rcm
               JOIN compliance_controls cc ON rcm.control_id = cc.control_id
               WHERE rcm.risk_id = %s
               ORDER BY cc.regulation, cc.control_code""",
            (risk_id,),
            fetch=True,
        )

        # Build a set of already-mapped control IDs for template filtering
        mapped_ids = {m['control_id'] for m in existing_mappings}

        return render_template(
            'compliance/map_risk.html',
            risk=risk,
            controls=all_controls,          # template uses 'controls'
            existing_mappings=existing_mappings,
            mapped_ids=mapped_ids,          # template uses 'mapped_ids'
        )

    except Exception:
        print(traceback.format_exc())
        flash('Error managing risk-control mapping.', 'danger')
        return redirect(url_for('compliance.controls'))