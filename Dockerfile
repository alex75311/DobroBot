FROM python:3.8
WORKDIR /
COPY requirements.txt /
RUN pip install -r requirements.txt
COPY . /
RUN pip install -U https://github.com/timoniq/vkbottle/archive/v2.0.zip
RUN python dobrobot.py
