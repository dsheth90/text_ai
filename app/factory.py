from flask import Flask
import os
from .celery_utils import init_celery
from flask_restful import Api
from .resource import CeleryTest, JobTask, Prediction
from db import db
from flask_migrate import Migrate

PKG_NAME = os.path.dirname(os.path.realpath(__file__)).split("/")[-1]


def create_app(app_name=PKG_NAME, **kwargs):
    app = Flask(app_name)
    if kwargs.get("celery"):
        init_celery(kwargs.get("celery"), app)
    api = Api(app)
    api.add_resource(CeleryTest, '/<string:fname>/<string:content>')
    api.add_resource(JobTask, '/job')
    api.add_resource(Prediction, '/predict')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dev-data.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    migrate = Migrate(app, db, render_as_batch=True)
    @app.before_first_request
    def create_table():
        db.create_all()
    return app, api
