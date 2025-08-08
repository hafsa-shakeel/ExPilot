from flask import Blueprint, request, jsonify, session
from umd_app.db import get_connection
import pyodbc

branch_bp = Blueprint('branch_bp', __name__)
# token needed


@branch_bp.route('/branch-add', methods=['POST'])
def add_branch():
    identity = session.get('user')
    current_user_role = identity.get("role_id")
    current_business_id = identity.get("business_id")

    if current_user_role != 1:
        return jsonify({"error": "Only admins can add branches."}), 403
    data = request.json

    branch_name = data.get('branch_name')
    blocation = data.get('blocation')
    handled_by = data.get('handled_by')
    handled_by = int(handled_by) if handled_by else None

    if not branch_name:
        return jsonify({"error": "Missing required fields: branch_name."}), 400

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # check that branch manager belongs to same business
        if handled_by:
            cursor.execute("""
                SELECT user_id FROM users
                WHERE user_id = ? AND role_id = 2 AND business_id = ?
            """, (handled_by, current_business_id))

            manager = cursor.fetchone()
            if not manager:
                return jsonify({"error": "Assigned branch manager not found in your business."}), 400

        # check that manager is not assigned before
            cursor.execute("""
                SELECT user_id FROM users
                WHERE user_id = ? AND role_id = 2 AND business_id = ? AND availablecurrently = 1
            """, (handled_by, current_business_id))

            manager = cursor.fetchone()
            if not manager:
                return jsonify({"error": " Branch manager already assigned."}), 400

        # Insert branch
        cursor.execute("""
            INSERT INTO branches (branch_name, blocation, business_id, handled_by)
            VALUES (?, ?, ?, ?)
        """, (branch_name, blocation, current_business_id, handled_by))

        # Update branch manager's availability
        if handled_by:
            cursor.execute("""
                update users set availablecurrently = 0 where user_id = ?
            """, (handled_by,))

        print("Rows updated for availability:", cursor.rowcount)

        conn.commit()
        return jsonify({"message": "Branch added successfully and manager marked unavailable."}), 201

    except Exception as e:
        if conn:
            conn.rollback()
            print("Error in /branch-add:", str(e))
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# token needed in future


