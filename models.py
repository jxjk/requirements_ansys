# models.py - 修复后的模型
from database import db
from datetime import datetime

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    stakeholders = db.relationship('Stakeholder', backref='project', lazy=True, cascade='all, delete-orphan')
    requirements = db.relationship('Requirement', backref='project', lazy=True, cascade='all, delete-orphan')
    milestones = db.relationship('Milestone', backref='project', lazy=True, cascade='all, delete-orphan')

class Stakeholder(db.Model):
    __tablename__ = 'stakeholders'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100))
    influence = db.Column(db.Integer, default=3)  # 1-5
    interest = db.Column(db.Integer, default=3)   # 1-5
    requirements = db.Column(db.Text)  # 该干系人关注的需求
    contact_info = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Requirement(db.Model):
    __tablename__ = 'requirements'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    
    # 九要素字段
    requirement_type = db.Column(db.String(50))  # 类型
    scenario = db.Column(db.Text)  # 场景
    problem = db.Column(db.Text)  # 解决的问题
    current_solution = db.Column(db.Text)  # 当前解决方案
    goal = db.Column(db.Text)  # 目标
    expected_solution = db.Column(db.Text)  # 预期方案
    value = db.Column(db.Text)  # 价值
    priority_level = db.Column(db.String(20), default='medium')  # 优先级
    other_info = db.Column(db.Text)  # 其他
    
    source = db.Column(db.String(100))  # 需求来源
    category = db.Column(db.String(50))  # 需求类别
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    status = db.Column(db.String(20), default='collected')  # collected, analyzing, confirmed, rejected, completed
    acceptance_criteria = db.Column(db.Text)  # 验收标准
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 价值评估字段
    estimated_business_value = db.Column(db.Integer, default=5)  # 预估业务价值 (1-10)
    estimated_user_value = db.Column(db.Integer, default=5)      # 预估用户价值 (1-10)
    estimated_technical_value = db.Column(db.Integer, default=5) # 预估技术价值 (1-10)
    estimated_effort = db.Column(db.Integer, default=5)          # 预估工作量 (1-10)
    estimated_roi = db.Column(db.Float, default=0.0)             # 预估ROI
    
    actual_business_value = db.Column(db.Integer, default=0)     # 实际业务价值 (1-10)
    actual_user_value = db.Column(db.Integer, default=0)         # 实际用户价值 (1-10)
    actual_technical_value = db.Column(db.Integer, default=0)    # 实际技术价值 (1-10)
    actual_effort = db.Column(db.Integer, default=0)             # 实际工作量 (1-10)
    actual_roi = db.Column(db.Float, default=0.0)                # 实际ROI
    
    value_assessor = db.Column(db.String(100))                   # 价值评估人
    value_assessment_date = db.Column(db.DateTime)               # 价值评估日期
    actual_value_assessor = db.Column(db.String(100))            # 实际价值评估人
    actual_value_assessment_date = db.Column(db.DateTime)        # 实际价值评估日期 
    
class Milestone(db.Model):
    __tablename__ = 'milestones'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    deadline = db.Column(db.Date)
    status = db.Column(db.String(20), default='planned')  # planned, in_progress, completed, delayed
    requirements = db.Column(db.Text)  # 关联的需求ID列表
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)