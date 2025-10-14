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

@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证输入
        if not username or not password:
            return render_template('register.html', error='用户名和密码不能为空')
        
        if password != confirm_password:
            return render_template('register.html', error='密码不匹配')
        
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

@app.route('/')
def index():
    """主页 - 项目列表"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    projects = Project.query.all()
    response = make_response(render_template('index.html', projects=projects))
    return response

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
    return add_cache_headers(response)

@app.route('/api/stakeholders/<int:project_id>/<int:stakeholder_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_stakeholder_detail(project_id, stakeholder_id):
    """单个干系人API接口"""
    stakeholder = Stakeholder.query.filter_by(id=stakeholder_id, project_id=project_id).first_or_404()
    
    if request.method == 'GET':
        response = jsonify({
            'id': stakeholder.id,
            'name': stakeholder.name,
            'role': stakeholder.role,
            'influence': stakeholder.influence,
            'interest': stakeholder.interest,
            'requirements': stakeholder.requirements,
            'contact_info': stakeholder.contact_info,
            'notes': stakeholder.notes
        })
        return add_cache_headers(response)
    
    elif request.method == 'PUT':
        data = request.get_json()
        old_name = stakeholder.name
        stakeholder.name = data.get('name', stakeholder.name)
        stakeholder.role = data.get('role', stakeholder.role)
        stakeholder.influence = int(data.get('influence', stakeholder.influence))
        stakeholder.interest = int(data.get('interest', stakeholder.interest))
        stakeholder.requirements = data.get('requirements', stakeholder.requirements)
        stakeholder.contact_info = data.get('contact_info', stakeholder.contact_info)
        stakeholder.notes = data.get('notes', stakeholder.notes)
        stakeholder.updated_at = datetime.utcnow()
        
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
            estimated_roi = total_estimated_value / estimated_effort if estimated_effort > 0 else 0
            
            requirement = Requirement(
                project_id=project_id,
                title=data['title'],
                requirement_type=data.get('requirement_type', ''),
                scenario=data.get('scenario', ''),
                problem=data.get('problem', ''),
                current_solution=data.get('current_solution', ''),
                goal=data.get('goal', ''),
                expected_solution=data.get('expected_solution', ''),
                value=data.get('value', ''),
                priority_level=data.get('priority_level', 'medium'),
                other_info=data.get('other_info', ''),
                source=data.get('source', ''),
                category=data.get('category', 'functional'),
                priority=data.get('priority', 'medium'),
                acceptance_criteria=data.get('acceptance_criteria', ''),
                estimated_business_value=estimated_business_value,
                estimated_user_value=estimated_user_value,
                estimated_technical_value=estimated_technical_value,
                estimated_effort=estimated_effort,
                estimated_roi=estimated_roi,
                value_assessor=data.get('value_assessor', ''),
                expected_completion_date=data.get('expected_completion_date')
            )
            db.session.add(requirement)
            db.session.commit()
            logger.info(f"用户 {session['user_id']} 创建了需求: {data['title']}")
            return add_cache_headers(jsonify({'success': True, 'id': requirement.id}))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error saving requirement: {str(e)}")
            logger.error(f"Error saving requirement: {str(e)}")
            return add_cache_headers(jsonify({'success': False, 'error': str(e)}), 500)
    
    # GET方法
    try:
        requirements = Requirement.query.filter_by(project_id=project_id).all()
        result = []
        for r in requirements:
            req_data = {
                'id': r.id,
                'title': r.title if r.title else '',
                'description': build_description_from_fields(r),
                'requirement_type': r.requirement_type if r.requirement_type else '',
                'scenario': r.scenario if r.scenario else '',
                'problem': r.problem if r.problem else '',
                'current_solution': r.current_solution if r.current_solution else '',
                'goal': r.goal if r.goal else '',
                'expected_solution': r.expected_solution if r.expected_solution else '',
                'value': r.value if r.value else '',
                'priority_level': r.priority_level if r.priority_level else 'medium',
                'other_info': r.other_info if r.other_info else '',
                'source': r.source if r.source else '',
                'category': r.category if r.category else 'functional',
                'priority': r.priority if r.priority else 'medium',
                'status': r.status if r.status else 'collected',
                'acceptance_criteria': r.acceptance_criteria if r.acceptance_criteria else '',
                'estimated_business_value': r.estimated_business_value if r.estimated_business_value else 5,
                'estimated_user_value': r.estimated_user_value if r.estimated_user_value else 5,
            }
            result.append(req_data)
        
        return add_cache_headers(jsonify(result))
    except Exception as e:
        print(f"Error fetching requirements: {str(e)}")
        logger.error(f"Error fetching requirements: {str(e)}")
        return add_cache_headers(jsonify({'success': False, 'error': str(e)}), 500)

def parse_description_content(description):
    if not description:
        return {}
    
    fields = {}
    sections = description.split('\n\n')
    
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

@app.route('/api/requirements/<int:req_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_requirement_detail(req_id):
    """单个需求API接口"""
    requirement = Requirement.query.get_or_404(req_id)
    
    if request.method == 'GET':
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
            'priority_level': requirement.priority_level,
            'other_info': requirement.other_info,
            'source': requirement.source,
            'category': requirement.category,
            'priority': requirement.priority,
            'status': requirement.status,
            'acceptance_criteria': requirement.acceptance_criteria,
            'estimated_business_value': requirement.estimated_business_value,
            'estimated_user_value': requirement.estimated_user_value,
            'estimated_technical_value': requirement.estimated_technical_value,
            'estimated_effort': requirement.estimated_effort,
            'estimated_roi': requirement.estimated_roi,
            'actual_business_value': requirement.actual_business_value,
            'actual_user_value': requirement.actual_user_value,
            'actual_technical_value': requirement.actual_technical_value,
            'actual_effort': requirement.actual_effort,
            'actual_roi': requirement.actual_roi,
            'value_assessor': requirement.value_assessor,
            'actual_value_assessor': requirement.actual_value_assessor,
            'expected_completion_date': requirement.expected_completion_date.strftime('%Y-%m-%d') if requirement.expected_completion_date else None
        })
        return add_cache_headers(response)
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            old_title = requirement.title
            
            requirement.title = data.get('title', requirement.title)
            requirement.requirement_type = data.get('requirement_type', requirement.requirement_type)
            requirement.scenario = data.get('scenario', requirement.scenario)
            requirement.problem = data.get('problem', requirement.problem)
            requirement.current_solution = data.get('current_solution', requirement.current_solution)
            requirement.goal = data.get('goal', requirement.goal)
            requirement.expected_solution = data.get('expected_solution', requirement.expected_solution)
            requirement.value = data.get('value', requirement.value)
            requirement.priority_level = data.get('priority_level', requirement.priority_level)
            requirement.other_info = data.get('other_info', requirement.other_info)
            requirement.source = data.get('source', requirement.source)
            requirement.category = data.get('category', requirement.category)
            requirement.priority = data.get('priority', requirement.priority)
            requirement.status = data.get('status', requirement.status)
            requirement.acceptance_criteria = data.get('acceptance_criteria', requirement.acceptance_criteria)
            
            # 处理日期字段
            if 'expected_completion_date' in data:
                if data['expected_completion_date']:
                    try:
                        requirement.expected_completion_date = datetime.strptime(data['expected_completion_date'], '%Y-%m-%d').date()
                    except ValueError:
                        requirement.expected_completion_date = None
                else:
                    requirement.expected_completion_date = None
            
            # 更新预估价值
            if any(key in data for key in ['estimated_business_value', 'estimated_user_value', 'estimated_technical_value', 'estimated_effort']):
                requirement.estimated_business_value = int(data.get('estimated_business_value', requirement.estimated_business_value))
                requirement.estimated_user_value = int(data.get('estimated_user_value', requirement.estimated_user_value))
                requirement.estimated_technical_value = int(data.get('estimated_technical_value', requirement.estimated_technical_value))
                requirement.estimated_effort = int(data.get('estimated_effort', requirement.estimated_effort))
                
                # 重新计算ROI
                total_value = (requirement.estimated_business_value + 
                            requirement.estimated_user_value + 
                            requirement.estimated_technical_value)
                requirement.estimated_roi = total_value / requirement.estimated_effort if requirement.estimated_effort > 0 else 0
            
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

@app.route('/api/requirements/<int:req_id>/update', methods=['POST'])
@login_required
def update_requirement(req_id):
    """更新需求状态"""
    requirement = Requirement.query.get_or_404(req_id)
    data = request.get_json()
    
    if 'status' in data:
        requirement.status = data['status']
    if 'priority' in data:
        requirement.priority = data['priority']
    
    requirement.updated_at = datetime.utcnow()
    db.session.commit()
    
    logger.info(f"用户 {session['user_id']} 更新了需求 {requirement.title} 的状态为 {requirement.status}")
    return add_cache_headers(jsonify({'success': True}))

@app.route('/api/requirements/<int:req_id>/assign', methods=['POST'])
@login_required
def assign_requirement_to_milestone(req_id):
    """将需求分配到里程碑"""
    requirement = Requirement.query.get_or_404(req_id)
    data = request.get_json()
    milestone_id = data.get('milestone_id')
    
    requirement.assigned_milestone_id = milestone_id
    requirement.updated_at = datetime.utcnow()
    db.session.commit()
    
    logger.info(f"用户 {session['user_id']} 将需求 {requirement.title} 分配到里程碑 {milestone_id}")
    return add_cache_headers(jsonify({'success': True, 'message': '分配成功'}))

# 需求分析路由
@app.route('/project/<int:project_id>/analysis')
@login_required
def requirement_analysis(project_id):
    """需求分析页面"""
    project = Project.query.get_or_404(project_id)
    requirements = Requirement.query.filter_by(project_id=project_id).all()
    
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
        'analyzing': [],
        'confirmed': [],
        'rejected': [],
        'completed': [],
        'in_progress': []
    }
    
    for req in requirements:
        if req.status in status_groups:
            status_groups[req.status].append(req)
        else:
            status_groups['collected'].append(req)
    
    # 将需求分配到里程碑
    milestone_requirements = {}
    for milestone in milestones:
        req_ids = [int(r) for r in milestone.requirements.split(',')] if milestone.requirements else []
        milestone_requirements[milestone.id] = [r for r in requirements if r.id in req_ids]
    
    response = make_response(render_template('roadmap_planning.html',
                          project=project,
                          milestones=milestones,
                          requirements=requirements,
                          status_groups=status_groups,
                          milestone_requirements=milestone_requirements))
    return response

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
        return add_cache_headers(jsonify({'success': True, 'id': milestone.id}))
    
    milestones = Milestone.query.filter_by(project_id=project_id).order_by(Milestone.deadline).all()
    response = jsonify([{
        'id': m.id,
        'title': m.title,
        'description': m.description,
        'deadline': m.deadline.strftime('%Y-%m-%d') if m.deadline else None,
        'status': m.status,
        'requirements': [int(r) for r in m.requirements.split(',')] if m.requirements else []
    } for m in milestones])
    return add_cache_headers(response)

@app.route('/api/milestones/<int:project_id>/<int:milestone_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_milestone_detail(project_id, milestone_id):
    """单个里程碑API接口"""
    milestone = Milestone.query.filter_by(id=milestone_id, project_id=project_id).first_or_404()
    
    if request.method == 'GET':
        response = jsonify({
            'id': milestone.id,
            'title': milestone.title,
            'description': milestone.description,
            'deadline': milestone.deadline.strftime('%Y-%m-%d') if milestone.deadline else None,
            'status': milestone.status,
            'requirements': [int(r) for r in milestone.requirements.split(',')] if milestone.requirements else []
        })
        return add_cache_headers(response)
    
    elif request.method == 'PUT':
        data = request.get_json()
        old_title = milestone.title
        milestone.title = data.get('title', milestone.title)
        milestone.description = data.get('description', milestone.description)
        
        # 处理截止日期更新
        if 'deadline' in data:
            if data['deadline']:
                try:
                    milestone.deadline = datetime.strptime(data['deadline'], '%Y-%m-%d').date()
                except ValueError:
                    milestone.deadline = None
            else:
                milestone.deadline = None
        
        # 处理需求关联更新
        if 'requirements' in data:
            milestone.requirements = ','.join(map(str, data['requirements']))
        
        if 'status' in data:
            milestone.status = data['status']
            
        milestone.updated_at = datetime.utcnow()
        
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

# 添加更新里程碑需求关联的API（用于支持拖拽功能）
@app.route('/api/milestones/<int:milestone_id>/requirements', methods=['PUT'])
@login_required
def update_milestone_requirements(milestone_id):
    """更新里程碑关联的需求"""
    milestone = Milestone.query.get_or_404(milestone_id)
    data = request.get_json()
    
    requirement_ids = data.get('requirement_ids', [])
    milestone.requirements = ','.join(map(str, requirement_ids)) if requirement_ids else ''
    milestone.updated_at = datetime.utcnow()
    
    db.session.commit()
    logger.info(f"用户 {session['user_id']} 更新了里程碑 {milestone.title} 的需求关联")
    return add_cache_headers(jsonify({'success': True}))

# 添加路线图视图专用的里程碑API
@app.route('/api/roadmap/milestones/<int:project_id>', methods=['GET'])
@login_required
def api_roadmap_milestones(project_id):
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

# 添加路线图时间线数据API
@app.route('/api/roadmap/timeline/<int:project_id>', methods=['GET'])
@login_required
def api_roadmap_timeline(project_id):
    """获取路线图时间线数据"""
    milestones = Milestone.query.filter_by(project_id=project_id).order_by(Milestone.deadline).all()
    
    timeline_data = []
    for m in milestones:
        # 计算里程碑的统计信息
        req_ids = [int(r) for r in m.requirements.split(',')] if m.requirements else []
        requirements = Requirement.query.filter(Requirement.id.in_(req_ids)).all()
        
        # 按优先级统计
        priority_counts = {'high': 0, 'medium': 0, 'low': 0}
        for req in requirements:
            if req.priority in priority_counts:
                priority_counts[req.priority] += 1
        
        # 按状态统计
        status_counts = {'collected': 0, 'analyzing': 0, 'confirmed': 0, 'rejected': 0, 'in_progress': 0, 'completed': 0}
        for req in requirements:
            if req.status in status_counts:
                status_counts[req.status] += 1
        
        timeline_data.append({
            'id': m.id,
            'title': m.title,
            'deadline': m.deadline.strftime('%Y-%m-%d') if m.deadline else None,
            'requirements_count': len(requirements),
            'priority_counts': priority_counts,
            'status_counts': status_counts
        })
    
    return add_cache_headers(jsonify(timeline_data))

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

# 价值评估路由
@app.route('/project/<int:project_id>/value-assessment')
@login_required
def value_assessment(project_id):
    """价值评估分析页面"""
    project = Project.query.get_or_404(project_id)
    requirements = Requirement.query.filter_by(project_id=project_id).all()
    
    completed_requirements = [r for r in requirements if r.status == 'completed' and r.actual_roi > 0]
    
    accuracy_scores = []
    for req in completed_requirements:
        if req.actual_roi > 0:
            accuracy = (1 - abs(req.actual_roi - req.estimated_roi) / req.actual_roi) * 100
            accuracy_scores.append(accuracy)
    
    average_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0
    
    performer_scores = {}
    for req in completed_requirements:
        if req.value_assessor:
            accuracy = (1 - abs(req.actual_roi - req.estimated_roi) / req.actual_roi) * 100
            if req.value_assessor in performer_scores:
                performer_scores[req.value_assessor].append(accuracy)
            else:
                performer_scores[req.value_assessor] = [accuracy]
    
    best_performer = "暂无数据"
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
        'priority_level': requirement.priority_level,
        'other_info': requirement.other_info,
        'source': requirement.source,
        'category': requirement.category,
        'priority': requirement.priority,
        'status': requirement.status,
        'acceptance_criteria': requirement.acceptance_criteria,
        'expected_completion_date': requirement.expected_completion_date.strftime('%Y-%m-%d') if requirement.expected_completion_date else None
    })
    return add_cache_headers(response)

@app.route('/api/requirements/<int:req_id>/actual-assessment', methods=['POST'])
@login_required
def save_actual_assessment(req_id):
    """保存实际价值评估"""
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
        
        potential_requirements = []
        for req in incorrect_requirements + orphaned_requirements:
            if str(project_id) in (req.title or '') or str(project.name) in (req.title or ''):
                potential_requirements.append(req)
        
        diagnosis = {
            'project_id': project_id,
            'project_name': project.name,
            'total_requirements': len(all_requirements),
            'correct_requirements_count': len(correct_requirements),
            'incorrect_requirements_count': len(incorrect_requirements),
            'orphaned_requirements_count': len(orphaned_requirements),
            'potential_requirements_count': len(potential_requirements),
            'correct_requirements': [{
                'id': r.id,
                'title': r.title,
                'project_id': r.project_id,
                'status': r.status,
                'category': r.category,
                'priority': r.priority
            } for r in correct_requirements],
            'potential_requirements': [{
                'id': r.id,
                'title': r.title,
                'project_id': r.project_id,
                'status': r.status,
                'category': r.category,
                'priority': r.priority
            } for r in potential_requirements]
        }
        
        logger.info(f"用户 {session['user_id']} 对项目 {project.name} 进行了需求数据诊断")
        return jsonify({'success': True, 'diagnosis': diagnosis})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# 自定义模板过滤器
@app.template_filter('percentage')
def percentage_filter(numerator, denominator):
    """计算百分比，避免除以零错误"""
    if denominator == 0:
        return 0
    return round((numerator / denominator) * 100)

@app.template_filter('confirmed_requirements_count')
def confirmed_requirements_count(requirements):
    """计算已确认需求的数量"""
    return len([r for r in requirements if r.status == 'confirmed'])

@app.template_filter('requirements_by_status')
def requirements_by_status(requirements, status):
    """按状态筛选需求"""
    return [r for r in requirements if r.status == status]

def add_cache_headers(response, status_code=200):
    """为响应添加缓存控制头"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.status_code = status_code
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
