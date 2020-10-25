FROM python:3.8-slim-buster

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

ADD requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY alertify.py /app
COPY src /app/src

RUN useradd appuser && chown -R appuser /app
USER appuser

EXPOSE 8080

CMD ["python", "alertify.py"]

HEALTHCHECK --interval=30s --timeout=3s --retries=1 \
  CMD python3 /app/alertify.py --healthcheck
