from db import db
import datetime
from datetime import date
from sqlalchemy import func, and_
from .training_model import TrainingModel


class TaskModel(db.Model):
    __tablename__ = 'task'

    job_id = db.Column(db.String, primary_key=True)
    status = db.Column(db.Integer, nullable=False)
    created_on = db.Column(db.DateTime(), default=datetime.datetime.utcnow, nullable=False)
    finished_on = db.Column(db.DateTime(), nullable=True)
    error_message = db.Column(db.Text)
    is_error = db.Column(db.Integer, nullable=True)
    model_id_fk = db.Column(db.String(80), db.ForeignKey('models.model_id'))
    user_id_fk = db.Column(db.String(80), db.ForeignKey('users.id'))
    task_res = db.relationship('TaskResultModel', backref='task', lazy='dynamic')

    def __init__(self, job_id, status, model_id_fk, user_id_fk, finished_on=None):
        self.job_id = job_id
        self.status = status
        self.model_id_fk = model_id_fk
        self.user_id_fk = user_id_fk
        self.finished_on = finished_on

    @classmethod
    def find_by_job_id(cls, job_id):
        return cls.query.filter_by(id=job_id).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def update_status_job_id(cls, job_id, status):
        change_status_add = cls.query.filter_by(job_id=job_id).update(dict(status=status))
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
    def update_finish_time(cls, job_id):
        change_finished_on = cls.query.filter_by(job_id=job_id).update(dict(finished_on=datetime.datetime.utcnow()))
        db.session.commit()

    @classmethod
    def get_error_flag(cls, job_id):
        error_flag = cls.query.filter_by(job_id=job_id).first()
        return error_flag if hasattr(error_flag, 'is_error') else None

    @classmethod
    def get_error_msg(cls, job_id):
        error_msg = cls.query.filter_by(job_id=job_id).first()
        return error_msg if hasattr(error_msg, 'error_message') else None

    @classmethod
    def update_error_flag(cls, job_id, ef):
        change_error_by_jobid = cls.query.filter_by(job_id=job_id).update(dict(is_error=ef))
        db.session.commit()

    @classmethod
    def update_error_msg(cls, job_id, e):
        change_errorm_by_jobid = cls.query.filter_by(job_id=job_id).update(dict(error_message=e))
        db.session.commit()

    @classmethod
    def get_task_by_date(cls, user_id, start_date, end_date):
        def to_json(x):
            if x[0].status == 2:
                stat = 'Failed'
            elif x[0].status == 0:
                stat = 'In_progress'
            else:
                stat = 'Success'
            return {
                'model_id': x[0].model_id_fk,
                'model_name': x[1].model_name,
                'job_id': x[0].job_id,
                'created_on': str(x[0].created_on),
                'finished_on': str(x[0].finished_on),
                'status': stat
            }

        start = date(year=start_date['year'], month=start_date['month'], day=start_date['day'])
        end = date(year=end_date['year'], month=end_date['month'], day=end_date['day'])
        return {'tasks': list(map(lambda x: to_json(x), db.session.query(TaskModel, TrainingModel).join(TrainingModel). \
            filter(TaskModel.user_id_fk == user_id). \
            filter(and_(TaskModel.created_on > start, TaskModel.created_on < end)).\
            all()))}
