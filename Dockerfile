FROM python:3.10.8-bullseye

WORKDIR /app/

COPY docker/sources.list /etc/apt/
COPY main.py main.py
COPY requirements.txt requirements.txt
COPY conf/ conf/

RUN apt-get update && apt-get upgrade -y && apt-get install -y chromium chromium-l10n

RUN python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install -r requirements.txt

CMD python main.py