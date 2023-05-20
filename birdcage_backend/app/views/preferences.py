from flask import Blueprint, request, jsonify
import sqlite3
from config import DATABASE_FILE
from ..models.preferences import check_password
from functools import wraps
import bcrypt

preferences_blueprint = Blueprint('preferences', __name__)


def password_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        password_input = request.headers.get('X-Password')
        if password_input is None:
            return jsonify({"error": "Password header is missing"}), 401
        if not check_password(password_input):
            return jsonify({"error": "Invalid password"}), 403
        return f(*args, **kwargs)
    return decorated_function


@preferences_blueprint.route('/api/preferences/<int:user_id>', methods=['GET'])
def get_preferences(user_id):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('SELECT preference_key, preference_value FROM user_preferences WHERE user_id = ?', (user_id,))
    preferences = cursor.fetchall()

    preferences_dict = {key: value for (key, value) in preferences}

    connection.close()

    return jsonify(preferences_dict)


def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."

    return True, None


# Add a validation function to check preference constraints
def validate_preference(preference_key, preference_value):
    if preference_key == 'password':
        return validate_password(preference_value)

    try:
        numeric_value = float(preference_value)
    except ValueError:
        return False, "Value must be numeric."

    constraints = {
        "recordinglength": (3, 120),
        "confidence": (0, 1),
        "extractionlength": (3, 120),
        "latitude": (-90, 90),
        "longitude": (-180, 180),
        "overlap": (0, 2.9),
        "sensitivity": (0.5, 1.5),
        "sf_thresh": (0.01, 0.99),
    }

    if preference_key not in constraints:
        return False, "Invalid preference key."

    min_value, max_value = constraints[preference_key]

    if not (min_value <= numeric_value <= max_value):
        return False, f"Value must be between {min_value} and {max_value}."

    return True, None


@preferences_blueprint.route('/api/preferences', methods=['POST'])
@password_required
def set_preference():
    data = request.get_json()

    user_id = data['user_id']
    preference_key = data['preference_key']
    preference_value = data['preference_value']

    # Validate the preference before inserting into the database
    is_valid, error_message = validate_preference(preference_key, preference_value)
    if not is_valid:
        return jsonify({"error": error_message}), 400

    # Hash the password if the preference_key is 'password'
    if preference_key == 'password':
        preference_value = bcrypt.hashpw(preference_value.encode(), bcrypt.gensalt()).decode()

    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute(
        'INSERT OR REPLACE INTO user_preferences (user_id, preference_key, preference_value, last_updated) VALUES (?, ?, ?, datetime())',
        (user_id, preference_key, preference_value))

    connection.commit()
    connection.close()

    if preference_key == 'password':
        return jsonify({"message": "Password set successfully."})
    else:
        return jsonify({"message": "Preference set successfully."})


@preferences_blueprint.route('/api/preferences/<int:user_id>/<string:preference_key>', methods=['DELETE'])
def delete_preference(user_id, preference_key):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('DELETE FROM user_preferences WHERE user_id = ? AND preference_key = ?', (user_id, preference_key))

    connection.commit()
    connection.close()

    return jsonify({"message": "Preference deleted successfully."})
