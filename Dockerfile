FROM python:3.8-slim

ENV PYTHONUNBUFFERED 1

WORKDIR /home


ADD requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY code .

CMD ["python3", "server.py"]
