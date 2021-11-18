FROM python:3-slim

WORKDIR /src

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT ["python", "main.py"]
#ENTRYPOINT ["python", "secret_santa.py"]

