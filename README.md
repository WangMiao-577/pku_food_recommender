# 今天吃什么？ - 北京大学食堂智能推荐系统

## 一、项目简介

**今天吃什么？** 是一款基于多维度决策模型与个性化画像的校园食堂智能推荐系统，旨在解决"今天吃什么"的选择困难问题。系统覆盖北京大学校属20+个供餐点，基于10维决策矩阵，采用三层流水线推荐逻辑，为用户提供个性化菜品推荐。

### 主要功能

- **智能问卷推荐**：通过问卷调查评估选择困难程度，从多个维度生成推荐
- **食堂浏览**：按食堂、菜系、搜索等多种方式浏览菜品
- **菜品详情**：营养成分、评分、口味标签等详细信息展示
- **就餐记录**：自动记录就餐历史，支持新鲜度评分
- **评价反馈**：1-5星评分+标签评价，贝叶斯平均算法
- **个性化设置**：预算、营养目标、距离偏好等个性化配置

### 技术特色

- **水彩印象派UI风格**：温馨柔和的配色方案，融入北大未名湖元素
- **10维决策矩阵**：新鲜度、营养、距离、时间、特殊需求、人流量、社交、评分、忌口、随机性
- **三层流水线推荐**：分层过滤（硬约束）→ 加权评分（软偏好）→ 扰动输出（多样性）
- **贝叶斯平均评分**：平滑处理，避免新菜品被埋没
- **ε-greedy探索机制**：兼顾精准推荐与长尾探索

---

## 二、运行环境

### 系统要求

- **操作系统**：Windows 10/11, macOS 10.14+, Linux
- **Python**：3.7 或更高版本
- **内存**：4GB 及以上

### 依赖安装

运行前需要安装以下Python包：

```bash
# 核心依赖（必须）
pip install PyQt5

# 可选依赖（用于预留接口功能扩展）
pip install requests          # API接口调用
pip install pika              # RabbitMQ消息队列
pip install kafka-python      # Kafka消息队列
```

**最小依赖安装（仅运行基本功能）：**

```bash
pip install PyQt5
```

---

## 三、在PyQt中运行程序

### 步骤1：解压项目

将项目解压到任意目录，确保目录结构如下：

```
pku_food_recommender/
├── main.py                   # 程序入口
├── backend/                  # 后端模块
│   ├── __init__.py
│   ├── data_manager.py       # 数据管理
│   ├── recommender.py        # 推荐算法
│   └── interfaces.py         # 预留接口
├── frontend/                 # 前端模块
│   ├── __init__.py
│   ├── watercolor_style.py   # 水彩风格主题
│   ├── main_window.py        # 主窗口
│   └── pages/                # 各功能页面
│       ├── __init__.py
│       ├── welcome_page.py
│       ├── survey_page.py
│       ├── recommendation_page.py
│       ├── canteen_page.py
│       ├── dish_detail_page.py
│       ├── history_page.py
│       ├── feedback_page.py
│       └── settings_page.py
├── images/                   # 图片资源
│   ├── bg_weiminghu.jpg      # 未名湖水彩背景
│   ├── bg_warm_light.jpg     # 温暖背景
│   ├── warm_dining_scene.jpg # 用餐场景
│   ├── dish_1_mapo_tofu.jpg  # 菜品图片
│   ├── dish_2_kung_pao_chicken.jpg
│   ├── dish_3_hongshaorou.jpg
│   ├── dish_4_tomato_egg.jpg
│   ├── dish_5_shuizhuyu.jpg
│   ├── dish_6_beef_noodle.jpg
│   ├── dish_7_bibimbap.jpg
│   ├── dish_8_pasta.jpg
│   ├── dish_9_steamed_fish.jpg
│   ├── dish_10_sweet_sour.jpg
│   ├── dish_11_dumplings.jpg
│   └── dish_12_claypot.jpg
├── data/                     # 数据目录（运行时自动创建）
└── README.md                 # 本文档
```

### 步骤2：安装依赖

```bash
cd pku_food_recommender
pip install PyQt5
```

### 步骤3：运行程序

**方式一：命令行运行**

```bash
# 进入项目目录
cd pku_food_recommender

# 运行主程序
python main.py
```

**方式二：IDE中运行**

1. 打开 PyCharm / VSCode / 其他IDE
2. 打开 `pku_food_recommender` 目录作为项目
3. 右键 `main.py` → 运行

**方式三：双击运行（Windows）**

创建 `run.bat` 文件：

```batch
@echo off
cd /d "%~dp0"
python main.py
pause
```

### 运行效果

程序启动后：
1. 首先加载水彩风格的主界面
2. 默认显示**欢迎主页**，包含今日推荐和快捷入口
3. 左侧边栏可切换各功能页面
4. 顶部显示随机温馨诗句，可手动刷新

---

## 四、后端接口在程序中的位置

### 接口1：导入菜品数据接口

**文件位置**：`backend/interfaces.py`
**函数名**：`import_dish_data()`

```python
def import_dish_data(data_source: str, data_format: str = "json",
                     callback: Optional[Callable] = None) -> Dict:
```

