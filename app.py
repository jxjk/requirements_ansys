# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for, make_response, session, flash
from datetime import datetime
from database import db, init_db
from models import Project, Stakeholder, Requirement, Milestone
import json
import functools
import logging
import hashlib
import os
import secrets
from configparser import ConfigParser
import csv
import PyPDF2
import io
import re
from werkzeug.utils import secure_filename


app = Flask(__name__)

# 读取配置文件
config = ConfigParser()
config_file = 'config.ini'

# 如果配置文件不存在，创建一个默认的
if not os.path.exists(config_file):
    config['DEFAULT'] = {
        'secret_key': secrets.token_hex(16)  # 生成随机密钥
    }
    config['USERS'] = {
        'admin': hashlib.sha256('admin123'.encode()).hexdigest()  # 默认用户: admin / admin123
    }
    with open(config_file, 'w') as f:
        config.write(f)

config.read(config_file)
app.secret_key = config.get('DEFAULT', 'secret_key')

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化数据库
init_db(app)

# 添加响应后处理器，禁用缓存
@app.after_request
def after_request(response):
    """为所有响应添加缓存控制头"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

def login_required(f):
    """装饰器：要求用户登录"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': '需要登录'}), 401
        return f(*args, **kwargs)
    return decorated_function

def verify_user(username, password):
    """验证用户凭据"""
    if 'USERS' not in config:
        return False
    
    users = dict(config['USERS'])
    if username in users:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        return users[username] == hashed_password
    return False

def add_user(username, password):
    """添加新用户"""
    # 检查用户是否已存在
    if 'USERS' not in config:
        config['USERS'] = {}
    
    users = dict(config['USERS'])
    if username in users:
        return False  # 用户已存在
    
    # 添加新用户
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    config['USERS'][username] = hashed_password
    
    # 保存到配置文件
    with open(config_file, 'w') as f:
        config.write(f)
    
    return True

def log_deletion(user_id, item_type, item_id, item_name):
    """记录删除操作日志"""
    logger.info(f"用户 {user_id} 删除了 {item_type} (ID: {item_id}, 名称: {item_name})")

def add_cache_headers(response, status_code=200):
    """为响应添加缓存控制头"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.status_code = status_code
    return response

# 主页路由
@app.route('/')
def index():
    """主页 - 项目列表"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    projects = Project.query.all()
    response = make_response(render_template('index.html', projects=projects))
    return response

# 用户认证路由
@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return render_template('register.html', error='用户名和密码不能为空')
        
        if len(password) < 6:
            return render_template('register.html', error='密码长度至少为6位')
        
        # 添加用户
        if add_user(username, password):
            flash('注册成功，请登录', 'success')
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error='用户名已存在')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 验证用户凭据
        if verify_user(username, password):
            session['user_id'] = username
            session['username'] = username
            return redirect(url_for('index'))
        else:
            # 登录失败，返回错误信息
            return render_template('login.html', error='用户名或密码错误')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """用户登出"""
    session.pop('user_id', None)
    session.pop('username', None)
    flash('您已成功登出', 'info')
    return redirect(url_for('login'))

# 项目管理路由
@app.route('/project/create', methods=['POST'])
@login_required
def create_project():
    """创建新项目"""
    name = request.form.get('name')
    description = request.form.get('description')
    
    if name:
        project = Project(name=name, description=description)
        db.session.add(project)
        db.session.commit()
        logger.info(f"用户 {session['user_id']} 创建了项目: {name}")
    
    return redirect(url_for('index'))

