FROM python:3.9-alpine3.13

ENV PYTHONUNBUFFERED=1 

COPY ./nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./app /app
WORKDIR /app
EXPOSE 8000

ARG DEV=false

RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client jpeg-dev && \
    apk add --update --no-cache --virtual .tmp-build-deps \
        build-base postgresql-dev musl-dev zlib zlib-dev linux-headers && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ]; \
        then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi && \
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    adduser \
        --disabled-password \
        --no-create-home \
        appuser && \
    rm /etc/nginx/conf.d/default.conf && \
    mkdir -p /vol/web/media && \
    mkdir -p /vol/web/static && \
    chown -R appuser:appuser /vol && \
    chmod -R 755 /vol 

ENV PATH="/py/bin:$PATH"

RUN chown -R appuser /app
USER appuser

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "config.wsgi:application"]