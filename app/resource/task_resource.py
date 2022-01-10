from ..model import TaskModel, UserModel, TrainingModel, APIRequestModel
from ..tasks import make_file, training_model, evaluate_result
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, reqparse
from flask_restful import request
import pandas as pd
import datetime
import werkzeug
import random
import string
import json
import os


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


@jwt_required()
def website_call():
    current_user = get_jwt_identity()
    user_id = UserModel.find_by_username(current_user)
    return user_id


class APICheck(Resource):
    """Test celery"""
    def get(self):
        return "Hello!"


class CeleryTest(Resource):
    """Test celery"""
    @jwt_required()
    def get(self, fname, content):
        fpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), fname)
        print(fpath, content)
        result = make_file.delay(fpath, content)
        data = {'job_id': result.id, 'status': 0}
        task1 = TaskModel(**data)
        task1.save_to_db()
        return f"Find your file @ <code>{fpath}</code>"


class JobTask(Resource):
    """
        SDK call
        headers -: SDK_Authorization - Bearer c6fd0502-1fd6-4a31-be13-eef285b1ea17
        Website call
        headers -: SDK_Authorization - Bearer access token
        request -:
        {
            file -: csv format file with file key name
            model_name -: test1
        }
        response -:
        {
            "job_id": "e27486d5-7ba9-45c6-a705-07a5141948df"
        }
    """
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')
            parser.add_argument('model_name', help='This field cannot be empty', required=True)
            args = parser.parse_args()
            read_file = args['file']
            model_name = args['model_name']
            headers = request.headers
            if headers.get('SDK_Authorization') is not None:
                access_key = headers['SDK_Authorization'].split(" ")[-1]
                user_id = UserModel.get_user_id(access_key)
            else:
                user_id = website_call()
            if user_id:
                disable_status = UserModel.get_disable_status_id(user_id.id)
                if not disable_status:
                    UserModel.set_count_by_id(user_id.id)
                    UserModel.update_last_api_call_time(user_id.id)
                    am = APIRequestModel(user_id=user_id.id)
                    am.add()
                    model_id = 'C' + id_generator()
                    if not os.path.exists('app/AI/data/'+user_id.id+'/'+model_id):
                        os.makedirs('app/AI/data/'+user_id.id+'/'+model_id)
                    fname = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                    df = pd.read_csv(read_file, encoding='latin1')
                    filename = 'app/AI/data/'+user_id.id+'/'+model_id+'/'+fname+'.csv'
                    df.to_csv(filename, header=True, index=False)
                    res = training_model.delay(filename, model_id, user_id.id)
                    data = {'model_id':model_id, 'user_id_fk':user_id.id, 'status': 0, 'model_name': model_name, 'job_id': res.id,
                            'model_type': 'Custom'}
                    trainingdb = TrainingModel(**data)
                    trainingdb.save_to_db()
                    return {'job_id': res.id}, 200
                else:
                    return {'message': 'User profile is disabled'}, 403
            else:
                return {'message': 'Not authorized'}, 403
        except Exception as e:
            return {'message': 'Something went wrong {}'.format(e),
                    }, 500


class Prediction(Resource):
    """
        SDK call
        headers -: SDK_Authorization - Bearer c6fd0502-1fd6-4a31-be13-eef285b1ea17
        request -:
        {
            "model_name":"test2",
            "model_type":"Custom",
            "text": [
                        {
                            "text": "i am updating my blog because i feel shitty",
                            "text_id": 1
                        },
                        {
                            "text": "i find myself in the odd position of feeling supportive of",
                            "text_id": 2
                        }
                    ]
        }
        response -:
        {
            "job_id": "e27486d5-7ba9-45c6-a705-07a5141948df"
        }
    """
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('model_type', help='This field cannot be empty', required=True)
            parser.add_argument('model_name', help='This field cannot be empty', required=True)
            parser.add_argument('text', help='This field cannot be empty', required=True)
            text = request.data
            json_data = json.loads(text)
            headers = request.headers
            access_key = headers['SDK_Authorization'].split(" ")[-1]
            user_id = UserModel.get_user_id(access_key)
            if user_id:
                disable_status = UserModel.get_disable_status_id(user_id.id)
                if not disable_status:
                    disable_status_model = TrainingModel.get_disable_model_status_id(user_id.id)
                    if not disable_status_model:
                        UserModel.set_count_by_id(user_id.id)
                        UserModel.update_last_api_call_time(user_id.id)
                        train_obj = TrainingModel.get_model_id(user_id.id, json_data['model_name'])
                        res = evaluate_result.delay(json_data['text'], train_obj.model_id, json_data['model_type'], user_id.id)
                        data = {'model_id_fk': train_obj.model_id, 'user_id_fk': user_id.id, 'status': 0,
                                'job_id': res.id}
                        taskdb = TaskModel(**data)
                        taskdb.save_to_db()
                        TrainingModel.set_count_by_model_id(train_obj.model_id)
                        am = APIRequestModel(user_id=user_id.id)
                        am.add()
                        return {'job_id': res.id}, 200
                    else:
                        return {'message': 'Model is disabled'}, 403
                else:
                    return {'message': 'User profile is disabled'}, 403
            else:
                return {'message': 'Not authorized'}, 403
        except Exception as e:
            return {'message': 'Something went wrong {}'.format(e),
                    }, 500