@app.route('/project/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    """删除项目"""
    project = Project.query.get_or_404(project_id)
    
    # 记录删除日志
    log_deletion(session['user_id'], '项目', project_id, project.name)
    
    # 删除项目相关的所有数据
    Stakeholder.query.filter_by(project_id=project_id).delete()
    Requirement.query.filter_by(project_id=project_id).delete()
    Milestone.query.filter_by(project_id=project_id).delete()
    
    # 删除项目本身
    db.session.delete(project)
    db.session.commit()
    
    logger.info(f"用户 {session['user_id']} 删除了项目: {project.name}")
    return jsonify({'success': True})

@app.route('/project/<int:project_id>')
@login_required
def project_detail(project_id):
    """项目详情页"""
    project = Project.query.get_or_404(project_id)
    response = make_response(render_template('project_detail.html', project=project))
    return response

# 干系人管理路由
@app.route('/project/<int:project_id>/stakeholders')
@login_required
def stakeholder_management(project_id):
    """干系人管理页面"""
    project = Project.query.get_or_404(project_id)
    response = make_response(render_template('stakeholder_management.html', project=project))
    return response

@app.route('/api/stakeholders/<int:project_id>', methods=['GET', 'POST'])
@login_required
def api_stakeholders(project_id):
    """干系人API接口"""
    if request.method == 'POST':
        data = request.get_json()
        stakeholder = Stakeholder(
            project_id=project_id,
            name=data['name'],
            role=data['role'],
            influence=int(data['influence']),
            interest=int(data['interest']),
            requirements=data['requirements'],
            contact_info=data['contact_info'],
            notes=data['notes']
        )
        db.session.add(stakeholder)
        db.session.commit()
        logger.info(f"用户 {session['user_id']} 创建了干系人: {data['name']}")
        response = jsonify({'success': True, 'id': stakeholder.id})
        return add_cache_headers(response)
    
    stakeholders = Stakeholder.query.filter_by(project_id=project_id).all()
    response = jsonify([{
        'id': s.id,
        'name': s.name,
        'role': s.role,
        'influence': s.influence,
        'interest': s.interest,
        'requirements': s.requirements,
        'contact_info': s.contact_info,
        'notes': s.notes
    } for s in stakeholders])
    return response

@app.route('/api/stakeholders/<int:stakeholder_id>', methods=['PUT', 'DELETE'])
@login_required
def api_stakeholder_detail(stakeholder_id):
    """单个干系人API接口"""
    stakeholder = Stakeholder.query.get_or_404(stakeholder_id)
    
    if request.method == 'PUT':
        data = request.get_json()
        old_name = stakeholder.name
        stakeholder.name = data['name']
        stakeholder.role = data['role']
        stakeholder.influence = int(data['influence'])
        stakeholder.interest = int(data['interest'])
        stakeholder.requirements = data['requirements']
        stakeholder.contact_info = data['contact_info']
        stakeholder.notes = data['notes']
        
        db.session.commit()
        logger.info(f"用户 {session['user_id']} 更新了干系人: {old_name} -> {stakeholder.name}")
        return add_cache_headers(jsonify({'success': True}))
    
    elif request.method == 'DELETE':
        # 记录删除日志
        log_deletion(session['user_id'], '干系人', stakeholder_id, stakeholder.name)
        
        db.session.delete(stakeholder)
        db.session.commit()
        logger.info(f"用户 {session['user_id']} 删除了干系人: {stakeholder.name}")
        return add_cache_headers(jsonify({'success': True}))

# 需求采集路由
@app.route('/project/<int:project_id>/requirements')
@login_required
def requirement_collection(project_id):
    """需求采集页面"""
    project = Project.query.get_or_404(project_id)
    stakeholders = Stakeholder.query.filter_by(project_id=project_id).all()
    response = make_response(render_template('requirement_collection.html', 
                          project=project, stakeholders=stakeholders))
    return response

# 需求API接口 - 完整版本
@app.route('/api/requirements/<int:project_id>', methods=['GET', 'POST'])
@login_required
def api_requirements(project_id):
    """需求API接口"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            print(f"Received requirement data: {data}")
            
            if not data or 'title' not in data:
                return add_cache_headers(jsonify({'success': False, 'error': '缺少必要字段: title'}), 400)
            
            # 计算预估ROI
            estimated_business_value = int(data.get('estimated_business_value', 5))
            estimated_user_value = int(data.get('estimated_user_value', 5))
            estimated_technical_value = int(data.get('estimated_technical_value', 5))
            estimated_effort = int(data.get('estimated_effort', 5))
            
            if estimated_effort <= 0:
                estimated_effort = 1
            
            total_estimated_value = estimated_business_value + estimated_user_value + estimated_technical_value
            estimated_roi = total_estimated_value / estimated_effort
            
            requirement = Requirement(
                project_id=project_id,
                title=data['title'],
                priority=data.get('priority', 'medium'),
                status=data.get('status', 'proposed'),
                category=data.get('category', 'business'),
                requirement_type=data.get('requirement_type', 'functional'),
                source=data.get('source', ''),
                value_assessor=data.get('value_assessor', ''),
                
                # 九要素字段
                scenario=data.get('scenario', ''),
                problem=data.get('problem', ''),
                current_solution=data.get('current_solution', ''),
                goal=data.get('goal', ''),
                expected_solution=data.get('expected_solution', ''),
                value=data.get('value', ''),
                other_info=data.get('other_info', ''),
                
                # 价值评估字段
                estimated_business_value=estimated_business_value,
                estimated_user_value=estimated_user_value,
                estimated_technical_value=estimated_technical_value,
                estimated_effort=estimated_effort,
                estimated_roi=estimated_roi,
                
                # KANO分类
                kano_category=data.get('kano_category', ''),
                
                # VSM相关字段
                vsm_process_steps=data.get('vsm_process_steps', ''),
                cycle_time=data.get('cycle_time'),
                lead_time=data.get('lead_time'),
                
                # SMART目标字段
                smart_specific=data.get('smart_specific', ''),
                smart_measurable=data.get('smart_measurable', ''),
                smart_achievable=data.get('smart_achievable', True),
                smart_relevant=data.get('smart_relevant', ''),
                smart_timebound=data.get('smart_timebound')
            )
            
            db.session.add(requirement)
            db.session.commit()
            logger.info(f"用户 {session['user_id']} 创建了需求: {data['title']}")
            response = jsonify({'success': True, 'id': requirement.id})
            return add_cache_headers(response)
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating requirement: {str(e)}")
            return add_cache_headers(jsonify({'success': False, 'error': str(e)}), 500)
    
    # GET方法 - 获取项目的所有需求
    requirements = Requirement.query.filter_by(project_id=project_id).all()
    response = jsonify([{
        'id': r.id,
        'title': r.title,
        'description': r.description,
        'priority': r.priority,
        'status': r.status,
        'category': r.category,
        'requirement_type': r.requirement_type,
        'source': r.source,
        'estimated_roi': float(r.estimated_roi) if r.estimated_roi else 0,
        'actual_roi': float(r.actual_roi) if r.actual_roi else 0,
        'kano_category': r.kano_category,
        'created_at': r.created_at.isoformat() if r.created_at else None,
        'updated_at': r.updated_at.isoformat() if r.updated_at else None
    } for r in requirements])
    return response

@app.route('/api/requirements/<int:req_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_requirement_detail(req_id):
    """单个需求API接口"""
    requirement = Requirement.query.get_or_404(req_id)
    
    if request.method == 'GET':
        response = jsonify({
            'id': requirement.id,
            'title': requirement.title,
            'description': requirement.description,
            'priority': requirement.priority,
            'status': requirement.status,
            'category': requirement.category,
            'requirement_type': requirement.requirement_type,
            'source': requirement.source,
            'value_assessor': requirement.value_assessor,
            'estimated_business_value': requirement.estimated_business_value,
            'estimated_user_value': requirement.estimated_user_value,
            'estimated_technical_value': requirement.estimated_technical_value,
            'estimated_effort': requirement.estimated_effort,
            'estimated_roi': float(requirement.estimated_roi) if requirement.estimated_roi else 0,
            'actual_business_value': requirement.actual_business_value,
            'actual_user_value': requirement.actual_user_value,
            'actual_technical_value': requirement.actual_technical_value,
            'actual_effort': requirement.actual_effort,
            'actual_roi': float(requirement.actual_roi) if requirement.actual_roi else 0,
            'actual_value_assessor': requirement.actual_value_assessor,
            'actual_value_assessment_date': requirement.actual_value_assessment_date.isoformat() if requirement.actual_value_assessment_date else None,
            'kano_category': requirement.kano_category,
            'vsm_process_steps': requirement.vsm_process_steps,
            'cycle_time': requirement.cycle_time,
            'lead_time': requirement.lead_time,
            'smart_specific': requirement.smart_specific,
            'smart_measurable': requirement.smart_measurable,
            'smart_achievable': requirement.smart_achievable,
            'smart_relevant': requirement.smart_relevant,
            'smart_timebound': requirement.smart_timebound.isoformat() if requirement.smart_timebound else None,
            'scenario': requirement.scenario,
            'problem': requirement.problem,
            'current_solution': requirement.current_solution,
            'goal': requirement.goal,
            'expected_solution': requirement.expected_solution,
            'value': requirement.value,
            'other_info': requirement.other_info,
            'created_at': requirement.created_at.isoformat() if requirement.created_at else None,
            'updated_at': requirement.updated_at.isoformat() if requirement.updated_at else None
        })
        return response
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            old_title = requirement.title
            requirement.title = data['title']
            requirement.description = data.get('description', requirement.description)
            requirement.priority = data.get('priority', requirement.priority)
            requirement.status = data.get('status', requirement.status)
            requirement.category = data.get('category', requirement.category)
            requirement.requirement_type = data.get('requirement_type', requirement.requirement_type)
            requirement.source = data.get('source', requirement.source)
            
            # 更新九要素字段
            requirement.scenario = data.get('scenario', requirement.scenario)
            requirement.problem = data.get('problem', requirement.problem)
            requirement.current_solution = data.get('current_solution', requirement.current_solution)
            requirement.goal = data.get('goal', requirement.goal)
            requirement.expected_solution = data.get('expected_solution', requirement.expected_solution)
            requirement.value = data.get('value', requirement.value)
            requirement.other_info = data.get('other_info', requirement.other_info)
            
            # 更新价值评估字段
            requirement.estimated_business_value = int(data.get('estimated_business_value', requirement.estimated_business_value))
            requirement.estimated_user_value = int(data.get('estimated_user_value', requirement.estimated_user_value))
            requirement.estimated_technical_value = int(data.get('estimated_technical_value', requirement.estimated_technical_value))
            requirement.estimated_effort = int(data.get('estimated_effort', requirement.estimated_effort))
            
            # 重新计算预估ROI
            if requirement.estimated_effort > 0:
                total_value = (requirement.estimated_business_value + 
                              requirement.estimated_user_value + 
                              requirement.estimated_technical_value)
                requirement.estimated_roi = total_value / requirement.estimated_effort
            else:
                requirement.estimated_roi = 0
            
            requirement.value_assessor = data.get('value_assessor', requirement.value_assessor)
            requirement.updated_at = datetime.utcnow()
            
            db.session.commit()
            logger.info(f"用户 {session['user_id']} 更新了需求: {old_title} -> {requirement.title}")
            return add_cache_headers(jsonify({'success': True}))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating requirement: {str(e)}")
            return add_cache_headers(jsonify({'success': False, 'error': str(e)}), 500)

    elif request.method == 'DELETE':
        # 记录删除日志
        log_deletion(session['user_id'], '需求', req_id, requirement.title)
        
        db.session.delete(requirement)
        db.session.commit()
        logger.info(f"用户 {session['user_id']} 删除了需求: {requirement.title}")
        return add_cache_headers(jsonify({'success': True}))

@app.route('/api/requirements/detail/<int:req_id>')
@login_required
def get_requirement_detail(req_id):
    """获取需求详情"""
    requirement = Requirement.query.get_or_404(req_id)
    response = jsonify({
        'id': requirement.id,
        'title': requirement.title,
        'requirement_type': requirement.requirement_type,
        'scenario': requirement.scenario,
        'problem': requirement.problem,
        'current_solution': requirement.current_solution,
        'goal': requirement.goal,
        'expected_solution': requirement.expected_solution,
        'value': requirement.value,
        'other_info': requirement.other_info
    })
    return response

# 价值评估路由
@app.route('/project/<int:project_id>/value-assessment')
@login_required
def value_assessment(project_id):
    """价值评估页面"""
    project = Project.query.get_or_404(project_id)
    requirements = Requirement.query.filter_by(project_id=project_id).all()
    
    # 计算已完成价值评估的需求
    completed_requirements = [r for r in requirements if r.actual_roi is not None]
    
    # 计算平均准确度
    average_accuracy = 0
    if completed_requirements:
        total_accuracy = 0
        for r in completed_requirements:
            if r.actual_roi and r.estimated_roi:
                accuracy = (1 - abs(r.actual_roi - r.estimated_roi) / r.actual_roi) * 100
                total_accuracy += accuracy
        average_accuracy = total_accuracy / len(completed_requirements)
    
    # 计算最佳评估者
    performer_scores = {}
    for r in completed_requirements:
        if r.actual_value_assessor:
            if r.actual_value_assessor not in performer_scores:
                performer_scores[r.actual_value_assessor] = []
            if r.actual_roi and r.estimated_roi:
                accuracy = (1 - abs(r.actual_roi - r.estimated_roi) / r.actual_roi) * 100
                performer_scores[r.actual_value_assessor].append(accuracy)
    
    best_performer = None
    if performer_scores:
        avg_scores = {k: sum(v)/len(v) for k, v in performer_scores.items()}
        best_performer = max(avg_scores.items(), key=lambda x: x[1])[0]
    
    response = make_response(render_template('value_assessment.html',
                         project=project,
                         requirements=requirements,
                         completed_requirements=completed_requirements,
                         average_accuracy=average_accuracy/100,
                         best_performer=best_performer,
                         improvement_trend="↑ 改善" if len(completed_requirements) > 3 else "→ 稳定"))
    return response

@app.route('/api/requirements/<int:req_id>/actual-value', methods=['POST'])
@login_required
def submit_actual_value(req_id):
    """提交实际价值评估"""
    requirement = Requirement.query.get_or_404(req_id)
    data = request.get_json()
    
    requirement.actual_business_value = data['actual_business_value']
    requirement.actual_user_value = data['actual_user_value']
    requirement.actual_technical_value = data['actual_technical_value']
    requirement.actual_effort = data['actual_effort']
    requirement.actual_value_assessor = data['actual_value_assessor']
    requirement.actual_value_assessment_date = datetime.utcnow()
    
    # 计算实际ROI
    total_actual_value = (requirement.actual_business_value + 
                         requirement.actual_user_value + 
                         requirement.actual_technical_value)
    requirement.actual_roi = total_actual_value / requirement.actual_effort if requirement.actual_effort > 0 else 0
    
    db.session.commit()
    
    logger.info(f"用户 {session['user_id']} 为需求 {requirement.title} 提交了实际价值评估")
    return add_cache_headers(jsonify({'success': True}))

@app.route('/api/projects/<int:project_id>/value-report')
@login_required
def export_value_report(project_id):
    """导出价值评估报告"""
    project = Project.query.get_or_404(project_id)
    requirements = Requirement.query.filter_by(project_id=project_id).all()
    
    # 这里应该生成Excel文件，暂时返回JSON数据
    report_data = {
        'project_name': project.name,
        'export_date': datetime.utcnow().isoformat(),
        'requirements': []
    }
    
    for req in requirements:
        report_data['requirements'].append({
            'title': req.title,
            'estimated_roi': float(req.estimated_roi) if req.estimated_roi else 0,
            'actual_roi': float(req.actual_roi) if req.actual_roi else 0,
            'accuracy': (1 - abs((req.actual_roi or 0) - (req.estimated_roi or 0)) / (req.actual_roi or 1)) * 100 if req.actual_roi else 0,
            'value_assessor': req.value_assessor or ''
        })
    
    response = jsonify(report_data)
    response.headers['Content-Disposition'] = f'attachment; filename=value_report_{project_id}.json'
    logger.info(f"用户 {session['user_id']} 导出了项目 {project.name} 的价值评估报告")
    return response

# 需求分析路由
@app.route('/project/<int:project_id>/requirement-analysis')
@login_required
def requirement_analysis(project_id):
    """需求分析页面"""
    project = Project.query.get_or_404(project_id)
    requirements = Requirement.query.filter_by(project_id=project_id).all()
    
    # 统计优先级和分类
    priority_stats = {}
    category_stats = {}
    for req in requirements:
        priority_stats[req.priority] = priority_stats.get(req.priority, 0) + 1
        category_stats[req.category] = category_stats.get(req.category, 0) + 1
    
    response = make_response(render_template('requirement_analysis.html',
                          project=project,
                          requirements=requirements,
                          priority_stats=priority_stats,
                          category_stats=category_stats))
    return response

# 路线图规划路由
@app.route('/project/<int:project_id>/roadmap')
@login_required
def roadmap_planning(project_id):
    """路线图规划页面"""
    project = Project.query.get_or_404(project_id)
    milestones = Milestone.query.filter_by(project_id=project_id).order_by(Milestone.deadline).all()
    requirements = Requirement.query.filter_by(project_id=project_id).all()
    
    # 按状态分组需求
    status_groups = {
        'collected': [],
        'analyzed': [],
        'approved': [],
        'implemented': [],
        'validated': []
    }
    
    for req in requirements:
        if req.status in status_groups:
            status_groups[req.status].append(req)
    
    response = make_response(render_template('roadmap_planning.html',
                          project=project,
                          milestones=milestones,
                          status_groups=status_groups))
    return response

@app.route('/api/roadmap/<int:project_id>')
@login_required
def api_roadmap_data(project_id):
    """获取用于路线图显示的里程碑数据"""
    milestones = Milestone.query.filter_by(project_id=project_id).order_by(Milestone.deadline).all()
    result = []
    for m in milestones:
        # 获取关联的需求
        req_ids = [int(r) for r in m.requirements.split(',')] if m.requirements else []
        requirements = Requirement.query.filter(Requirement.id.in_(req_ids)).all()
        
        result.append({
            'id': m.id,
            'title': m.title,
            'description': m.description,
            'deadline': m.deadline.strftime('%Y-%m-%d') if m.deadline else None,
            'status': m.status,
            'requirements': [{
                'id': r.id,
                'title': r.title,
                'priority': r.priority,
                'status': r.status,
                'category': r.category,
                'estimated_roi': float(r.estimated_roi) if r.estimated_roi is not None else 0
            } for r in requirements]
        })
    
    return add_cache_headers(jsonify(result))

@app.route('/api/milestones/<int:project_id>', methods=['GET', 'POST'])
@login_required
def api_milestones(project_id):
    """里程碑API接口"""
    if request.method == 'POST':
        data = request.get_json()
        # 处理截止日期，允许为空
        deadline = None
        if data.get('deadline'):
            try:
                deadline = datetime.strptime(data['deadline'], '%Y-%m-%d').date()
            except ValueError:
                pass  # 如果日期格式不正确，保持为None
        
        milestone = Milestone(
            project_id=project_id,
            title=data['title'],
            description=data.get('description', ''),
            deadline=deadline,
            requirements=','.join(map(str, data.get('requirements', []))),
            status=data.get('status', 'planned')
        )
        db.session.add(milestone)
        db.session.commit()
        logger.info(f"用户 {session['user_id']} 创建了里程碑: {data['title']}")
        response = jsonify({'success': True, 'id': milestone.id})
        return add_cache_headers(response)
    
    milestones = Milestone.query.filter_by(project_id=project_id).all()
    response = jsonify([{
        'id': m.id,
        'title': m.title,
        'description': m.description,
        'deadline': m.deadline.strftime('%Y-%m-%d') if m.deadline else None,
        'requirements': m.requirements,
        'status': m.status
    } for m in milestones])
    return response

@app.route('/api/milestones/<int:milestone_id>', methods=['PUT', 'DELETE'])
@login_required
def api_milestone_detail(milestone_id):
    """单个里程碑API接口"""
    milestone = Milestone.query.get_or_404(milestone_id)
    
    if request.method == 'PUT':
        data = request.get_json()
        old_title = milestone.title
        milestone.title = data['title']
        milestone.description = data.get('description', milestone.description)
        
        # 处理截止日期
        deadline = None
        if data.get('deadline'):
            try:
                deadline = datetime.strptime(data['deadline'], '%Y-%m-%d').date()
            except ValueError:
                pass
        milestone.deadline = deadline
        
        milestone.requirements = ','.join(map(str, data.get('requirements', [])))
        milestone.status = data.get('status', milestone.status)
        
        db.session.commit()
        logger.info(f"用户 {session['user_id']} 更新了里程碑: {old_title} -> {milestone.title}")
        return add_cache_headers(jsonify({'success': True}))
    
    elif request.method == 'DELETE':
        # 记录删除日志
        log_deletion(session['user_id'], '里程碑', milestone_id, milestone.title)
        
        db.session.delete(milestone)
        db.session.commit()
        logger.info(f"用户 {session['user_id']} 删除了里程碑: {milestone.title}")
        return add_cache_headers(jsonify({'success': True}))

# KANO分析路由
@app.route('/project/<int:project_id>/kano')
@login_required
def kano_analysis(project_id):
    """KANO分析页面"""
    project = Project.query.get_or_404(project_id)
    requirements = Requirement.query.filter_by(project_id=project_id).all()
    
    # 按KANO分类分组
    kano_groups = {
        'must_be': [],
        'one_dimensional': [],
        'attractive': [],
        'indifferent': [],
        'reverse': []
    }
    
    for req in requirements:
        if req.kano_category in kano_groups:
            kano_groups[req.kano_category].append(req)
    
    response = make_response(render_template('kano_analysis.html',
                          project=project,
                          kano_groups=kano_groups))
    return response

# VSM分析路由
@app.route('/project/<int:project_id>/vsm')
@login_required
def vsm_analysis(project_id):
    """VSM分析页面"""
    project = Project.query.get_or_404(project_id)
    requirements = Requirement.query.filter_by(project_id=project_id).filter(Requirement.vsm_process_steps != None).all()
    
    response = make_response(render_template('vsm_analysis.html',
                          project=project,
                          requirements=requirements))
    return response

# SMART目标路由
@app.route('/project/<int:project_id>/smart')
@login_required
def smart_goals(project_id):
    """SMART目标页面"""
    project = Project.query.get_or_404(project_id)
    requirements = Requirement.query.filter_by(project_id=project_id).filter(Requirement.smart_specific != None).all()
    
    response = make_response(render_template('smart_goals.html',
                          project=project,
                          requirements=requirements))
    return response

# WFMT分析路由
@app.route('/project/<int:project_id>/wfmt')
@login_required
def wfmt_analysis(project_id):
    """WFMT分析页面"""
    project = Project.query.get_or_404(project_id)
    requirements = Requirement.query.filter_by(project_id=project_id).all()
    
    # 筛选有WFMT数据的需求
    wfmt_requirements = [r for r in requirements if r.standard_time is not None]
    
    response = make_response(render_template('wfmt_analysis.html',
                          project=project,
                          requirements=wfmt_requirements))
    return response

# 看板视图路由
@app.route('/project/<int:project_id>/kanban')
@login_required
def kanban_view(project_id):
    """看板视图页面"""
    project = Project.query.get_or_404(project_id)
    requirements = Requirement.query.filter_by(project_id=project_id).all()
    
    status_groups = {
        'collected': [r for r in requirements if r.status == 'collected'],
        'analyzing': [r for r in requirements if r.status == 'analyzing'],
        'confirmed': [r for r in requirements if r.status == 'confirmed'],
        'rejected': [r for r in requirements if r.status == 'rejected']
    }
    
    response = make_response(render_template('kanban.html',
                          project=project,
                          status_groups=status_groups))
    return response

@app.route('/api/wfmt/<int:project_id>', methods=['GET', 'POST'])
@login_required
def api_wfmt_analysis(project_id):
    """WFMT分析API"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            requirement_id = data.get('requirement_id')
            
            requirement = Requirement.query.filter_by(id=requirement_id, project_id=project_id).first_or_404()
            
            # 更新WFMT相关字段
            requirement.wfmt_analysis = data.get('analysis_data')
            requirement.standard_time = data.get('standard_time')
            requirement.improvement_potential = data.get('improvement_potential')
            requirement.wfmt_tmu_total = data.get('tmu_total')
            requirement.wfmt_allowance_rate = data.get('allowance_rate', 15.0)  # 默认15%宽放率
            
            db.session.commit()
            logger.info(f"用户 {session['user_id']} 为需求 {requirement.title} 更新了WFMT分析数据")
            return add_cache_headers(jsonify({'success': True}))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in WFMT analysis: {str(e)}")
            return add_cache_headers(jsonify({'success': False, 'error': str(e)}), 500)
    
    # GET方法 - 获取项目的WFMT分析概览
    requirements = Requirement.query.filter_by(project_id=project_id).all()
    wfmt_data = []
    
    for req in requirements:
        if req.standard_time:
            wfmt_data.append({
                'id': req.id,
                'title': req.title,
                'standard_time': req.standard_time,
                'improvement_potential': req.improvement_potential,
                'tmu_total': req.wfmt_tmu_total,
                'allowance_rate': req.wfmt_allowance_rate
            })
    
    return add_cache_headers(jsonify(wfmt_data))

# 综合分析报告API
@app.route('/project/<int:project_id>/comprehensive-analysis')
@login_required
def comprehensive_analysis(project_id):
    """综合分析页面"""
    project = Project.query.get_or_404(project_id)
    response = make_response(render_template('comprehensive_analysis.html', project=project))
    return response

@app.route('/api/comprehensive-analysis/<int:project_id>')
@login_required
def comprehensive_analysis_api(project_id):
    """综合分析报告API"""
    try:
        project = Project.query.get_or_404(project_id)
        requirements = Requirement.query.filter_by(project_id=project_id).all()
        
        # 数据质量分析
        total_requirements = len(requirements)
        requirements_with_kano = len([r for r in requirements if r.kano_category])
        requirements_with_vsm = len([r for r in requirements if r.vsm_process_steps])
        requirements_with_smart = len([r for r in requirements if r.smart_specific])
        requirements_with_wfmt = len([r for r in requirements if r.standard_time is not None])
        requirements_with_value = len([r for r in requirements if r.estimated_roi is not None])
        
        data_quality = {
            'total_requirements': total_requirements,
            'kano_completion_rate': (requirements_with_kano / total_requirements * 100) if total_requirements > 0 else 0,
            'vsm_completion_rate': (requirements_with_vsm / total_requirements * 100) if total_requirements > 0 else 0,
            'smart_completion_rate': (requirements_with_smart / total_requirements * 100) if total_requirements > 0 else 0,
            'wfmt_completion_rate': (requirements_with_wfmt / total_requirements * 100) if total_requirements > 0 else 0,
            'value_completion_rate': (requirements_with_value / total_requirements * 100) if total_requirements > 0 else 0,
        }
        
        # 计算整体完成率
        overall_completion_rate = (
            data_quality['kano_completion_rate'] +
            data_quality['vsm_completion_rate'] +
            data_quality['smart_completion_rate'] +
            data_quality['wfmt_completion_rate'] +
            data_quality['value_completion_rate']
        ) / 5
        
        data_quality['overall_completion_rate'] = overall_completion_rate
        
        # 价值分析
        total_estimated_value = sum([r.estimated_roi or 0 for r in requirements])
        total_actual_value = sum([r.actual_roi or 0 for r in requirements if r.actual_roi is not None])
        
        value_analysis = {
            'total_estimated_value': total_estimated_value,
            'total_actual_value': total_actual_value,
            'value_accuracy': (total_actual_value / total_estimated_value * 100) if total_estimated_value > 0 else 0
        }
        
        # 分类统计
        priority_stats = {}
        category_stats = {}
        kano_stats = {}
        
        for req in requirements:
            priority_stats[req.priority] = priority_stats.get(req.priority, 0) + 1
            category_stats[req.category] = category_stats.get(req.category, 0) + 1
            kano_stats[req.kano_category] = kano_stats.get(req.kano_category, 0) + 1
        
        analysis_data = {
            'project_name': project.name,
            'data_quality': data_quality,
            'value_analysis': value_analysis,
            'priority_stats': priority_stats,
            'category_stats': category_stats,
            'kano_stats': kano_stats
        }
        
        # 生成建议
        recommendations = []
        if data_quality['overall_completion_rate'] < 50:
            recommendations.append('数据采集完成率较低，建议完善各分析方法的数据')
        elif data_quality['overall_completion_rate'] < 80:
            recommendations.append('数据采集完成率良好，建议继续完善剩余数据')
        else:
            recommendations.append('数据采集完成率优秀，可进行深度分析')
        
        analysis_data['recommendations'] = recommendations
        
        logger.info(f"用户 {session['user_id']} 查看了项目 {project.name} 的综合分析报告")
        return add_cache_headers(jsonify(analysis_data))
        
    except Exception as e:
        logger.error(f"综合分析报告生成失败: {str(e)}")
        return add_cache_headers(jsonify({'success': False, 'error': str(e)}), 500)

# 根据description字段解析九要素内容
def parse_description_fields(description):
    """解析description字段中的九要素内容"""
    if not description:
        return {}
    
    # 按照九要素分割描述内容
    sections = re.split(r'\n\s*\n', description.strip())
    fields = {}
    
    for section in sections:
        if section.startswith('【场景描述】'):
            fields['scenario'] = section.replace('【场景描述】', '').strip()
        elif section.startswith('【解决的问题】'):
            fields['problem'] = section.replace('【解决的问题】', '').strip()
        elif section.startswith('【当前解决方案】'):
            fields['current_solution'] = section.replace('【当前解决方案】', '').strip()
        elif section.startswith('【目标】'):
            fields['goal'] = section.replace('【目标】', '').strip()
        elif section.startswith('【预期解决方案】'):
            fields['expected_solution'] = section.replace('【预期解决方案】', '').strip()
        elif section.startswith('【价值】'):
            fields['value'] = section.replace('【价值】', '').strip()
        elif section.startswith('【其他信息】'):
            fields['other_info'] = section.replace('【其他信息】', '').strip()
    
    return fields

# 根据九要素字段构建description
def build_description_from_fields(requirement):
    description = ''
    if requirement.scenario:
        description += f"【场景描述】\n{requirement.scenario}\n\n"
    if requirement.problem:
        description += f"【解决的问题】\n{requirement.problem}\n\n"
    if requirement.current_solution:
        description += f"【当前解决方案】\n{requirement.current_solution}\n\n"
    if requirement.goal:
        description += f"【目标】\n{requirement.goal}\n\n"
    if requirement.expected_solution:
        description += f"【预期解决方案】\n{requirement.expected_solution}\n\n"
    if requirement.value:
        description += f"【价值】\n{requirement.value}\n\n"
    if requirement.other_info:
        description += f"【其他信息】\n{requirement.other_info}\n\n"
    return description

# 数据诊断和修复端点
@app.route('/api/diagnose/requirements/<int:project_id>')
@login_required
def diagnose_requirements(project_id):
    """诊断需求数据问题"""
    try:
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'success': False, 'error': f'项目 {project_id} 不存在'})
        
        all_requirements = Requirement.query.all()
        
        correct_requirements = []
        incorrect_requirements = []
        orphaned_requirements = []
        
        for req in all_requirements:
            if req.project_id == project_id:
                correct_requirements.append(req)
            elif req.project_id is None or req.project_id == 0:
                orphaned_requirements.append(req)
            else:
                incorrect_requirements.append(req)
        
        # 修复孤立的需求
        fixed_count = 0
        for req in orphaned_requirements:
            req.project_id = project_id
            fixed_count += 1
        
        if fixed_count > 0:
            db.session.commit()
        
        result = {
            'success': True,
            'project_name': project.name,
            'total_requirements': len(all_requirements),
            'correct_requirements': len(correct_requirements),
            'incorrect_requirements': len(incorrect_requirements),
            'orphaned_requirements': len(orphaned_requirements),
            'fixed_orphaned': fixed_count,
            'message': f'诊断完成，修复了 {fixed_count} 个孤立需求'
        }
        
        logger.info(f"用户 {session['user_id']} 对项目 {project.name} 进行了需求数据诊断")
        return add_cache_headers(jsonify(result))
        
    except Exception as e:
        logger.error(f"需求数据诊断失败: {str(e)}")
        return add_cache_headers(jsonify({'success': False, 'error': str(e)}), 500)

