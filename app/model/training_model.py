from db import db
import datetime
from datetime import date
from sqlalchemy import func, and_
import sqlalchemy as sa


class TrainingModel(db.Model):
    __tablename__ = 'models'

    model_id = db.Column(db.String(80), primary_key=True)
    job_id = db.Column(db.String(80), unique=True, nullable=True)
    model_name = db.Column(db.String(80), nullable=False)
    created_on = db.Column(db.DateTime(), default=datetime.datetime.utcnow, nullable=False)
    finished_on = db.Column(db.DateTime(), nullable=True)
    disable = db.Column(db.Boolean(), nullable=False)
    disable_reason = db.Column(db.String(160), nullable=True)
    status = db.Column(db.Integer, nullable=True)
    model_type = db.Column(db.String(80), nullable=False)
    error_message = db.Column(db.Text)
    is_error = db.Column(db.Integer, nullable=True)
    model_used_count = db.Column(db.Integer, nullable=True)
    user_id_fk = db.Column(db.String(80), db.ForeignKey('users.id'))
    task = db.relationship('TaskModel', backref='models', lazy='dynamic')
    mod = db.relationship('TaskResultModel', backref='models', lazy='dynamic')

    def __init__(self, model_id, user_id_fk, status, model_name, job_id, model_type, disable=False):
        self.job_id = job_id
        self.model_id = model_id
        self.model_name = model_name
        self.disable = disable
        self.status = status
        self.model_type = model_type
        self.user_id_fk = user_id_fk
        self.disable_reason = None
        self.model_used_count = 0

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_status(cls, job_id):
        obj = cls.query.filter_by(job_id=job_id).first()
        return obj.status if hasattr(obj, 'status') else None

    @classmethod
    def update_job_id(cls, model_id, job_id):
        add_job_id = cls.query.filter_by(model_id=model_id).update(dict(job_id=job_id))
        db.session.commit()

    @classmethod
    def update_status(cls, model_id, status):
        change_status = cls.query.filter_by(model_id=model_id).update(dict(status=status))
        db.session.commit()

    @classmethod
    def update_status_job_id(cls, job_id, status):
        change_status_by_jobid = cls.query.filter_by(job_id=job_id).update(dict(status=status))
        db.session.commit()

    @classmethod
    def update_finish_time(cls, job_id):
        change_finished_on = cls.query.filter_by(job_id=job_id).update(dict(finished_on=datetime.datetime.utcnow()))
        db.session.commit()

    @classmethod
    def get_model_id(cls, user_id, model_name):
        return cls.query.filter_by(user_id_fk=user_id).filter_by(model_name=model_name).first()

    @classmethod
    def get_error_flag(cls, job_id):
        error_flag = cls.query.filter_by(job_id=job_id).first()
        return error_flag.is_error if hasattr(error_flag, 'is_error') else None

    @classmethod
    def get_error_msg(cls, job_id):
        error_msg = cls.query.filter_by(job_id=job_id).first()
        return error_msg.error_message if hasattr(error_msg, 'error_message') else None

    @classmethod
    def update_error_flag(cls, job_id, ef):
        change_error_by_jobid = cls.query.filter_by(job_id=job_id).update(dict(is_error=ef))
        db.session.commit()

    @classmethod
    def update_error_msg(cls, job_id, e):
        change_errorm_by_jobid = cls.query.filter_by(job_id=job_id).update(dict(error_message=e))
        db.session.commit()

    @classmethod
    def get_model_details(cls, user_id):
        def to_json(x):
            return {
                'model_id': x.model_id,
                'model_name': x.model_name,
                'created_on': str(x.created_on),
                'finished_on': str(x.finished_on),
                'model_type':x.model_type,
                'status':x.status
            }
        return {'models': list(map(lambda x: to_json(x), cls.query.filter_by(user_id_fk=user_id).all()))}

    @classmethod
    def set_count_by_model_id(cls, model_id):
        to = cls.query.filter_by(model_id=model_id).first()
        count = to.model_used_count
        count = count + 1
        upate_count = cls.query.filter_by(model_id=model_id).update(dict(model_used_count=count))
        db.session.commit()

    @classmethod
    def get_model_details_admin(cls, start_date, end_date):
        if start_date:
            start = date(year=start_date['year'], month=start_date['month'], day=start_date['day'])
            end = date(year=end_date['year'], month=end_date['month'], day=end_date['day'])
            return db.session.query(TrainingModel). \
                filter(and_(TrainingModel.created_on > start, TrainingModel.created_on < end)). \
                with_entities(TrainingModel.created_on, db.func.count(TrainingModel.model_id).label('count')). \
                group_by(sa.func.date(TrainingModel.created_on)). \
                all()
        return db.session.query(TrainingModel). \
            with_entities(TrainingModel.created_on, db.func.count(TrainingModel.model_id).label('count')). \
            group_by(sa.func.date(TrainingModel.created_on)). \
            all()


    @classmethod
    def get_disable_model_status_id(cls, user_id):
        do = cls.query.filter_by(user_id_fk=user_id).first()
        if do is None:
            return None
        return do.disable
