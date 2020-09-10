import time
import subprocess
from collections import defaultdict
import sys
import os

def get_used():
    errmsg = defaultdict(dict)
    # 获取cpu大小
    cpu_total = "lscpu |grep CPU\(s\):|awk 'NR==1 {print $2}'"
    status, cpu_total = sdk_subprocess(cpu_total)
    if not status:
        errmsg['cpu_total'] = cpu_total

    # 获取内存大小
    mem_total = "free -m |awk 'NR==2 {print $2}'"
    status, mem_total = sdk_subprocess(mem_total)
    if not status:
        errmsg['mem_total'] = mem_total
    # 获取总的GPU占用  现在只支持查看单张看  多张卡记录 需要舒勇"nvidia-smi |grep Default|awk '{print $11}'"
    gpu_total = "nvidia-smi |grep Default|awk 'NR==1 {print $11}'"
    status, gpu_total = sdk_subprocess(gpu_total)
    if not status:
        errmsg['gpu_total'] = gpu_total

    # 获取GPU使用
    gpu_used = "nvidia-smi |grep Default|awk 'NR==1 {print $9}'"
    status, gpu_used_before = sdk_subprocess(gpu_used)
    if not status:
        errmsg['gpu_used_before'] = gpu_used_before

    # 运行sdk
    file = sys.argv[1]
    cmd = f"nohup /usr/local/ev_sdk/bin/test-ji-api -f 1 -i /tmp/{file}  -l /usr/local/ev_sdk/bin/license.txt -r 100000  > run.log 2>&1 &"
    os.system(cmd)

    time.sleep(200)
    # cpu占用需要获取一段时间内的cpu 输出cpu占用区间 默认30秒内cpu跳动
    # 获取cpu 占用
    pid_test_ji_api = str(os.popen("pidof test-ji-api").read().replace('\n', ""))
    
    cmd = "top -n 1 -p %s|grep test|awk '{print $10}'"%pid_test_ji_api
    cpu_list = []
    for i in range(30):
        time.sleep(1)
        status, cpu_use = sdk_subprocess(cmd)
        if not status:
            errmsg['cpu_use'] = cpu_use
            continue
        cpu_list.append(cpu_use)
    cpu_min = min(cpu_list)
    cpu_max = max(cpu_list)
    # 获取内存占用
    cmd = "top -n 1 -p %s|grep test|awk '{print $11}'" % pid_test_ji_api
    status,  mem_used = sdk_subprocess(cmd)
    if not status:
        errmsg['mem_used'] = mem_used
    mem_used = int(float(mem_used) * float(mem_total) / 100)

    # 获取GPU使用
    gpu_used = "nvidia-smi |grep Default|awk 'NR==1 {print $9}'"
    status, gpu_used_after = sdk_subprocess(gpu_used)
    if not status:
        errmsg['gpu_used_after'] = gpu_used_after
    gpu_used = int(gpu_used_after[:-3]) - int(gpu_used_before[:-3])
    os.system("touch /tmp/res_used.txt")
    with open("/tmp/res_used.txt", 'w', encoding='utf-8') as f:
        f.write(f"当前服务器CPU核数:{cpu_total}, 内存大小:{mem_total}MiB, 显存大小:{gpu_total}\n")
        f.write(f"算法运行资源占用:CPU占用区间{cpu_min}~{cpu_max}, MEM:{mem_used}, GPU:{gpu_used}")

def sdk_subprocess(cmd):
    """
    封装 subprocess 用来定制化返回消息
    :param cmd:
    :param msg:
    :return:
    """
    res_p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = res_p.communicate()
    returncode = res_p.returncode
    if returncode == 0:
        if stdout.decode('utf-8').endswith('\n'):
             return True, stdout.decode('utf-8').replace("\n", '')
        return True, stdout.decode('utf-8')
    else:
        return False, stderr.decode()

get_used()

