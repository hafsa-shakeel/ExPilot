from flask import Blueprint, request, jsonify, session
from umd_app.db import get_connection

business_bp = Blueprint('business_bp', __name__)


@business_bp.route('/test', methods=['GET'])
def test_route():
    return jsonify({"message": "route is working!"})


@business_bp.route('/delete/<int:business_id>', methods=['DELETE'])
def soft_delete_business(business_id):
    identity = session.get('user')
    current_user_role = identity.get('role_id')
    current_business_id = identity.get('business_id')
    # current_user_id = identity.get('user_id')

    print(">>> Update route hit", business_id)

    if current_user_role != 1:
        return jsonify({"error": "Unauthorized. Only admins can delete a business."}), 403

    if current_business_id != business_id:
        return jsonify({"error": "You can only delete your own business."}), 403

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Check business exists
        cursor.execute(
            "SELECT * FROM business WHERE business_id = ?", (business_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Business not found."}), 404

        # 2. Mark business as inactive
        cursor.execute(
            "UPDATE business SET status = 0 WHERE business_id = ?", (business_id,))

        # 3. Mark all users of the business as inactive
        cursor.execute(
            "UPDATE users SET status = 0 WHERE business_id = ?", (business_id,))

        conn.commit()
        return jsonify({"message": "Business and its users marked as inactive."}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@business_bp.route('/reactivate-business/<int:business_id>', methods=['PATCH'])
def reactivate_business(business_id):
    identity = session.get('user')
    current_user_role = identity.get('role_id')
    current_business_id = identity.get('business_id')

    print(">>> Update route hit", business_id)

    if current_user_role != 1:
        return jsonify({"error": "Unauthorized. Only admins can reactivate business."}), 403

    if current_business_id != business_id:
        return jsonify({"error": "You can only re-activate your own business."}), 403

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check business exists and is inactive
        cursor.execute(
            "SELECT status FROM business WHERE business_id = ?", (business_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Business not found."}), 404
        if row[0] == 1:
            return jsonify({"message": "Business is already active."}), 200

        # Reactivate business and associated data
        cursor.execute(
            "UPDATE business SET status = 1 WHERE business_id = ?", (business_id,))
        cursor.execute(
            "UPDATE users SET status = 1 WHERE business_id = ?", (business_id,))

        conn.commit()
        return jsonify({"message": "Business and users reactivated."}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@business_bp.route('/get-business', methods=['POST'])
def get_business_info():
    identity = session.get('user')
    current_user_role = identity.get('role_id')
    current_business_id = identity.get('business_id')

    if current_user_role != 1:
        return jsonify({"error": "Unauthorized. Only admins can access this data."}), 403

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT business_id, business_name, industry,email, contact_person, created_at, status
            FROM business
            WHERE business_id = ?
        """, (current_business_id,))

        business = cursor.fetchone()
        if not business:
            return jsonify({"error": "Business not found."}), 404

        keys = ['business_id', 'business_name', 'industry', 'email',
                'contact_person', 'created_at', 'status']

        business_dict = dict(zip(keys, business))

        return jsonify({"business_info": business_dict}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@business_bp.route('/update-business/<int:business_id>', methods=['PATCH'])
def update_business(business_id):
    identity = session.get('user')
    current_user_role = identity.get('role_id')
    current_business_id = identity.get('business_id')
    print(">>> Update route hit", business_id)

    if current_user_role != 1:
        return jsonify({"error": "Unauthorized. Only admin can update business info."}), 403

    if current_business_id != business_id:
        return jsonify({"error": "You can only update your own business."}), 403

    data = request.json
    business_name = data.get('business_name')
    industry = data.get('industry')
    contact_person = data.get('contact_person')

    updates = []
    values = []

    if 'business_name' in data:
        updates.append("business_name = ?")
        values.append(data['business_name'])
    if 'industry' in data:
        updates.append("industry = ?")
        values.append(data['industry'])
    if 'contact_person' in data:
        updates.append("contact_person = ?")
        values.append(data['contact_person'])

    if not updates:
        return jsonify({"error": "No valid fields to update."}), 400

    values.append(business_id)

    try:
        conn = get_connection()
        cursor = conn.cursor()

        update_query = f"UPDATE business SET {', '.join(updates)} WHERE business_id = ?"
        cursor.execute(update_query, values)
        conn.commit()

        return jsonify({"message": "Business updated successfully."}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()