# PDF数据导入功能
@app.route('/api/import/pdf/<int:project_id>', methods=['POST'])
@login_required
def import_pdf_data(project_id):
    """导入PDF文件数据"""
    try:
        if 'pdf_file' not in request.files:
            return jsonify({'success': False, 'error': '未选择文件'})
        
        pdf_file = request.files['pdf_file']
        if pdf_file.filename == '':
            return jsonify({'success': False, 'error': '未选择文件'})
        
        if not pdf_file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': '请上传PDF文件'})
        
        # 读取PDF内容
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text_content = ""
        for page in pdf_reader.pages:
            text_content += page.extract_text() + "\n"
        
        # 解析PDF内容并创建需求
        requirements_created = parse_pdf_content_and_create_requirements(project_id, text_content, pdf_file.filename)
        
        logger.info(f"用户 {session['user_id']} 从PDF文件 {pdf_file.filename} 导入了 {requirements_created} 个需求")
        return jsonify({
            'success': True, 
            'requirements_created': requirements_created,
            'message': f'成功导入 {requirements_created} 个需求'
        })
        
    except Exception as e:
        logger.error(f"PDF导入失败: {str(e)}")
        return jsonify({'success': False, 'error': f'导入失败: {str(e)}'})

def parse_pdf_content_and_create_requirements(project_id, text_content, filename):
    """解析PDF内容并创建需求"""
    requirements_created = 0
    
    # 根据文件名判断PDF类型并调用相应的解析器
    filename_lower = filename.lower()
    
    if 'kano' in filename_lower:
        requirements_created = parse_kano_pdf(project_id, text_content)
    elif 'vsm' in filename_lower:
        requirements_created = parse_vsm_pdf(project_id, text_content)
    elif 'smart' in filename_lower or 'smat' in filename_lower:
        requirements_created = parse_smart_pdf(project_id, text_content)
    elif 'wfmt' in filename_lower or '动作时间' in filename_lower:
        requirements_created = parse_wfmt_pdf(project_id, text_content)
    else:
        # 通用PDF解析
        requirements_created = parse_general_pdf(project_id, text_content)
    
    return requirements_created

