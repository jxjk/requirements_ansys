# app.py - 修复需求采集页面显示问题
from flask import Flask, render_template, request, jsonify, redirect, url_for, make_response
from datetime import datetime
from database import db, init_db
from models import Project, Stakeholder, Requirement, Milestone

app = Flask(__name__)

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

@app.route('/')
def index():
    """主页 - 项目列表"""
    projects = Project.query.all()
    response = make_response(render_template('index.html', projects=projects))
    return response

@app.route('/project/create', methods=['POST'])
def create_project():
    """创建新项目"""
    name = request.form.get('name')
    description = request.form.get('description')
    
    if name:
        project = Project(name=name, description=description)
        db.session.add(project)
        db.session.commit()
    
    return redirect(url_for('index'))

# 添加项目删除路由
@app.route('/project/<int:project_id>/delete', methods=['POST'])
def delete_project(project_id):
    """删除项目"""
    project = Project.query.get_or_404(project_id)
    
    # 删除项目相关的所有数据
    # 删除干系人
    Stakeholder.query.filter_by(project_id=project_id).delete()
    # 删除需求
    Requirement.query.filter_by(project_id=project_id).delete()
    # 删除里程碑
    Milestone.query.filter_by(project_id=project_id).delete()
    
    # 删除项目本身
    db.session.delete(project)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    """项目详情页"""
    project = Project.query.get_or_404(project_id)
    response = make_response(render_template('project_detail.html', project=project))
    return response

# 干系人管理路由
@app.route('/project/<int:project_id>/stakeholders')
def stakeholder_management(project_id):
    """干系人管理页面"""
    project = Project.query.get_or_404(project_id)
    response = make_response(render_template('stakeholder_management.html', project=project))
    return response

@app.route('/api/stakeholders/<int:project_id>', methods=['GET', 'POST'])
def api_stakeholders(project_id):
    """干系人API接口"""
    # 为API添加缓存控制头
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
        response = jsonify({'success': True, 'id': stakeholder.id})
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    
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
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# 需求采集路由
@app.route('/project/<int:project_id>/requirements')
def requirement_collection(project_id):
    """需求采集页面"""
    project = Project.query.get_or_404(project_id)
    stakeholders = Stakeholder.query.filter_by(project_id=project_id).all()
    response = make_response(render_template('requirement_collection.html', 
                          project=project, stakeholders=stakeholders))
    return response

# 需求分析路由
@app.route('/project/<int:project_id>/analysis')
def requirement_analysis(project_id):
    """需求分析页面"""
    project = Project.query.get_or_404(project_id)
    requirements = Requirement.query.filter_by(project_id=project_id).all()
    
    # 按优先级和类别统计
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

@app.route('/api/requirements/<int:req_id>/update', methods=['POST'])
def update_requirement(req_id):
    """更新需求状态"""
    requirement = Requirement.query.get_or_404(req_id)
    data = request.get_json()
    
    if 'status' in data:
        requirement.status = data['status']
    if 'priority' in data:
        requirement.priority = data['priority']
    
    db.session.commit()
    
    response = jsonify({'success': True})
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# 路线图规划路由
@app.route('/project/<int:project_id>/roadmap')
def roadmap_planning(project_id):
    """路线图规划页面"""
    project = Project.query.get_or_404(project_id)
    milestones = Milestone.query.filter_by(project_id=project_id).all()
    requirements = Requirement.query.filter_by(project_id=project_id).all()
    response = make_response(render_template('roadmap_planning.html',
                          project=project,
                          milestones=milestones,
                          requirements=requirements))
    return response

@app.route('/api/milestones/<int:project_id>', methods=['GET', 'POST'])
def api_milestones(project_id):
    """里程碑API接口"""
    # 为API添加缓存控制头
    if request.method == 'POST':
        data = request.get_json()
        milestone = Milestone(
            project_id=project_id,
            title=data['title'],
            description=data['description'],
            deadline=datetime.strptime(data['deadline'], '%Y-%m-%d').date(),
            requirements=','.join(map(str, data.get('requirements', [])))
        )
        db.session.add(milestone)
        db.session.commit()
        response = jsonify({'success': True, 'id': milestone.id})
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    
    milestones = Milestone.query.filter_by(project_id=project_id).all()
    response = jsonify([{
        'id': m.id,
        'title': m.title,
        'description': m.description,
        'deadline': m.deadline.strftime('%Y-%m-%d'),
        'status': m.status,
        'requirements': [int(r) for r in m.requirements.split(',')] if m.requirements else []
    } for m in milestones])
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# 看板视图路由
@app.route('/project/<int:project_id>/kanban')
def kanban_view(project_id):
    """看板视图页面"""
    project = Project.query.get_or_404(project_id)
    requirements = Requirement.query.filter_by(project_id=project_id).all()
    
    # 按状态分组
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

