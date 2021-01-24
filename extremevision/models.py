from datetime import datetime
from extremevision import db
from werkzeug.security import check_password_hash, generate_password_hash


class BaseModel(object):
    """模型基类，为每个模型补充创建时间与更新时间"""
    create_time = db.Column(db.DateTime, default=datetime.now)  # 记录的创建时间
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 记录的更新时间


class User(BaseModel, db.Model):
    __tablename__ = "ex_user_profile"
    id = db.Column(db.Integer, primary_key=True)  # 用户编号
    username = db.Column(db.String(32), unique=True, nullable=False)  # 用户账号
    nickname = db.Column(db.String(32), unique=True)  # 用户昵称
    password_hash = db.Column(db.String(128), nullable=False)  # 加密的密码

    @property
    def password(self):
        raise AttributeError("only read")

    @password.setter
    def password(self, value):
        """对密码加密"""
        self.password_hash = generate_password_hash(value)

    def check_password(self, passwd):
        return check_password_hash(self.password_hash, passwd)


class CentosServer(BaseModel, db.Model):
    __tablename__ = 'ex_centos_server'
    id = db.Column(db.Integer, primary_key=True)  # 服务器编号
    ip = db.Column(db.String(32))  # IP
    user = db.Column(db.String(32))
    root = db.Column(db.String(32))
    port = db.Column(db.Integer, unique=True)  # 服务器端口
    name = db.Column(db.String(64))  # 启动算法名称
    contain_id = db.Column(db.String(64))  # 启动的容器ID


