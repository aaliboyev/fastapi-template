FROM python:3.10.13-slim-bookworm
LABEL authors="aaliboyev"

WORKDIR /app/
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED 1

RUN pip install poetry
RUN poetry config virtualenvs.create false
COPY ./pyproject.toml ./poetry.lock* /app/

ARG INSTALL_DEV=false
RUN if [ "$INSTALL_DEV" = "true" ]; then \
    poetry install --no-root; \
else \
    poetry install --no-root --no-dev && poetry add uvloop; \
fi

ARG INSTALL_JUPYTER=false
RUN if [ "$INSTALL_JUPYTER" = "true" ]; then  \
    pip install jupyterlab ;  \
fi

COPY ./.env /app/.env
COPY ./docker/gunicorn_conf.py /gunicorn_conf.py
COPY ./docker/start.sh /start.sh
RUN chmod +x /start.sh
COPY ./docker/start-reload.sh /start-reload.sh
RUN chmod +x /start-reload.sh

COPY ./src /app/src

EXPOSE 80
CMD ["/start-reload.sh"]
