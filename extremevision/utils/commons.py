"""
    #  @ModuleName: commons
    #  @Function: 
    #  @Author: Ljx
    #  @Time: 2020/7/9 10:53
"""

from werkzeug.routing import BaseConverter

class ReConverter(BaseConverter):
    """
    # 定义一个re万能转换器
    """
    def __init__(self, url_map, regex):
        super(ReConverter, self).__init__(url_map)
        self.regex = regex