**功能**：从外部数据源导入菜品数据，支持 JSON、CSV、API、数据库四种格式。

**使用示例**：

```python
from backend.interfaces import import_dish_data

# 从JSON文件导入
result = import_dish_data("./new_dishes.json", "json")
print(f"导入成功: {result['imported_count']}条")

# 从CSV文件导入
result = import_dish_data("./dishes.csv", "csv")
```

**预留说明**：
- CSV导入：已预留，需安装 `csv` 模块（Python内置）
- API导入：已预留，需安装 `requests` 库后取消注释代码启用
- 数据库导入：已预留，需安装对应数据库驱动后配置连接

**回调函数**（可选）：
```python
def progress_callback(current, total, item_name):
    print(f"导入进度: {current}/{total} - {item_name}")

import_dish_data("./dishes.json", "json", callback=progress_callback)
```

---

### 接口2：连接菜品选择程序接口

**文件位置**：`backend/interfaces.py`
**函数名**：`connect_dish_selector()`

```python
def connect_dish_selector(selector_type: str = "internal",
                          config: Optional[Dict] = None) -> Dict:
```

**功能**：连接到外部或内部的菜品选择/决策系统。

**支持的选择器类型**：

| 类型 | 说明 | 状态 |
|------|------|------|
| `internal` | 使用内置推荐引擎 | 已实现 |
| `random` | 完全随机选择 | 已实现（测试用）|
| `api` | 调用外部API | 已预留 |
| `webhook` | 通过Webhook对接 | 已预留 |
| `mq` | 通过消息队列对接 | 已预留 |

**使用示例**：

```python
from backend.interfaces import connect_dish_selector

# 使用内置推荐引擎
result = connect_dish_selector("internal", {"mode": "normal", "top_k": 5})
if result["success"]:
    dish = result["selected_dish"]
    print(f"推荐菜品: {dish['name']}")

# 随机选择（测试用）
result = connect_dish_selector("random")

# 连接外部API（需配置）
result = connect_dish_selector("api", {
    "api_endpoint": "https://food-api.pku.edu.cn/select",
    "timeout": 10,
    "auth_token": "your_token"
})
```

---

## 五、需要修改的部分

### 1. 菜品数据自定义

**文件**：`backend/data_manager.py`
**位置**：`DEFAULT_DISHES` 列表

默认包含12道示例菜品。你需要修改为自己的菜品数据：

```python
DEFAULT_DISHES = [
    {
        "id": "d001",                    # 唯一ID
        "name": "菜品名称",               # 菜品名称
        "canteen": "食堂名称",            # 所属食堂
        "window": "档口名称",             # 档口
        "price": 15,                     # 价格（元）
        "cuisine": "川",                  # 菜系：川/鲁/粤/西北/日韩/西式/融合
        "flavor": ["辣", "鲜"],           # 口味标签
        "cooking": "现炒",                # 烹饪方式
        "appearance": 4,                 # 卖相评分1-5
        "calories": 320,                 # 热量(kcal)
        "protein": 25,                   # 蛋白质(g)
        "carbs": 15,                     # 碳水(g)
        "fat": 18,                       # 脂肪(g)
        "fiber": 2,                      # 膳食纤维(g)
        "prep_time": 8,                  # 出餐时间(分钟)
        "image": "dish_1_mapo_tofu.jpg", # 菜品图片文件名
        "tags": ["下饭", "经典"],         # 标签
        "rating": 4.2,                   # 初始评分
        "rating_count": 156,             # 评价人数
        "hours": {                       # 供应时段
            "lunch": True,
            "dinner": True,
            "late_night": False
        }
    },
    # ... 更多菜品
]
```

### 2. 食堂数据自定义

**文件**：`backend/data_manager.py`
**位置**：`CANTEENS` 列表

```python
CANTEENS = [
    {
        "id": "jiayuan",
        "name": "食堂名称",
        "floors": 3,                    # 楼层数
        "x": 116.316, "y": 39.999,     # GIS坐标（用于距离计算）
        "windows": ["档口1", "档口2"]    # 档口列表
    },
    # ... 更多食堂
]
```

### 3. 菜品图片替换

**目录**：`images/`

将菜品图片替换为自己的图片，注意：
- 图片格式：JPG 或 PNG
- 建议尺寸：4:3 比例，如 400x300 像素
- 命名格式：`dish_N_英文名.jpg`
- 修改 `DEFAULT_DISHES` 中对应菜品的 `image` 字段

### 4. 背景图片替换

**目录**：`images/`

- `bg_weiminghu.jpg` - 未名湖水彩背景（主界面水印）
- `bg_warm_light.jpg` - 温暖背景
- `warm_dining_scene.jpg` - 用餐场景

### 5. 预留接口启用

**文件**：`backend/interfaces.py`

API/数据库/Webhook/消息队列接口已预留代码框架，需要时：

1. 安装对应依赖（requests/pika等）
2. 取消注释对应函数的实现代码
3. 配置连接参数

### 6. 营养目标参数调整