def parse_kano_pdf(project_id, text_content):
    """解析KANO分析PDF"""
    requirements_created = 0
    
    # 查找需求标题和KANO分类
    lines = text_content.split('\n')
    current_requirement = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # 查找需求标题（通常包含"需求"、"功能"等关键词）
        if any(keyword in line for keyword in ['需求', '功能', '特性', 'feature']):
            title = line
            # 查找KANO分类
            kano_category = None
            for j in range(i+1, min(i+5, len(lines))):
                next_line = lines[j].strip()
                if any(cat in next_line for cat in ['基本型', '期望型', '兴奋型', '无差异型', '反向型']):
                    kano_category = extract_kano_category(next_line)
                    break
            
            if title and len(title) > 3:  # 确保标题有意义
                requirement = Requirement(
                    project_id=project_id,
                    title=title,
                    source='KANO分析PDF导入',
                    kano_category=kano_category
                )
                db.session.add(requirement)
                requirements_created += 1
    
    if requirements_created > 0:
        db.session.commit()
    
    return requirements_created

def extract_kano_category(text):
    """从文本中提取KANO分类"""
    if '基本型' in text:
        return 'must_be'
    elif '期望型' in text:
        return 'one_dimensional'
    elif '兴奋型' in text:
        return 'attractive'
    elif '无差异型' in text:
        return 'indifferent'
    elif '反向型' in text:
        return 'reverse'
    return None