class StatusTask(Resource):
    """
        SDK call
        headers -: SDK_Authorization - Bearer c6fd0502-1fd6-4a31-be13-eef285b1ea17
        Website call
        headers -: SDK_Authorization - Bearer access token
        request -:
        {
            "job_id":"8e8a6d89-9af5-497c-9ce1-25df6b94b663"
        }
        response -:
        {
            "status": "Successful"
        }
    """
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('job_id', help='This field cannot be empty', required=True)
            args = parser.parse_args()
            job_id = args['job_id']
            headers = request.headers
            if headers.get('SDK_Authorization') is not None:
                access_key = headers['SDK_Authorization'].split(" ")[-1]
                user_id = UserModel.get_user_id(access_key)
            else:
                user_id = website_call()
            if user_id:
                disable_status = UserModel.get_disable_status_id(user_id.id)
                if not disable_status:
                    UserModel.set_count_by_id(user_id.id)
                    UserModel.update_last_api_call_time(user_id.id)
                    am = APIRequestModel(user_id=user_id.id)
                    am.add()
                    task_obj = TaskModel.get_status(job_id)
                    status = 'In_progress'
                    if task_obj == 1:
                        status = 'Successful'
                    elif task_obj is None:
                        status = 'Invalid Job Id'
                    return {'status': status}, 200
                else:
                    return {'message': 'User profile is disabled'}, 403
            else:
                return {'message': 'Not authorized'}, 403
        except Exception as e:
            return {'message': 'Something went wrong {}'.format(e),
                }, 500


class StatusTrain(Resource):
    """
        SDK call
        headers -: SDK_Authorization - Bearer c6fd0502-1fd6-4a31-be13-eef285b1ea17
        Website call
        headers -: SDK_Authorization - Bearer access token
        request -:
        {
            "job_id":"8e8a6d89-9af5-497c-9ce1-25df6b94b663"
        }
        response -:
        {
            "status": "Successful"
        }
    """
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('job_id', help='This field cannot be empty', required=True)
            args = parser.parse_args()
            job_id = args['job_id']
            headers = request.headers
            if headers.get('SDK_Authorization') is not None:
                access_key = headers['SDK_Authorization'].split(" ")[-1]
                user_id = UserModel.get_user_id(access_key)
            else:
                user_id = website_call()
            if user_id:
                disable_status = UserModel.get_disable_status_id(user_id.id)
                if not disable_status:
                    UserModel.set_count_by_id(user_id.id)
                    UserModel.update_last_api_call_time(user_id.id)
                    am = APIRequestModel(user_id=user_id.id)
                    am.add()
                    train_obj = TrainingModel.get_status(job_id)
                    print(train_obj)
                    status = 'In_progress'
                    if train_obj == 1:
                        status = 'Successful'
                    elif train_obj is None:
                        status = 'Invalid Job Id'
                    return {'status': status}, 200
                else:
                    return {'message': 'User profile is disabled'}, 403
            else:
                return {'message': 'Not authorized'}, 403
        except Exception as e:
            return {'message': 'Something went wrong {}'.format(e),
                    }, 500


