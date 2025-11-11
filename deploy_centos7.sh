#!/bin/bash

# 部署脚本用于在CentOS 7上安装Docker并部署需求分析系统

echo "开始在CentOS 7上部署需求分析系统..."

# 更新系统
echo "更新系统..."
sudo yum update -y

# 安装必要的工具
echo "安装必要工具..."
sudo yum install -y yum-utils device-mapper-persistent-data lvm2

# 添加阿里云Docker CE镜像源
echo "添加阿里云Docker CE镜像源..."
sudo yum-config-manager --add-repo http://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo

# 安装Docker
echo "安装Docker..."
sudo yum install -y docker-ce docker-ce-cli containerd.io

# 启动并启用Docker服务
echo "启动Docker服务..."
sudo systemctl start docker
sudo systemctl enable docker

# 配置Docker镜像加速器（阿里云）
echo "配置Docker镜像加速器..."
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://docker.mirrors.ustc.edu.cn"
  ]
}
EOF

# 重启Docker服务以应用配置
sudo systemctl daemon-reload
sudo systemctl restart docker

# 安装docker-compose（使用较旧但兼容CentOS 7的版本）
echo "安装docker-compose..."
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
echo "验证Docker和docker-compose安装..."
docker --version
docker-compose --version

# 构建并启动应用
echo "构建并启动需求分析系统..."
docker-compose up -d --build

echo "部署完成！应用已在端口5001上运行。"
echo "请确保服务器防火墙和阿里云安全组已开放5001端口。"
echo "您可以通过 http://<服务器IP>:5001 访问需求分析系统。"