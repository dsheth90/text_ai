from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, \
    get_jwt_identity, get_jwt
from ..model import UserModel, RevokedTokenModel, AccessTokenModel, TrainingModel, RoleModel
from app.admin_decorator import admin_required
from flask_restful import Resource, reqparse
import pandas as pd
import string
import random
import uuid


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


class UserRegister(Resource):
    """
    Website Call
    request-: {
                "username":"Dhrumil",
                "email_address": "dhrumilsheth@gmail.com",
                "password": "abc"
                }
    Response-:
                {
                "message": "User Dhrumil was created",
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY0MTYxNDI5Mywi",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY0MTYxNDI5Myw"
            }

    """
    def post(self):
        try:
            # data = request.data
            # json_data = json.loads(data)
            parser = reqparse.RequestParser()
            parser.add_argument('username', help='This field cannot be empty', required=True)
            parser.add_argument('email_address', help='This field cannot be empty', required=True)
            parser.add_argument('password', help='This field cannot be empty', required=True)
            data = parser.parse_args()
            if UserModel.find_by_username(data['username']):
                return {"message": "User with that username already exists."}, 400
            data['password'] = UserModel.generate_hash(data['password'])
            data['disable'] = 0
            data['id'] = 'U'+id_generator()
            data['total_requests'] = 0
            user = UserModel(**data)
            user.save_to_db()
            print("username =", data['username'])
            # create refresh and access token
            access_token = create_access_token(identity=data['username'])
            refresh_token = create_refresh_token(identity=data['username'])
            UserModel.add_refresh_token(data['username'], refresh_token)
            at = AccessTokenModel(uname=data['username'], access_token=access_token)
            at.add()
            # create model of new registered user
            model_id = 'D'+id_generator()
            user_id_fk = data['id']
            tm = TrainingModel(model_id=model_id, user_id_fk=user_id_fk, status=None, model_name='Initial_model',
                               model_type='General', job_id=None)
            tm.save_to_db()
            # create role for new user
            rm = RoleModel(user_id=user_id_fk, role_type='User')
            rm.save_to_db()
            # create model path
            df2 = pd.DataFrame()
            df2 = df2.append(pd.DataFrame({
                'model_id': model_id, 'model_path': 'app/AI/weights/general/Weights-001--0.53028.hdf5',
                'tokenizer_path': 'app/AI/weights/general/tokenizer.pickle', 'model_type': 'general'},
                index=[0]), ignore_index=True)
            df2.to_csv('app/AI/weights/model_path.csv', header=False, index=False, mode='a')
            return {
                'message': 'User {} was created'.format(data['username']),
                'access_token': access_token,
                'refresh_token': refresh_token
            }, 201
        except Exception as e:
            return {'message': 'Something went wrong {}'.format(e),
                    }, 500


class UserLogin(Resource):
    """
    Website call
    request
    {
        "username":"Dhrumil",
        "password": "abc"
    }
    response
    {
        "message": "Logged in as Dhrumil",
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY0MTYxNzcwMSwianRpIjoiNzI2MzhlOTQtYjQ1NC00NmMyLWFhNDMtMDU5ODRlNDk2NDZmIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IkRocnVtaWwiLCJuYmYiOjE2NDE2MTc3MDEsImV4cCI6MTY0MTYyMTMwMX0.k0m6YKt6Amx7KE9mUvB7Lrt18ThxDGSK4pK_6tNQBko",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY0MTYxNzcwMSwianRpIjoiY2ZkZGY4M2ItMTBmZS00MmJmLWFjNTctODE2YmJkY2ZiOWFiIiwidHlwZSI6InJlZnJlc2giLCJzdWIiOiJEaHJ1bWlsIiwibmJmIjoxNjQxNjE3NzAxLCJleHAiOjE2NDQyMDk3MDF9._RidfrZVt44Ljetkxq9WWmqXVUdQn8f0KMr6zQkj95E"
    }
    """
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('username', help='This field cannot be empty', required=True)
            parser.add_argument('password', help='This field cannot be empty', required=True)
            data = parser.parse_args()
            current_user = UserModel.find_by_username(data['username'])

            if not current_user:
                return {'message': 'User {} doesn\'t exist'.format(data['username'])}

            if UserModel.verify_hash(data['password'], current_user.password):
                access_token = create_access_token(identity=data['username'])
                refresh_token = create_refresh_token(identity=data['username'])
                UserModel.add_refresh_token(data['username'], refresh_token)
                AccessTokenModel.update_access_token(data['username'], access_token)
                return {'message': 'Logged in as {}'.format(current_user.username),
                        'access_token': access_token,
                        'refresh_token': refresh_token
                        }
            else:
                return {'message': 'Wrong credentials'}
        except Exception as e:
            return {'message': 'Something went wrong',
                    }, 500


