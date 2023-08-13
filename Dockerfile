FROM python:3.9-slim-bullseye

WORKDIR /app

RUN echo 'deb http://deb.debian.org/debian testing main' >> /etc/apt/sources.list \
    && apt-get update
RUN apt-get install -y --no-install-recommends -o APT::Immediate-Configure=false gcc wget curl libgd-dev

RUN pip install fastapi==0.91.0
RUN pip install sqlalchemy==2.0.17
RUN pip install asyncpg==0.27.0
RUN pip install psycopg2-binary==2.9.5
RUN pip install uvicorn

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "main.py"]
