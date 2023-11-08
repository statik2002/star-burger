FROM unit:1.31.1-python3.11

EXPOSE 8000

WORKDIR /www/

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY . .
COPY unit_docker/config.json /docker-entrypoint.d/.unit.conf.json

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
#CMD ["python", "manage.py", "migrate"]
CMD ["unitd", "--no-daemon", "--control", "unix:/var/run/control.unit.sock"]

