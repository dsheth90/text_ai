from ..model import UserModel, TrainingModel, TaskResultModel, APIRequestModel
from app.admin_decorator import admin_required
from flask_restful import Resource, reqparse


class AdminCheck(Resource):
    """Checking admin decorator"""
    @admin_required()
    def get(self):
        return "Admin access verified"


class ModelList(Resource):
    """
    Website call
    headers -: Authorization - Bearer access_token
    Response-:
    {
        "models": [
            {
                "user_id": "U3BOX6U",
                "username": "Dhrumil",
                "Email_address": "dhrumilsheth@gmail.com",
                "model_id": "DDQ6PK5",
                "model_name": "Initial_model",
                "model_used_count": 0,
                "Enable/Disable": false
            },
            {
                "user_id": "U3BOX6U",
                "username": "Dhrumil",
                "Email_address": "dhrumilsheth@gmail.com",
                "model_id": "CT03TBQ",
                "model_name": "test1",
                "model_used_count": 11,
                "Enable/Disable": false
            }
            ]
    }
    """
    @admin_required()
    def get(self):
        try:
            return UserModel.get_model_details_admin(), 200
        except Exception as e:
            return {'message': 'Something went wrong {}'.format(e)}, 500


class UserListAdmin(Resource):
    """
    Website call
    headers -: Authorization - Bearer access_token
    Response-:{
                "models": [
                    {
                        "user_id": "U3BOX6U",
                        "username": "Dhrumil",
                        "Email_address": "dhrumilsheth@gmail.com",
                        "model_id": "DDQ6PK5",
                        "last_api_call": "2022-01-08 11:28:32.747711",
                        "model_used_count": 6,
                        "Enable/Disable": false
                    }
                ]
            }

    """
    @admin_required()
    def get(self):
        try:
            return UserModel.get_user_details_admin(), 200
        except Exception as e:
            return {'message': 'Something went wrong {}'.format(e)}, 500


class ResultAdmin(Resource):
    """
    Website call
    headers -: Authorization - Bearer access_token
    Response-:
    {
        "results": [
            {
                "user_id": "U3BOX6U",
                "username": "Dhrumil",
                "model_id": "CPRND9O",
                "text": "i am updating my blog because i feel shitty",
                "tag": "sadness"
            },
            {
                "user_id": "U3BOX6U",
                "username": "Dhrumil",
                "model_id": "CPRND9O",
                "text": "i find myself in the odd position of feeling supportive of",
                "tag": "sadness"
            },
            {
                "user_id": "U3BOX6U",
                "username": "Dhrumil",
                "model_id": "CPRND9O",
                "text": "i feel like i m defective or something for not having baby fever",
                "tag": "sadness"
            }
            ]
        }
    """
    @admin_required()
    def get(self):
        try:
            return UserModel.get_result_admin(), 200
        except Exception as e:
            return {'message': 'Something went wrong {}'.format(e)}, 500


