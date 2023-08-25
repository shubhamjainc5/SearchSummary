FROM python:3.8-slim

RUN apt-get update && apt-get -y install \
    build-essential libpq-dev wget

WORKDIR /opt
COPY . .

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

EXPOSE 9050
ENV PORT 9050

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9050", "--workers","5"]