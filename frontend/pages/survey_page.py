"""
survey_page.py - 问卷调查页面
评估用户选择困难程度，收集偏好信息，生成推荐
"""

import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QButtonGroup, QRadioButton, QCheckBox, QComboBox, QSpinBox,
    QSlider, QGraphicsDropShadowEffect, QFrame, QScrollArea,
    QGridLayout, QSizePolicy, QSpacerItem, QProgressBar, QMessageBox
)
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt, pyqtSignal

from frontend.watercolor_style import COLORS, get_font, get_button_style, POEMS


class QuestionCard(QFrame):
    """问题卡片"""

    def __init__(self, question_num, question_text, parent=None):
        super().__init__(parent)
        self.question_num = question_num
        self.setup_ui(question_text)

    def setup_ui(self, question_text):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # 问题标题
        title = QLabel(f"Q{self.question_num}: {question_text}")
        title.setFont(get_font(13, bold=True))
        title.setStyleSheet(f"color: {COLORS['text_dark'].name()};")
        title.setWordWrap(True)
        layout.addWidget(title)

        # 答案区域（由子类填充）
        self.answer_area = QWidget()
        self.answer_layout = QVBoxLayout(self.answer_area)
        self.answer_layout.setSpacing(8)
        layout.addWidget(self.answer_area)

        # 样式
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card'].name()};
                border: 1px solid {COLORS['border_light'].name()};
                border-radius: 12px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)


class RadioQuestion(QuestionCard):
    """单选题"""

    def __init__(self, num, text, options, parent=None):
        super().__init__(num, text, parent)
        self.group = QButtonGroup(self)
        self.options = []
        for i, opt in enumerate(options):
            rb = QRadioButton(opt)
            rb.setFont(get_font(11))
            rb.setStyleSheet(f"color: {COLORS['text_medium'].name()}; padding: 3px;")
            self.group.addButton(rb, i)
            self.answer_layout.addWidget(rb)
            self.options.append(rb)

    def get_answer(self):
        return self.group.checkedId()


class CheckQuestion(QuestionCard):
    """多选题"""

    def __init__(self, num, text, options, parent=None):
        super().__init__(num, text, parent)
        self.checks = []
        for opt in options:
            cb = QCheckBox(opt)
            cb.setFont(get_font(11))
            cb.setStyleSheet(f"color: {COLORS['text_medium'].name()}; padding: 3px;")
            self.answer_layout.addWidget(cb)
            self.checks.append(cb)

    def get_answer(self):
        return [i for i, cb in enumerate(self.checks) if cb.isChecked()]