class ResultAnalytics(Resource):
    """
    Website call
    headers -: Authorization - Bearer access_token
    Request -:
    {
        "start_date":"2022-01-01",
        "end_date":"2022-01-10"
    }
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
    @admin_required()
    def post(self):
        try:
            out = {'result': {'sadness': 0, 'joy': 0, 'love': 0, 'anger': 0, 'fear': 0, 'surprise': 0}}
            parser = reqparse.RequestParser()
            parser.add_argument('start_date', help='This field cannot be empty', required=True)
            parser.add_argument('end_date', help='This field cannot be empty', required=True)
            args = parser.parse_args()
            sd = args['start_date']
            ed = args['end_date']
            start_date_dict = None
            end_date_dict = None
            if sd:
                start_date = sd.split('-')
                start_date_dict = {'year': int(start_date[0]), 'month': int(start_date[1]), 'day': int(start_date[2])}
                end_date = ed.split('-')
                end_date_dict = {'year': int(end_date[0]), 'month': int(end_date[1]), 'day': int(end_date[2])}
            result = TaskResultModel.get_all_results_admin(start_date_dict, end_date_dict)
            for r in result:
                out['result'][r[0]] = r[1]
            return out, 200
        except Exception as e:
            return {'message': 'Something went wrong {}'.format(e)}, 500


class ModelAnalytics(Resource):
    """
    Website call
    headers -: Authorization - Bearer access_token
    Request -:
    {
        "start_date":"",
        "end_date":""
    }
    Response -:
    {
        "model_list": {
            "2022-01-08 03:58:13.848057": 6
        }
    }
    """
    @admin_required()
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('start_date', help='This field cannot be empty', required=True)
            parser.add_argument('end_date', help='This field cannot be empty', required=True)
            args = parser.parse_args()
            sd = args['start_date']
            ed = args['end_date']
            start_date_dict = None
            end_date_dict = None
            output = {'model_list':{}}
            if sd:
                start_date = sd.split('-')
                start_date_dict = {'year': int(start_date[0]), 'month': int(start_date[1]), 'day': int(start_date[2])}
                end_date = ed.split('-')
                end_date_dict = {'year': int(end_date[0]), 'month': int(end_date[1]), 'day': int(end_date[2])}
            result = TrainingModel.get_model_details_admin(start_date_dict, end_date_dict)
            for d,c in result:
                output['model_list'][str(d)] = c
            return output, 200
        except Exception as e:
            return {'message': 'Something went wrong {}'.format(e)}, 500


class RequestsAnalytics(Resource):
    """
        Website call
        headers -: Authorization - Bearer access_token
        Request -:
        {
            "start_date":"",
            "end_date":""
        }
        Response -:
        {
            "request_list": {
                "2022-01-08 09:11:35.700269": 75
            }
        }
    """
    @admin_required()
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('start_date', help='This field cannot be empty', required=True)
            parser.add_argument('end_date', help='This field cannot be empty', required=True)
            args = parser.parse_args()
            sd = args['start_date']
            ed = args['end_date']
            start_date_dict = None
            end_date_dict = None
            output = {'request_list': {}}
            if sd:
                start_date = sd.split('-')
                start_date_dict = {'year': int(start_date[0]), 'month': int(start_date[1]), 'day': int(start_date[2])}
                end_date = ed.split('-')
                end_date_dict = {'year': int(end_date[0]), 'month': int(end_date[1]), 'day': int(end_date[2])}
            result = APIRequestModel.get_request_details_admin(start_date_dict, end_date_dict)
            for d, c in result:
                output['request_list'][str(d)] = c
            return output, 200
        except Exception as e:
            return {'message': 'Something went wrong {}'.format(e)}, 500


class UsersAnalytics(Resource):
    """
        Website call
        headers -: Authorization - Bearer access_token
        Request -:
        {
            "start_date":"2022-01-01",
            "end_date":"2022-01-10"
        }
        Response -:
        {
            "user_list": {
                "2022-01-08 03:58:13.842433": 1,
                "2022-01-09 03:04:24.973732": 1
            }
        }
    """
    @admin_required()
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('start_date', help='This field cannot be empty', required=True)
            parser.add_argument('end_date', help='This field cannot be empty', required=True)
            args = parser.parse_args()
            sd = args['start_date']
            ed = args['end_date']
            start_date_dict = None
            end_date_dict = None
            output = {'user_list': {}}
            if sd:
                start_date = sd.split('-')
                start_date_dict = {'year': int(start_date[0]), 'month': int(start_date[1]), 'day': int(start_date[2])}
                end_date = ed.split('-')
                end_date_dict = {'year': int(end_date[0]), 'month': int(end_date[1]), 'day': int(end_date[2])}
            result = UserModel.get_user_admin(start_date_dict, end_date_dict)
            for d, c in result:
                output['user_list'][str(d)] = c
            return output, 200
        except Exception as e:
            return {'message': 'Something went wrong {}'.format(e)}, 500
