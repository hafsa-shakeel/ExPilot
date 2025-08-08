from flask import Blueprint, request, jsonify, session
from umd_app.db import get_connection
from datetime import datetime, timedelta

alert_bp = Blueprint('alert_bp', __name__)


@alert_bp.route('/alerts', methods=['GET'])
def get_active_alerts():
    identity = session.get('user')
    role_id = identity.get("role_id")
    business_id = identity.get("business_id")
    user_id = identity.get("user_id")

    if not all([role_id, business_id, user_id]):
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Admin: get all unresolved alerts from their business branches
        if role_id == 1:
            cursor.execute("""
                SELECT a.alertsid, a.branch_id, b.branch_name, a.alert_type, a.severity, a.message, a.created_at
                FROM alerts a
                JOIN branches b ON a.branch_id = b.branch_id
                WHERE b.business_id = ? AND a.status = 1 AND a.is_resolved = 0
                ORDER BY a.created_at DESC
            """, (business_id,))

        # Branch Manager: only unresolved alerts of their assigned branch
        elif role_id == 2:
            cursor.execute("""
                SELECT a.alertsid, a.branch_id, b.branch_name, a.alert_type, a.severity, a.message, a.created_at
                FROM alerts a
                JOIN branches b ON a.branch_id = b.branch_id
                WHERE b.handled_by = ? AND b.business_id = ? AND a.status = 1 AND a.is_resolved = 0
                ORDER BY a.created_at DESC
            """, (user_id, business_id))

        else:
            return jsonify({"error": "Unauthorized access"}), 403

        rows = cursor.fetchall()

        alerts = [{
            "id": row[0],
            "branch_id": row[1],
            "branch_name": row[2],
            "type": row[3],
            "severity": row[4],
            "message": row[5],
            "created_at": str(row[6])
        } for row in rows]

        return jsonify({"alerts": alerts}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

# alerts_routes.py


@alert_bp.route('/budget-reminders/today', methods=["GET"])
def get_today_budget_reminders():
    identity = session.get('user')
    role_id = identity.get("role_id")
    business_id = identity.get("business_id")

    try:
        conn = get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")

        query = """
            SELECT a.alertsid, a.message, a.created_at, b.branch_name
            FROM alerts a
            JOIN branches b ON a.branch_id = b.branch_id
            WHERE CAST(a.created_at AS DATE) = ?
            AND a.alert_type = 'budget_reminder'
            AND a.status = 1
        """
        if role_id == 1 and role_id == 2:
            query += " AND b.business_id = ?"
            cursor.execute(query, (today, business_id))
        else:
            return jsonify({"error": "Unauthorized"}), 403

        rows = cursor.fetchall()
        alerts = [{
            "id": row[0],
            "message": row[1],
            "created_at": row[2],
            "branch_name": row[3]
        } for row in rows]

        return jsonify({"alerts": alerts}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@alert_bp.route('/alerts/filter', methods=['GET'])
def filter_alerts():
    identity = session.get('user')
    role_id = identity.get("role_id")
    business_id = identity.get("business_id")
    user_id = identity.get("user_id")

    severity = request.args.get('severity')
    filter_status = request.args.get('filter', 'active')  # default to active

    if not all([role_id, business_id, user_id]):
        return jsonify({"error": "Missing required parameters"}), 400

    query = """
        SELECT a.alertsid, a.branch_id, b.branch_name, a.alert_type, a.severity, 
               a.message, a.is_resolved, a.status, a.created_at
        FROM alerts a
        JOIN branches b ON a.branch_id = b.branch_id
        WHERE b.business_id = ?
    """
    params = [business_id]

    if role_id == 2:
        query += " AND b.handled_by = ?"
        params.append(user_id)

    # Status filters
    if filter_status == 'active':
        query += " AND a.status = 1 AND a.is_resolved = 0"
    elif filter_status == 'resolved':
        query += " AND a.is_resolved = 1"
    elif filter_status == 'inactive':
        query += " AND a.status = 0"
    # 'all' applies no filter

    # Severity filter
    if severity:
        query += " AND a.severity = ?"
        params.append(severity)

    query += " ORDER BY a.created_at DESC"

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

        alerts = [{
            "id": row[0],
            "branch_id": row[1],
            "branch_name": row[2],
            "type": row[3],
            "severity": row[4],
            "message": row[5],
            "is_resolved": bool(row[6]),
            "status": bool(row[7]),
            "created_at": str(row[8])
        } for row in rows]

        return jsonify({"filtered_alerts": alerts}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@alert_bp.route('/alerts/resolve/<int:alert_id>', methods=['PATCH'])
def resolve_alert(alert_id):
    identity = session.get('user')
    role_id = identity.get("role_id")
    business_id = identity.get("business_id")
    user_id = identity.get("user_id")

    if not all([role_id, business_id]):
        return jsonify({"error": "Missing role or business context."}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Get branch & business linked to the alert
        cursor.execute("""
            SELECT a.branch_id, b.business_id, b.handled_by
            FROM alerts a
            JOIN branches b ON a.branch_id = b.branch_id
            WHERE a.alertsid = ? AND a.status = 1 AND is_resolved = 0
        """, (alert_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({"error": "Alert not found, already resolved or already deleted."}), 404

        alert_branch_id, alert_business_id, handled_by = row

        if role_id == 1:
            # Admin can resolve only if alert is in their business
            if alert_business_id != business_id:
                return jsonify({"error": "Unauthorized."}), 403

        elif role_id == 2:
            # Manager can resolve only if alert belongs to their branch
            if alert_business_id != business_id or handled_by != user_id:
                return jsonify({"error": "Unauthorized."}), 403

        else:
            return jsonify({"error": "Invalid role."}), 403

        # Mark the alert as resolved
        cursor.execute("""
            UPDATE alerts
            SET is_resolved = 1, resolved_at = GETDATE()
            WHERE alertsid = ?
        """, (alert_id,))
        conn.commit()

        return jsonify({"message": "Alert resolved successfully."}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@alert_bp.route('/alerts/delete/<int:alert_id>', methods=['PATCH'])
def delete_alert(alert_id):
    data = request.json or {}
    role_id = data.get("role_id")
    business_id = data.get("business_id")
    user_id = data.get("user_id")

    if not all([role_id, business_id]):
        return jsonify({"error": "Missing role or business context."}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

    # Get branch, business, and manager info from alert
        cursor.execute("""
            SELECT a.branch_id, b.business_id, b.handled_by
            FROM alerts a
            JOIN branches b ON a.branch_id = b.branch_id
            WHERE a.alertsid = ? AND a.status = 1
        """, (alert_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({"error": "Alert not found or already deleted."}), 404

        branch_id, alert_business_id, handled_by = row

        if role_id == 1:
            if alert_business_id != business_id:
                return jsonify({"error": "Unauthorized."}), 403
        elif role_id == 2:
            if alert_business_id != business_id or handled_by != user_id:
                return jsonify({"error": "Unauthorized."}), 403
        else:
            return jsonify({"error": "Invalid role."}), 403

    # Soft delete the alert
        cursor.execute("""
            UPDATE alerts
            SET status = 0
            WHERE alertsid = ?
        """, (alert_id,))
        conn.commit()

        return jsonify({"message": "Alert soft-deleted successfully."}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@alert_bp.route("/unread-count", methods=["GET"])
def get_unread_alerts_count():
    identity = session.get('user')
    business_id = identity.get("business_id")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM alerts a
            JOIN branches b ON a.branch_id = b.branch_id
            WHERE b.business_id = ? AND a.status = 1 AND ISNULL(a.is_viewed, 0) = 0
        """, (business_id,))
        count = cursor.fetchone()[0]
        return jsonify({"unread_count": count}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@alert_bp.route('/mark-viewed', methods=['PATCH'])
def mark_alerts_as_viewed():
    identity = session.get('user')
    business_id = identity.get('business_id')

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE a
            SET a.is_viewed = 1
            FROM alerts a
            JOIN branches b ON a.branch_id = b.branch_id
            WHERE b.business_id = ? AND a.status = 1 AND ISNULL(a.is_viewed, 0) = 0
        """, (business_id,))
        conn.commit()
        return jsonify({"message": "Alerts marked as viewed."}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@alert_bp.route('/alerts/reopen/<int:alert_id>', methods=['PATCH'])
def reopen_alert(alert_id):
    identity = session.get('user')
    role_id = identity.get("role_id")
    business_id = identity.get("business_id")
    user_id = identity.get("user_id")

    if not all([role_id, business_id]):
        return jsonify({"error": "Missing role or business context."}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Fetch alert and branch details
        cursor.execute("""
            SELECT a.branch_id, b.business_id, b.handled_by, a.is_resolved
            FROM alerts a
            JOIN branches b ON a.branch_id = b.branch_id
            WHERE a.alertsid = ? AND a.status = 1
        """, (alert_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({"error": "Alert not found or deleted."}), 404

        branch_id, alert_business_id, handled_by, is_resolved = row

        if is_resolved == 0:
            return jsonify({"message": "Alert is already active."}), 200

        if role_id == 1:
            if alert_business_id != business_id:
                return jsonify({"error": "Unauthorized."}), 403
        elif role_id == 2:
            if alert_business_id != business_id or handled_by != user_id:
                return jsonify({"error": "Unauthorized."}), 403
        else:
            return jsonify({"error": "Invalid role."}), 403

        # Reopen the alert
        cursor.execute("""
            UPDATE alerts
            SET is_resolved = 0, resolved_at = NULL
            WHERE alertsid = ?
        """, (alert_id,))
        conn.commit()

        return jsonify({"message": "Alert reopened successfully."}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
