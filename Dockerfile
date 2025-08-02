FROM centos/python-38-centos7:latest

USER root

WORKDIR /app

# 修复 CentOS 7 源问题
RUN sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-*.repo && \
    sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*.repo && \
    yum clean all

# 安装编译和运行时依赖
RUN yum-config-manager --disable centos-sclo-rh centos-sclo-sclo || true
RUN yum update -y
RUN yum install -y gcc make wget curl nc telnet strace redhat-lsb vim libtiff-devel libwebp-devel

# 编译安装libgd
RUN wget https://github.com/libgd/libgd/releases/download/gd-2.2.5/libgd-2.2.5.tar.gz && \
    tar -xf libgd-2.2.5.tar.gz && cd libgd-2.2.5 && \
    ./configure --bindir=/usr/sbin/ --sbindir=/usr/sbin/ --sysconfdir=/etc/ --libdir=/usr/lib64/ --mandir=/usr/share/man/ && \
    make && make install

# 配置pip
RUN mkdir -p ~/.pip && \
    echo "[global]" > ~/.pip/pip.conf && \
    echo "index-url = https://mirrors.aliyun.com/pypi/simple/" >> ~/.pip/pip.conf && \
    echo "trusted-host = mirrors.aliyun.com" >> ~/.pip/pip.conf && \
    echo "[install]" >> ~/.pip/pip.conf && \
    echo "trusted-host = mirrors.aliyun.com" >> ~/.pip/pip.conf

RUN python3.8 -m pip install --upgrade pip setuptools wheel

# 安装Python依赖
RUN pip install fastapi==0.91.0
RUN pip install sqlalchemy==2.0.17
RUN pip install asyncpg==0.27.0
RUN pip install psycopg2-binary==2.9.5
RUN pip install uvicorn==0.32.1
RUN pip install httpx==0.28.0
RUN pip install transformers==4.46.3
RUN pip install uvloop==0.21.0
RUN pip install pillow==10.4.0
RUN pip install torch==2.4.0
# 在容器内通过pip安装libimgsmlr，确保在正确的架构上编译
RUN pip install libimgsmlr --global-option="build_ext"

COPY requirements.txt requirements.txt
# 移除requirements.txt中的libimgsmlr行，因为我们已经手动安装了
RUN sed -i '/libimgsmlr/d' requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "img-smlr-server.py"]
