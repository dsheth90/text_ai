from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.model import RoleModel
from functools import wraps


def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            current_user = get_jwt_identity()
            roletype = RoleModel.is_admin(current_user)
            if roletype == 'Admin':
                return fn(*args, **kwargs)
            else:
                return {'Message': "Admins only access"}, 403
        return decorator
    return wrapper
