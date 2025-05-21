FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY ./app /app

EXPOSE 8000

CMD ["gunicorn", "-b", ":8000", "app.web.wsgi:app"]
