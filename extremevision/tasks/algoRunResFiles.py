"""
    #  @ModuleName: algoCelery
    #  @Function: 
    #  @Author: Ljx
    #  @Time: 2020/8/28 17:30
"""
from extremevision import celery
from extremevision.sdk_config import request_host_without_port
from collections import defaultdict
import os
import requests
import base64


@celery.task(bind=True)
def algo_ias_files(self, ori_files_dir, res_files_dir, file_name, port, args, random_str):
    """
    后台进行 ias 运行算法得到结果
    :param args:
    :param random_str:
    :param ori_files_dir: 数据集目录
    :param self: 更新自己获取当前状态
    :param res_files_dir: 数据集运行结果目录
    :param file_name: 文件名称
    :param port: 端口
    :return:
    """
    # 解压文件
    os.system(f"unzip {file_name} -d {ori_files_dir}")

    # 调用ias, image , video
    filesname = iter_files(ori_files_dir)
    # 获取文件全路径列表
    images_dir = filesname["image_dir"]
    videos_dir = filesname["video_dir"]
    err_files = filesname["err_file"]

    file_nums = len(images_dir) + len(videos_dir) - len(err_files)
    res_files_count = 0

    for image_dir in images_dir:
        url = request_host_without_port + ":" + str(port) + "/api/analysisImage"
        # 原文件名称 文件路径
        file_dir, image = os.path.split(image_dir)
        # 结果文件路径
        res_file_dir = file_dir.repalce(f"ori_{random_str}", f"res_{random_str}")
        print(res_file_dir, "res_file_dir")
        os.makedirs(res_file_dir)
        res_file_name = os.path.join(res_file_dir, image)
        # 调用IAS
        ias_interface(url, image, image_dir, args, res_file_name)
        res_files_count += 1
        process = int((res_files_count / file_nums) * 100)
        self.update_state(state='PROGRESS', meta={'current': res_files_count, 'total': file_nums, 'status': process})

    for video_dir in videos_dir:
        url = request_host_without_port + ":" + str(port) + "/api/analysisVideo"
        # 原文件名称 文件路径
        file_dir, video = os.path.split(video_dir)
        # 结果文件路径
        res_file_dir = file_dir.repalce(f"ori_{random_str}", f"res_{random_str}")
        print(res_file_dir, "res_file_dir")
        os.makedirs(res_file_dir)
        res_file_name = os.path.join(res_file_dir, video)
        # 调用IAS
        ias_interface(url, video, video_dir, args, res_file_name)
        res_files_count += 1
        process = int((res_files_count / file_nums) * 100)
        self.update_state(state='PROGRESS', meta={'current': res_files_count, 'total': file_nums, 'status': process})

    # 打包下载结果
    os.system(f"cd {res_files_dir};tar -cvf result.tar *")
    store_path = f"{res_files_dir}/result.tar"

    return {'current': 100, 'total': 100, 'status': 'Task completed!', 'result': store_path, "error_files": err_files}


def ias_interface(url, file, file_name, args, res_file_name):
    data = {
        'image': (file, open(file_name, 'rb')),
        "args": args
    }
    res_base64 = requests.post(url, files=data).json().get('buffer')
    res = base64.decodebytes(res_base64.encode('ascii'))
    with open(res_file_name, 'wb') as f:
        f.write(res)


def iter_files(rootDir):
    """
    根据文件路径 返回文件名称 以及文件路径名称
    :param rootDir:
    :return:
    """
    filenames = defaultdict(list)
    for root, dirs, files in os.walk(rootDir):
        for file in files:
            file = os.path.join(root, file)
            if file.lower().endswith("jpg") or file.lower().endswith("png") or file.lower().endswith("jpeg"):
                filenames["image_dir"].append(file)
            elif file.lower().endswith("avi") or file.lower().endswith("mp4") or file.lower().endswith("flv"):
                filenames["video_dir"].append(file)
            else:
                filenames["error_file"].append(file)
        for dir in dirs:
            iter_files(dir)

    return filenames



