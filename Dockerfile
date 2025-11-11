# 使用Python 3.9作为基础镜像（适合CentOS 7）
FROM python:3.9-slim-buster

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 复制依赖文件
COPY requirements_analyst/requirements.txt .

# 安装系统依赖和Python依赖
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libc-dev \
        libpq-dev \
        build-essential \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制应用代码
COPY requirements_analyst/ .

# 暴露端口
EXPOSE 5001

# 启动应用
CMD ["python", "app.py"]