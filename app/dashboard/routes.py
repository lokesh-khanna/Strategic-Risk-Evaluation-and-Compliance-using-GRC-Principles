"""
Dashboard routes - PaySecure Technologies GRC Platform
Pulls live metrics from DB for real-time risk and compliance visibility
"""
from flask import Blueprint, render_template, jsonify
from app.auth.utils import login_required
from app.db import db

# Import the blueprint instance from package __init__
from . import dashboard_bp


@dashboard_bp.route('/dashboard')
@login_required
def view():
    """Main dashboard view with real-time GRC metrics"""
    try:
        # ── Risk Metrics ──────────────────────────────────────────
        risk_summary = db.execute_query("""
            SELECT
                COUNT(*)                                                          AS total_risks,
                SUM(CASE WHEN risk_level = 'High'   THEN 1 ELSE 0 END)           AS high_risks,
                SUM(CASE WHEN risk_level = 'Medium' THEN 1 ELSE 0 END)           AS medium_risks,
                SUM(CASE WHEN risk_level = 'Low'    THEN 1 ELSE 0 END)           AS low_risks,
                SUM(CASE WHEN status NOT IN ('Accepted','Closed') THEN 1 ELSE 0 END) AS open_risks,
                AVG(risk_score)                                                   AS avg_risk_score
            FROM risks
        """, fetch=True)[0]

        # Top 3 High risks for dashboard callout
        high_risks = db.execute_query("""
            SELECT risk_code, risk_title, risk_score, status
            FROM risks
            WHERE risk_level = 'High'
            ORDER BY risk_score DESC
            LIMIT 3
        """, fetch=True)

        # ── Compliance Metrics ────────────────────────────────────
        compliance_by_framework = db.execute_query("""
            SELECT
                regulation,
                COUNT(*) AS total_controls,
                SUM(CASE WHEN implementation_status = 'Implemented' THEN 1 ELSE 0 END) AS implemented,
                ROUND(
                    SUM(CASE WHEN implementation_status = 'Implemented' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
                    1
                ) AS compliance_pct
            FROM compliance_controls
            WHERE is_active = TRUE
            GROUP BY regulation
            ORDER BY regulation
        """, fetch=True)

        # ── Audit Metrics ─────────────────────────────────────────
        audit_stats = db.execute_query("""
            SELECT
                COUNT(*)                                   AS total_events_7d,
                COUNT(DISTINCT user_id)                    AS active_users_7d,
                SUM(CASE WHEN action = 'USER_LOGIN' THEN 1 ELSE 0 END)  AS login_events,
                SUM(CASE WHEN action LIKE 'RISK_%'  THEN 1 ELSE 0 END)  AS risk_events
            FROM audit_logs
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """, fetch=True)[0]

        # ── Recent Critical Audit Events ──────────────────────────
        recent_events = db.execute_query("""
            SELECT al.action, al.details, al.created_at,
                   u.full_name, u.job_title
            FROM audit_logs al
            LEFT JOIN users u ON al.user_id = u.user_id
            WHERE al.action NOT IN ('USER_LOGIN', 'USER_LOGOUT', 'AUDIT_TRAIL_VIEWED')
            ORDER BY al.created_at DESC
            LIMIT 5
        """, fetch=True)

        # ── Open Audit Findings (risks not yet mitigated) ─────────
        open_findings = db.execute_query("""
            SELECT risk_code, risk_title, risk_level, status, risk_score
            FROM risks
            WHERE status IN ('Identified', 'Assessed')
            ORDER BY risk_score DESC
            LIMIT 5
        """, fetch=True)

        # ── Risk Trend by Category ────────────────────────────────
        risk_by_category = db.execute_query("""
            SELECT rc.category_name, COUNT(r.risk_id) AS count,
                   MAX(r.risk_score) AS max_score
            FROM risks r
            JOIN risk_categories rc ON r.category_id = rc.category_id
            GROUP BY rc.category_name
            ORDER BY count DESC
        """, fetch=True)

        return render_template(
            'dashboard/index.html',
            risk_summary=risk_summary,
            high_risks=high_risks,
            compliance_by_framework=compliance_by_framework,
            audit_stats=audit_stats,
            recent_events=recent_events,
            open_findings=open_findings,
            risk_by_category=risk_by_category
        )

    except Exception as e:
        # Graceful fallback - render with empty data so page still loads
        import traceback
        print(f"Dashboard error: {e}\n{traceback.format_exc()}")
        return render_template(
            'dashboard/index.html',
            risk_summary={'total_risks': 0, 'high_risks': 0, 'medium_risks': 0,
                          'low_risks': 0, 'open_risks': 0, 'avg_risk_score': 0},
            high_risks=[],
            compliance_by_framework=[],
            audit_stats={'total_events_7d': 0, 'active_users_7d': 0,
                         'login_events': 0, 'risk_events': 0},
            recent_events=[],
            open_findings=[],
            risk_by_category=[],
            db_error=str(e)
        )