@app.route('/api/requirements/<int:req_id>/assign', methods=['POST'])
def assign_requirement_to_milestone(req_id):
    """将需求分配到里程碑"""
    requirement = Requirement.query.get_or_404(req_id)
    data = request.get_json()
    milestone_id = data.get('milestone_id')
    
    # 这里简化处理，实际应该更新需求的milestone_id字段
    # 目前先返回成功消息
    response = jsonify({'success': True, 'message': '分配功能开发中'})
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/project/<int:project_id>/value-assessment')
def value_assessment(project_id):
    """价值评估分析页面"""
    project = Project.query.get_or_404(project_id)
    requirements = Requirement.query.filter_by(project_id=project_id).all()
    
    # 计算统计信息
    completed_requirements = [r for r in requirements if r.status == 'completed' and r.actual_roi > 0]
    
    accuracy_scores = []
    for req in completed_requirements:
        if req.actual_roi > 0:
            accuracy = (1 - abs(req.actual_roi - req.estimated_roi) / req.actual_roi) * 100
            accuracy_scores.append(accuracy)
    
    average_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0
    
    # 找出最佳提案人（基于预估准确率）
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
                         average_accuracy=average_accuracy/100,  # 转换为小数
                         best_performer=best_performer,
                         improvement_trend="↑ 改善" if len(completed_requirements) > 3 else "→ 稳定"))
    return response

