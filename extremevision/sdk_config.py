"""
    #  @ModuleName: sdk_config
    #  @Function: 
    #  @Author: Ljx
    #  @Time: 2020/7/28 12:09
"""


run_sdk_config_GPU = f"docker run -itd --runtime=nvidia --privileged -v /tmp/ljx:/tmp  -e LANG=C.UTF-8 -e NVIDIA_VISIBLE_DEVICES=0 --rm "

run_sdk_config_CPU = f"docker run -itd --privileged -v /tmp/ljx:/tmp  -e LANG=C.UTF-8 -e --rm "

request_host = "http://192.168.1.147:5000"

request_host_without_port = "http://192.168.1.147"