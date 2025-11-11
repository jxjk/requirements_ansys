# 需求分析系统开发文档

## 项目概述

需求分析系统是一个基于Python Flask框架开发的Web应用，用于帮助项目团队进行需求收集、分析和管理。系统实现了多种需求分析方法，包括KANO模型、价值流图(VSM)、SMART目标设定、WFMT动作时间分析等。

## 技术架构

### 后端技术栈
- Python 3.6+
- Flask Web框架
- SQLite数据库
- SQLAlchemy ORM

### 前端技术栈
- HTML5/CSS3
- Bootstrap 5
- JavaScript (原生)
- Jinja2模板引擎

### 第三方库依赖
- Flask: Web框架
- SQLAlchemy: ORM框架
- PyPDF2: PDF文件处理
- 其他依赖详见requirements.txt

## 项目结构

```
requirements_analyst/
├── app.py                 # 应用主文件
├── models.py              # 数据模型定义
├── database.py            # 数据库配置
├── config.ini             # 配置文件
├── requirements.txt       # 依赖包列表
├── instance/
│   └── database.db        # SQLite数据库文件
├── templates/             # HTML模板文件
├── static/                # 静态资源文件
│   ├── css/
│   ├── js/
│   └── images/
└── ...
```

## 数据模型

### Project (项目)
- id: 整数，主键
- name: 字符串，项目名称
- description: 文本，项目描述
- created_at: 日期时间，创建时间
- updated_at: 日期时间，更新时间

### Stakeholder (干系人)
- id: 整数，主键
- project_id: 整数，外键关联项目
- name: 字符串，干系人姓名
- role: 字符串，干系人角色
- influence: 整数(1-5)，影响力
- interest: 整数(1-5)，关注度
- requirements: 文本，关注的需求
- contact_info: 字符串，联系方式
- notes: 文本，备注
- created_at: 日期时间，创建时间
- updated_at: 日期时间，更新时间

### Requirement (需求)
需求模型包含多个分析维度的字段：

#### 基础信息
- id: 整数，主键
- project_id: 整数，外键关联项目
- title: 字符串，需求标题
- requirement_type: 字符串，需求类型
- priority_level: 字符串，优先级
- source: 字符串，需求来源
- created_at: 日期时间，创建时间
- updated_at: 日期时间，更新时间

#### 九要素字段
- scenario: 文本，场景描述
- problem: 文本，解决的问题
- current_solution: 文本，当前解决方案
- goal: 文本，目标
- expected_solution: 文本，预期解决方案
- value: 文本，价值
- other_info: 文本，其他信息

#### 价值评估字段
- estimated_business_value: 整数(1-10)，预估商业价值
- estimated_user_value: 整数(1-10)，预估用户价值
- estimated_technical_value: 整数(1-10)，预估技术价值
- estimated_effort: 整数(1-10)，预估实现难度
- estimated_roi: 浮点数，预估投资回报率
- actual_business_value: 整数(1-10)，实际商业价值
- actual_user_value: 整数(1-10)，实际用户价值
- actual_technical_value: 整数(1-10)，实际技术价值
- actual_effort: 整数(1-10)，实际实现难度
- actual_roi: 浮点数，实际投资回报率
- value_assessor: 字符串，价值评估人
- actual_value_assessor: 字符串，实际价值评估人

#### KANO分析字段
- kano_category: 字符串，KANO分类
- kano_priority_score: 整数，KANO优先级分数

#### VSM分析字段
- vsm_process_steps: 文本，VSM流程步骤
- cycle_time: 浮点数，周期时间
- lead_time: 浮点数，交付时间

#### SMART目标字段
- smart_specific: 文本，明确性
- smart_measurable: 文本，可衡量
- smart_achievable: 布尔值，可实现
- smart_relevant: 文本，相关性
- smart_timebound: 字符串，时限性

#### WFMT分析字段
- standard_time: 浮点数，标准时间
- improvement_potential: 浮点数，改善潜力
- wfmt_tmu_total: 浮点数，总TMU时间
- wfmt_allowance_rate: 浮点数，宽放率

### Milestone (里程碑)
- id: 整数，主键
- project_id: 整数，外键关联项目
- title: 字符串，里程碑标题
- description: 文本，描述
- deadline: 日期，截止日期
- status: 字符串，状态
- requirements: 文本，关联的需求ID列表
- created_at: 日期时间，创建时间
- updated_at: 日期时间，更新时间

## 核心功能模块

### 用户认证模块
- 用户登录/登出
- 会话管理
- 权限控制

### 项目管理模块
- 项目创建、查看、删除
- 项目详情展示

### 干系人管理模块
- 干系人增删改查
- 干系人影响力/关注度分析

### 需求管理模块
- 需求增删改查
- 需求九要素信息管理
- 需求状态管理

### 分析模块
#### KANO分析
- 需求分类管理
- 优先级评分计算

#### VSM分析
- 流程步骤管理
- 周期时间和交付时间分析

