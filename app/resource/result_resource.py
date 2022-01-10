from ..model import TaskModel, UserModel, TrainingModel, TaskResultModel, APIRequestModel
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, reqparse
from collections import defaultdict
from flask_restful import request


@jwt_required()
def website_call():
    current_user = get_jwt_identity()
    user_id = UserModel.find_by_username(current_user)
    return user_id


class Result(Resource):
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
        "prediction": [
                {
                    "id": "1",
                    "job_id_fk": "8e8a6d89-9af5-497c-9ce1-25df6b94b663",
                    "text_id": "1",
                    "text": "i am updating my blog because i feel shitty",
                    "emotion": "sadness",
                    "created_on": "2022-01-08 09:43:35.577292",
                    "model_id_fk": "CPRND9O"
                },
                {
                    "id": "2",
                    "job_id_fk": "8e8a6d89-9af5-497c-9ce1-25df6b94b663",
                    "text_id": "2",
                    "text": "i find myself in the odd position of feeling supportive of",
                    "emotion": "sadness",
                    "created_on": "2022-01-08 09:43:35.580665",
                    "model_id_fk": "CPRND9O"
                }
            ]
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
                    obj = TaskModel.get_error_flag(job_id)
                    if obj.is_error == 1:
                        return {'error': obj.error_message}, 500
                    else:
                        obj = TaskResultModel.get_results(job_id)
                        return {'prediction': obj}, 200
                else:
                    return {'message': 'User profile is disabled'}, 403
            else:
                return {'message': 'Not authorized'}, 403
        except Exception as e:
            return {'message': 'Something went wrong {}'.format(e),
                    }, 500


class UserModelList(Resource):
    """
    SDK call
    headers -: SDK_Authorization - Bearer c6fd0502-1fd6-4a31-be13-eef285b1ea17
    Website call
    headers -: SDK_Authorization - Bearer access token
    response-: {
                "models": [
                    {
                        "model_id": "DDQ6PK5",
                        "model_name": "Initial_model",
                        "created_on": "2022-01-08 03:58:13.848057",
                        "finished_on": "None",
                        "model_type": "General",
                        "status": null
                    },
                    {
                        "model_id": "CT03TBQ",
                        "model_name": "test1",
                        "created_on": "2022-01-08 09:14:45.253751",
                        "finished_on": "2022-01-08 09:18:07.124283",
                        "model_type": "Custom",
                        "status": 1
                    }
                ]
            }
    """
    def get(self):
        try:
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
                    return TrainingModel.get_model_details(user_id.id), 200
                else:
                    return {'message': 'User profile is disabled'}, 403
            else:
                return {'message': 'Not authorized'}, 403
        except Exception as e:
            return {'message': 'Something went wrong {}'.format(e),
                    }, 500


class ModelWiseResult(Resource):
    """
    SDK call
    headers -: SDK_Authorization - Bearer c6fd0502-1fd6-4a31-be13-eef285b1ea17
    Website call
    headers -: SDK_Authorization - Bearer access token
    Response -:
    {
        "result": [
                    {
                        "C840CGY": {
                            "sadness": 0,
                            "joy": 110,
                            "love": 0,
                            "anger": 0,
                            "fear": 0,
                            "surprise": 0
                        },
                        "CPRND9O": {
                            "sadness": 30,
                            "joy": 0,
                            "love": 0,
                            "anger": 0,
                            "fear": 0,
                            "surprise": 0
                        },
                        "CT03TBQ": {
                            "sadness": 55,
                            "joy": 0,
                            "love": 0,
                            "anger": 0,
                            "fear": 0,
                            "surprise": 0
                        }
                    }
                ]
        }
    """
    def get(self):
        try:
            headers = request.headers
            if headers.get('SDK_Authorization') is not None:
                access_key = headers['SDK_Authorization'].split(" ")[-1]
                user_id = UserModel.get_user_id(access_key)
            else:
                user_id = website_call()
            out = {'result':[]}
            res = defaultdict(dict)
            if user_id:
                disable_status = UserModel.get_disable_status_id(user_id.id)
                if not disable_status:
                    result = TaskResultModel.get_model_results(user_id.id)
                    am = APIRequestModel(user_id=user_id.id)
                    am.add()
                    for r in result:
                        if not res[r[0]]:
                            res[r[0]] = {'sadness': 0, 'joy': 0, 'love': 0, 'anger': 0, 'fear': 0, 'surprise': 0}
                    for r in result:
                        res[r[0]][r[1]] = r[2]
                    out['result'].append(res)
                    UserModel.set_count_by_id(user_id.id)
                    UserModel.update_last_api_call_time(user_id.id)
                    return out, 200
                else:
                    return {'message': 'User profile is disabled'}, 403
            else:
                return {'message': 'Not authorized'}, 403
        except Exception as e:
            return {'message': 'Something went wrong {}'.format(e)}, 500


