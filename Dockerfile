FROM python:3.7
WORKDIR /home/ljx

COPY requirements.txt ./
RUN pip --default-timeout=10000 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

RUN chmod +x run.sh
#CMD ["gunicorn", "manage:app", "-c", "./gunicorn.conf.py"]
#CMD ["celery", "-A", "celery_worker.celery", "worker", "--loglevel=info", "--autoscale=4,2"]

CMD ["/home/ljx/run.sh"]