@app.route('/api/requirements/detail/<int:req_id>')
def get_requirement_detail(req_id):
    """获取需求详情"""
    requirement = Requirement.query.get_or_404(req_id)
    response = jsonify({
        'id': requirement.id,
        'title': requirement.title,
        'description': requirement.description,
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
        'status': requirement.status
    })
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/api/requirements/<int:req_id>/actual-assessment', methods=['POST'])
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
    
    response = jsonify({'success': True})
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# 数据诊断和修复端点
@app.route('/api/diagnose/requirements/<int:project_id>')
def diagnose_requirements(project_id):
    """诊断需求数据问题"""
    try:
        print(f"=== 开始诊断项目 {project_id} 的需求数据 ===")
        
        # 获取项目信息
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'success': False, 'error': f'项目 {project_id} 不存在'})
        
        print(f"项目名称: {project.name}")
        
        # 获取所有需求
        all_requirements = Requirement.query.all()
        print(f"数据库中总共有 {len(all_requirements)} 条需求")
        
        # 分类需求
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
        
        print(f"属于项目 {project_id} 的需求数量: {len(correct_requirements)}")
        print(f"不属于项目 {project_id} 但可能相关的需求数量: {len(incorrect_requirements)}")
        print(f"孤儿需求数量 (project_id 为空或0): {len(orphaned_requirements)}")
        
        # 检查可能属于该项目但project_id不正确的需求数量
        potential_requirements = []
        for req in incorrect_requirements + orphaned_requirements:
            # 简单检查标题是否包含项目相关信息
            if str(project_id) in (req.title or '') or str(project.name) in (req.title or ''):
                potential_requirements.append(req)
        
        print(f"可能属于项目 {project_id} 但project_id不正确的需求数量: {len(potential_requirements)}")
        
        # 构建诊断结果
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
                'priority': r.priority,
                'estimated_roi': float(r.estimated_roi) if r.estimated_roi else 0,
                'actual_roi': float(r.actual_roi) if r.actual_roi else 0
            } for r in correct_requirements],
            'potential_requirements': [{
                'id': r.id,
                'title': r.title,
                'project_id': r.project_id,
                'status': r.status,
                'category': r.category,
                'priority': r.priority,
                'estimated_roi': float(r.estimated_roi) if r.estimated_roi else 0,
                'actual_roi': float(r.actual_roi) if r.actual_roi else 0
            } for r in potential_requirements]
        }
        
        print("=== 诊断结束 ===")
        return jsonify({'success': True, 'diagnosis': diagnosis})
        
    except Exception as e:
        print(f"诊断过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

# 需求API接口 - 修复版本
@app.route('/api/requirements/<int:project_id>', methods=['GET', 'POST'])
def api_requirements(project_id):
    """需求API接口"""
    # 为所有API响应添加缓存控制头
    if request.method == 'POST':
        try:
            data = request.get_json()
            print(f"Received requirement data: {data}")
            
            # 验证必要字段
            if not data or 'title' not in data or 'description' not in data:
                response = jsonify({'success': False, 'error': '缺少必要字段: title 或 description'}), 400
                response[0].headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response[0].headers["Pragma"] = "no-cache"
                response[0].headers["Expires"] = "0"
                return response
            
            # 计算预估ROI
            estimated_business_value = int(data.get('estimated_business_value', 5))
            estimated_user_value = int(data.get('estimated_user_value', 5))
            estimated_technical_value = int(data.get('estimated_technical_value', 5))
            estimated_effort = int(data.get('estimated_effort', 5))
            
            # 确保工作量不为0以避免除零错误
            if estimated_effort <= 0:
                estimated_effort = 1
            
            total_estimated_value = estimated_business_value + estimated_user_value + estimated_technical_value
            estimated_roi = total_estimated_value / estimated_effort if estimated_effort > 0 else 0
            
            requirement = Requirement(
                project_id=project_id,
                title=data['title'],
                description=data['description'],
                source=data.get('source', ''),
                category=data.get('category', 'functional'),
                priority=data.get('priority', 'medium'),
                acceptance_criteria=data.get('acceptance_criteria', ''),
                estimated_business_value=estimated_business_value,
                estimated_user_value=estimated_user_value,
                estimated_technical_value=estimated_technical_value,
                estimated_effort=estimated_effort,
                estimated_roi=estimated_roi,
                value_assessor=data.get('value_assessor', '')
            )
            db.session.add(requirement)
            db.session.commit()
            print(f"Requirement saved with ID: {requirement.id}")
            response = jsonify({'success': True, 'id': requirement.id})
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
            
        except Exception as e:
            db.session.rollback()
            print(f"Error saving requirement: {str(e)}")
            response = jsonify({'success': False, 'error': str(e)}), 500
            response[0].headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response[0].headers["Pragma"] = "no-cache"
            response[0].headers["Expires"] = "0"
            return response
    # GET方法：返回项目的所有需求
    try:
        print(f"=== 开始查询项目 {project_id} 的需求 ===")
        
        # 首先检查项目是否存在
        project = Project.query.get(project_id)
        print(f"项目存在: {project is not None}")
        if project:
            print(f"项目名称: {project.name}")
        
        # 查询所有需求（不加过滤条件）用于调试
        all_requirements = Requirement.query.all()
        print(f"数据库中总共有 {len(all_requirements)} 条需求:")
        for i, r in enumerate(all_requirements):
            print(f"  需求 {i+1}: ID={r.id}, Title={r.title}, ProjectID={r.project_id}, Status={r.status}")
        
        # 查询指定项目的需求
        requirements = Requirement.query.filter_by(project_id=project_id).all()
        print(f"项目 {project_id} 找到 {len(requirements)} 条需求:")
        
        # 打印每条需求的详细信息用于调试
        for i, r in enumerate(requirements):
            print(f"  需求 {i+1}: ID={r.id}, Title={r.title}, ProjectID={r.project_id}, Status={r.status}")
        
        result = []
        for r in requirements:
            try:
                req_data = {
                    'id': r.id,
                    'title': r.title if r.title else '',
                    'description': r.description if r.description else '',
                    'source': r.source if r.source else '',
                    'category': r.category if r.category else 'functional',
                    'priority': r.priority if r.priority else 'medium',
                    'status': r.status if r.status else 'collected',
                    'estimated_roi': float(r.estimated_roi) if r.estimated_roi is not None else 0,
                    'actual_roi': float(r.actual_roi) if r.actual_roi is not None else 0,
                    'created_at': r.created_at.isoformat() if r.created_at else None
                }
                result.append(req_data)
                print(f"  处理需求 {r.id}: {req_data}")
            except Exception as e:
                print(f"  处理需求 {r.id} 时出错: {str(e)}")
                # 即使某个需求出错，也继续处理其他需求
                continue
        
        print(f"返回 {len(result)} 条需求的JSON数据")
        print(f"返回的数据: {result}")
        print("=== 查询结束 ===")
        
        response = jsonify(result)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    except Exception as e:
        print(f"Error fetching requirements: {str(e)}")
        import traceback
        traceback.print_exc()
        response = jsonify({'success': False, 'error': str(e)}), 500
        response[0].headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response[0].headers["Pragma"] = "no-cache"
        response[0].headers["Expires"] = "0"
        return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)