def parse_vsm_pdf(project_id, text_content):
    """解析VSM分析PDF"""
    requirements_created = 0
    
    # 查找流程步骤和时间数据
    lines = text_content.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # 查找流程步骤
        if any(keyword in line for keyword in ['步骤', '流程', '活动', 'task']):
            title = f"VSM流程: {line}"
            
            # 查找相关的时间数据
            cycle_time = extract_time_data(lines, i, '周期时间', 'cycle')
            lead_time = extract_time_data(lines, i, '交付时间', 'lead')
            
            if title and len(title) > 5:
                requirement = Requirement(
                    project_id=project_id,
                    title=title,
                    source='VSM分析PDF导入',
                    vsm_process_steps=line,
                    cycle_time=cycle_time,
                    lead_time=lead_time
                )
                db.session.add(requirement)
                requirements_created += 1
    
    if requirements_created > 0:
        db.session.commit()
    
    return requirements_created

def extract_time_data(lines, start_index, keyword_ch, keyword_en):
    """从文本中提取时间数据"""
    for i in range(start_index+1, min(start_index+10, len(lines))):
        line = lines[i].strip()
        if keyword_ch in line or keyword_en in line:
            # 尝试提取数字
            numbers = re.findall(r'\d+\.?\d*', line)
            if numbers:
                return float(numbers[0])
    return None