#### SMART目标
- 目标设定管理
- 目标完成情况跟踪

#### WFMT分析
- 动作时间分析
- 改善潜力评估

### 价值评估模块
- 需求价值评估
- ROI计算
- 评估准确性分析

### 路线图模块
- 里程碑管理
- 需求分配
- 进度跟踪

### 数据导入导出模块
- CSV数据导入
- PDF文档解析
- 模板下载

## API接口

### 项目相关接口
- `GET /api/projects` - 获取项目列表
- `POST /api/projects` - 创建项目
- `GET /api/projects/<id>` - 获取项目详情
- `PUT /api/projects/<id>` - 更新项目
- `DELETE /api/projects/<id>` - 删除项目

### 干系人相关接口
- `GET /api/stakeholders/<project_id>` - 获取项目干系人列表
- `POST /api/stakeholders/<project_id>` - 创建干系人
- `GET /api/stakeholders/<project_id>/<id>` - 获取干系人详情
- `PUT /api/stakeholders/<project_id>/<id>` - 更新干系人
- `DELETE /api/stakeholders/<project_id>/<id>` - 删除干系人

### 需求相关接口
- `GET /api/requirements/<project_id>` - 获取项目需求列表
- `POST /api/requirements/<project_id>` - 创建需求
- `GET /api/requirements/<id>` - 获取需求详情
- `PUT /api/requirements/<id>` - 更新需求
- `DELETE /api/requirements/<id>` - 删除需求

### 里程碑相关接口
- `GET /api/milestones/<project_id>` - 获取项目里程碑列表
- `POST /api/milestones/<project_id>` - 创建里程碑
- `GET /api/milestones/<project_id>/<id>` - 获取里程碑详情
- `PUT /api/milestones/<project_id>/<id>` - 更新里程碑
- `DELETE /api/milestones/<project_id>/<id>` - 删除里程碑

### 分析相关接口
- `GET /api/comprehensive-analysis/<project_id>` - 获取综合分析数据
- `GET /api/kano/<project_id>` - 获取KANO分析数据
- `POST /api/kano/<project_id>` - 更新KANO分析数据
- `GET /api/vsm/<project_id>` - 获取VSM分析数据
- `POST /api/vsm/<project_id>` - 更新VSM分析数据
- `GET /api/smart/<project_id>` - 获取SMART目标数据
- `POST /api/smart/<project_id>` - 更新SMART目标数据
- `GET /api/wfmt/<project_id>` - 获取WFMT分析数据
- `POST /api/wfmt/<project_id>` - 更新WFMT分析数据

### 导入导出接口
- `GET /api/templates/<template_type>` - 下载模板文件
- `POST /api/import/pdf/<project_id>` - 导入PDF文件
- `GET /api/export/<data_type>/<project_id>` - 导出数据

## 数据库设计

系统使用SQLite数据库，通过SQLAlchemy ORM进行数据库操作。主要数据表包括：

1. projects - 项目表
2. stakeholders - 干系人表
3. requirements - 需求表
4. milestones - 里程碑表

所有表都包含created_at和updated_at字段用于记录创建和更新时间。

## 部署说明

### 环境要求
- Python 3.6或更高版本
- pip包管理工具

### 安装步骤
1. 克隆项目代码到本地
2. 安装依赖包：
   ```
   pip install -r requirements.txt
   ```
3. 运行应用：
   ```
   python app.py
   ```
4. 在浏览器中访问 `http://localhost:5000`

### 配置说明
系统会在首次运行时自动生成配置文件config.ini，包含以下配置项：
- secret_key: Flask应用密钥
- 默认用户账号和密码

## 开发规范

### 代码规范
- 遵循PEP8 Python编码规范
- 使用Flask应用工厂模式组织代码
- 合理使用蓝图(Blueprint)进行模块化开发

### 命名规范
- 类名使用大驼峰命名法
- 函数和变量使用小写字母加下划线命名法
- 常量使用全大写字母加下划线命名法

### 注释规范
- 类和函数需要添加文档字符串
- 复杂逻辑需要添加行内注释
- 变量命名应具有自解释性

## 扩展开发

### 添加新的分析方法
1. 在Requirement模型中添加相应的字段
2. 在数据库中添加对应的列
3. 创建对应的模板页面
4. 实现数据处理API接口
5. 在综合分析中添加相关统计

### 添加新的导出格式
1. 在导出API中添加新的格式处理逻辑
2. 实现对应的文件生成方法
3. 在前端界面中添加格式选项

## 常见问题

### 数据库迁移
系统使用SQLite数据库，如需修改数据模型，需要手动更新数据库结构或使用数据库迁移工具。

### 性能优化
对于大量数据处理，建议：
1. 添加适当的数据库索引
2. 使用分页查询
3. 合理使用缓存机制

### 安全性
1. 系统使用会话认证，确保用户登录后才能访问
2. 对用户输入进行验证和过滤
3. 敏感操作使用POST请求