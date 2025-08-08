from umd_app.db import get_connection  # adjust import if needed
from datetime import timedelta
from flask import Blueprint, request, jsonify, session
# from umd_app.models.user_model import cleanup_user_references
from umd_app.db import get_connection
import bcrypt

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/test', methods=['GET'])
def test_route():
    return jsonify({"message": "Auth route is working!"})


@auth_bp.route('/me', methods=['GET'])
def get_logged_in_user():
    user = session.get('user')
    return jsonify({"user": user}), 200


@auth_bp.route('/register-business', methods=['POST'])
def register_business():
    print("Register Business route hit!")

    data = request.json
    business_name = data.get('business_name')
    industry = data.get('industry')
    contact_person = data.get('contact_person')
    user_email = data.get('user_email')  # Also used as business email
    username = data.get('username')
    contact_no = data.get('contact_no')
    raw_password = data.get('password')

    if not all([business_name, industry, contact_person, user_email, username, contact_no, raw_password]):
        return jsonify({"error": "Missing required fields."}), 400

    hashed_password = bcrypt.hashpw(raw_password.encode(
        'utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check if business with same name/email exists
        cursor.execute("""
            SELECT business_id FROM business WHERE business_name = ? OR email = ?
        """, (business_name, user_email))
        existing = cursor.fetchone()
        if existing:
            return jsonify({"error": "A business with this name or email already exists."}), 409

        # Insert business with pending status
        cursor.execute("""
            INSERT INTO business (business_name, industry, email, contact_person, req_status)
            OUTPUT INSERTED.business_id
            VALUES (?, ?, ?, ?, 'pending')
        """, (business_name, industry, user_email, contact_person))
        business_id = cursor.fetchone()[0]

        # Store admin info in pending_admins table
        cursor.execute("""
            INSERT INTO pending_admins (username, user_email, contact_no, password, business_id)
            VALUES (?, ?, ?, ?, ?)
        """, (username, user_email, contact_no, hashed_password, business_id))

        conn.commit()
        return jsonify({"message": "We have received your request! Wait till we approve it."}), 201

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@auth_bp.route('/approve-business/<int:business_id>', methods=['POST'])
def approve_business(business_id):
    current_user = session.get('user')
    if not current_user or current_user.get("role_id") != 3:
        return jsonify({"error": "Unauthorized. SuperAdmin only."}), 403

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check if business exists and is pending
        cursor.execute("""
            SELECT req_status FROM business WHERE business_id = ?
        """, (business_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "Business not found."}), 404
        if result[0] != 'pending':
            return jsonify({"error": "Business is already approved or rejected."}), 400

        # Get pending admin info
        cursor.execute("""
            SELECT username, user_email, contact_no, password FROM pending_admins
            WHERE business_id = ?
        """, (business_id,))
        admin_data = cursor.fetchone()
        if not admin_data:
            return jsonify({"error": "No pending admin data found for this business."}), 404

        username, user_email, contact_no, hashed_password = admin_data

        # Insert into users table with role_id = 1 (admin)
        cursor.execute("""
            INSERT INTO users (username, email, contact_no, userpassword, role_id, business_id)
            VALUES (?, ?, ?, ?, 1, ?)
        """, (username, user_email, contact_no, hashed_password, business_id))

        # Update business status to approved
        cursor.execute("""
            UPDATE business SET req_status = 'approved' WHERE business_id = ?
        """, (business_id,))

        # Delete from pending_admins
        cursor.execute("""
            DELETE FROM pending_admins WHERE business_id = ?
        """, (business_id,))

        conn.commit()
        return jsonify({"message": "Business approved and admin created successfully."}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@auth_bp.route('/reject-business/<int:business_id>', methods=['POST'])
def reject_business(business_id):
    current_user = session.get('user')
    if not current_user or current_user.get("role_id") != 3:
        return jsonify({"error": "Unauthorized. SuperAdmin only."}), 403

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check business exists and is pending
        cursor.execute("""
            SELECT req_status FROM business WHERE business_id = ?
        """, (business_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "Business not found."}), 404
        if result[0] != 'pending':
            return jsonify({"error": "Business already approved or rejected."}), 400

        # Update business status
        cursor.execute("""
            UPDATE business SET req_status = 'rejected' WHERE business_id = ?
        """, (business_id,))

        # Delete pending admin
        cursor.execute("""
            DELETE FROM pending_admins WHERE business_id = ?
        """, (business_id,))

        conn.commit()
        return jsonify({"message": "Business request rejected successfully."}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@auth_bp.route('/users', methods=['GET'])
def get_all_users_in_business():
    identity = session.get('user')
    current_user_role = identity.get("role_id")
    business_id = identity.get("business_id")
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=10, type=int)
    offset = (page - 1) * limit

    # check if it's an admin
    if current_user_role != 1:
        return jsonify({"error": "Only admins can view users."}), 403

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Get total count of users for this business
        cursor.execute("""
            SELECT COUNT(*) FROM users WHERE business_id = ?
        """, (business_id,))
        total_users = cursor.fetchone()[0]

        # Now fetch only the paginated users
        cursor.execute("""
            SELECT user_id, username, email, contact_no, role_id
            FROM users
            WHERE business_id = ?
            ORDER BY user_id
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """, (business_id, offset, limit))
        users = cursor.fetchall()

        user_list = [
            {
                "user_id": row[0],
                "username": row[1],
                "email": row[2],
                "contact_no": row[3],
                "role_id": row[4]
            }
            for row in users
        ]

        return jsonify({
            "page": page,
            "limit": limit,
            "total_users": total_users,
            "total_pages": (total_users + limit - 1) // limit,
            "users": user_list
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@auth_bp.route('/add-user', methods=['POST'])
def add_user():
    identity = session.get('user')
    current_user_role = identity.get("role_id")
    business_id = identity.get("business_id")
    data = request.json

    # Allow only Admins
    if current_user_role != 1:
        return jsonify({"error": "Unauthorized. Only admins can add users."}), 403

    conn = None
    cursor = None

    try:
        username = data.get('username')
        email = data.get('email')
        contact_no = data.get('contact_no')
        password = data.get('password')
        role_id = data.get('role_id')

        # ✅ No need to check for business_id from frontend anymore
        if not all([username, email, contact_no, password, role_id]):
            return jsonify({"error": "Missing required fields."}), 400

        conn = get_connection()
        cursor = conn.cursor()

        # Check for duplicates
        cursor.execute("""
            SELECT user_id FROM users WHERE username = ? OR email = ?
        """, (username, email))
        existing_user = cursor.fetchone()
        if existing_user:
            return jsonify({"error": "A user with this username or email already exists."}), 409

        # Hash password
        hashed_pw = bcrypt.hashpw(password.encode(
            'utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Insert new user
        cursor.execute("""
            INSERT INTO users (username, email, contact_no, userpassword, role_id, business_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, email, contact_no, hashed_pw, role_id, business_id))

        conn.commit()
        return jsonify({"message": "User added successfully."}), 201

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@auth_bp.route('/delete-user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    identity = session.get('user')
    current_user_role = identity.get("role_id")
    current_business_id = identity.get("business_id")
    current_user_id = identity.get("user_id")

# check that it's the admin that can delete only
    if current_user_role != 1:
        return jsonify({"error": "Unauthorized. Only admins can delete users."}), 403

# prevention for admin to NOT delete his own account!!
    if current_user_id == user_id:
        return jsonify({"error": "You cannot delete your own admin account."}), 400

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Check if user exists and belongs to same business
        cursor.execute("""
            SELECT role_id, business_id FROM users WHERE user_id = ?
        """, (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found."}), 404

        target_role_id, target_business_id = user

        # 2. Prevent deleting admins of other business
        if target_role_id == 1:
            return jsonify({"error": "Cannot delete other admins."}), 403

        # 3. Check if target user is in the same business, if not give error
        if target_business_id != current_business_id:
            return jsonify({"error": "You can only delete users from your own business."}), 403

        # 4. Safe to delete
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()
        return jsonify({"message": f"User ID {user_id} deleted successfully."}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@auth_bp.route('/update-user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    identity = session.get('user')
    current_user_role = identity.get("role_id")
    current_business_id = identity.get("business_id")
    data = request.json or {}

    if current_user_role != 1:
        return jsonify({"error": "Unauthorized. Only admins can update users."}), 403

    email = data.get('email')
    username = data.get('username')
    contact_no = data.get('contact_no')
    role_id = data.get('role_id')
    # password = data.get('password')

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

    # Check if the user exists and belongs to same business
        cursor.execute(
            "SELECT business_id, role_id FROM users WHERE user_id = ?", (user_id,))
        user_row = cursor.fetchone()
        if not user_row:
            return jsonify({"error": "User not found."}), 404

        target_user_business_id, target_user_role_id = user_row

# cannot update admin
        if target_user_role_id == 1:
            return jsonify({"error": "Admins cannot be updated via this endpoint."}), 403
# user to be updated is not present in the business, can't delete from other business
        if target_user_business_id != current_business_id:
            return jsonify({"error": "Unauthorized. Cannot modify users from other businesses."}), 403

        fields = []
        values = []

        if email:
            fields.append("email = ?")
            values.append(email)
        if username:
            fields.append("username = ?")
            values.append(username)
        if contact_no:
            fields.append("contact_no = ?")
            values.append(contact_no)
        if role_id:
            fields.append("role_id = ?")
            values.append(role_id)

        if not fields:
            return jsonify({"error": "No fields to update."}), 400

        values.append(user_id)
        update_query = f"UPDATE users SET {', '.join(fields)} WHERE user_id = ?"
        cursor.execute(update_query, values)
        conn.commit()

        return jsonify({"message": f"User ID {user_id} updated successfully."}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    print("Login route hit")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Fetch user info
        cursor.execute("""
            SELECT user_id, username, userpassword, role_id, business_id
            FROM users
            WHERE email = ?
        """, (email,))
        row = cursor.fetchone()

        if not row:
            return jsonify({"error": "Invalid email or password"}), 401

        user_id, username, hashed_password, role_id, business_id = row

        if not bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
            return jsonify({"error": "Invalid email or password"}), 401

        # Get branch_id for branch managers (role_id == 2)
        branch_id = None
        if role_id == 2:
            cursor.execute(
                "SELECT branch_id FROM branches WHERE handled_by = ?", (user_id,))
            branch_row = cursor.fetchone()
            if branch_row:
                branch_id = branch_row[0]

        # Store session
        session.permanent = True  # So session lasts beyond browser close
        session['user'] = {
            "user_id": user_id,
            "username": username,
            "role_id": role_id,
            "business_id": business_id,
            "branch_id": branch_id
        }

        print("Session created for:", session['user'])
        # identity = session.get('user')print("Session Identity:", identity)

        return jsonify({
            "message": "Login successful",
            "user": session['user']
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route('/permissions', methods=['GET'])
def get_permissions():
    role_id = request.args.get('role_id', type=int)

    if not role_id:
        return jsonify({"error": "Missing role_id"}), 400

    # Define permissions based on role
    if role_id == 1:  # Admin
        permissions = {
            "can_add_users": True,
            "can_delete_users": True,
            "can_manage_branches": True,
            "can_view_all_branches": True,
            "can_upload_bills": False,
            "can_view_dashboard": True
        }
    elif role_id == 2:  # Branch Manager
        permissions = {
            "can_add_users": False,
            "can_delete_users": False,
            "can_manage_branches": False,
            "can_view_all_branches": False,
            "can_upload_bills": True,
            "can_view_dashboard": True
        }
    else:
        return jsonify({"error": "Invalid role_id"}), 403

    return jsonify({"permissions": permissions}), 200


# 1. View All Businesses


@auth_bp.route('/businesses', methods=['GET'])
def view_all_businesses():
    identity = session.get('user')
    print("Session Identity:", identity)

    if not identity or not isinstance(identity, dict):
        return jsonify({"error": "Unauthorized"}), 403

    # Only allow SuperAdmin (role_id = 3)
    if identity.get("role_id") != 3:
        return jsonify({"error": "Unauthorized - Super Admins only"}), 403

    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT business_id, business_name, industry, email, contact_person, status, req_status
            FROM business
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        businesses = [
            {
                "business_id": row[0],
                "business_name": row[1],
                "industry": row[2],
                "email": row[3],
                "contact_person": row[4],
                "status": row[5],
                "req_status": row[6]
            }
            for row in rows
        ]

        return jsonify({"businesses": businesses}), 200

    except Exception as e:
        print("Error fetching businesses:", str(e))
        return jsonify({"error": "Internal server error"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@auth_bp.route('/businesses/<int:business_id>', methods=['GET'])
def view_business_detail(business_id):
    identity = session.get('user')
    print("Session identity in view_business_detail:", identity)

    # Session check and role check
    if not identity or identity.get("role_id") != 3:
        return jsonify({"error": "Unauthorized - Super Admins only"}), 403

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Business info
        cursor.execute("""
            SELECT business_name, industry, email, contact_person, status, req_status
            FROM business WHERE business_id = ?
        """, (business_id,))
        business = cursor.fetchone()
        if not business:
            return jsonify({"error": "Business not found"}), 404

        # Count branches
        cursor.execute(
            "SELECT COUNT(*) FROM branches WHERE business_id = ?", (business_id,))
        branch_count = cursor.fetchone()[0]

        # Count users
        cursor.execute(
            "SELECT COUNT(*) FROM users WHERE business_id = ?", (business_id,))
        user_count = cursor.fetchone()[0]

        # print("Fetched business row:", business[4])

        return jsonify({
            "business": {
                "business_id": business_id,
                "business_name": business[0],
                "industry": business[1],
                "email": business[2],
                "contact_person": business[3],
                "status": "Active" if business[4] else "Inactive",
                "req_status": business[5]


            },
            "total_branches": branch_count,
            "total_users": user_count
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