def parse_smart_pdf(project_id, text_content):
    """解析SMART目标PDF"""
    requirements_created = 0
    
    lines = text_content.split('\n')
    current_goal = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # 查找目标标题
        if any(keyword in line for keyword in ['目标', 'goal', 'objective']):
            title = line
            smart_data = extract_smart_data(lines, i)
            
            if title and len(title) > 3:
                requirement = Requirement(
                    project_id=project_id,
                    title=title,
                    source='SMART目标PDF导入',
                    smart_specific=smart_data.get('specific'),
                    smart_measurable=smart_data.get('measurable'),
                    smart_achievable=True,
                    smart_relevant=smart_data.get('relevant'),
                    smart_timebound=smart_data.get('timebound')
                )
                db.session.add(requirement)
                requirements_created += 1
    
    if requirements_created > 0:
        db.session.commit()
    
    return requirements_created

def extract_smart_data(lines, start_index):
    """提取SMART目标数据"""
    smart_data = {}
    for i in range(start_index+1, min(start_index+20, len(lines))):
        line = lines[i].strip()
        if '具体' in line or 'specific' in line.lower():
            smart_data['specific'] = line
        elif '可衡量' in line or 'measurable' in line.lower():
            smart_data['measurable'] = line
        elif '相关' in line or 'relevant' in line.lower():
            smart_data['relevant'] = line
        elif '时限' in line or 'time' in line.lower():
            # 尝试提取日期
            date_match = re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', line)
            if date_match:
                try:
                    date_str = date_match.group()
                    smart_data['timebound'] = datetime.strptime(date_str.replace('/', '-'), '%Y-%m-%d').date()
                except:
                    pass
    
    return smart_data

