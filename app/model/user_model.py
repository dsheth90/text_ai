from db import db
from passlib.hash import pbkdf2_sha256 as sha256
from .training_model import TrainingModel
from .task_result_model import TaskResultModel
import datetime
from datetime import date
from sqlalchemy import func, and_
import sqlalchemy as sa


class UserModel(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(20), primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email_address = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(80), nullable=False)
    created_on = db.Column(db.DateTime(), default=datetime.datetime.utcnow, nullable=False)
    refresh_token = db.Column(db.String(160), nullable=True)
    sdk_access_token = db.Column(db.String(80), nullable=True)
    last_api_call = db.Column(db.DateTime(), nullable=True)
    disable = db.Column(db.Boolean(), nullable=False)
    disable_reason = db.Column(db.String(160), nullable=True)
    total_requests = db.Column(db.Integer, nullable=True)

    uname = db.relationship('AccessTokenModel', backref='users', lazy='dynamic')
    model = db.relationship('TrainingModel', backref='users', lazy='dynamic')
    role = db.relationship('RoleModel', backref='users', lazy='dynamic')
    api = db.relationship('APIRequestModel', backref='users', lazy='dynamic')

    def __init__(self, id, username, password, email_address, disable, total_requests):
        self.id = id
        self.username = username
        self.email_address = email_address
        self.password = password
        self.disable = disable
        self.total_requests = total_requests

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def add_refresh_token(cls, username, refresh_token):
        upate_refresh_token = cls.query.filter_by(username=username).update(dict(refresh_token=refresh_token))
        db.session.commit()

    @classmethod
    def remove_refresh_token(cls, refresh_token):
        remove_refresh_token = cls.query.filter_by(refresh_token=refresh_token).update(dict(refresh_token=None))
        db.session.commit()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def return_all(cls):
        def to_json(x):
            return {
                'username': x.username,
                'password': x.password
            }
        return {'users': list(map(lambda x: to_json(x), UserModel.query.all()))}

    @classmethod
    def delete_all(cls):
        try:
            num_rows_deleted = db.session.query(cls).delete()
            db.session.commit()
            return {'message': '{} row(s) deleted'.format(num_rows_deleted)}
        except:
            return {'message': 'Something went wrong'}

    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)

    @staticmethod
    def verify_hash(password, hash):
        return sha256.verify(password, hash)

    @classmethod
    def get_refresh_token(cls, access_token):
        ref_obj = cls.query.join(AccessTokenModel).filter_by(access_token=access_token).first()
        if ref_obj is None:
            return None
        return ref_obj.refresh_token

    @classmethod
    def change_email(cls, username, email_address):
        change_email_add = cls.query.filter_by(username=username).update(dict(email_address=email_address))
        db.session.commit()

    @classmethod
    def change_password(cls, username, password):
        change_pass = cls.query.filter_by(username=username).update(dict(password=password))
        db.session.commit()

    @classmethod
    def update_access_sdk(cls, username, acc):
        print(type(acc))
        change_sdk = cls.query.filter_by(username=username).update(dict(sdk_access_token=acc))
        db.session.commit()

    @classmethod
    def get_model_id(cls, access_token):
        model_obj = cls.query.join(TrainingModel).filter_by(sdk_access_token=access_token).all()
        return model_obj.model_id

    @classmethod
    def get_user_id(cls, access_token):
        print("access token =", access_token)
        return cls.query.filter_by(sdk_access_token=access_token).first()

    @classmethod
    def set_count_by_username(cls, username):
        uo = cls.query.filter_by(username=username).first()
        count = uo.total_requests
        count = count + 1
        upate_count = cls.query.filter_by(username=username).update(dict(total_requests=count))
        db.session.commit()

    @classmethod
    def set_count_by_id(cls, user_id):
        uo = cls.query.filter_by(id=user_id).first()
        count = uo.total_requests
        count = count + 1
        upate_count = cls.query.filter_by(id=user_id).update(dict(total_requests=count))
        db.session.commit()

    @classmethod
    def update_last_api_call_time(cls, user_id):
        change_api_time = cls.query.filter_by(id=user_id).update(dict(last_api_call=datetime.datetime.utcnow()))
        db.session.commit()

    @classmethod
    def get_model_details_admin(cls):
        def to_json(x):
            return {
                'user_id': x[1].user_id_fk,
                'username': x[0].username,
                'Email_address': x[0].email_address,
                'model_id': str(x[1].model_id),
                'model_name': str(x[1].model_name),
                'model_used_count': x[1].model_used_count,
                'Enable/Disable': x[1].disable
            }

        return {'models': list(map(lambda x: to_json(x), db.session.query(UserModel, TrainingModel).
                                   join(UserModel).all()))}

    @classmethod
    def get_user_details_admin(cls):
        def to_json(x):
            return {
                'user_id': x[0],
                'username': x[1],
                'Email_address': x[2],
                'model_id': x[3],
                'last_api_call':str(x[4]),
                'model_used_count': x[5],
                'Enable/Disable': x[6]
            }

        return {'Users': list(map(lambda x: to_json(x), db.session.query(UserModel, TrainingModel).join(UserModel). \
            with_entities(UserModel.id, UserModel.username, UserModel.email_address,
                          TrainingModel.model_id, UserModel.last_api_call,
                          db.func.count(TrainingModel.user_id_fk).label('count'), UserModel.disable). \
            group_by(TrainingModel.user_id_fk). \
            all()))}

    @classmethod
    def get_result_admin(cls):
        def to_json(x):
            return {
                'user_id': x[0],
                'username': x[1],
                'model_id': x[2],
                'text': x[3],
                'tag': x[4]
            }

        return {'results': list(map(lambda x: to_json(x), db.session.query(UserModel, TrainingModel, TaskResultModel).join(UserModel).join(TaskResultModel). \
            with_entities(UserModel.id, UserModel.username,
                          TrainingModel.model_id, TaskResultModel.text, TaskResultModel.emotion). \
            all()))}

    @classmethod
    def get_user_admin(cls, start_date, end_date):
        if start_date:
            start = date(year=start_date['year'], month=start_date['month'], day=start_date['day'])
            end = date(year=end_date['year'], month=end_date['month'], day=end_date['day'])
            return db.session.query(UserModel). \
                filter(and_(UserModel.created_on > start, UserModel.created_on < end)). \
                with_entities(UserModel.created_on, db.func.count(UserModel.id).label('count')). \
                group_by(sa.func.date(UserModel.created_on)). \
                all()
        return db.session.query(UserModel). \
            with_entities(UserModel.created_on, db.func.count(UserModel.id).label('count')). \
            group_by(sa.func.date(UserModel.created_on)). \
            all()

    @classmethod
    def get_disable_status_name(cls, user_name):
        do = cls.query.filter_by(username=user_name).first()
        if do is None:
            return None
        return do.disable

    @classmethod
    def get_disable_status_id(cls, user_id):
        do = cls.query.filter_by(id=user_id).first()
        if do is None:
            return None
        return do.disable


