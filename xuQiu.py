import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd

class StakeholderSurveyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("干系人需求调查系统")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        # 在 __init__ 方法中添加职级权重定义
        self.level_weights = {
            "初级": 1.0,
            "中级": 1.2,
            "高级": 1.5,
            "专家级": 1.8,
            "管理层": 2.0
        }
        
        # 数据存储
        self.stakeholders = []
        self.survey_questions = [
            {
                "id": 1,
                "category": "需求重要性",
                "question": "您认为以下需求对项目成功的重要性如何？",
                "type": "scale",
                "options": ["非常重要", "重要", "一般", "不重要", "完全不重要"]
            },
            {
                "id": 2,
                "category": "需求紧急性",
                "question": "您认为以下需求的紧急程度如何？",
                "type": "scale",
                "options": ["非常紧急", "紧急", "一般", "不紧急", "完全不紧急"]
            },
            {
                "id": 3,
                "category": "满意度",
                "question": "您对当前解决方案的满意度如何？",
                "type": "scale",
                "options": ["非常满意", "满意", "一般", "不满意", "非常不满意"]
            },
            {
                "id": 4,
                "category": "情绪状态",
                "question": "您对项目当前进展的情绪状态是？",
                "type": "emotion",
                "options": ["非常积极", "积极", "中性", "消极", "非常消极"]
            },
            {
                "id": 5,
                "category": "合作意愿",
                "question": "您愿意在多大程度上参与后续需求讨论？",
                "type": "scale",
                "options": ["非常愿意", "愿意", "视情况而定", "不太愿意", "完全不愿意"]
            }
        ]
        
        self.current_stakeholder_index = 0
        self.responses = defaultdict(list)
        
        self.load_data()
        self.create_widgets()
        
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建标题
        title_label = tk.Label(main_frame, text="干系人需求调查系统", 
                              font=("Arial", 20, "bold"), fg="#2c3e50", bg='#f0f0f0')
        title_label.pack(pady=(0, 20))
        
        # 创建笔记本控件（标签页）
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 创建各个标签页
        self.create_stakeholder_tab(notebook)
        self.create_survey_tab(notebook)
        self.create_analysis_tab(notebook)
        self.create_report_tab(notebook)
        
    def create_stakeholder_tab(self, notebook):
        stakeholder_frame = ttk.Frame(notebook)
        notebook.add(stakeholder_frame, text="干系人管理")
        
        # 干系人信息输入区域
        input_frame = ttk.LabelFrame(stakeholder_frame, text="添加/编辑干系人", padding=10)
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 干系人姓名
        ttk.Label(input_frame, text="姓名:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(input_frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # 职位
        ttk.Label(input_frame, text="职位:").grid(row=0, column=2, sticky=tk.W, pady=5)
        self.position_entry = ttk.Entry(input_frame, width=30)
        self.position_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # 职能类型
        ttk.Label(input_frame, text="职能类型:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.function_type = ttk.Combobox(input_frame, values=["技术职能", "业务职能", "管理职能", "支持职能"], width=27)
        self.function_type.grid(row=1, column=1, padx=5, pady=5)
        self.function_type.set("业务职能")
        
        # 职级
        ttk.Label(input_frame, text="职级:").grid(row=1, column=2, sticky=tk.W, pady=5)
        self.level = ttk.Combobox(input_frame, values=["初级", "中级", "高级", "专家级", "管理层"], width=27)
        self.level.grid(row=1, column=3, padx=5, pady=5)
        self.level.set("中级")
        
        # 影响力
        ttk.Label(input_frame, text="影响力:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.influence = ttk.Scale(input_frame, from_=1, to=5, orient=tk.HORIZONTAL, length=200)
        self.influence.grid(row=2, column=1, padx=5, pady=5)
        self.influence_label = ttk.Label(input_frame, text="3")
        self.influence_label.grid(row=2, column=2, sticky=tk.W)
        self.influence.configure(command=lambda x: self.influence_label.config(text=str(round(float(x)))))
        
        # 关注度
        ttk.Label(input_frame, text="关注度:").grid(row=2, column=2, sticky=tk.W, pady=5)
        self.interest = ttk.Scale(input_frame, from_=1, to=5, orient=tk.HORIZONTAL, length=200)
        self.interest.grid(row=2, column=3, padx=5, pady=5)
        self.interest_label = ttk.Label(input_frame, text="3")
        self.interest_label.grid(row=2, column=4, sticky=tk.W)
        self.interest.configure(command=lambda x: self.interest_label.config(text=str(round(float(x)))))
        
        # 情绪状态
        ttk.Label(input_frame, text="当前情绪:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.emotion = ttk.Combobox(input_frame, values=["非常积极", "积极", "中性", "消极", "非常消极"], width=27)
        self.emotion.grid(row=3, column=1, padx=5, pady=5)
        self.emotion.set("中性")
        
        # 联系方式
        ttk.Label(input_frame, text="联系方式:").grid(row=3, column=2, sticky=tk.W, pady=5)
        self.contact_entry = ttk.Entry(input_frame, width=30)
        self.contact_entry.grid(row=3, column=3, padx=5, pady=5)
        
        # 按钮区域
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=4, column=0, columnspan=5, pady=10)
        
        ttk.Button(button_frame, text="添加干系人", command=self.add_stakeholder).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="更新干系人", command=self.update_stakeholder).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除干系人", command=self.delete_stakeholder).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空表单", command=self.clear_form).pack(side=tk.LEFT, padx=5)
        
        # 干系人列表区域
        list_frame = ttk.LabelFrame(stakeholder_frame, text="干系人列表", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建表格
        columns = ("ID", "姓名", "职位", "职能类型", "职级", "影响力", "关注度", "情绪状态")
        self.stakeholder_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # 设置列标题
        for col in columns:
            self.stakeholder_tree.heading(col, text=col)
            self.stakeholder_tree.column(col, width=100, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.stakeholder_tree.yview)
        self.stakeholder_tree.configure(yscroll=scrollbar.set)
        
        self.stakeholder_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.stakeholder_tree.bind("<<TreeviewSelect>>", self.on_stakeholder_select)
        
        # 加载数据
        self.load_data()
        self.refresh_stakeholder_list()
        
        
    def create_survey_tab(self, notebook):
        survey_frame = ttk.Frame(notebook)
        notebook.add(survey_frame, text="需求调查")
        
        # 调查控制区域
        control_frame = ttk.LabelFrame(survey_frame, text="调查控制", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(control_frame, text="选择干系人:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.survey_stakeholder = ttk.Combobox(control_frame, width=30)
        self.survey_stakeholder.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(control_frame, text="开始调查", command=self.start_survey).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(control_frame, text="保存结果", command=self.save_survey).grid(row=0, column=3, padx=5, pady=5)

        self.refresh_stakeholder_list()
        
        # 创建包含滚动条的画布和滚动区域
        survey_canvas_frame = ttk.Frame(survey_frame)
        survey_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建画布和滚动条
        self.survey_canvas = tk.Canvas(survey_canvas_frame)
        survey_scrollbar = ttk.Scrollbar(survey_canvas_frame, orient=tk.VERTICAL, command=self.survey_canvas.yview)
        self.survey_scrollable_frame = ttk.Frame(self.survey_canvas)
        
        # 配置画布滚动
        self.survey_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.survey_canvas.configure(
                scrollregion=self.survey_canvas.bbox("all")
            )
        )
        
        self.survey_canvas.create_window((0, 0), window=self.survey_scrollable_frame, anchor="nw")
        self.survey_canvas.configure(yscrollcommand=survey_scrollbar.set)
        
        # 绑定鼠标滚轮事件
        self.survey_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.survey_scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)
        
        # 打包画布和滚动条
        self.survey_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        survey_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 调查问题区域（现在放在可滚动框架中）
        self.question_frame = ttk.LabelFrame(self.survey_scrollable_frame, text="调查问题", padding=10)
        self.question_frame.pack(fill=tk.BOTH, expand=True)
        
        # 初始化为空
        self.question_vars = {}
        
        # 调查进度
        self.progress = ttk.Progressbar(survey_frame, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress.pack(padx=10, pady=5)
        self.progress_label = ttk.Label(survey_frame, text="请先选择干系人并开始调查")
        self.progress_label.pack(pady=5)

    def _on_mousewheel(self, event):
        # 处理鼠标滚轮事件
        self.survey_canvas.yview_scroll(int(-1*(event.delta/120)), "units")


    def create_analysis_tab(self, notebook):
        analysis_frame = ttk.Frame(notebook)
        notebook.add(analysis_frame, text="数据分析")
        
        # 控制面板
        control_panel = ttk.Frame(analysis_frame)
        control_panel.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(control_panel, text="生成分析报告", command=self.generate_analysis).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_panel, text="导出数据", command=self.export_data).pack(side=tk.LEFT, padx=5)
        
        # 图表区域
        self.chart_frame = ttk.Frame(analysis_frame)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建默认图表
        self.create_default_charts()
        
    def create_report_tab(self, notebook):
        report_frame = ttk.Frame(notebook)
        notebook.add(report_frame, text="调查报告")
        
        # 报告控制
        report_control = ttk.Frame(report_frame)
        report_control.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(report_control, text="生成报告", command=self.generate_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(report_control, text="保存报告", command=self.save_report).pack(side=tk.LEFT, padx=5)
        
        # 报告显示区域
        report_text_frame = ttk.Frame(report_frame)
        report_text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.report_text = tk.Text(report_text_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(report_text_frame, orient=tk.VERTICAL, command=self.report_text.yview)
        self.report_text.configure(yscroll=scrollbar.set)
        
        self.report_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def add_stakeholder(self):
        name = self.name_entry.get().strip()
        position = self.position_entry.get().strip()
        function_type = self.function_type.get()
        level = self.level.get()
        influence = int(round(self.influence.get()))
        interest = int(round(self.interest.get()))
        emotion = self.emotion.get()
        contact = self.contact_entry.get().strip()
        
        if not name:
            messagebox.showwarning("输入错误", "请输入干系人姓名")
            return
            
        stakeholder = {
            "id": len(self.stakeholders) + 1,
            "name": name,
            "position": position,
            "function_type": function_type,
            "level": level,
            "influence": influence,
            "interest": interest,
            "emotion": emotion,
            "contact": contact,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.stakeholders.append(stakeholder)
        self.refresh_stakeholder_list()
        self.clear_form()
        self.save_data()
        messagebox.showinfo("成功", f"干系人 {name} 已添加")
        
    def update_stakeholder(self):
        selected = self.stakeholder_tree.selection()
        if not selected:
            messagebox.showwarning("选择错误", "请先选择要更新的干系人")
            return
            
        item = self.stakeholder_tree.item(selected[0])
        stakeholder_id = int(item['values'][0])
        
        name = self.name_entry.get().strip()
        position = self.position_entry.get().strip()
        function_type = self.function_type.get()
        level = self.level.get()
        influence = int(round(self.influence.get()))
        interest = int(round(self.interest.get()))
        emotion = self.emotion.get()
        contact = self.contact_entry.get().strip()
        
        if not name:
            messagebox.showwarning("输入错误", "请输入干系人姓名")
            return
            
        for i, stakeholder in enumerate(self.stakeholders):
            if stakeholder["id"] == stakeholder_id:
                self.stakeholders[i] = {
                    "id": stakeholder_id,
                    "name": name,
                    "position": position,
                    "function_type": function_type,
                    "level": level,
                    "influence": influence,
                    "interest": interest,
                    "emotion": emotion,
                    "contact": contact,
                    "created_at": stakeholder["created_at"]
                }
                break
                
        self.refresh_stakeholder_list()
        self.save_data()
        messagebox.showinfo("成功", f"干系人 {name} 已更新")
        
    def delete_stakeholder(self):
        selected = self.stakeholder_tree.selection()
        if not selected:
            messagebox.showwarning("选择错误", "请先选择要删除的干系人")
            return
            
        if messagebox.askyesno("确认删除", "确定要删除选中的干系人吗？"):
            item = self.stakeholder_tree.item(selected[0])
            stakeholder_id = int(item['values'][0])
            
            self.stakeholders = [s for s in self.stakeholders if s["id"] != stakeholder_id]
            self.refresh_stakeholder_list()
            self.clear_form()
            self.save_data()
            messagebox.showinfo("成功", "干系人已删除")
            
    def clear_form(self):
        self.name_entry.delete(0, tk.END)
        self.position_entry.delete(0, tk.END)
        self.function_type.set("业务职能")
        self.level.set("中级")
        self.influence.set(3)
        self.interest.set(3)
        self.influence_label.config(text="3")
        self.interest_label.config(text="3")
        self.emotion.set("中性")
        self.contact_entry.delete(0, tk.END)


    def refresh_stakeholder_list(self):
        # 清空现有数据
        for item in self.stakeholder_tree.get_children():
            self.stakeholder_tree.delete(item)
            
        # 添加数据
        for stakeholder in self.stakeholders:
            self.stakeholder_tree.insert("", tk.END, values=(
                stakeholder["id"],
                stakeholder["name"],
                stakeholder["position"],
                stakeholder["function_type"],
                stakeholder["level"],
                stakeholder["influence"],
                stakeholder["interest"],
                stakeholder["emotion"]
            ))
            
        # 更新调查下拉框（如果已创建）
        stakeholder_names = [s["name"] for s in self.stakeholders]
        # 只有当 survey_stakeholder 已经创建时才更新它
        if hasattr(self, 'survey_stakeholder') and self.survey_stakeholder is not None:
            self.survey_stakeholder['values'] = stakeholder_names

    def on_stakeholder_select(self, event):
        selected = self.stakeholder_tree.selection()
        if selected:
            item = self.stakeholder_tree.item(selected[0])
            values = item['values']
            
            # 填充表单
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, values[1])
            
            self.position_entry.delete(0, tk.END)
            self.position_entry.insert(0, values[2])
            
            self.function_type.set(values[3])
            self.level.set(values[4])
            self.influence.set(values[5])
            self.interest.set(values[6])
            self.influence_label.config(text=str(values[5]))
            self.interest_label.config(text=str(values[6]))
            self.emotion.set(values[7])
            
    def start_survey(self):
        stakeholder_name = self.survey_stakeholder.get()
        if not stakeholder_name:
            messagebox.showwarning("选择错误", "请先选择干系人")
            return
            
        # 清空之前的问卷
        for widget in self.question_frame.winfo_children():
            widget.destroy()
            
        self.question_vars = {}
        
        # 创建问卷问题
        for i, question in enumerate(self.survey_questions):
            question_frame = ttk.LabelFrame(self.question_frame, text=f"问题 {i+1}: {question['question']}", padding=10)
            question_frame.pack(fill=tk.X, padx=5, pady=5)
            
            self.question_vars[question['id']] = tk.StringVar()
            
            if question['type'] == 'scale' or question['type'] == 'emotion':
                for j, option in enumerate(question['options']):
                    ttk.Radiobutton(
                        question_frame, 
                        text=option, 
                        variable=self.question_vars[question['id']], 
                        value=option
                    ).pack(anchor=tk.W, pady=2)
            
        # 设置进度条
        self.progress['value'] = 0
        self.progress['maximum'] = len(self.survey_questions)
        self.progress_label.config(text=f"进度: 0/{len(self.survey_questions)}")
        
        messagebox.showinfo("开始调查", f"开始对 {stakeholder_name} 进行调查")
        
    def save_survey(self):
        stakeholder_name = self.survey_stakeholder.get()
        if not stakeholder_name:
            messagebox.showwarning("保存错误", "请先选择干系人")
            return
            
        # 检查是否所有问题都已回答
        unanswered = []
        responses = {}
        for q_id, var in self.question_vars.items():
            answer = var.get()
            if not answer:
                unanswered.append(q_id)
            else:
                responses[q_id] = answer
                
        if unanswered:
            messagebox.showwarning("未完成", "请回答所有问题")
            return
            
        # 保存响应
        response_data = {
            "stakeholder": stakeholder_name,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "responses": responses
        }
        
        self.responses[stakeholder_name].append(response_data)
        self.save_responses()
        
        messagebox.showinfo("保存成功", f"{stakeholder_name} 的调查结果已保存")
        
  
    def generate_analysis(self):
        # 清空图表区域
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
            
        if not self.responses:
            messagebox.showwarning("无数据", "暂无调查数据可供分析")
            return
        # 设置matplotlib支持中文显示
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
            
        # 创建图表
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('干系人需求调查分析报告', fontsize=16)
        
        # 1. 干系人情绪分布
        emotions = []
        for responses in self.responses.values():
            for response in responses:
                for q_id, answer in response['responses'].items():
                    question = next((q for q in self.survey_questions if q['id'] == q_id), None)
                    if question and question['category'] == '情绪状态':
                        emotions.append(answer)
                        
        if emotions:
            emotion_counts = pd.Series(emotions).value_counts()
            ax1.pie(emotion_counts.values, labels=emotion_counts.index, autopct='%1.1f%%')
            ax1.set_title('干系人情绪状态分布')
        
        # 2. 需求重要性分析
        # 加权重要性分析
        weighted_importance_scores = []
        total_weight = 0
        
        for stakeholder_name, responses in self.responses.items():
            # 获取干系人职级
            stakeholder = next((s for s in self.stakeholders if s['name'] == stakeholder_name), None)
            if not stakeholder:
                continue
                
            weight = self.level_weights.get(stakeholder['level'], 1.0)
            
            for response in responses:
                for q_id, answer in response['responses'].items():
                    question = next((q for q in self.survey_questions if q['id'] == q_id), None)
                    if question and question['category'] == '需求重要性':
                        score_map = {
                            "非常重要": 5, "重要": 4, "一般": 3, "不重要": 2, "完全不重要": 1
                        }
                        score = score_map.get(answer, 0)
                        weighted_importance_scores.append(score * weight)
                        total_weight += weight
        
        if weighted_importance_scores:
            ax2.hist(weighted_importance_scores, bins=5, edgecolor='black')
            ax2.set_xlabel('重要性评分')
            ax2.set_ylabel('频次')
            ax2.set_title('需求重要性分布')
            ax2.set_xticks([1, 2, 3, 4, 5])
            ax2.set_xticklabels(['完全不重要', '不重要', '一般', '重要', '非常重要'], rotation=45)
        
        # 3. 需求紧急性分析 (新增)
        urgency_scores = []
        for responses in self.responses.values():
            for response in responses:
                for q_id, answer in response['responses'].items():
                    question = next((q for q in self.survey_questions if q['id'] == q_id), None)
                    if question and question['category'] == '需求紧急性':
                        # 将文字转换为分数
                        score_map = {
                            "非常紧急": 5, "紧急": 4, "一般": 3, "不紧急": 2, "完全不紧急": 1
                        }
                        urgency_scores.append(score_map.get(answer, 0))
                        
        if urgency_scores:
            ax3.hist(urgency_scores, bins=5, edgecolor='black')
            ax3.set_xlabel('紧急性评分')
            ax3.set_ylabel('频次')
            ax3.set_title('需求紧急性分布')
            ax3.set_xticks([1, 2, 3, 4, 5])
            ax3.set_xticklabels(['完全不紧急', '不紧急', '一般', '紧急', '非常紧急'], rotation=45)
        else:
            ax3.text(0.5, 0.5, '暂无紧急性数据', ha='center', va='center', transform=ax3.transAxes)
        
        # 4. 职能类型分布
        function_types = [s['function_type'] for s in self.stakeholders]
        if function_types:
            function_counts = pd.Series(function_types).value_counts()
            ax4.bar(function_counts.index, function_counts.values)
            ax4.set_xlabel('职能类型')
            ax4.set_ylabel('人数')
            ax4.set_title('干系人职能类型分布')
            ax4.tick_params(axis='x', rotation=45)
        
        # 如果没有职能类型数据，则在第4个子图显示提示信息
        else:
            ax4.text(0.5, 0.5, '暂无职能类型数据', ha='center', va='center', transform=ax4.transAxes)
        
        plt.tight_layout()
        
        # 在Tkinter中显示图表
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def generate_report(self):
        self.report_text.delete(1.0, tk.END)
        
        report = f"""
    干系人需求调查报告
    生成时间: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    ====================================================

    一、干系人概况
    ----------------------------------------------------
    总干系人数: {len(self.stakeholders)}

    职能类型分布:
    """
        # 职能类型统计
        function_types = [s['function_type'] for s in self.stakeholders]
        function_counts = pd.Series(function_types).value_counts()
        for func, count in function_counts.items():
            report += f"  {func}: {count}人\n"
            
        report += "\n职级分布:\n"
        # 职级统计
        levels = [s['level'] for s in self.stakeholders]
        level_counts = pd.Series(levels).value_counts()
        for level, count in level_counts.items():
            report += f"  {level}: {count}人\n"
            
        report += f"\n二、调查数据概览\n----------------------------------------------------\n"
        report += f"已完成调查人数: {len(self.responses)}\n"
        total_responses = sum(len(responses) for responses in self.responses.values())
        report += f"总调查次数: {total_responses}\n"
        
        # 情绪分析
        emotions = []
        for responses in self.responses.values():
            for response in responses:
                for q_id, answer in response['responses'].items():
                    question = next((q for q in self.survey_questions if q['id'] == q_id), None)
                    if question and question['category'] == '情绪状态':
                        emotions.append(answer)
                        
        if emotions:
            emotion_counts = pd.Series(emotions).value_counts()
            report += "\n情绪状态分布:\n"
            for emotion, count in emotion_counts.items():
                percentage = (count / len(emotions)) * 100
                report += f"  {emotion}: {count}人 ({percentage:.1f}%)\n"
                
        # 需求重要性分析
        importance_scores = []
        for responses in self.responses.values():
            for response in responses:
                for q_id, answer in response['responses'].items():
                    question = next((q for q in self.survey_questions if q['id'] == q_id), None)
                    if question and question['category'] == '需求重要性':
                        score_map = {
                            "非常重要": 5, "重要": 4, "一般": 3, "不重要": 2, "完全不重要": 1
                        }
                        importance_scores.append(score_map.get(answer, 0))
                        
        if importance_scores:
            avg_importance = sum(importance_scores) / len(importance_scores)
            report += f"\n平均需求重要性评分: {avg_importance:.2f} (满分5分)\n"
            
        # 需求紧急性分析 (新增)
        urgency_scores = []
        for responses in self.responses.values():
            for response in responses:
                for q_id, answer in response['responses'].items():
                    question = next((q for q in self.survey_questions if q['id'] == q_id), None)
                    if question and question['category'] == '需求紧急性':
                        score_map = {
                            "非常紧急": 5, "紧急": 4, "一般": 3, "不紧急": 2, "完全不紧急": 1
                        }
                        urgency_scores.append(score_map.get(answer, 0))
                        
        if urgency_scores:
            avg_urgency = sum(urgency_scores) / len(urgency_scores)
            report += f"平均需求紧急性评分: {avg_urgency:.2f} (满分5分)\n"
            
        self.report_text.insert(tk.END, report)




    def export_data(self):
        if not self.stakeholders and not self.responses:
            messagebox.showwarning("无数据", "没有数据可供导出")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            data = {
                "stakeholders": self.stakeholders,
                "responses": dict(self.responses),
                "exported_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("导出成功", f"数据已导出到 {file_path}")
            except Exception as e:
                messagebox.showerror("导出失败", f"导出数据时出错: {str(e)}")
                
    def generate_report(self):
        self.report_text.delete(1.0, tk.END)
        
        report = f"""
干系人需求调查报告
生成时间: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

====================================================

一、干系人概况
----------------------------------------------------
总干系人数: {len(self.stakeholders)}

职能类型分布:
"""
        # 职能类型统计
        function_types = [s['function_type'] for s in self.stakeholders]
        function_counts = pd.Series(function_types).value_counts()
        for func, count in function_counts.items():
            report += f"  {func}: {count}人\n"
            
        report += "\n职级分布:\n"
        # 职级统计
        levels = [s['level'] for s in self.stakeholders]
        level_counts = pd.Series(levels).value_counts()
        for level, count in level_counts.items():
            report += f"  {level}: {count}人\n"
            
        report += f"\n二、调查数据概览\n----------------------------------------------------\n"
        report += f"已完成调查人数: {len(self.responses)}\n"
        total_responses = sum(len(responses) for responses in self.responses.values())
        report += f"总调查次数: {total_responses}\n"
        
        # 情绪分析
        emotions = []
        for responses in self.responses.values():
            for response in responses:
                for q_id, answer in response['responses'].items():
                    question = next((q for q in self.survey_questions if q['id'] == q_id), None)
                    if question and question['category'] == '情绪状态':
                        emotions.append(answer)
                        
        if emotions:
            emotion_counts = pd.Series(emotions).value_counts()
            report += "\n情绪状态分布:\n"
            for emotion, count in emotion_counts.items():
                percentage = (count / len(emotions)) * 100
                report += f"  {emotion}: {count}人 ({percentage:.1f}%)\n"
                
        # 需求重要性分析
        importance_scores = []
        for responses in self.responses.values():
            for response in responses:
                for q_id, answer in response['responses'].items():
                    question = next((q for q in self.survey_questions if q['id'] == q_id), None)
                    if question and question['category'] == '需求重要性':
                        score_map = {
                            "非常重要": 5, "重要": 4, "一般": 3, "不重要": 2, "完全不重要": 1
                        }
                        importance_scores.append(score_map.get(answer, 0))
                        
        if importance_scores:
            avg_importance = sum(importance_scores) / len(importance_scores)
            report += f"\n平均需求重要性评分: {avg_importance:.2f} (满分5分)\n"
            
        self.report_text.insert(tk.END, report)
        
    def save_report(self):
        report_content = self.report_text.get(1.0, tk.END)
        if not report_content.strip():
            messagebox.showwarning("无内容", "没有报告内容可供保存")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                messagebox.showinfo("保存成功", f"报告已保存到 {file_path}")
            except Exception as e:
                messagebox.showerror("保存失败", f"保存报告时出错: {str(e)}")
                
    def create_default_charts(self):
        # 设置matplotlib支持中文显示
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        # 创建默认的占位图表
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, '请点击"生成分析报告"按钮\n以查看数据分析结果', 
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=14)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def save_data(self):
        data = {
            "stakeholders": self.stakeholders,
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            with open("stakeholders.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存干系人数据时出错: {e}")
            
    def load_data(self):
        try:
            with open("stakeholders.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                self.stakeholders = data.get("stakeholders", [])
        except FileNotFoundError:
            # 文件不存在，使用默认数据
            self.stakeholders = [
                {
                    "id": 1,
                    "name": "张经理",
                    "position": "项目经理",
                    "function_type": "管理职能",
                    "level": "高级",
                    "influence": 5,
                    "interest": 5,
                    "emotion": "积极",
                    "contact": "zhang@company.com",
                    "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                {
                    "id": 2,
                    "name": "李工程师",
                    "position": "系统架构师",
                    "function_type": "技术职能",
                    "level": "专家级",
                    "influence": 4,
                    "interest": 4,
                    "emotion": "中性",
                    "contact": "li@company.com",
                    "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                {
                    "id": 3,
                    "name": "王业务",
                    "position": "业务分析师",
                    "function_type": "业务职能",
                    "level": "中级",
                    "influence": 3,
                    "interest": 5,
                    "emotion": "积极",
                    "contact": "wang@company.com",
                    "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            ]
        except Exception as e:
            print(f"加载干系人数据时出错: {e}")
            
    def save_responses(self):
        try:
            with open("responses.json", "w", encoding="utf-8") as f:
                json.dump(dict(self.responses), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存调查数据时出错: {e}")
            
    def load_responses(self):
        try:
            with open("responses.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                self.responses = defaultdict(list, data)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"加载调查数据时出错: {e}")

def main():
    root = tk.Tk()
    app = StakeholderSurveyApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()