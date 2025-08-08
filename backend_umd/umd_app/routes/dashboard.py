from flask import Blueprint, request, jsonify, session
from umd_app.db import get_connection
import calendar
from statistics import mean

dashboard_bp = Blueprint('dashboard_bp', __name__)


@dashboard_bp.route('/summary', methods=['POST'])
def get_dashboard_summary():
    identity = session.get('user')
    role_id = identity.get("role_id")
    business_id = identity.get("business_id")
    branch_id = identity.get("branch_id")  # Optional for manager

    print(role_id)

    if not role_id or not business_id:
        return jsonify({"error": "Missing required data"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        if role_id == 1:
            cursor.execute(
                "SELECT COUNT(*) FROM branches WHERE business_id = ?", (business_id,))
            total_branches = cursor.fetchone()[0]

            cursor.execute("""
                SELECT ISNULL(SUM(total_budget), 0)
                FROM budget
                WHERE branch_id IN (SELECT branch_id FROM branches WHERE business_id = ?)
                    AND MONTH(created_at) = MONTH(GETDATE())
                    AND YEAR(created_at) = YEAR(GETDATE())
            """, (business_id,))
            monthly_budget = cursor.fetchone()[0]

            cursor.execute("""
                SELECT ISNULL(SUM(amount), 0)
                FROM utility_bills
                WHERE branch_id IN (SELECT branch_id FROM branches WHERE business_id = ?) AND status = 1
                    AND MONTH(uploaded_at) = MONTH(GETDATE())
                    AND YEAR(uploaded_at) = YEAR(GETDATE())
            """, (business_id,))
            total_expenses = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM alerts
                WHERE branch_id IN (SELECT branch_id FROM branches WHERE business_id = ?) 
                      AND is_resolved = 0
            """, (business_id,))
            active_alerts = cursor.fetchone()[0]

        elif role_id == 2:
            if not branch_id:
                return jsonify({"error": "Branch ID is required for managers"}), 400

            total_branches = 1

            cursor.execute("""
                SELECT ISNULL(SUM(total_budget), 0)
                FROM budget
                WHERE branch_id = ? 
            """, (branch_id,))
            monthly_budget = cursor.fetchone()[0]

            cursor.execute("""
                SELECT ISNULL(SUM(amount), 0)
                FROM utility_bills
                WHERE branch_id = ? AND MONTH(uploaded_at) = MONTH(GETDATE()) AND YEAR(uploaded_at) = YEAR(GETDATE())
            """, (branch_id,))
            total_expenses = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM alerts
                WHERE branch_id = ? AND is_resolved = 0
            """, (branch_id,))
            active_alerts = cursor.fetchone()[0]

        else:
            return jsonify({"error": "Invalid role"}), 403

        return jsonify({
            "total_branches": total_branches,
            "monthly_budget": float(monthly_budget),
            "total_expenses": float(total_expenses),
            "active_alerts": active_alerts
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

# budget management dashboard

# this looks like branch compare so leave it for now


@dashboard_bp.route('/branch-performance', methods=['POST'])
def branch_performance():
    identity = session.get('user')
    role_id = identity.get("role_id")
    business_id = identity.get("business_id")
    user_id = identity.get("user_id")
    # optional
    branch_id = identity.get("branch_id")

    if not role_id or not business_id:
        return jsonify({"error": "Missing role_id or business_id"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        if role_id == 1:
            # Admin view: All branches or specific branch if branch_id provided # performance of specific branch
            cursor.execute("""
                SELECT b.branch_id, b.branch_name,
                        ISNULL(SUM(bg.total_budget), 0) AS total_budget,
                        ISNULL(SUM(ub.amount), 0) AS total_expense,
                        (SELECT COUNT(*) FROM alerts a WHERE a.branch_id = b.branch_id) AS alerts
                FROM branches b
                LEFT JOIN budget bg ON b.branch_id = bg.branch_id
                LEFT JOIN utility_bills ub ON b.branch_id = ub.branch_id
                WHERE b.branch_id = ? AND b.business_id = ? AND b.status = 1
                GROUP BY b.branch_id, b.branch_name
            """, (branch_id, business_id))
        else:
            # Branch Manager: must provide branch_id
            if not branch_id:
                return jsonify({"error": "Branch ID required for branch manager"}), 400

            # Validate branch ownership
            cursor.execute("""
                SELECT handled_by FROM branches WHERE branch_id = ? AND business_id = ? AND status = 1
            """, (branch_id, business_id))
            result = cursor.fetchone()
            if not result or result[0] != user_id:
                return jsonify({"error": "Unauthorized or branch not found"}), 403

            cursor.execute("""
               SELECT
    b.branch_id,
    b.branch_name,

    -- Total budget for this branch
    (
        SELECT ISNULL(SUM(bg.total_budget), 0)
        FROM budget bg
        WHERE bg.branch_id = b.branch_id AND bg.status = 1
    ) AS total_budget,

    -- Total expenses for this branch
    (
        SELECT ISNULL(SUM(ub.amount), 0)
        FROM utility_bills ub
        WHERE ub.branch_id = b.branch_id AND ub.status = 1
    ) AS total_expense,

    -- Alerts count for this branch
    (
        SELECT COUNT(*) FROM alerts a WHERE a.branch_id = b.branch_id
    ) AS alert_count

FROM branches b
WHERE b.status = 1 AND b.branch_id = ?

                
            """, (branch_id,))

        rows = cursor.fetchall()

        data = []
        for row in rows:
            branch_id, branch_name, total_budget, total_expense, alerts = row
            remaining = float(total_budget) - float(total_expense)
            over_budget_amount = abs(remaining) if remaining < 0 else 0
            data.append({
                "branch_id": branch_id,
                # add total bills uploaded too
                "branch_name": branch_name,
                "total_budget": float(total_budget),
                "total_expense": float(total_expense),
                "remaining_budget": round(remaining, 2),
                "over_budget_amount": round(over_budget_amount, 2),
                "alerts_count": alerts
            })

        return jsonify({"branch_performance": data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

# admin only feature - branchwise(a list showing all of this and button of"show chart" on right)

# DONEEE - when added branches later then make a chart


@dashboard_bp.route('/branches/compare', methods=['POST'])
def compare_branches():
    identity = session.get('user')
    print("Session identity:", identity)

    if not identity:
        return jsonify({"error": "Unauthorized"}), 401

    role_id = identity.get("role_id")
    business_id = identity.get("business_id")

    if role_id != 1:
        return jsonify({"error": "Only admins can access this route"}), 403

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
    b.branch_id,
    b.branch_name,

    -- Total budget (correct per branch)
    (
        SELECT ISNULL(SUM(bg.total_budget), 0)
        FROM budget bg
        WHERE bg.branch_id = b.branch_id AND bg.status = 1
    ) AS total_budget,

    -- Total expenses (correct per branch)
    (
        SELECT ISNULL(SUM(ub.amount), 0)
        FROM utility_bills ub
        WHERE ub.branch_id = b.branch_id AND ub.status = 1
    ) AS total_expense,

    -- Alerts count
    (
        SELECT COUNT(*) FROM alerts a WHERE a.branch_id = b.branch_id
    ) AS alert_count,

    -- Utility bills count
    (
        SELECT COUNT(*) FROM utility_bills ub2 WHERE ub2.branch_id = b.branch_id
    ) AS total_bills_uploaded

FROM branches b
WHERE b.business_id = ? AND b.status = 1

        """, (business_id,))
        rows = cursor.fetchall()

        data = []
        for row in rows:
            branch_id, branch_name, total_budget, total_expense, alert_count, total_bills = row
            remaining = float(total_budget) - float(total_expense)
            over_budget_amount = abs(remaining) if remaining < 0 else 0
            status = "Profit" if remaining >= 0 else "Loss"

            data.append({
                "branch_id": branch_id,
                "branch_name": branch_name,
                "total_budget": float(total_budget),
                "total_expense": float(total_expense),
                "remaining_budget": round(remaining, 2),
                "over_budget_amount": round(over_budget_amount, 2),
                "status": status,
                "alert_count": alert_count,
                "total_bills_uploaded": total_bills
            })

        return jsonify({"branches_comparison": data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@dashboard_bp.route('/branches/<int:branch_id>/budget-vs-expense', methods=['GET'])
def budget_vs_expense_chart(branch_id):
    year = request.args.get("year")
    if not year:
        return jsonify({"error": "Year is required"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Budgets
        cursor.execute("""
            SELECT month, SUM(total_budget) AS total_budget
            FROM budget
            WHERE branch_id = ? AND year = ? AND status = 1
            GROUP BY month
        """, (branch_id, year))
        budget_data = {int(row[0]): float(row[1] or 0)
                       for row in cursor.fetchall()}

        # Expenses
        cursor.execute("""
            SELECT month, SUM(amount) AS total_expense
            FROM utility_bills
            WHERE branch_id = ? AND year = ? AND status = 1
            GROUP BY month
        """, (branch_id, year))
        expense_data = {int(row[0]): float(row[1] or 0)
                        for row in cursor.fetchall()}

        months = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']

        result = []
        for i in range(1, 13):
            result.append({
                "month": months[i - 1],
                "total_budget": budget_data.get(i, 0),
                "total_expense": expense_data.get(i, 0)
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@dashboard_bp.route('/expenses/branch-pie', methods=['GET'])
def branch_expenses_pie():
    business_id = session.get("user", {}).get("business_id")
    year = request.args.get("year")  # Optional

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Build SQL query with optional year filter
        sql = """
            SELECT b.branch_id, b.branch_name, ISNULL(SUM(ub.amount), 0) AS total_expense
            FROM branches b
            LEFT JOIN utility_bills ub 
                ON b.branch_id = ub.branch_id 
                AND ub.status = 1
                {year_condition}
            WHERE b.business_id = ? AND b.status = 1
            GROUP BY b.branch_id, b.branch_name
        """
        year_condition = ""
        params = []
        if year:
            year_condition = "AND ub.year = ?"
            sql = sql.format(year_condition=year_condition)
            params.append(int(year))
        else:
            sql = sql.format(year_condition="")
        params.append(business_id)
        cursor.execute(sql, tuple(params))

        rows = cursor.fetchall()
        data = [
            {
                "branch_id": row[0],
                "branch_name": row[1],
                "total_expense": float(row[2])
            } for row in rows
        ]
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# expense management page


@dashboard_bp.route('/expenses/all', methods=['POST'])
def get_all_expenses():
    identity = session.get('user')
    role_id = identity.get("role_id")
    business_id = identity.get("business_id")
    user_id = identity.get("user_id")

    data = request.json or {}
    page = data.get("page", 1)
    page_size = data.get("page_size", 10)

    filter_branch_id = data.get("branch_id")
    filter_year = data.get("year")
    filter_month = data.get("month")
    filter_utility_type_id = data.get("utility_type_id")

    try:
        conn = get_connection()
        cursor = conn.cursor()
        offset = (page - 1) * page_size

        query = """
            SELECT ub.id, b.branch_name, uet.utility_name, uet.category,
                   ub.year, ub.month, ub.units_used, ub.amount, ub.uploaded_at, u.username AS uploaded_by
            FROM utility_bills ub
            JOIN branches b ON ub.branch_id = b.branch_id
            JOIN utility_expense_types uet ON ub.utility_type_id = uet.id
            LEFT JOIN users u ON ub.uploaded_by = u.user_id
            WHERE 1 = 1 and ub.status = 1
        """
        params = []

        # Role-based filtering
        if role_id == 1:
            query += " AND b.business_id = ?"
            params.append(business_id)
        elif role_id == 2:
            cursor.execute(
                "SELECT branch_id, business_id FROM branches WHERE handled_by = ?", (user_id,))
            branch_row = cursor.fetchone()
            if not branch_row:
                return jsonify({"error": "No branch assigned or invalid user."}), 403
            branch_id, branch_business_id = branch_row
            if branch_business_id != business_id:
                return jsonify({"error": "Access denied: Mismatched business."}), 403

            query += " AND b.branch_id = ?"
            params.append(branch_id)
            filter_branch_id = None
        else:
            return jsonify({"error": "Unauthorized access."}), 403

        # Apply filters if provided
        if filter_branch_id:
            query += " AND b.branch_id = ?"
            params.append(filter_branch_id)
        if filter_year:
            query += " AND ub.year = ?"
            params.append(filter_year)
        if filter_month:
            query += " AND ub.month = ?"
            params.append(filter_month)
        if filter_utility_type_id:
            query += " AND ub.utility_type_id = ?"
            params.append(filter_utility_type_id)

        query += " ORDER BY ub.uploaded_at DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, page_size])

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        result = [
            {
                "expense_id": r[0],
                "branch_name": r[1],
                "utility_name": r[2],
                "category": r[3],
                "year": r[4],
                "month": r[5],
                "units_used": r[6],
                "amount": float(r[7]),
                "uploaded_at": str(r[8]),
                "uploaded_by": r[9],

            }
            for r in rows
        ]

        print("Filters received:", data)

        return jsonify({
            "page": page,
            "page_size": page_size,
            "expenses": result,
            "total_pages": 1  # Optional: you can add pagination count logic here if needed
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# expense management page
@dashboard_bp.route('/expenses/filters', methods=['GET'])
def get_expense_filters():
    identity = session.get('user')
    role_id = identity.get("role_id")
    business_id = identity.get("business_id")
    user_id = identity.get("user_id")

    try:
        conn = get_connection()
        cursor = conn.cursor()

    # Get relevant branches first
        if role_id == 1:
            cursor.execute("""
                SELECT branch_id, branch_name 
                FROM branches 
                WHERE business_id = ?
            """, (business_id,))
        elif role_id == 2:
            cursor.execute("""
                SELECT branch_id, branch_name 
                FROM branches 
                WHERE handled_by = ?
            """, (user_id,))
        else:
            return jsonify({"error": "Unauthorized access."}), 403

        branch_rows = cursor.fetchall()
        branch_ids = [r[0] for r in branch_rows]
        branches = [{"branch_id": r[0], "branch_name": r[1]}
                    for r in branch_rows]

        if not branch_ids:
            return jsonify({
                "years": [],
                "months": [],
                "utility_types": [],
                "branches": []
            }), 200

    # Get distinct years
        cursor.execute(f"""
            SELECT DISTINCT ub.year
            FROM utility_bills ub
            JOIN branches b ON ub.branch_id = b.branch_id
            WHERE ub.branch_id IN ({','.join('?' for _ in branch_ids)})
            ORDER BY ub.year DESC
        """, tuple(branch_ids))
        years = [row[0] for row in cursor.fetchall()]

    # Get distinct months
        cursor.execute(f"""
            SELECT DISTINCT ub.month
            FROM utility_bills ub
            JOIN branches b ON ub.branch_id = b.branch_id
            WHERE ub.branch_id IN ({','.join('?' for _ in branch_ids)})
        """, tuple(branch_ids))
        months = [row[0] for row in cursor.fetchall()]

    # Get all utility types
        cursor.execute("SELECT id, utility_name FROM utility_expense_types")
        utility_types = [{"id": r[0], "utility_name": r[1]}
                         for r in cursor.fetchall()]

        return jsonify({
            "years": years,
            "months": months,
            "utility_types": utility_types,
            "branches": branches
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# reports and analytics page
@dashboard_bp.route('/reports/profit-loss/summary', methods=['GET'])
def profit_loss_summary():
    year = request.args.get("year")
    month = request.args.get("month")
    identity = session.get('user')
    role_id = identity.get("role_id")
    business_id = identity.get("business_id")
    user_id = identity.get("user_id")

    if not all([year, month, role_id, business_id, user_id]):
        return jsonify({"error": "Missing parameters"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                b.branch_id,
                b.branch_name,
                ISNULL(SUM(bg.total_budget), 0) AS budget,
                ISNULL(SUM(ub.amount), 0) AS expense
            FROM branches b
            LEFT JOIN budget bg ON bg.branch_id = b.branch_id
            AND bg.status = 1
            AND CAST(bg.year AS INT) = ?
            AND CAST(bg.month AS INT) = ?

            LEFT JOIN utility_bills ub ON ub.branch_id = b.branch_id
            AND ub.status = 1
            AND CAST(ub.year AS INT) = ?
            AND CAST(ub.month AS INT) = ?

        """
        params = [year, month, year, month]
        print("== DEBUG Params ===")
        print("Params:", params)

        if role_id == 1:
            query += " WHERE b.business_id = ?"
            params.append(business_id)
        elif role_id == 2:
            query += " WHERE b.business_id = ? AND b.handled_by = ?"
            params.extend([business_id, user_id])
        else:
            return jsonify({"error": "Unauthorized"}), 403

        query += " GROUP BY b.branch_id, b.branch_name ORDER BY b.branch_name"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        print("=== DEBUG Rows ===")
        print(rows)

        summary = [{
            "branch_id": row[0],
            "branch_name": row[1],
            "budget": float(row[2]),
            "expense": float(row[3]),
            "profit_or_loss": float(row[2]) - float(row[3]),
            "status": "Profit" if float(row[2]) >= float(row[3]) else "Loss"
        } for row in rows]
        print("=== PROFIT/LOSS DEBUG ===")
        print("Params:", year, month, role_id, business_id)
        print("Result rows:", rows)

        return jsonify({
            "month": month,
            "year": year,
            "summary": summary
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# add in budget management


@dashboard_bp.route('/reports/budget-recommendation/<int:branch_id>', methods=['GET'])
def budget_recommendation(branch_id):
    identity = session.get('user')
    business_id = identity.get("business_id")
    role_id = identity.get("role_id")
    user_id = identity.get("user_id")
    target_year = request.args.get("year", type=int)
    target_month = request.args.get("month")

    print(role_id, business_id, user_id)
    if not all([business_id, role_id, user_id]):
        return jsonify({"error": "Missing parameters"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Access check
        cursor.execute(
            "SELECT business_id, handled_by FROM branches WHERE branch_id = ?", (branch_id,))
        branch = cursor.fetchone()
        if not branch:
            return jsonify({"error": "Branch not found"}), 404

        branch_business_id, handled_by = branch
        if branch_business_id != business_id or (role_id == 2 and handled_by != user_id):
            return jsonify({"error": "Unauthorized"}), 403

        cursor.execute("""
            WITH monthly AS (
            SELECT  year,
                month,
            SUM(amount) AS total_expense
            FROM    utility_bills
            WHERE   branch_id = ?     -- current branch
            AND   status     = 1
            GROUP BY year, month
        )
        SELECT TOP 6
           year,
           month,
           total_expense
        FROM   monthly
        ORDER  BY year DESC, month DESC;
    """, (branch_id,))

        rows = cursor.fetchall()
        print("⇢ 6‑month expense rows for branch", branch_id)
        for y, m, exp in rows:
            print(f"  • {y}-{str(m).zfill(2)}  →  Rs. {exp}")

        if not rows:
            return jsonify({"message": "Not enough data to predict."}), 200


# rows now look like:  [(2025, 7, 5467.00), (2025, 6, 5000.00), …]

        monthly_totals = [float(row[2]) for row in rows]   # 6 values
        six_month_sum = mean(monthly_totals)               # add them up
        recommended = round(six_month_sum * 1.05, 2)    # +5 % buffer

        return jsonify({
            "branch_id":          branch_id,
            "months_considered":  len(monthly_totals),        # up to 6
            "six_month_expenses": round(six_month_sum, 2),
            "recommended_budget": recommended,
            "note": "Last 6 months summed, plus 5% buffer"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()
