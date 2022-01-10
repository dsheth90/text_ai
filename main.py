from app import factory
import app
from app.resource import APICheck
from flask_jwt_extended import JWTManager
from app.resource import (UserRegister, UserLogin, UserLogoutAccess, UserLogoutRefresh, TokenRefresh,
                                    AllUsers, SecretResource, ExpiredAccessToken, ChangeEmailAddress, ChangePassword,
                          AccessSdk, StatusTask, StatusTrain, Result, UserModelList, ModelWiseResult, OverallResult,
                          DateWiseModelResult, DateWiseOverallResult, TaskDateFilter, AdminCheck, ModelList,
                          UserListAdmin, ResultAdmin, ResultAnalytics, ModelAnalytics, RequestsAnalytics,
                          PredictionFile, UsersAnalytics)
from app.model import RevokedTokenModel
from datetime import timedelta


# if __name__ == "__main__":
app, api = factory.create_app(celery=app.celery)
ACCESS_EXPIRES = timedelta(hours=1)
app.config['JWT_SECRET_KEY'] = 'D@ps#45V!9cg%r'
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = ACCESS_EXPIRES
jwt = JWTManager(app)


@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    jti = jwt_payload['jti']
    return RevokedTokenModel.is_jti_blacklisted(jti)


api.add_resource(UserRegister, '/register')
api.add_resource(UserLogin, '/login')
api.add_resource(UserLogoutAccess, '/logout/access')
api.add_resource(UserLogoutRefresh, '/logout/refresh')
api.add_resource(TokenRefresh, '/token/refresh')
api.add_resource(AllUsers, '/users')
api.add_resource(SecretResource, '/secret')
api.add_resource(ExpiredAccessToken, '/expired-token')
api.add_resource(ChangeEmailAddress, '/change-email')
api.add_resource(ChangePassword, '/change-password')
api.add_resource(APICheck, '/')
api.add_resource(AccessSdk, '/get-sdk-token')
api.add_resource(StatusTask, '/task-status')
api.add_resource(StatusTrain, '/train-status')
api.add_resource(Result, '/get-result')
api.add_resource(UserModelList, '/get-model-list')
api.add_resource(ModelWiseResult, '/get-result-model')
api.add_resource(OverallResult, '/get-result-overall')
api.add_resource(DateWiseModelResult, '/get-range-model-result')
api.add_resource(DateWiseOverallResult, '/get-range-result')
api.add_resource(TaskDateFilter, '/get-task')
api.add_resource(AdminCheck, '/admin-check')
api.add_resource(ModelList, '/model-list-admin')
api.add_resource(UserListAdmin, '/user-list-admin')
api.add_resource(ResultAdmin, '/get-result-admin')
api.add_resource(ResultAnalytics, '/get-result-admin-analytics')
api.add_resource(ModelAnalytics, '/get-model-admin-analytics')
api.add_resource(RequestsAnalytics, '/get-request-admin-analytics')
api.add_resource(PredictionFile, '/prediction-file')
api.add_resource(UsersAnalytics, '/get-user-admin-analytics')

app.run(port=5000, debug=True)
