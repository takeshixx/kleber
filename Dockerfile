FROM python:3.8-alpine
ENV PYTHONUNBUFFERED=1
RUN apk update && apk add postgresql-libs gcc musl-dev postgresql-dev libffi-dev make libmagic exiftool bash
RUN mkdir -p /srv/kleber/logs
RUN touch /srv/kleber/logs/kleber.log
WORKDIR /srv/kleber
ADD requirements.txt manage.py /srv/kleber/
RUN chmod +x manage.py
ADD api /srv/kleber/api/
ADD kleber /srv/kleber/kleber/
ADD mal /srv/kleber/mal/
ADD web /srv/kleber/web/
RUN find . -iname \*.pyc -exec rm -f {} \;
RUN pip3 install -r requirements.txt
RUN pip3 install uwsgi
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]