class SliderQuestion(QuestionCard):
    """滑块题"""

    def __init__(self, num, text, min_val=1, max_val=5, labels=None, parent=None):
        super().__init__(num, text, parent)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(min_val, max_val)
        self.slider.setValue((min_val + max_val) // 2)
        self.slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: 8px;
                background: {COLORS['border'].name()};
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                width: 20px;
                height: 20px;
                background: {COLORS['primary'].name()};
                border-radius: 10px;
                margin: -6px 0;
            }}
            QSlider::sub-page:horizontal {{
                background: {COLORS['primary_light'].name()};
                border-radius: 4px;
            }}
        """)

        if labels:
            label_row = QHBoxLayout()
            for lbl in labels:
                l = QLabel(lbl)
                l.setFont(get_font(9))
                l.setStyleSheet(f"color: {COLORS['text_light'].name()};")
                label_row.addWidget(l)
                label_row.addStretch() if lbl != labels[-1] else None
            self.answer_layout.addLayout(label_row)

        self.answer_layout.addWidget(self.slider)

    def get_answer(self):
        return self.slider.value()


class SurveyPage(QWidget):
    """问卷调查页面"""

    recommendation_ready = pyqtSignal(list)

    def __init__(self, dm, recommender, parent=None):
        super().__init__(parent)
        self.dm = dm
        self.recommender = recommender
        self.questions = []
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 顶部提示区
        header = QWidget()
        header.setMaximumHeight(80)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)

        title = QLabel("智能推荐")
        title.setFont(get_font(20, bold=True))
        title.setStyleSheet(f"color: {COLORS['primary_dark'].name()};")
        header_layout.addWidget(title)

        subtitle = QLabel("回答几个简单的问题，我们为你找到最合适的菜品 「人间有味是清欢」")
        subtitle.setFont(get_font(10))
        subtitle.setStyleSheet(f"color: {COLORS['text_light'].name()};")
        header_layout.addWidget(subtitle)

        main_layout.addWidget(header)

        # 滚动内容区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        container = QWidget()
        self.content = QVBoxLayout(container)
        self.content.setSpacing(15)
        self.content.setContentsMargins(20, 10, 20, 20)

        # 进度条
        self.progress = QProgressBar()
        self.progress.setMaximumHeight(6)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background: {COLORS['border_light'].name()};
                border-radius: 3px;
                max-height: 6px;
            }}
            QProgressBar::chunk {{
                background: {COLORS['primary'].name()};
                border-radius: 3px;
            }}
        """)
        self.content.addWidget(self.progress)

        # 创建问题
        self.create_questions()

        # 提交按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.submit_btn = QPushButton("获取推荐 ✨")
        self.submit_btn.setFont(get_font(14, bold=True))
        self.submit_btn.setMinimumHeight(48)
        self.submit_btn.setMinimumWidth(180)
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.setStyleSheet(get_button_style("primary", radius=24))
        self.submit_btn.clicked.connect(self.on_submit)
        btn_row.addWidget(self.submit_btn)

        btn_row.addStretch()
        self.content.addLayout(btn_row)

        self.content.addStretch()

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def create_questions(self):
        """创建问卷问题"""
        self.questions.clear()

        # 问题1：选择困难程度
        q1 = RadioQuestion(1, "你今天选择困难的程度如何？",
                          ["完全不纠结，随便吃",
                           "稍微想一下就行",
                           "有点纠结，需要建议",
                           "非常纠结，完全不知道吃什么"])
        self.questions.append(q1)
        self.content.addWidget(q1)

        # 问题2：用餐场景
        q2 = RadioQuestion(2, "今天的用餐场景是？",
                          ["一个人快速解决",
                           "一个人慢慢享用",
                           "和同学/朋友一起",
                           "聚餐/庆祝"])
        self.questions.append(q2)
        self.content.addWidget(q2)

        # 问题3：时间紧迫度
        q3 = SliderQuestion(3, "你有多少时间用餐？（1=非常赶，5=很充裕）",
                           1, 5, ["很赶", "", "一般", "", "充裕"])
        self.questions.append(q3)
        self.content.addWidget(q3)

        # 问题4：营养目标
        q4 = RadioQuestion(4, "今天的饮食目标是？",
                          ["减脂控卡", "均衡饮食", "想多吃点蛋白质", "无所谓，好吃就行"])
        self.questions.append(q4)
        self.content.addWidget(q4)

        # 问题5：口味偏好
        q5 = CheckQuestion(5, "今天想吃的口味？（可多选）",
                          ["清淡鲜美", "微辣开胃", "麻辣重口", "酸甜可口", "浓郁香醇"])
        self.questions.append(q5)
        self.content.addWidget(q5)

        # 问题6：菜系偏好
        q6 = CheckQuestion(6, "偏好哪些菜系？（可多选）",
                          ["川湘麻辣", "粤式清淡", "北方家常", "日韩料理", "西式简餐"])
        self.questions.append(q6)
        self.content.addWidget(q6)

        # 问题7：距离
        q7 = RadioQuestion(7, "你愿意走多远去吃饭？",
                          ["就在附近", "多走几步没问题", "远一点也可以", "无所谓距离"])
        self.questions.append(q7)
        self.content.addWidget(q7)

        # 问题8：预算
        q8 = RadioQuestion(8, "今天的预算大概是？",
                          ["10元以内", "10-20元", "20-30元", "30元以上"])
        self.questions.append(q8)
        self.content.addWidget(q8)

        # 更新进度条
        self.progress.setMaximum(len(self.questions))
        self.progress.setValue(0)
        for q in self.questions:
            if hasattr(q, 'group'):
                q.group.buttonClicked.connect(self.update_progress)
            elif hasattr(q, 'slider'):
                q.slider.valueChanged.connect(self.update_progress)
            elif hasattr(q, 'checks'):
                for cb in q.checks:
                    cb.stateChanged.connect(self.update_progress)

    def update_progress(self):
        """更新进度"""
        answered = sum(1 for q in self.questions if self.is_answered(q))
        self.progress.setValue(answered)

    def is_answered(self, question):
        """检查问题是否已回答"""
        if isinstance(question, RadioQuestion):
            return question.get_answer() >= 0
        elif isinstance(question, CheckQuestion):
            return len(question.get_answer()) > 0
        elif isinstance(question, SliderQuestion):
            return True  # 滑块总有值
        return False

    def on_submit(self):
        """提交问卷，生成推荐"""
        # 检查是否都回答了
        unanswered = [i + 1 for i, q in enumerate(self.questions) if not self.is_answered(q)]
        if unanswered:
            QMessageBox.information(self, "提示",
                                    f"请回答第 {', '.join(map(str, unanswered))} 题后再提交~")
            return

        # 解析答案，更新用户画像
        answers = self.collect_answers()
        self.update_profile(answers)

        # 确定推荐模式
        mode = self.determine_mode(answers)

        # 生成推荐
        recommendations = self.recommender.recommend(top_k=5, mode=mode)

        if recommendations:
            self.recommendation_ready.emit(recommendations)
        else:
            QMessageBox.information(self, "提示",
                                    "没有找到匹配的菜品，建议放宽条件再试~")

    def collect_answers(self):
        """收集答案"""
        return [q.get_answer() for q in self.questions]

    def update_profile(self, answers):
        """根据答案更新用户画像"""
        profile = self.dm.get_profile()

        # 问题2：用餐场景 -> 社交属性
        scene_map = {0: 1, 1: 1, 2: 2, 3: 4}
        if answers[1] in scene_map:
            profile["social"]["companions"] = scene_map[answers[1]]

        # 问题3：时间 -> 偏好
        if answers[2] <= 2:
            profile["preferences"]["distance"] = "就近优先"
        else:
            profile["preferences"]["distance"] = "愿意多走"

        # 问题4：营养目标
        goal_map = {0: "减脂", 1: "均衡", 2: "增肌", 3: "无"}
        if answers[3] in goal_map:
            profile["goals"] = goal_map[answers[3]]

        # 问题7：距离
        dist_map = {0: "就近优先", 1: "就近优先", 2: "愿意多走", 3: "愿意多走"}
        if answers[6] in dist_map:
            profile["preferences"]["distance"] = dist_map[answers[6]]

        # 问题8：预算
        budget_map = {0: 10, 1: 20, 2: 30, 3: 50}
        if answers[7] in budget_map:
            profile["constraints"]["budget_limit"] = budget_map[answers[7]]

        self.dm.update_profile(profile)

    def determine_mode(self, answers):
        """确定推荐模式"""
        # 问题1：选择困难程度
        if answers[0] in [0, 1]:
            return "normal"
        # 问题3：时间紧迫
        if answers[2] == 1:
            return "rush"
        # 问题2：聚餐
        if answers[1] in [2, 3]:
            return "social"
        return "normal"

    def refresh(self):
        """刷新页面"""
        pass