class RevokedTokenModel(db.Model):
    __tablename__ = 'revoked_tokens'

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(120))

    def add(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def is_jti_blacklisted(cls, jti):
        query = cls.query.filter_by(jti=jti).first()
        return bool(query)


class AccessTokenModel(db.Model):
    __tablename__ = 'accesstoken_details'

    id = db.Column(db.Integer, primary_key=True)
    uname = db.Column(db.String(80), db.ForeignKey('users.username'))
    access_token = db.Column(db.String(200), nullable=False)

    def add(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def update_access_token(cls, username, access_token):
        upate_access_token = cls.query.filter_by(uname=username).update(dict(access_token=access_token))
        db.session.commit()


class APIRequestModel(db.Model):
    __tablename__ = 'api_calls'

    id = db.Column(db.Integer, primary_key=True)
    requested_on = db.Column(db.DateTime(), default=datetime.datetime.utcnow, nullable=False)
    user_id_fk = db.Column(db.String(80), db.ForeignKey('users.id'))

    def __init__(self, user_id):
        self.user_id_fk = user_id

    def add(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_request_details_admin(cls, start_date, end_date):
        if start_date:
            start = date(year=start_date['year'], month=start_date['month'], day=start_date['day'])
            end = date(year=end_date['year'], month=end_date['month'], day=end_date['day'])
            return db.session.query(APIRequestModel). \
                filter(and_(APIRequestModel.requested_on > start, APIRequestModel.requested_on < end)). \
                with_entities(APIRequestModel.requested_on, db.func.count(APIRequestModel.user_id_fk).label('count')). \
                group_by(sa.func.date(APIRequestModel.requested_on)). \
                all()
        return db.session.query(APIRequestModel). \
            with_entities(APIRequestModel.requested_on, db.func.count(APIRequestModel.user_id_fk).label('count')). \
            group_by(sa.func.date(APIRequestModel.requested_on)). \
            all()
