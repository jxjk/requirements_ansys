#!/bin/bash

# 部署脚本用于在Windows 11上部署需求分析系统

echo "开始在Windows 11上部署需求分析系统..."

# 检查Docker是否已安装
echo "检查Docker是否已安装..."
if ! command -v docker &> /dev/null
then
    echo "Docker未安装，请先安装Docker Desktop for Windows"
    echo "下载地址: https://www.docker.com/products/docker-desktop/"
    exit 1
else
    echo "Docker已安装"
fi

# 检查docker-compose是否已安装
echo "检查docker-compose是否已安装..."
if ! command -v docker-compose &> /dev/null
then
    echo "docker-compose未安装，请先安装Docker Desktop for Windows（已包含docker-compose）"
    exit 1
else
    echo "docker-compose已安装"
fi

# 配置Docker镜像加速器（可选，适用于中国用户）
echo "注意：如需配置Docker镜像加速器，请在Docker Desktop中手动配置"
echo "参考地址: https://github.com/DaoCloud/public-image-mirror"

# 构建并启动应用
echo "构建并启动需求分析系统..."
if docker-compose up -d --build; then
    echo "部署完成！应用已在端口5001上运行。"
    echo "您可以通过 http://localhost:5001 访问需求分析系统。"
else
    echo "部署失败，请检查以上错误信息。"
    echo "常见问题及解决方案："
    echo "1. 网络连接问题：请确保您的网络连接正常，可以访问镜像源"
    echo "2. 镜像源问题：如果使用国内网络，建议配置Docker镜像加速器"
    echo "3. 权限问题：在某些系统上可能需要管理员权限运行Docker"
    echo "4. 端口占用：确保5001端口未被其他程序占用"
    exit 1
fi