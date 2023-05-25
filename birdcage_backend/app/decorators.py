# app/decorators.py
from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity


def admin_required(fn):
    @jwt_required()
    @wraps(fn)  # Add this line to preserve the original function name
    def wrapper(*args, **kwargs):
        if get_jwt_identity() != 'admin':
            return jsonify({"msg": "Admin access required"}), 403
        return fn(*args, **kwargs)

    return wrapper