class OverallResult(Resource):
    """
    SDK call
    headers -: SDK_Authorization - Bearer c6fd0502-1fd6-4a31-be13-eef285b1ea17
    Website call
    headers -: SDK_Authorization - Bearer access token
    Response -:
    {
        "result": {
            "sadness": 85,
            "joy": 110,
            "love": 0,
            "anger": 0,
            "fear": 0,
            "surprise": 0
        }
    }
    """
    def get(self):
        try:
            headers = request.headers
            if headers.get('SDK_Authorization') is not None:
                access_key = headers['SDK_Authorization'].split(" ")[-1]
                user_id = UserModel.get_user_id(access_key)
            else:
                user_id = website_call()
            out = {'result': {'sadness': 0, 'joy': 0, 'love': 0, 'anger': 0, 'fear': 0, 'surprise': 0}}
            if user_id:
                disable_status = UserModel.get_disable_status_id(user_id.id)
                if not disable_status:
                    result = TaskResultModel.get_general_results(user_id.id)
                    am = APIRequestModel(user_id=user_id.id)
                    am.add()
                    for r in result:
                        out['result'][r[0]] = r[1]
                    UserModel.set_count_by_id(user_id.id)
                    UserModel.update_last_api_call_time(user_id.id)
                    return out, 200
                else:
                    return {'message': 'User profile is disabled'}, 403
            else:
                return {'message': 'Not authorized'}, 403
        except Exception as e:
            return {'message': 'Something went wrong {}'.format(e)}, 500


class DateWiseModelResult(Resource):
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
        "result": [
            {
                "C840CGY": {
                    "sadness": 0,
                    "joy": 110,
                    "love": 0,
                    "anger": 0,
                    "fear": 0,
                    "surprise": 0
                },
                "CPRND9O": {
                    "sadness": 30,
                    "joy": 0,
                    "love": 0,
                    "anger": 0,
                    "fear": 0,
                    "surprise": 0
                },
                "CT03TBQ": {
                    "sadness": 55,
                    "joy": 0,
                    "love": 0,
                    "anger": 0,
                    "fear": 0,
                    "surprise": 0
                }
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
            start_date_dict = {'year':int(start_date[0]), 'month':int(start_date[1]), 'day':int(start_date[2])}
            end_date = ed.split('-')
            end_date_dict = {'year': int(end_date[0]), 'month': int(end_date[1]), 'day': int(end_date[2])}
            out = {'result': []}
            res = defaultdict(dict)
            headers = request.headers
            if headers.get('SDK_Authorization') is not None:
                access_key = headers['SDK_Authorization'].split(" ")[-1]
                user_id = UserModel.get_user_id(access_key)
            else:
                user_id = website_call()
            if user_id:
                disable_status = UserModel.get_disable_status_id(user_id.id)
                if not disable_status:
                    result = TaskResultModel.get_date_model_results(user_id.id, start_date_dict, end_date_dict)
                    for r in result:
                        if not res[r[0]]:
                            res[r[0]] = {'sadness': 0, 'joy': 0, 'love': 0, 'anger': 0, 'fear': 0, 'surprise': 0}
                    for r in result:
                        res[r[0]][r[1]] = r[2]
                    out['result'].append(res)
                    UserModel.set_count_by_id(user_id.id)
                    UserModel.update_last_api_call_time(user_id.id)
                    am = APIRequestModel(user_id=user_id.id)
                    am.add()
                    return out, 200
                else:
                    return {'message': 'User profile is disabled'}, 403
            else:
                return {'message': 'Not authorized'}, 403
        except Exception as e:
            return {'message': 'Something went wrong {}'.format(e)}, 500


class DateWiseOverallResult(Resource):
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
    response-:
    {
        "result": {
            "sadness": 85,
            "joy": 110,
            "love": 0,
            "anger": 0,
            "fear": 0,
            "surprise": 0
        }
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
            out = {'result': {'sadness': 0, 'joy': 0, 'love': 0, 'anger': 0, 'fear': 0, 'surprise': 0}}
            headers = request.headers
            if headers.get('SDK_Authorization') is not None:
                access_key = headers['SDK_Authorization'].split(" ")[-1]
                user_id = UserModel.get_user_id(access_key)
            else:
                user_id = website_call()
            if user_id:
                disable_status = UserModel.get_disable_status_id(user_id.id)
                if not disable_status:
                    result = TaskResultModel.get_date_overall_results(user_id.id, start_date_dict, end_date_dict)
                    for r in result:
                        out['result'][r[0]] = r[1]
                    UserModel.set_count_by_id(user_id.id)
                    UserModel.update_last_api_call_time(user_id.id)
                    am = APIRequestModel(user_id=user_id.id)
                    am.add()
                    return out, 200
                else:
                    return {'message': 'User profile is disabled'}, 403
            else:
                return {'message': 'Not authorized'}, 403
        except Exception as e:
            return {'message': 'Something went wrong {}'.format(e)}, 500
