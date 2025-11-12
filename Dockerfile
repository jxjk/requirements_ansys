# 使用Python 3.9作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 复制依赖文件
COPY requirements_analyst/requirements.txt .

# 尝试安装系统依赖（如果失败则跳过）并安装Python依赖
RUN apt-get update 2>/dev/null || echo "apt-get update skipped" \
    && apt-get install -y --no-install-recommends \
        gcc \
        libc-dev 2>/dev/null || echo "System dependencies installation skipped" \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean 2>/dev/null || echo "apt-get clean skipped" \
    && rm -rf /var/lib/apt/lists/* 2>/dev/null || echo "apt lists cleanup skipped"

# 复制应用代码
COPY requirements_analyst/ .

# 暴露端口
EXPOSE 5001

# 设置容器启动命令
CMD ["python", "app.py"]