class UserLogoutAccess(Resource):
    """
    Website call
    Headers -: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTYxODM5ODcxNCwianRpIjoiNzJkNDF
    response {'Message': 'Access token has been removed'}
    """
    @jwt_required()
    def post(self):
        jti = get_jwt()['jti']
        try:
            revoked_token = RevokedTokenModel(jti=jti)
            revoked_token.add()
            return {'Message': 'Access token has been removed'}
        except:
            return {'Message': 'Something went wrong'}, 500


class UserLogoutRefresh(Resource):
    """
    Website call
    Headers -: Authorization - Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTYxODM5
    {
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTYxODM5ODkxMywianRpIjoiZ"
    }
    response
    {'Message': 'Refresh token has been removed'}
    """
    @jwt_required(refresh=True)
    def post(self):
        jti = get_jwt()['jti']
        try:
            revoked_token = RevokedTokenModel(jti=jti)
            revoked_token.add()
            parser = reqparse.RequestParser()
            parser.add_argument('refresh_token', help='This field cannot be empty', required=True)
            data = parser.parse_args()
            UserModel.remove_refresh_token(data['refresh_token'])
            return {'Message': 'Refresh token has been removed'}
        except:
            return {'Message': 'Something went wrong'}, 500


class TokenRefresh(Resource):
    """
    Website call
    Headers -: Authorization Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTYzOTk3MTQxM
    response {'access_token': access_token}
    """
    @jwt_required(refresh=True)
    def post(self):
        try:
            current_user = get_jwt_identity()
            access_token = create_access_token(identity=current_user)
            AccessTokenModel.update_access_token(current_user, access_token)
            return {'access_token': access_token}
        except Exception as e:
            return {'message': 'Something went wrong',
                    }, 500


class AllUsers(Resource):
    """Just for testing"""
    @admin_required()
    def get(self):
        return UserModel.return_all()

    @admin_required()
    def delete(self):
        return UserModel.delete_all()


class SecretResource(Resource):
    """Just for testing"""
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        print("current_user =", current_user)
        return {'Answer': 42}


class ExpiredAccessToken(Resource):
    """
    Website call
    request
    {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTYzOTk3MTQxMiwianRpIjoiOT"
    }
    response
    {'message': 'Successful',
                'refresh_token': "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaC"
    }
    """
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('access_token', help='This field cannot be empty', required=True)
            data = parser.parse_args()
            refresh_token = UserModel.get_refresh_token(data['access_token'])
            if refresh_token is None:
                return {'message': 'Refresh token not found'
                        }, 404
            return {'message': 'Successful',
                    'refresh_token': refresh_token
                    }, 200
        except Exception as e:
            return {'message': 'Something went wrong',
                    }, 500


class ChangeEmailAddress(Resource):
    """
    Website call
    header Authorization Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTYxODM5ODkxMyw
    Request
    {
        "email_address":"dhrumilsheth9009@gmail.com"
    }
    Response
    {
        message': "Email address changed successfully"
    }
    """
    @jwt_required()
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('email_address', help='This field cannot be empty', required=True)
            data = parser.parse_args()
            current_user = get_jwt_identity()
            UserModel.change_email(current_user, data['email_address'])
            return {'message': "Email address changed successfully"}, 200
        except Exception as e:
            return {'message': 'Something went wrong',
                    }, 500


class ChangePassword(Resource):
    """
    Website call
    header Authorization Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTYxODM5ODkxMyw
    Request
    {
        "password":"Dhrumil"
    }
    Response
    {
        message': "Password changed successfully"
    }
    """
    @jwt_required()
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('password', help='This field cannot be empty', required=True)
            data = parser.parse_args()
            current_user = get_jwt_identity()
            data['password'] = UserModel.generate_hash(data['password'])
            UserModel.change_password(current_user, data['password'])
            return {'message': "Password changed successfully"}, 200
        except Exception as e:
            return {'message': 'Something went wrong',
                    }, 500


class AccessSdk(Resource):
    """
       Website call
       header Authorization Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTYxODM5ODkxMyw
       Response
       {
           message': "Password changed successfully"
       }
       {
            "message": "access_token for SDK created successfully"
        }
    """
    @jwt_required()
    def get(self):
        try:
            access_token_sdk = uuid.uuid4()
            current_user = get_jwt_identity()
            if not UserModel.get_disable_status_name(current_user):
                UserModel.update_access_sdk(current_user, str(access_token_sdk))
                return {'message': "access_token for SDK created successfully"}, 200
            else:
                return {'message': 'User profile is disabled'}, 403
        except Exception as e:
            return {'message': 'Something went wrong{}'.format(e),
                    }, 500