def parse_wfmt_pdf(project_id, text_content):
    """解析WFMT动作时间分析PDF"""
    requirements_created = 0
    
    lines = text_content.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # 查找动作分析
        if any(keyword in line for keyword in ['动作', '操作', '步骤', 'action']):
            title = f"WFMT分析: {line}"
            
            # 查找标准时间
            standard_time = extract_time_data(lines, i, '标准时间', 'standard')
            improvement = extract_time_data(lines, i, '改善潜力', 'improvement')
            
            if title and len(title) > 5:
                requirement = Requirement(
                    project_id=project_id,
                    title=title,
                    source='WFMT分析PDF导入',
                    standard_time=standard_time,
                    improvement_potential=improvement
                )
                db.session.add(requirement)
                requirements_created += 1
    
    if requirements_created > 0:
        db.session.commit()
    
    return requirements_created

def parse_general_pdf(project_id, text_content):
    """通用PDF解析"""
    requirements_created = 0
    
    # 简单的段落分割，每个段落作为一个需求
    paragraphs = re.split(r'\n\s*\n', text_content)
    
    for para in paragraphs:
        para = para.strip()
        if len(para) > 50:  # 只处理有足够内容的段落
            # 提取第一行作为标题
            lines = para.split('\n')
            title = lines[0].strip() if lines else "PDF导入需求"
            
            if len(title) > 5:
                requirement = Requirement(
                    project_id=project_id,
                    title=title[:200],  # 限制标题长度
                    description=para,
                    source='PDF文件导入'
                )
                db.session.add(requirement)
                requirements_created += 1
    
    if requirements_created > 0:
        db.session.commit()
    
    return requirements_created

