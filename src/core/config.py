import os
from datetime import timedelta


class Config(object):
    @property
    def DEBUG(self): return os.getenv("FLASK_ENV", "production") == 'development'

    @property
    def SECRET_KEY(self): return os.environ.get('SECRET_KEY')

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        db_name = os.getenv("DATABASE_NAME")
        db_username = os.getenv("DATABASE_USERNAME")
        db_password = os.getenv("DATABASE_PASSWORD")
        db_host = os.getenv("DATABASE_HOST")
        db_url = f'mysql+pymysql://{db_username}:{db_password}@{db_host}/{db_name}'
        return db_url

    @property
    def SQLALCHEMY_TRACK_MODIFICATIONS(self): return False

    @property
    def JWT_SECRET_KEY(self): return os.environ.get('JWT_SECRET_KEY')

    @property
    def JWT_ACCESS_TOKEN_EXPIRES(self): return timedelta(hours=1)

    @property
    def JWT_REFRESH_TOKEN_EXPIRES(self): return timedelta(days=30)
