FROM python:3.9

WORKDIR /app

RUN pip install gunicorn==20.1.0

COPY requirements/requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram_backend.wsgi"]