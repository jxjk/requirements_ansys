# models.py
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
    
    # 计划相关字段
    expected_completion_date = db.Column(db.Date)                # 期望完成日期
    assigned_milestone_id = db.Column(db.Integer, db.ForeignKey('milestones.id'))  # 分配的里程碑
    
    # VSM相关字段
    vsm_process_steps = db.Column(db.Text)  # 价值流步骤
    cycle_time = db.Column(db.Float)        # 周期时间
    lead_time = db.Column(db.Float)         # 交付时间
    process_efficiency = db.Column(db.Float) # 流程效率
    vsm_current_state = db.Column(db.Text)  # 当前状态图
    vsm_future_state = db.Column(db.Text)   # 未来状态图
    
    # KANO相关字段
    kano_category = db.Column(db.String(20))  # KANO分类: must-be, one-dimensional, attractive, indifferent, reverse
    kano_survey_data = db.Column(db.Text)     # 调查数据
    kano_priority_score = db.Column(db.Float) # 优先级评分
    kano_positive_answer = db.Column(db.String(20))  # 正向问题答案
    kano_negative_answer = db.Column(db.String(20))  # 反向问题答案
    
    # SMART目标字段
    smart_specific = db.Column(db.Text)       # 明确性
    smart_measurable = db.Column(db.Text)     # 可衡量
    smart_achievable = db.Column(db.Boolean)  # 可实现
    smart_relevant = db.Column(db.Text)       # 相关性  
    smart_timebound = db.Column(db.Date)      # 时限性
    smart_target_level = db.Column(db.String(20))  # 目标级别: basic, challenge, ideal
    
    # 动作时间分析字段
    wfmt_analysis = db.Column(db.Text)        # 动作分析数据
    standard_time = db.Column(db.Float)       # 标准时间
    improvement_potential = db.Column(db.Float) # 改善潜力
    wfmt_tmu_total = db.Column(db.Float)      # 总TMU时间
    wfmt_allowance_rate = db.Column(db.Float) # 宽放率
    
    # 用户相关字段 (支持"看用户")
    user_research_data = db.Column(db.Text)           # 用户调研数据
    user_feedback = db.Column(db.Text)                # 用户反馈
    user_satisfaction = db.Column(db.Integer)         # 用户满意度评分 (1-10)
    target_user_group = db.Column(db.String(100))     # 目标用户群体
    
    # 竞品分析字段 (支持"拆竞品")
    competitor_analysis = db.Column(db.Text)          # 竞品分析
    competitor_products = db.Column(db.String(200))   # 相关竞品列表
    competitive_advantage = db.Column(db.Text)        # 竞争优势
    
    # 市场分析字段 (支持"盯市场")
    market_research = db.Column(db.Text)              # 市场调研数据
    market_size = db.Column(db.String(50))            # 市场规模
    market_trends = db.Column(db.Text)                # 市场趋势
    
    # 现状分析字段 (支持"查现状")
    current_state_analysis = db.Column(db.Text)       # 当前产品状态分析
    product_lifecycle_stage = db.Column(db.String(50)) # 产品生命周期阶段
    technical_constraints = db.Column(db.Text)         # 技术约束条件
    resource_constraints = db.Column(db.Text)          # 资源约束条件
    
    # 规划相关字段 (支持"定规划")
    short_term_plan = db.Column(db.Text)              # 短期规划
    medium_term_plan = db.Column(db.Text)             # 中期规划
    long_term_plan = db.Column(db.Text)               # 长期规划
    strategic_alignment = db.Column(db.Text)           # 战略对齐说明
    
    # 风险评估字段
    risk_assessment = db.Column(db.Text)              # 风险评估
    technical_risks = db.Column(db.Text)              # 技术风险
    business_risks = db.Column(db.Text)               # 业务风险
    implementation_risks = db.Column(db.Text)         # 实施风险
    
    # 成本效益分析字段 (支持成本收益评估)
    development_cost_estimate = db.Column(db.Integer) # 开发成本估算
    operational_cost_estimate = db.Column(db.Integer) # 运营成本估算
    expected_revenue = db.Column(db.Integer)          # 预期收益
    cost_benefit_analysis = db.Column(db.Text)        # 成本效益分析
    
    # 其他分析字段
    implementation_priority = db.Column(db.String(20)) # 实施优先级
    dependencies = db.Column(db.Text)                  # 依赖关系
    alternative_solutions = db.Column(db.Text)         # 替代方案
    success_metrics = db.Column(db.Text)               # 成功指标
    
    @property
    def description(self):
        """
        构建完整的需求描述，将多个字段组合成一个描述文本
        """
        parts = []
        if self.scenario:
            parts.append(self.scenario)
        if self.problem:
            parts.append(self.problem)
        if self.goal:
            parts.append(self.goal)
        if self.current_solution:
            parts.append(self.current_solution)
        return ' '.join(parts) if parts else ''

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
    
    # 关系
    assigned_requirements = db.relationship('Requirement', backref='milestone', lazy=True)
