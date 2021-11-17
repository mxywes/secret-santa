FROM python:2-slim

WORKDIR /src

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

#ENTRYPOINT ["python", "secret_santa.py"]

