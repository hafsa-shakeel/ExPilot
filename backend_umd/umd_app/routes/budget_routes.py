from flask import Blueprint, request, jsonify, session
from umd_app.db import get_connection
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

budget_bp = Blueprint('budget_bp', __name__)

# budget allocate


@budget_bp.route('/add', methods=['POST'])
def add_budget():
    identity = session.get('user')
    role_id = identity.get("role_id")
    business_id = identity.get("business_id")
    allocated_by = identity.get("user_id")

    data = request.json
    branch_id = data.get("branch_id")
    year = data.get("year")
    month = data.get("month")
    total_budget = data.get("total_budget")

    if role_id != 1:
        return jsonify({"error": "Only admins can add budgets."}), 403

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT business_id FROM branches WHERE branch_id = ?", (branch_id,))
        row = cursor.fetchone()
        if not row or row[0] != business_id:
            return jsonify({"error": "Unauthorized. Branch not in your business."}), 403

        cursor.execute("""
            SELECT id FROM budget WHERE branch_id = ? AND year = ? AND month = ?
        """, (branch_id, year, month))
        if cursor.fetchone():
            return jsonify({"error": "Budget already exists for this period."}), 409

        cursor.execute("""
            INSERT INTO budget (branch_id, year, month, total_budget, allocated_by)
            VALUES (?, ?, ?, ?, ?)
        """, (branch_id, year, month, total_budget, allocated_by))

        # Insert future alert for same date next month
        next_month_same_day = datetime.now() + relativedelta(months=1)

        cursor.execute("""
            INSERT INTO alerts (branch_id, utility_bill_id, alert_type, severity, message, created_at)
            VALUES (?, NULL, 'budget_reminder', 'medium', ?, ?)
        """, (
            branch_id,  # from the inserted budget
            f"Reminder to allocate budget again to this branch.",
            next_month_same_day.strftime("%Y-%m-%d")
        ))

        conn.commit()
        return jsonify({"message": "Budget added successfully."}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@budget_bp.route('/view', methods=['POST'])
def view_budgets():
    from datetime import datetime
    identity = session.get('user')
    role_id = identity.get("role_id")
    business_id = identity.get("business_id")

    data = request.json or {}
    year = data.get("year")
    month = data.get("month")
    branch_id = data.get("branch_id")

    page = data.get('page', 1)
    limit = data.get('limit', 10)
    offset = (page - 1) * limit
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT bg.id, bg.branch_id, b.branch_name, bg.year, bg.month, bg.total_budget,
                   ISNULL(SUM(ub.amount), 0) as total_spent
            FROM budget bg
            JOIN branches b ON bg.branch_id = b.branch_id
            LEFT JOIN utility_bills ub 
                ON bg.branch_id = ub.branch_id AND bg.year = ub.year AND bg.month = ub.month
            WHERE b.status = 1
        """
        params = []

        if role_id == 1:
            query += " AND b.business_id = ?"
            params.append(business_id)
        elif role_id == 2:
            query += " AND b.handled_by = ?"
            params.append(identity.get("user_id"))
        else:
            return jsonify({"error": "Unauthorized access."}), 403

        if year:
            query += " AND bg.year = ?"
            params.append(year)
        if month:
            query += " AND bg.month = ?"
            params.append(month)
        if branch_id:
            query += " AND bg.branch_id = ?"
            params.append(branch_id)

        query += """
            GROUP BY bg.id, bg.branch_id, b.branch_name, bg.year, bg.month, bg.total_budget
            ORDER BY bg.year DESC, bg.month DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        params += [offset, limit]

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        result = [{
            "id": r[0],
            "branch_id": r[1],
            "branch": r[2],
            "year": r[3],
            "month": r[4],
            "total_budget": float(r[5]),
            "total_spent": float(r[6])
        } for r in rows]

        return jsonify({"budgets": result, "total_records": len(result)}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# PATCH /budgets/update/<int:budget_id>
@budget_bp.route('/update/<int:budget_id>', methods=['PATCH'])
def update_budget(budget_id):
    identity = session.get('user')
    role_id = identity.get("role_id")
    business_id = identity.get("business_id")

    data = request.json or {}
    total_budget = data.get("total_budget")
    month = data.get("month")
    year = data.get("year")

    reallocate = request.args.get("reallocate", "false").lower() == "true"

    if role_id != 1:
        return jsonify({"error": "Only admin can update budgets."}), 403

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Fetch original budget entry
        cursor.execute("""
            SELECT bg.id, bg.created_at, b.business_id, bg.branch_id
            FROM budget bg
            JOIN branches b ON bg.branch_id = b.branch_id
            WHERE bg.id = ?
        """, (budget_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({"error": "Budget not found."}), 404

        _, created_at, budget_business_id, branch_id = row

        if budget_business_id != business_id:
            return jsonify({"error": "Unauthorized. Only update your own business"}), 403

        # Handle datetime conversion
        if not isinstance(created_at, datetime):
            created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")

        # Enforce 48-hour limit unless reallocating
        if not reallocate and datetime.now() > created_at + timedelta(hours=48):
            return jsonify({"error": "Cannot edit now. 48-hour update window expired."}), 403

        # Prepare update query
        if reallocate:
            # Also update created_at to now
            cursor.execute("""
                UPDATE budget
                SET total_budget = ?, month = ?, year = ?, created_at = GETDATE()
                WHERE id = ?
            """, (total_budget, month, year, budget_id))
        else:
            # Keep existing created_at
            cursor.execute("""
                UPDATE budget
                SET total_budget = ?, month = ?, year = ?
                WHERE id = ?
            """, (total_budget, month, year, budget_id))

        # Insert future alert for same date next month
        next_month_same_day = datetime.now() + relativedelta(months=1)

        cursor.execute("""
            INSERT INTO alerts (branch_id, utility_bill_id, alert_type, severity, message, created_at)
            VALUES (?, NULL, 'budget_reminder', 'medium', ?, ?)
        """, (
            branch_id,  # from the inserted budget
            f"Reminder to allocate budget again to this branch.",
            next_month_same_day.strftime("%Y-%m-%d")
        ))

        conn.commit()
        return jsonify({"message": "Budget updated successfully."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# budget of a certain branch of a business by entering it's budget_id
# when we click on a budget from a list of budgets allocated before


@budget_bp.route('/budgets/<int:budget_id>', methods=['GET'])
def get_budget(budget_id):
    identity = session.get('user')
    business_id = identity.get("business_id")

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT b.branch_name, bg.year, bg.month, bg.total_budget, bg.created_at,
                   ISNULL(SUM(ub.amount), 0) as total_spent
            FROM budget bg
            JOIN branches b ON bg.branch_id = b.branch_id
            LEFT JOIN utility_bills ub 
                ON bg.branch_id = ub.branch_id AND bg.year = ub.year AND bg.month = ub.month
            WHERE bg.id = ? AND b.business_id = ?
            GROUP BY b.branch_name, bg.year, bg.month, bg.total_budget, bg.created_at
        """, (budget_id, business_id))

        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Budget not found or unauthorized."}), 404

        result = {
            "branch": row[0], "year": row[1], "month": row[2],
            "total_budget": float(row[3]), "created_at": row[4], "total_spent": float(row[5])
        }
        return jsonify({"budget": result}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@budget_bp.route('/budgets/history/<int:branch_id>', methods=['GET'])
def budget_history(branch_id):
    role_id = request.args.get("role_id", type=int)
    business_id = request.args.get("business_id", type=int)
    user_id = request.args.get("user_id", type=int)
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 10, type=int)

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Authorization checks
        if role_id == 2:
            cursor.execute(
                "SELECT handled_by FROM branches WHERE branch_id = ?", (branch_id,))
            row = cursor.fetchone()
            if not row or row[0] != user_id:
                return jsonify({"error": "Access denied."}), 403
        elif role_id == 1:
            cursor.execute(
                "SELECT business_id FROM branches WHERE branch_id = ?", (branch_id,))
            row = cursor.fetchone()
            if not row or row[0] != business_id:
                return jsonify({"error": "Unauthorized."}), 403

        # Count total rows for pagination metadata
        cursor.execute(
            "SELECT COUNT(*) FROM budget WHERE branch_id = ?", (branch_id,))
        total_records = cursor.fetchone()[0]

        offset = (page - 1) * page_size

        # Fetch paginated history with total spent per row
        cursor.execute("""
            SELECT bg.year, bg.month, bg.total_budget,
                ISNULL(SUM(ub.amount), 0) AS total_spent
            FROM budget bg
            LEFT JOIN utility_bills ub
                ON bg.branch_id = ub.branch_id AND bg.year = ub.year AND bg.month = ub.month
            WHERE bg.branch_id = ?
            GROUP BY bg.year, bg.month, bg.total_budget
            ORDER BY bg.year DESC, bg.month DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """, (branch_id, offset, page_size))

        rows = cursor.fetchall()
        history = [
            {
                "year": r[0],
                "month": r[1],
                "total_budget": float(r[2]),
                "total_spent": float(r[3])
            }
            for r in rows
        ]

        return jsonify({
            "page": page,
            "page_size": page_size,
            "total_records": total_records,
            "budget_history": history
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

# GET /budgets/alerts going
# show all alerts whether that be active/inactive/deleted


@budget_bp.route('/budgets/alerts', methods=['GET'])
def budget_alerts():
    identity = session.get('user')
    role_id = identity.get("role_id")
    business_id = identity.get("business_id")

    if role_id != 1:
        return jsonify({"error": "Only admin can access alerts."}), 403

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT b.branch_name, bg.year, bg.month, bg.total_budget,
                   ISNULL(SUM(ub.amount), 0) as total_expense,
                   (ISNULL(SUM(ub.amount), 0) - bg.total_budget) as overspent
            FROM budget bg
            JOIN branches b ON bg.branch_id = b.branch_id
            LEFT JOIN utility_bills ub 
                ON bg.branch_id = ub.branch_id AND bg.year = ub.year AND bg.month = ub.month
            WHERE b.business_id = ?
            GROUP BY b.branch_name, bg.year, bg.month, bg.total_budget
            HAVING ISNULL(SUM(ub.amount), 0) > bg.total_budget
        """, (business_id,))

        rows = cursor.fetchall()
        result = [{
            "branch": r[0],
            "year": r[1],
            "month": r[2],
            "budget": float(r[3]),
            "spent": float(r[4]),
            "overspent": float(r[5])
        } for r in rows]

        return jsonify({"alerts": result}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
