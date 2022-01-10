from db import db
import datetime
from datetime import date
import jsonify
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy import func, and_
from .training_model import TrainingModel


class TaskResultModel(db.Model, SerializerMixin):
    __tablename__ = 'task_result'
    id = db.Column(db.Integer, primary_key=True)
    job_id_fk = db.Column(db.String(80), db.ForeignKey('task.job_id'))
    text_id = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    emotion = db.Column(db.String(80))
    created_on = db.Column(db.DateTime(), default=datetime.datetime.utcnow, nullable=False)
    model_id_fk = db.Column(db.String(80), db.ForeignKey('models.model_id'))

    def __init__(self, job_id_fk, text, text_id, emotion, model_id_fk):
        self.job_id_fk = job_id_fk
        self.text = text
        self.text_id = text_id
        self.emotion = emotion
        self.model_id_fk = model_id_fk

    def to_dict(self):
        result = {}
        for key in self.__mapper__.c.keys():
            if getattr(self, key) is not None:
                result[key] = str(getattr(self, key))
            else:
                result[key] = getattr(self, key)
        return result

    def to_json(all_vendors):
        v = [ven.to_dict() for ven in all_vendors]
        return v

    @classmethod
    def get_results(cls, job_id):
        item = cls.query.filter_by(job_id_fk=job_id).all()
        data = cls.to_json(item)
        return data

    @classmethod
    def get_model_results(cls, user_id):
        return db.session.query(TaskResultModel, TrainingModel).join(TrainingModel).\
            filter(TrainingModel.user_id_fk==user_id).\
            with_entities(TaskResultModel.model_id_fk, TaskResultModel.emotion, db.func.count(TaskResultModel.emotion).label('count')).\
            group_by(TaskResultModel.model_id_fk).group_by(TaskResultModel.emotion).\
            all()

    @classmethod
    def get_general_results(cls, user_id):
        return db.session.query(TaskResultModel, TrainingModel).join(TrainingModel). \
            filter(TrainingModel.user_id_fk == user_id). \
            with_entities(TaskResultModel.emotion, db.func.count(TaskResultModel.emotion).label('count')). \
            group_by(TaskResultModel.emotion). \
            all()

    @classmethod
    def get_date_model_results(cls, user_id, start_date, end_date):
        start = date(year=start_date['year'], month=start_date['month'], day=start_date['day'])
        end = date(year=end_date['year'], month=end_date['month'], day=end_date['day'])
        return db.session.query(TaskResultModel, TrainingModel).join(TrainingModel). \
            filter(TrainingModel.user_id_fk == user_id).\
            filter(and_(TaskResultModel.created_on > start, TaskResultModel.created_on < end)).\
            with_entities(TaskResultModel.model_id_fk, TaskResultModel.emotion,
                          db.func.count(TaskResultModel.emotion).label('count')). \
            group_by(TaskResultModel.model_id_fk).group_by(TaskResultModel.emotion). \
            all()

    @classmethod
    def get_date_overall_results(cls, user_id, start_date, end_date):
        start = date(year=start_date['year'], month=start_date['month'], day=start_date['day'])
        end = date(year=end_date['year'], month=end_date['month'], day=end_date['day'])
        return db.session.query(TaskResultModel, TrainingModel).join(TrainingModel). \
            filter(TrainingModel.user_id_fk == user_id).\
            filter(and_(TaskResultModel.created_on > start, TaskResultModel.created_on < end)).\
            with_entities(TaskResultModel.emotion, db.func.count(TaskResultModel.emotion).label('count')). \
            group_by(TaskResultModel.emotion). \
            all()

    @classmethod
    def get_all_results_admin(cls, start_date, end_date):
        if start_date:
            start = date(year=start_date['year'], month=start_date['month'], day=start_date['day'])
            end = date(year=end_date['year'], month=end_date['month'], day=end_date['day'])
            return db.session.query(TaskResultModel, TrainingModel).join(TrainingModel). \
                filter(and_(TaskResultModel.created_on > start, TaskResultModel.created_on < end)).\
                with_entities(TaskResultModel.emotion, db.func.count(TaskResultModel.emotion).label('count')). \
                group_by(TaskResultModel.emotion). \
                all()
        return db.session.query(TaskResultModel, TrainingModel).join(TrainingModel). \
            with_entities(TaskResultModel.emotion, db.func.count(TaskResultModel.emotion).label('count')). \
            group_by(TaskResultModel.emotion). \
            all()

    def save_to_db(self):
            db.session.add(self)
            db.session.commit()
