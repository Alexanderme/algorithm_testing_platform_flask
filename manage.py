from extremevision import create_app
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
# 需要导入才能生成表
from extremevision.models import *

app = create_app("development")
manager = Manager(app)
# 启动流程
Migrate(app, db)
manager.add_command("db", MigrateCommand)

if __name__ == "__main__":
    manager.run()