# 批量PDF导入功能
@app.route('/api/import/batch-pdf/<int:project_id>', methods=['POST'])
@login_required
def import_batch_pdf(project_id):
    """批量导入当前目录下的PDF文件"""
    try:
        current_dir = os.getcwd()
        pdf_files = [f for f in os.listdir(current_dir) if f.lower().endswith('.pdf')]
        
        total_requirements = 0
        import_results = []
        
        for pdf_file in pdf_files:
            file_path = os.path.join(current_dir, pdf_file)
            try:
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    text_content = ""
                    for page in pdf_reader.pages:
                        text_content += page.extract_text() + "\n"
                
                requirements_created = parse_pdf_content_and_create_requirements(project_id, text_content, pdf_file)
                total_requirements += requirements_created
                import_results.append({
                    'filename': pdf_file,
                    'requirements_created': requirements_created,
                    'status': 'success'
                })
                
            except Exception as e:
                import_results.append({
                    'filename': pdf_file,
                    'requirements_created': 0,
                    'status': 'error',
                    'error': str(e)
                })
        
        logger.info(f"用户 {session['user_id']} 批量导入了 {total_requirements} 个需求")
        return jsonify({
            'success': True,
            'total_requirements': total_requirements,
            'import_results': import_results,
            'message': f'批量导入完成，共创建 {total_requirements} 个需求'
        })
        
    except Exception as e:
        logger.error(f"批量PDF导入失败: {str(e)}")
        return jsonify({'success': False, 'error': f'批量导入失败: {str(e)}'})

# 导入导出页面路由
@app.route('/import-export')
@login_required
def import_export():
    """导入导出页面"""
    return render_template('import_export.html')

# 模板下载API
@app.route('/api/templates/<template_type>')
@login_required
def download_template(template_type):
    """下载CSV模板文件"""
    # 定义各种模板的字段
    templates = {
        'requirements_base': [
            'title', 'requirement_type', 'scenario', 'problem', 'current_solution',
            'goal', 'expected_solution', 'value', 'source', 'category', 'priority',
            'acceptance_criteria', 'target_user_group', 'estimated_business_value',
            'estimated_user_value', 'estimated_technical_value', 'estimated_effort'
        ],
        'kano_analysis': [
            'requirement_id', 'title', 'kano_category', 'kano_priority_score'
        ],
        'vsm_analysis': [
            'requirement_id', 'title', 'vsm_process_steps', 'cycle_time', 'lead_time'
        ],
        'smart_goals': [
            'requirement_id', 'title', 'smart_specific', 'smart_measurable', 
            'smart_achievable', 'smart_relevant', 'smart_timebound', 'smart_target_level'
        ],
        'wfmt_analysis': [
            'requirement_id', 'title', 'standard_time', 'improvement_potential', 
            'wfmt_tmu_total', 'wfmt_allowance_rate'
        ]
    }
    
    if template_type not in templates:
        return jsonify({'error': '模板类型不存在'}), 404
    
    # 创建CSV内容
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(templates[template_type])
    
    # 返回CSV文件
    csv_content = output.getvalue()
    output.close()
    
    response = make_response(csv_content)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename={template_type}_template.csv'
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
