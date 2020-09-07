"""
    #  @ModuleName: celery_worker
    #  @Function: 
    #  @Author: Ljx
    #  @Time: 2020/8/31 10:03
"""

import os
from extremevision import celery, create_app

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
app.app_context().push()
