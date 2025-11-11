# 需求分析系统部署指南

## 系统要求

- CentOS 7服务器
- 至少2GB内存
- 至少10GB磁盘空间
- 网络连接

## 部署方式

本系统支持多种部署方式，推荐使用Docker方式部署，以确保环境一致性和部署简便性.

## Docker部署（推荐）

### 1. 准备工作

将以下文件上传到服务器：
- 整个项目的代码目录
- [Dockerfile](file:///D:/Users/00596/Desktop/%E9%9C%80%E6%B1%82%E5%88%86%E6%9E%90/Dockerfile)
- [docker-compose.yml](file:///D:/Users/00596/Desktop/%E9%9C%80%E6%B1%82%E5%88%86%E6%9E%90/docker-compose.yml)
- [deploy_centos7.sh](file:///D:/Users/00596/Desktop/%E9%9C%80%E6%B1%82%E5%88%86%E6%9E%90/deploy_centos7.sh)

### 2. 自动部署（推荐）

在服务器上运行自动部署脚本：

```bash
chmod +x deploy_centos7.sh
./deploy_centos7.sh
```

该脚本将自动完成以下操作：
1. 更新系统
2. 安装Docker和Docker Compose
3. 配置阿里云镜像加速器
4. 构建并启动应用容器

### 3. 手动部署

如果您希望手动部署，可以按照以下步骤操作：

#### 安装Docker

```bash
# 更新系统
sudo yum update -y

# 安装必要的工具
sudo yum install -y yum-utils device-mapper-persistent-data lvm2

# 添加阿里云Docker CE镜像源
sudo yum-config-manager --add-repo http://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo

# 安装Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io

# 启动并启用Docker服务
sudo systemctl start docker
sudo systemctl enable docker
```

#### 配置Docker镜像加速器

```bash
# 配置阿里云镜像加速器
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
```

#### 安装Docker Compose

```bash
# 安装docker-compose（使用兼容CentOS 7的版本）
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 构建并启动应用

```bash
# 构建并启动应用
docker-compose up -d --build
```

## 访问应用

部署完成后，可以通过以下地址访问应用：

```
http://<服务器IP>:5002
```

默认登录账号：
- 用户名：admin
- 密码：admin123

## 防火墙配置

确保服务器防火墙和阿里云安全组已开放5002端口：

### CentOS 7防火墙配置

```bash
# 开放5002端口
sudo firewall-cmd --permanent --add-port=5002/tcp
sudo firewall-cmd --reload
```

### 阿里云安全组配置

在阿里云控制台的安全组规则中添加：
- 协议类型：TCP
- 端口范围：5002
- 授权对象：0.0.0.0/0（或指定IP段）

## 数据持久化

应用数据存储在`requirements_analyst/instance`目录下的SQLite数据库文件中。在Docker部署中，该目录已挂载为卷，确保容器重启后数据不会丢失。

## 备份与恢复

### 备份

```bash
# 备份数据库文件
cp requirements_analyst/instance/database.db database_backup_$(date +%Y%m%d).db
```

### 恢复

```bash
# 停止应用
docker-compose down

# 恢复数据库文件
cp database_backup_YYYYMMDD.db requirements_analyst/instance/database.db

# 启动应用
docker-compose up -d
```

## 日志查看

```bash
# 查看应用日志
docker-compose logs -f app
```

## 更新应用

当有新版本代码时，可以通过以下步骤更新应用：

```bash
# 拉取最新代码（或上传新代码）
# ...

# 重新构建并启动应用
docker-compose down
docker-compose up -d --build
```

## 常见问题

### 1. 部署过程中出现权限问题

确保运行部署脚本的用户具有sudo权限。

### 2. Docker镜像拉取缓慢或失败

脚本已配置多个国内镜像源，如果仍有问题，可以尝试：
1. 检查网络连接
2. 手动配置其他镜像源

### 3. 应用无法访问

检查以下几点：
1. 应用是否正常启动：`docker-compose ps`
2. 端口是否正确映射：`docker-compose port app`
3. 防火墙是否开放端口
4. 阿里云安全组是否开放端口

### 4. 数据库文件权限问题

如果遇到数据库访问问题，可以尝试：

```bash
# 设置正确的文件权限
sudo chown -R $(id -u):$(id -g) requirements_analyst/instance
```