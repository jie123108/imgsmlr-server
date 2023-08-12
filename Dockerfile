FROM centos/python-38-centos7:latest

USER root

WORKDIR /app
RUN mv /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.bak && wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo

RUN yum update -y
RUN yum install -y gcc make wget curl nc telnet strace redhat-lsb vim libtiff-devel libwebp-devel
RUN wget https://github.com/libgd/libgd/releases/download/gd-2.2.5/libgd-2.2.5.tar.gz && tar -xf libgd-2.2.5.tar.gz && cd libgd-2.2.5 && \
./configure --bindir=/usr/sbin/ --sbindir=/usr/sbin/ --sysconfdir=/etc/ --libdir=/usr/lib64/ --mandir=/usr/share/man/ && make && make install

RUN pip install fastapi==0.91.0
RUN pip install sqlalchemy==2.0.17
RUN pip install asyncpg==0.27.0
RUN pip install psycopg2-binary==2.9.5
RUN pip install uvicorn
RUN pip install httpx

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "main.py"]