**文件**：`backend/recommender.py`
**位置**：`NUTRITION_GOALS` 字典

```python
NUTRITION_GOALS = {
    "减脂": {"calories": (200, 400), "protein": (20, 40), "fat": (5, 15)},
    "增肌": {"calories": (400, 700), "protein": (25, 50), "fat": (10, 30)},
    "均衡": {"calories": (300, 600), "protein": (15, 35), "fat": (10, 25)},
    "无": None,
}
```

---

## 六、数据存储说明

### 数据目录

程序首次运行时自动创建 `data/` 目录，包含以下JSON文件：

| 文件 | 内容 | 说明 |
|------|------|------|
| `dishes.json` | 菜品数据 | 可修改 |
| `user_profile.json` | 用户画像 | 自动保存 |
| `history.json` | 就餐历史 | 自动保存 |
| `reviews.json` | 评价数据 | 自动保存 |
| `settings.json` | 应用设置 | 自动保存 |

### 数据导入导出

在**设置页面**中，可以：
- **导出所有数据**：将完整数据导出为JSON文件（用于备份或迁移）
- **导入数据**：从JSON文件导入数据
- **重置数据**：清空所有用户数据，恢复默认状态

---

## 七、项目结构说明

```
pku_food_recommender/
|
|-- main.py                          # 程序入口点
|
|-- backend/                         # 后端模块
|   |-- __init__.py
|   |-- data_manager.py             # 数据管理器（CRUD操作）
|   |-- recommender.py              # 推荐引擎（10维决策+3层流水线）
|   |-- interfaces.py               # 预留接口（数据导入+选择程序连接）
|
|-- frontend/                        # 前端模块
|   |-- __init__.py
|   |-- watercolor_style.py         # 水彩风格主题（配色+字体+样式）
|   |-- main_window.py              # 主窗口（导航+页面栈）
|   |-- pages/                       # 各功能页面
|       |-- __init__.py
|       |-- welcome_page.py         # 欢迎主页（今日推荐+快捷入口）
|       |-- survey_page.py          # 问卷调查（8个问题）
|       |-- recommendation_page.py  # 推荐结果展示
|       |-- canteen_page.py         # 食堂浏览+菜品搜索
|       |-- dish_detail_page.py     # 菜品详情（营养+评分）
|       |-- history_page.py         # 就餐历史
|       |-- feedback_page.py        # 评价反馈
|       |-- settings_page.py        # 设置+关于
|
|-- images/                          # 图片资源
|   |-- bg_weiminghu.jpg            # 未名湖水彩背景
|   |-- bg_warm_light.jpg           # 温暖水彩背景
|   |-- dish_1~12_*.jpg             # 水彩菜品图片
|
|-- data/                            # 运行时数据目录（自动创建）
|-- README.md                        # 本文档
```

---

## 八、常见问题

### Q1: 运行时报错 `No module named 'PyQt5'`

**解决**：
```bash
pip install PyQt5
```

### Q2: 图片加载失败

**检查**：
1. `images/` 目录是否存在
2. 图片文件名是否与 `DEFAULT_DISHES` 中的 `image` 字段一致
3. 图片格式是否正确（JPG/PNG）

### Q3: 数据丢失

**注意**：
- 数据存储在项目目录的 `data/` 文件夹中
- 请勿删除 `data/` 目录下的JSON文件
- 建议定期使用设置页面的导出功能备份数据

### Q4: 字体显示异常

**解决**：
程序使用微软雅黑字体（Microsoft YaHei）。如果在Linux/macOS上运行，可以修改 `frontend/watercolor_style.py` 中的字体设置：

```python
def get_font(size=12, bold=False, italic=False) -> QFont:
    font = QFont("Microsoft YaHei", size)  # 修改为系统可用字体
    # Linux可改为 "WenQuanYi Micro Hei" 或 "Noto Sans CJK SC"
    # macOS可改为 "PingFang SC" 或 "Heiti SC"
    font.setBold(bold)
    font.setItalic(italic)
    return font
```

---

## 九、开发计划

### 已实现功能 ✅
- [x] 水彩印象派UI风格
- [x] 10维决策矩阵推荐
- [x] 三层流水线推荐逻辑
- [x] 问卷调查界面
- [x] 推荐结果展示（含照片）
- [x] 食堂浏览与搜索
- [x] 菜品详情与营养信息
- [x] 就餐历史记录
- [x] 评价反馈系统
- [x] 用户偏好设置
- [x] 数据导入导出接口
- [x] 菜品选择程序连接接口
- [x] 贝叶斯平均评分
- [x] ε-greedy探索机制

### 预留功能（待扩展）🔜
- [ ] API接口对接
- [ ] 数据库连接
- [ ] Webhook通知
- [ ] 消息队列集成
- [ ] 实时人流量数据
- [ ] 多人偏好融合
- [ ] 群体聚餐推荐

---

## 十、许可证

本项目仅供学习和研究使用。

**「四方食事，不过一碗人间烟火」**

---

*文档版本: v1.0*
*最后更新: 2026-05-17*
