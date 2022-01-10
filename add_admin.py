from app.model import UserModel, AccessTokenModel, RoleModel
from app.factory import create_app
from flask_jwt_extended import JWTManager
from datetime import timedelta
from flask_jwt_extended import create_access_token, create_refresh_token
import string
import random

app = create_app()
jwt = JWTManager(app[0])
ACCESS_EXPIRES = timedelta(hours=1)
app[0].config['JWT_SECRET_KEY'] = 'D@ps#45V!9cg%r'
app[0].config["JWT_ACCESS_TOKEN_EXPIRES"] = ACCESS_EXPIRES


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def my_function():
    print(app)
    with app[0].app_context():
        data = {}
        data['password'] = 'admin1234'
        data['username'] = 'admin'
        data['email_address'] = 'admin@gmail.com'

        data['password'] = UserModel.generate_hash(data['password'])
        data['disable'] = 0
        data['id'] = 'U' + id_generator()
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
        user_id_fk = data['id']

        # create role for new user
        rm = RoleModel(user_id=user_id_fk, role_type='Admin')
        rm.save_to_db()


if __name__ == "__main__":
    my_function()
