# coding:utf-8

from flask import Flask
from config import config_map
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from extremevision.utils.commons import ReConverter
import pymysql
from flask_cors import CORS
from celery import Celery
from config import Config
from flask_socketio import SocketIO

pymysql.install_as_MySQLdb()
# 数据库
db = SQLAlchemy()
# celery
celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)

# 工厂模式
def create_app(config_name):
    """
    创建flask的应用对象
    :param config_name: str  配置模式的模式的名字 （"develop",  "product"）
    :return:
    """
    app = Flask(__name__)

    # 根据配置模式的名字获取配置参数的类
    config_class = config_map.get(config_name)
    app.config.from_object(config_class)

    # 使用app初始化db
    db.init_app(app)

    # celery
    celery.conf.update(app.config)
    # 为flask补充csrf防护
    # CSRFProtect(app)
    CORS(app, cors_allowed_origins='*')

    # 为flask添加自定义的转换器
    app.url_map.converters["re"] = ReConverter

    # 注册蓝图
    from extremevision import api_1_0
    app.register_blueprint(api_1_0.api, url_prefix="/api/v1.0")

    # 注册提供静态文件的蓝图
    from extremevision import web_html
    app.register_blueprint(web_html.html)

    return app


def make_celery(app):
    celery.conf.update(app.config)
    class ContextTask(celery.Task):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return celery.Task.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
