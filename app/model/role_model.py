from flask import jsonify
from functools import wraps
from db import db
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from ..model import UserModel


class RoleModel(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    user_id_fk = db.Column(db.String(80), db.ForeignKey('users.id'))
    role_type = db.Column(db.String(80), nullable=False)

    def __init__(self, user_id, role_type):
        self.user_id_fk = user_id
        self.role_type = role_type

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_role_type(cls, user_id):
        return cls.query.filter_by(user_id_fk=user_id).first()

    @classmethod
    def is_admin(cls, current_user):
        user_id = UserModel.find_by_username(current_user)
        output = db.session.query(RoleModel).join(UserModel).filter(UserModel.id == user_id.id).all()
        return str(output[0].role_type)