class TaskDateFilter(Resource):
    """
        SDK call
        headers -: SDK_Authorization - Bearer c6fd0502-1fd6-4a31-be13-eef285b1ea17
        Website call
        headers -: SDK_Authorization - Bearer access token
        request -:
       {
            "start_date":"2022-01-02",
            "end_date":"2022-01-10"
        }
        response -:
       {
        "tasks": [
                    {
                        "model_id": "CPRND9O",
                        "model_name": "test3",
                        "job_id": "8e8a6d89-9af5-497c-9ce1-25df6b94b663",
                        "created_on": "2022-01-08 09:43:33.285573",
                        "finished_on": "2022-01-08 09:43:35.587644",
                        "status": "Success"
                    },
                    {
                        "model_id": "CT03TBQ",
                        "model_name": "test1",
                        "job_id": "8488ba87-59bf-4304-b0ac-572cf6ccd5a6",
                        "created_on": "2022-01-08 10:16:20.640801",
                        "finished_on": "2022-01-08 10:16:23.635421",
                        "status": "Success"
                    }
                ]
        }
    """
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('start_date', help='This field cannot be empty', required=True)
            parser.add_argument('end_date', help='This field cannot be empty', required=True)
            args = parser.parse_args()
            sd = args['start_date']
            ed = args['end_date']
            start_date = sd.split('-')
            start_date_dict = {'year': int(start_date[0]), 'month': int(start_date[1]), 'day': int(start_date[2])}
            end_date = ed.split('-')
            end_date_dict = {'year': int(end_date[0]), 'month': int(end_date[1]), 'day': int(end_date[2])}
            headers = request.headers
            if headers.get('SDK_Authorization') is not None:
                access_key = headers['SDK_Authorization'].split(" ")[-1]
                user_id = UserModel.get_user_id(access_key)
            else:
                user_id = website_call()
            if user_id:
                disable_status = UserModel.get_disable_status_id(user_id.id)
                if not disable_status:
                    UserModel.set_count_by_id(user_id.id)
                    UserModel.update_last_api_call_time(user_id.id)
                    am = APIRequestModel(user_id=user_id.id)
                    am.add()
                    res = TaskModel.get_task_by_date(user_id.id, start_date_dict, end_date_dict)
                    return res, 200
                else:
                    return {'message': 'User profile is disabled'}, 403
            else:
                return {'message': 'Not authorized'}, 403
        except Exception as e:
            return {'message': 'Something went wrong {}'.format(e),
            }, 500


class PredictionFile(Resource):
    """
        SDK call
        headers -: SDK_Authorization - Bearer c6fd0502-1fd6-4a31-be13-eef285b1ea17
        Website call
        headers -: SDK_Authorization - Bearer access token
        request -:
        {
            file -: csv format file with text key name,
            model_name -: test1,
            model_type -: Custom
        }
        response -:
        {
            "job_id": "e27486d5-7ba9-45c6-a705-07a5141948df"
        }
    """
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('model_type', help='This field cannot be empty', required=True)
            parser.add_argument('model_name', help='This field cannot be empty', required=True)
            parser.add_argument('text', type=werkzeug.datastructures.FileStorage, location='files')
            print("1")
            args = parser.parse_args()
            print("2")
            read_file = args['text']
            model_name = args['model_name']
            model_type = args['model_type']
            print(read_file, model_type, model_name)
            headers = request.headers
            if headers.get('SDK_Authorization') is not None:
                access_key = headers['SDK_Authorization'].split(" ")[-1]
                user_id = UserModel.get_user_id(access_key)
            else:
                user_id = website_call()
            if user_id:
                disable_status = UserModel.get_disable_status_id(user_id.id)
                if not disable_status:
                    disable_status_model = TrainingModel.get_disable_model_status_id(user_id.id)
                    if not disable_status_model:
                        df = pd.read_csv(read_file, encoding='latin1')
                        data_raw = df.to_dict('records')
                        UserModel.set_count_by_id(user_id.id)
                        UserModel.update_last_api_call_time(user_id.id)
                        train_obj = TrainingModel.get_model_id(user_id.id, model_name)
                        res = evaluate_result.delay(data_raw, train_obj.model_id, model_type, user_id.id)
                        data = {'model_id_fk': train_obj.model_id, 'user_id_fk': user_id.id, 'status': 0,
                                'job_id': res.id}
                        taskdb = TaskModel(**data)
                        taskdb.save_to_db()
                        TrainingModel.set_count_by_model_id(train_obj.model_id)
                        am = APIRequestModel(user_id=user_id.id)
                        am.add()
                        return {'job_id': res.id}, 200
                    else:
                        return {'message': 'Model is disabled'}, 403
                else:
                    return {'message': 'User profile is disabled'}, 403
            else:
                return {'message': 'Not authorized'}, 403
        except Exception as e:
                return {'message': 'Something went wrong {}'.format(e)}, 500