@branch_bp.route('/branch-managers/available', methods=['GET'])
def get_available_branch_managers():
    identity = session.get('user')
    current_user_role = identity.get("role_id")
    current_business_id = identity.get("business_id")

    if not identity:
        return jsonify({"error": "Session expired or unauthorized"}), 401

    if current_user_role != 1:
        return jsonify({"error": "Only admins can access this data."}), 403

    branch_id = request.args.get('branch_id', type=int)

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Step 1: Get available managers
        cursor.execute("""
            SELECT user_id, username, email, contact_no
            FROM users 
            WHERE role_id = 2 AND business_id = ? AND availablecurrently = 1 AND status = 1
        """, (current_business_id,))
        users = cursor.fetchall()

        managers_available = {
            row[0]: {
                "user_id": row[0],
                "username": row[1],
                "email": row[2],
                "contact_no": row[3]
            }
            for row in users
        }

        # Step 2: If branch_id provided, fetch the currently assigned manager
        if branch_id:
            cursor.execute("""
                SELECT u.user_id, u.username, u.email, u.contact_no
                FROM branches b
                JOIN users u ON b.handled_by = u.user_id
                WHERE b.branch_id = ? AND b.business_id = ? AND u.status = 1
            """, (branch_id, current_business_id))
            assigned = cursor.fetchone()

            if assigned:
                user_id = assigned[0]
                if user_id not in managers_available:
                    managers_available[user_id] = {
                        "user_id": assigned[0],
                        "username": assigned[1],
                        "email": assigned[2],
                        "contact_no": assigned[3]
                    }

        return jsonify({"available_branch_managers": list(managers_available.values())}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@branch_bp.route('/branches/', methods=['POST'])
def get_all_branches():
    identity = session.get('user')
    current_user_role = identity.get("role_id")
    current_business_id = identity.get("business_id")
    current_user_id = identity.get("user_id")

    print(current_user_id)
    data = request.json or {}

    page = data.get('page', 1)
    limit = data.get('limit', 10)
    offset = (page - 1) * limit

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Count total branches
        if current_user_role == 1:
            cursor.execute("""
                SELECT COUNT(*) FROM branches
                WHERE business_id = ?
            """, (current_business_id,))
            total = cursor.fetchone()[0]

            cursor.execute("""
                SELECT b.branch_id, b.branch_name, b.blocation, b.status, b.budget_alert_threshold,
                       u.username AS manager_name, u.email AS manager_email, b.created_at
                FROM branches b
                LEFT JOIN users u ON b.handled_by = u.user_id
                WHERE b.business_id = ?
                ORDER BY b.created_at DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, (current_business_id, offset, limit))

        elif current_user_role == 2:
            cursor.execute("""
                SELECT COUNT(*) FROM branches
                WHERE handled_by = ?
            """, (current_user_id,))
            total = cursor.fetchone()[0]

            cursor.execute("""
                SELECT b.branch_id, b.branch_name, b.blocation, b.status, b.budget_alert_threshold,
                       u.username AS manager_name, u.email AS manager_email, b.created_at
                FROM branches b
                LEFT JOIN users u ON b.handled_by = u.user_id
                WHERE b.handled_by = ?
                ORDER BY b.created_at DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, (current_user_id, offset, limit))

        else:
            return jsonify({"error": "Unauthorized access."}), 403

        branches = cursor.fetchall()
        columns = [col[0] for col in cursor.description]

        result = []
        for row in branches:
            row_dict = dict(zip(columns, row))
            row_dict["status"] = "Active" if row_dict["status"] == 1 else "Deactivated"
            result.append(row_dict)

        return jsonify({
            "page": page,
            "limit": limit,
            "total": total,
            "branches": result
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@branch_bp.route('/set-threshold/<int:branch_id>', methods=['PATCH'])
def set_budget_alert_threshold(branch_id):
    identity = session.get('user')
    role_id = identity.get("role_id")
    business_id = identity.get("business_id")

    if role_id not in [1, 2]:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.json
    new_threshold = data.get('threshold')

    if not isinstance(new_threshold, int) or not (1 <= new_threshold <= 100):
        return jsonify({'error': 'Threshold must be a number between 1 and 100'}), 400

    conn = get_connection()
    cursor = conn.cursor()

    if role_id == 2:
        manager_branch_id = identity.get("branch_id")
        manager_branch_id = identity.get("branch_id")
        if branch_id != manager_branch_id:
            return jsonify({'error': 'Forbidden: Not your branch'}), 403

        cursor.execute("""
            UPDATE branches
            SET budget_alert_threshold = ?
            WHERE branch_id = ? AND business_id = ?
        """, (new_threshold, branch_id, business_id))
    elif role_id == 1:
        cursor.execute("""
            UPDATE branches
            SET budget_alert_threshold = ?
            WHERE branch_id = ? AND business_id = ?
        """, (new_threshold, branch_id, business_id))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Threshold updated successfully'}), 200


# 3. Get Single Branch by ID/name - filter
@branch_bp.route('/branches_filter', methods=['GET'])
def get_branch():
    identity = session.get('user')
    current_user_role = identity.get("role_id")
    current_business_id = identity.get("business_id")
    current_user_id = identity.get("user_id")

    if current_user_role != 1:
        return jsonify({"error": "Unauthorised. Only admin can access."}), 403

    branch_id = request.args.get('id', type=int)
    branch_name = request.args.get('name', '')

    if not branch_id and not branch_name:
        return jsonify({"error": "Provide either branch 'id' or 'name'."}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        if branch_id:
            cursor.execute("""
                SELECT branch_id, branch_name, blocation, business_id, handled_by, created_at, status
                FROM branches
                WHERE branch_id = ?
            """, (branch_id,))
        else:
            cursor.execute("""
                SELECT branch_id, branch_name, blocation, business_id, handled_by, created_at, status
                FROM branches
                WHERE branch_name LIKE ? AND business_id = ?
            """, (f"%{branch_name}%", current_business_id))

        results = cursor.fetchall()

        if not results:
            return jsonify({"error": "No matching branch found."}), 404

        branches = []
        for row in results:
            b_id, b_name, blocation, b_biz_id, handled_by, created_at, status = row

            # Access control
            if current_user_role == 1 and current_business_id != b_biz_id:
                continue
            if current_user_role == 2 and current_user_id != handled_by:
                continue

            branches.append({
                "branch_id": b_id,
                "branch_name": b_name,
                "blocation": blocation,
                "business_id": b_biz_id,
                "handled_by": handled_by,
                "created_at": created_at,
                "status": status
            })

        if not branches:
            return jsonify({"error": "No authorized branches found."}), 403

        return jsonify({"branches": branches}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# update route


@branch_bp.route('/branches/update/<int:branch_id>', methods=['PATCH'])
def update_branch(branch_id):
    identity = session.get('user')
    current_user_role = identity.get("role_id")
    current_business_id = identity.get("business_id")

    if current_user_role != 1:
        return jsonify({"error": "Only admin can update branches."}), 403

    data = request.json
    branch_name = data.get('branch_name')
    blocation = data.get('blocation')
    handled_by = data.get('handled_by')  # can be None

    if not branch_name or not blocation:
        return jsonify({"error": "Fields required: branch_name and blocation"}), 400

    conn, cursor = None, None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Confirm branch exists and belongs to business
        cursor.execute(
            "SELECT handled_by, business_id FROM branches WHERE branch_id = ?", (branch_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"error": "Branch not found."}), 404

        old_manager, branch_business_id = result
        if branch_business_id != current_business_id:
            return jsonify({"error": "Unauthorized."}), 403

        # If a new manager is selected, validate it
        if handled_by:
            if handled_by != old_manager:
                cursor.execute("""
                    SELECT user_id FROM users
                    WHERE user_id = ? AND business_id = ? AND role_id = 2 AND availablecurrently = 1 AND status = 1
                """, (handled_by, current_business_id))
                if not cursor.fetchone():
                    return jsonify({"error": "Branch manager not valid or already assigned."}), 400

        # Update branch with nullable handled_by
        cursor.execute("""
            UPDATE branches
            SET branch_name = ?, blocation = ?, handled_by = ?
            WHERE branch_id = ?
        """, (branch_name, blocation, handled_by if handled_by else None, branch_id))

        # Update availability if the manager was changed
        if old_manager and old_manager != handled_by:
            cursor.execute(
                "UPDATE users SET availablecurrently = 1 WHERE user_id = ?", (old_manager,))
        if handled_by and handled_by != old_manager:
            cursor.execute(
                "UPDATE users SET availablecurrently = 0 WHERE user_id = ?", (handled_by,))

        conn.commit()
        return jsonify({"message": "Branch updated successfully."}), 200

    except pyodbc.IntegrityError:
        return jsonify({"error": "This manager is already handling another branch."}), 400

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@branch_bp.route('/branches/<int:branch_id>', methods=['DELETE'])
def soft_delete_branch(branch_id):
    identity = session.get('user')
    current_user_role = identity.get("role_id")
    current_business_id = identity.get("business_id")

    if current_user_role != 1:
        return jsonify({"error": "Only admins can delete branches."}), 403

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Fetch branch and validate ownership
        cursor.execute("""
            SELECT business_id, handled_by FROM branches WHERE branch_id = ?
        """, (branch_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({"error": "Branch not found."}), 404

        branch_business_id, handled_by = row

        if branch_business_id != current_business_id:
            return jsonify({"error": "Unauthorized. You can only delete branches from your own business."}), 403

        # Soft delete the branch
        cursor.execute("""
            UPDATE branches SET status = 0, handled_by = NULL WHERE branch_id = ?
        """, (branch_id,))

        # Mark the previous manager as available again
        if handled_by:
            cursor.execute("""
                UPDATE users SET availablecurrently = 1 WHERE user_id = ?
            """, (handled_by,))

        conn.commit()
        return jsonify({"message": f"Branch {branch_id} soft-deleted and manager unassigned."}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@branch_bp.route('/reactivate/<int:branch_id>', methods=['PATCH'])
def reactivate_branch(branch_id):
    identity = session.get('user')
    current_user_role = identity.get("role_id")
    current_business_id = identity.get("business_id")

    if current_user_role != 1:
        return jsonify({"error": "Only admins can reactivate branches."}), 403

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT business_id, status FROM branches WHERE branch_id = ?
        """, (branch_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({"error": "Branch not found."}), 404

        branch_business_id, branch_status = row

        if branch_business_id != current_business_id:
            return jsonify({"error": "Unauthorized. You can only reactivate branches of your business."}), 403

        if branch_status == 1:
            return jsonify({"message": "Branch is already active."}), 200

        cursor.execute("""
            UPDATE branches SET status = 1 WHERE branch_id = ?
        """, (branch_id,))
        conn.commit()

        return jsonify({"message": f"Branch ID {branch_id} reactivated successfully."}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
