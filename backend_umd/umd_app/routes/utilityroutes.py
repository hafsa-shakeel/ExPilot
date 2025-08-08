from flask import Blueprint, request, jsonify, session, send_from_directory
from umd_app.db import get_connection
import os
from werkzeug.utils import secure_filename
from flask import current_app
import uuid
from datetime import datetime

utility_bp = Blueprint('utility_bp', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'csv', 'jpg', 'jpeg', 'png'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@utility_bp.route('/expense_utility_types', methods=['GET'])
def get_expense_utility_types():

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, utility_name, category
            FROM utility_expense_types
            ORDER BY utility_name
        """)

        rows = cursor.fetchall()

        result = [
            {
                "id": row[0],
                "utility_name": row[1],
                "category": row[2]
            }
            for row in rows
        ]

        return jsonify({"utility_types": result}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@utility_bp.route('/utility-bills/upload', methods=['POST'])
def upload_utility_bill():
    identity = session.get('user')
    role_id = identity.get("role_id")
    business_id = identity.get("business_id")
    branch_id = identity.get("branch_id")
    print("Session identity:", identity)

    data = request.form
    file = request.files.get('media_file')
    utility_type_id = data.get("utility_type_id", type=int)
    year = data.get("year")
    month = data.get("month")
    units_used = data.get("units_used")
    amount = data.get("amount")
    uploaded_by = identity.get("user_id")
    media_type = data.get("media_type")

    print("Received fields:")
    print("branch_id", branch_id)
    print("utility_type_id", utility_type_id)
    print("year", year)
    print("month", month)
    print("amount", amount)
    print("uploaded_by", uploaded_by)
    print("business_id", business_id)

    branch_id = identity.get("branch_id")
    if not branch_id:
        branch_id = request.form.get("branch_id", type=int)
    if not all([branch_id, utility_type_id, year, month, amount, uploaded_by, business_id]):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Verify branch ownership
        cursor.execute("""
            SELECT business_id, handled_by FROM branches WHERE branch_id = ?
        """, (branch_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({"error": "Branch not found"}), 404

        branch_business_id, handled_by = row

        if branch_business_id != business_id:
            return jsonify({"error": "You do not have access to this branch"}), 403

        if role_id == 2 and handled_by != uploaded_by:
            return jsonify({"error": "You can only upload bills for your own branch"}), 403

        # Insert utility bill
        cursor.execute("""
            INSERT INTO utility_bills (branch_id, utility_type_id, year, month, units_used, amount, uploaded_by)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (branch_id, utility_type_id, year, month, units_used, amount, uploaded_by))
        bill_id = cursor.fetchone()[0]

        # Save media file
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            filepath = os.path.join(
                current_app.config['UPLOAD_FOLDER'], unique_filename)
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(filepath)

            cursor.execute("""
                INSERT INTO media (media_name, media_path, uploaded_by, business_id, branch_id, utility_bill_id, media_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (unique_filename, unique_filename, uploaded_by, business_id, branch_id, bill_id, media_type))

        # === BUDGET CHECK ===
        cursor.execute("""
            SELECT ISNULL(SUM(total_budget), 0)
            FROM budget
            WHERE branch_id = ? AND year = ? AND month = ? AND status = 1
        """, (branch_id, year, month))
        total_budget = float(cursor.fetchone()[0])
        count = 1 if total_budget > 0 else 0

        cursor.execute("""
            SELECT ISNULL(SUM(amount), 0)
            FROM utility_bills
            WHERE branch_id = ? AND year = ? AND month = ? AND status = 1
        """, (branch_id, year, month))
        total_expenses = float(cursor.fetchone()[0])

        cursor.execute("""
            SELECT budget_alert_threshold FROM branches WHERE branch_id = ?
        """, (branch_id,))
        threshold_row = cursor.fetchone()
        threshold = threshold_row[0] if threshold_row and threshold_row[0] is not None else 90

        if count == 0:
            message = "No budget defined for this period"
            cursor.execute("""
                INSERT INTO alerts (branch_id, utility_bill_id, alert_type, severity, message)
                VALUES (?, ?, 'missing_budget', 'High', ?)
            """, (branch_id, bill_id, message))
        else:
            if total_expenses >= (threshold / 100) * total_budget:
                message = f"{threshold}% of the budget consumed: Rs. {total_expenses} of Rs. {total_budget}"
                cursor.execute("""
                    INSERT INTO alerts (branch_id, utility_bill_id, alert_type, severity, message)
                    VALUES (?, ?, 'budget_warning', 'medium', ?)
                """, (branch_id, bill_id, message))

        conn.commit()
        return jsonify({"message": "Utility bill and media uploaded", "bill_id": bill_id}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# show all utilities present
@utility_bp.route('/utility-bills/all', methods=['POST'])
def get_all_utilities():
    data = request.get_json()
    identity = session.get('user')
    role_id = identity.get("role_id")
    business_id = identity.get("business_id")
    user_id = identity.get("user_id")
    page = data.get("page", 1)
    page_size = data.get("page_size", 10)
    offset = (page - 1) * page_size

    if not all([role_id, business_id]):
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT ub.id, b.branch_name, uet.utility_name, uet.category,
                ub.year, ub.month, ub.units_used, ub.amount, ub.uploaded_at
            FROM utility_bills ub
            JOIN branches b ON ub.branch_id = b.branch_id
            JOIN utility_expense_types uet ON ub.utility_type_id = uet.id
            WHERE ub.status = 1
        """
        params = []

        if role_id == 1:
            query += " AND b.business_id = ?"
            params.append(business_id)
        elif role_id == 2:
            query += " AND b.business_id = ? AND b.handled_by = ?"
            params.extend([business_id, user_id])
        else:
            return jsonify({"error": "Unauthorized"}), 403

        query += " ORDER BY ub.uploaded_at DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, page_size])

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        results = [{
            "id": r[0],
            "branch_name": r[1],
            "utility_name": r[2],
            "category": r[3],
            "year": r[4],
            "month": r[5],
            "units_used": r[6],
            "amount": float(r[7]),
            "uploaded_at": str(r[8])
        } for r in rows]

        return jsonify({"utilities": results, "page": page, "page_size": page_size}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

# filtering of utilities


@utility_bp.route('/utility-bills/filter', methods=['POST'])
def filter_utilities():
    data = request.get_json()
    identity = session.get('user')
    role_id = identity.get("role_id")
    business_id = identity.get("business_id")
    user_id = identity.get("user_id")

# filters
    branch_id = data.get("branch_id")
    year = data.get("year")
    month = data.get("month")

    page = data.get("page", 1)
    page_size = data.get("page_size", 10)
    offset = (page - 1) * page_size

    if not all([role_id, business_id]):
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT ub.id, b.branch_name, uet.utility_name, uet.category,
                   ub.year, ub.month, ub.units_used, ub.amount, ub.uploaded_at
            FROM utility_bills ub
            JOIN branches b ON ub.branch_id = b.branch_id
            JOIN utility_expense_types uet ON ub.utility_type_id = uet.id
            WHERE ub.status = 1
        """
        params = []

        # Access control filters
        if role_id == 1:
            query += " AND b.business_id = ?"
            params.append(business_id)
        elif role_id == 2:
            query += " AND b.business_id = ? AND b.handled_by = ?"
            params.extend([business_id, user_id])
        else:
            return jsonify({"error": "Unauthorized"}), 403

        # Optional filters
        if branch_id:
            query += " AND ub.branch_id = ?"
            params.append(branch_id)

        if year:
            query += " AND ub.year = ?"
            params.append(year)

        if month:
            query += " AND ub.month = ?"
            params.append(month)

        # Pagination
        query += " ORDER BY ub.uploaded_at DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, page_size])

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        results = [{
            "id": r[0],
            "branch_name": r[1],
            "utility_name": r[2],
            "category": r[3],
            "year": r[4],
            "month": r[5],
            "units_used": r[6],
            "amount": float(r[7]),
            "uploaded_at": str(r[8])
        } for r in rows]

        return jsonify({
            "utilities": results,
            "page": page,
            "page_size": page_size
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@utility_bp.route('/utility-bills/<int:utility_id>', methods=['GET'])
def get_utility_detail(utility_id):
    identity = session.get('user')
    role_id = identity.get("role_id")
    business_id = identity.get("business_id")
    user_id = identity.get("user_id")

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ub.id, b.branch_name, b.business_id, b.handled_by,
                    uet.utility_name, uet.category, ub.year, ub.month,
                    ub.units_used, ub.amount, ub.uploaded_at, u.username, u.email
            FROM utility_bills ub
            JOIN branches b ON ub.branch_id = b.branch_id
            JOIN utility_expense_types uet ON ub.utility_type_id = uet.id
            LEFT JOIN users u ON ub.uploaded_by = u.user_id
            WHERE ub.id = ? AND ub.status = 1
        """, (utility_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({"error": "Utility not found"}), 404

        (
            id, branch_name, branch_business_id, handled_by,
            utility_name, category, year, month,
            units_used, amount, uploaded_at, username, email
        ) = row

        if role_id == 1 and branch_business_id != business_id:
            return jsonify({"error": "Unauthorized"}), 403
        if role_id == 2 and (branch_business_id != business_id or handled_by != user_id):
            return jsonify({"error": "Unauthorized"}), 403

        return jsonify({
            "id": id,
            "branch_name": branch_name,
            "utility_name": utility_name,
            "category": category,
            "year": year,
            "month": month,
            "units_used": units_used,
            "amount": float(amount),
            "uploaded_at": str(uploaded_at),
            "uploaded_by": username or email
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# media preview


UPLOAD_FOLDER = 'uploads/media'  # Ensure this folder exists
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads', 'media')


@utility_bp.route('/media/<int:image_id>', methods=['GET'])
def get_media_by_id(image_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT media_path FROM media WHERE id = ? AND status = 1", (image_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({"error": "Image not found"}), 404

        filename = row[0]
        return send_from_directory(UPLOAD_FOLDER, filename)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@utility_bp.route('/utility-bills/<int:utility_id>/media', methods=['PATCH'])
def update_utility_media(utility_id):
    identity = session.get('user')
    business_id = identity.get("business_id")

    file = request.files.get('media_file')
    media_type = request.form.get('media_type')
    uploaded_by = request.form.get('uploaded_by', type=int)

    if not all([file, media_type, uploaded_by, business_id]):
        return jsonify({"error": "Missing required fields"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    filepath = os.path.join(
        current_app.config['UPLOAD_FOLDER'], unique_filename)

    try:
        conn = get_connection()
        cursor = conn.cursor()

    # Soft delete previous media
        cursor.execute(
            "DELETE FROM media WHERE utility_bill_id = ?", (utility_id,))

    # Save new media
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(filepath)

        cursor.execute("""
            INSERT INTO media (media_name, media_path, media_type, uploaded_by, business_id, utility_bill_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (filename, filepath, media_type, uploaded_by, business_id, utility_id))

        conn.commit()
        return jsonify({"message": "Media updated successfully."}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# soft-deleting a utilitybill


@utility_bp.route('/utility-bills/delete/<int:utility_id>', methods=['DELETE'])
def soft_delete_utility_bill(utility_id):
    identity = session.get("user")
    if not identity:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE utility_bills SET status = 0 WHERE id = ?
        """, (utility_id,))

        if cursor.rowcount == 0:
            return jsonify({"error": "Utility not found"}), 404

        conn.commit()
        return jsonify({"message": "Utility bill deleted successfully."}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
