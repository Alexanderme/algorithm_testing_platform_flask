import os
import  flask_sqlalchemy

class Config:
    SQLALCHEMY_DATABASE_URI = "mysql://root:123456@180.76.151.82:3310/ex_sdk_palteform"
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.163.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '25'))
    MAIL_USERNAME = os.environ.get('470485145@qq.com')
    MAIL_PASSWORD = os.environ.get('XXXXXXXXXXXXXXXXXXXXX')
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    FLASKY_MAIL_SENDER = 'Flasky Admin <flasky@example.com>'
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    FLASKY_POSTS_PER_PAGE = 20
    SERVER_IP = "127.0.0.1"
    CELERY_BROKER_URL = "redis://192.168.1.147:6379/10"
    CELERY_RESULT_BACKEND = "redis://192.168.1.147:6379/0"

class DevelopmentConfig(Config):
    DEBUG = True
    pass


class ProductionConfig(Config):
    pass


class TestingConfig(Config):
    DEBUG = True
    pass


config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}

