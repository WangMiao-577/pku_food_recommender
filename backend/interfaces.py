"""
interfaces.py - 预留接口模块
提供两个核心预留接口：
  1. import_dish_data() - 导入菜品数据
  2. connect_dish_selector() - 连接菜品选择程序

所有预留接口均为独立入口，方便后续对接外部系统。
"""

import json
import os
from typing import List, Dict, Optional, Callable
from datetime import datetime

from backend.data_manager import DataManager
from backend.recommender import Recommender
from backend.ai_backend import create_ai_backend, AIModeBackend


# ============ 接口3: AI 模式后端（预留） ============

def connect_ai_backend(config: Optional[Dict] = None) -> Dict:
    """【预留接口】创建并返回 AI 模式后端实例信息

    Args:
        config: 可选配置 {"api_key", "api_base", "model"}

    Returns:
        {
            "success": bool,
            "backend": AIModeBackend instance,
            "configured": bool,
            "timestamp": str,
        }

    示例:
        result = connect_ai_backend({"api_key": "sk-..."})
        ai = result["backend"]
        reply = ai.chat_recommend("想吃点清淡的", DataManager().get_profile())
    """
    config = config or {}
    dm = DataManager()
    backend = create_ai_backend(dm)
    if config:
        backend._load_config(
            api_key=config.get("api_key"),
            api_base=config.get("api_base"),
            model=config.get("model"),
        )
    return {
        "success": True,
        "backend": backend,
        "configured": backend.is_configured(),
        "timestamp": datetime.now().isoformat(),
    }


def ai_chat_recommend(message: str, config: Optional[Dict] = None) -> Dict:
    """【预留接口】单次 AI 对话推荐（无 UI）"""
    conn = connect_ai_backend(config)
    backend: AIModeBackend = conn["backend"]
    return backend.chat_recommend(message, DataManager().get_profile())


def get_campus_navigation() -> Dict:
    """【预留接口】获取校园导航服务"""
    from backend.campus_navigation import CampusNavigationService
    nav = CampusNavigationService.get_instance()
    return {
        "success": True,
        "service": nav,
        "node_count": len(nav.list_nodes()),
        "timestamp": datetime.now().isoformat(),
    }


def plan_campus_route(start, goal) -> Dict:
    """【预留接口】A* 路径规划"""
    from backend.campus_navigation import CampusNavigationService
    nav = CampusNavigationService.get_instance()
    route = nav.plan_route(start, goal)
    if not route:
        return {"success": False, "route": None}
    image = nav.render_route_image(route["path_ids"])
    route["image_path"] = image
    return {"success": True, "route": route}


# ============ 接口1: 菜品数据导入 ============

def import_dish_data(data_source: str, data_format: str = "json",
                     callback: Optional[Callable] = None) -> Dict:
    """【预留接口】导入菜品数据
    
    支持从多种数据源导入菜品信息，可对接外部系统。
    
    Args:
        data_source: 数据源路径或连接字符串
            - JSON文件路径: "/path/to/dishes.json"
            - CSV文件路径: "/path/to/dishes.csv"
            - API端点: "https://api.example.com/dishes"
            - 数据库连接: "db://host:port/dbname"
        data_format: 数据格式 "json" / "csv" / "api" / "db"
        callback: 可选的回调函数，接收导入进度 (current, total, item_name)
    
    Returns:
        导入结果字典:
        {
            "success": bool,
            "imported_count": int,
            "updated_count": int,
            "failed_count": int,
            "errors": List[str],
            "timestamp": str
        }
    
    示例用法:
        result = import_dish_data("./new_dishes.json", "json")
        print(f"导入成功: {result['imported_count']}条")
    """
    result = {
        "success": False,
        "imported_count": 0,
        "updated_count": 0,
        "failed_count": 0,
        "errors": [],
        "timestamp": datetime.now().isoformat()
    }

    dm = DataManager()

    try:
        if data_format == "json":
            _import_from_json(data_source, dm, result, callback)
        elif data_format == "csv":
            _import_from_csv(data_source, dm, result, callback)
        elif data_format == "api":
            _import_from_api(data_source, dm, result, callback)
        elif data_format == "db":
            _import_from_database(data_source, dm, result, callback)
        else:
            result["errors"].append(f"不支持的数据格式: {data_format}")
            return result

        result["success"] = True
    except Exception as e:
        result["errors"].append(f"导入异常: {str(e)}")

    return result


def _import_from_json(filepath: str, dm: DataManager, result: Dict,
                      callback: Optional[Callable] = None):
    """从JSON文件导入菜品数据"""
    if not os.path.exists(filepath):
        result["errors"].append(f"文件不存在: {filepath}")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    dishes = data if isinstance(data, list) else data.get("dishes", [])
    total = len(dishes)

    for i, dish in enumerate(dishes):
        try:
            # 验证必要字段
            if "id" not in dish or "name" not in dish:
                result["failed_count"] += 1
                result["errors"].append(f"缺少必要字段: {dish.get('name', 'unknown')}")
                continue

            # 检查是否已存在
            existing = dm.get_dish_by_id(dish["id"])
            if existing:
                dm.update_dish(dish["id"], dish)
                result["updated_count"] += 1
            else:
                dm.add_dish(dish)
                result["imported_count"] += 1

            if callback:
                callback(i + 1, total, dish.get("name", ""))

        except Exception as e:
            result["failed_count"] += 1
            result["errors"].append(f"导入失败 {dish.get('name', 'unknown')}: {str(e)}")


def _import_from_csv(filepath: str, dm: DataManager, result: Dict,
                     callback: Optional[Callable] = None):
    """从CSV文件导入菜品数据（预留实现）"""
    try:
        import csv
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            dishes = list(reader)

        total = len(dishes)
        for i, row in enumerate(dishes):
            # CSV字段映射
            dish = {
                "id": row.get("id", f"imported_{i}"),
                "name": row.get("name", ""),
                "canteen": row.get("canteen", ""),
                "window": row.get("window", ""),
                "price": float(row.get("price", 0)),
                "cuisine": row.get("cuisine", ""),
                "flavor": row.get("flavor", "").split(","),
                "cooking": row.get("cooking", ""),
                "appearance": int(row.get("appearance", 3)),
                "calories": float(row.get("calories", 0)),
                "protein": float(row.get("protein", 0)),
                "carbs": float(row.get("carbs", 0)),
                "fat": float(row.get("fat", 0)),
                "fiber": float(row.get("fiber", 0)),
                "prep_time": int(row.get("prep_time", 5)),
                "tags": row.get("tags", "").split(","),
                "rating": float(row.get("rating", 3.5)),
                "rating_count": int(row.get("rating_count", 0)),
                "hours": {"lunch": True, "dinner": True, "late_night": False}
            }

            existing = dm.get_dish_by_id(dish["id"])
            if existing:
                dm.update_dish(dish["id"], dish)
                result["updated_count"] += 1
            else:
                dm.add_dish(dish)
                result["imported_count"] += 1

            if callback:
                callback(i + 1, total, dish["name"])

    except ImportError:
        result["errors"].append("CSV导入需要csv模块")
    except Exception as e:
        result["errors"].append(f"CSV导入错误: {str(e)}")


def _import_from_api(api_endpoint: str, dm: DataManager, result: Dict,
                     callback: Optional[Callable] = None):
    """从API导入菜品数据（预留实现，需配置网络请求）"""
    # 预留接口，实际需要时取消注释以下代码
    """
    import requests
    response = requests.get(api_endpoint, timeout=30)
    response.raise_for_status()
    data = response.json()
    dishes = data if isinstance(data, list) else data.get("dishes", [])
    
    total = len(dishes)
    for i, dish in enumerate(dishes):
        existing = dm.get_dish_by_id(dish.get("id"))
        if existing:
            dm.update_dish(dish["id"], dish)
            result["updated_count"] += 1
        else:
            dm.add_dish(dish)
            result["imported_count"] += 1
        
        if callback:
            callback(i + 1, total, dish.get("name", ""))
    """
    result["errors"].append("API导入功能已预留，需配置网络请求模块后启用")


def _import_from_database(db_connection: str, dm: DataManager, result: Dict,
                          callback: Optional[Callable] = None):
    """从数据库导入菜品数据（预留实现，需配置数据库驱动）"""
    # 预留接口，实际需要时取消注释以下代码
    """
    import sqlite3  # 或其他数据库驱动
    # 解析连接字符串 db://path/to/db
    db_path = db_connection.replace("db://", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dishes")
    rows = cursor.fetchall()
    
    total = len(rows)
    for i, row in enumerate(rows):
        # 字段映射逻辑...
        dish = map_db_row_to_dish(row)
        # 导入逻辑...
        if callback:
            callback(i + 1, total, dish["name"])
    
    conn.close()
    """
    result["errors"].append("数据库导入功能已预留，需配置数据库驱动后启用")


# ============ 接口2: 菜品选择程序连接 ============

def connect_dish_selector(selector_type: str = "internal",
                          config: Optional[Dict] = None) -> Dict:
    """【预留接口】连接菜品选择程序
    
    连接到外部或内部的菜品选择/决策系统，支持多种对接方式。
    
    Args:
        selector_type: 选择器类型
            - "internal": 使用内置推荐引擎
            - "random": 完全随机选择
            - "api": 调用外部API
            - "webhook": 通过Webhook对接
            - "mq": 通过消息队列对接
        config: 配置参数
            - api_endpoint: API端点URL
            - webhook_url: Webhook地址
            - mq_connection: 消息队列连接字符串
            - timeout: 超时时间（秒）
            - auth_token: 认证令牌
    
    Returns:
        连接结果字典:
        {
            "success": bool,
            "selector_type": str,
            "selected_dish": Dict or None,  # 选中的菜品
            "connection_info": Dict,        # 连接信息
            "timestamp": str
        }
    
    示例用法:
        result = connect_dish_selector("internal")
        if result["success"]:
            dish = result["selected_dish"]
            print(f"选中菜品: {dish['name']}")
        
        # 或连接外部API
        result = connect_dish_selector("api", {
            "api_endpoint": "https://food-api.pku.edu.cn/select",
            "timeout": 10
        })
    """
    result = {
        "success": False,
        "selector_type": selector_type,
        "selected_dish": None,
        "connection_info": {},
        "timestamp": datetime.now().isoformat()
    }

    if config is None:
        config = {}

    try:
        if selector_type == "internal":
            _select_internal(result, config)
        elif selector_type == "random":
            _select_random(result, config)
        elif selector_type == "api":
            _select_via_api(result, config)
        elif selector_type == "webhook":
            _select_via_webhook(result, config)
        elif selector_type == "mq":
            _select_via_mq(result, config)
        else:
            result["connection_info"]["error"] = f"未知的选择器类型: {selector_type}"
            return result

        result["success"] = True
    except Exception as e:
        result["connection_info"]["error"] = str(e)

    return result


def _select_internal(result: Dict, config: Dict):
    """使用内置推荐引擎选择菜品"""
    dm = DataManager()
    engine = Recommender(dm)

    mode = config.get("mode", "normal")
    top_k = config.get("top_k", 1)

    recommendations = engine.recommend(top_k=top_k, mode=mode)

    if recommendations:
        result["selected_dish"] = recommendations[0] if top_k == 1 else recommendations
        result["connection_info"] = {
            "method": "internal_recommender",
            "mode": mode,
            "candidates_count": len(recommendations),
            "data_source": "local_json"
        }
    else:
        result["connection_info"] = {"error": "无可用推荐结果"}


def _select_random(result: Dict, config: Dict):
    """完全随机选择（测试用）"""
    import random
    dm = DataManager()
    dishes = dm.get_all_dishes()

    if dishes:
        selected = random.choice(dishes)
        result["selected_dish"] = selected
        result["connection_info"] = {
            "method": "random_selection",
            "pool_size": len(dishes)
        }
    else:
        result["connection_info"] = {"error": "菜品池为空"}


def _select_via_api(result: Dict, config: Dict):
    """通过外部API选择菜品（预留实现）"""
    """
    import requests
    
    endpoint = config.get("api_endpoint", "")
    timeout = config.get("timeout", 10)
    auth_token = config.get("auth_token", "")
    
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    # 构建请求数据
    payload = {
        "timestamp": datetime.now().isoformat(),
        "user_profile": DataManager().get_profile(),
        "request_type": "dish_selection"
    }
    
    response = requests.post(endpoint, json=payload, headers=headers, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    
    result["selected_dish"] = data.get("dish")
    result["connection_info"] = {
        "method": "external_api",
        "endpoint": endpoint,
        "status_code": response.status_code
    }
    """
    result["connection_info"] = {
        "method": "external_api",
        "status": "reserved",
        "note": "需安装requests库并配置API端点后启用"
    }


def _select_via_webhook(result: Dict, config: Dict):
    """通过Webhook对接（预留实现）"""
    """
    import requests
    
    webhook_url = config.get("webhook_url", "")
    timeout = config.get("timeout", 10)
    
    payload = {
        "event": "dish_selection_request",
        "timestamp": datetime.now().isoformat(),
        "user_id": config.get("user_id", "anonymous")
    }
    
    response = requests.post(webhook_url, json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    
    result["selected_dish"] = data.get("dish")
    result["connection_info"] = {
        "method": "webhook",
        "url": webhook_url,
        "status_code": response.status_code
    }
    """
    result["connection_info"] = {
        "method": "webhook",
        "status": "reserved",
        "note": "需配置Webhook URL后启用"
    }


def _select_via_mq(result: Dict, config: Dict):
    """通过消息队列对接（预留实现）"""
    """
    # 使用 pika (RabbitMQ) 或 kafka-python (Kafka)
    # import pika
    # connection = pika.BlockingConnection(pika.URLParameters(config["mq_connection"]))
    # channel = connection.channel()
    # ...
    """
    result["connection_info"] = {
        "method": "message_queue",
        "status": "reserved",
        "note": "需安装消息队列客户端库后启用"
    }


# ============ 测试入口 ============

def test_interfaces():
    """接口测试"""
    print("=" * 60)
    print("预留接口测试")
    print("=" * 60)

    # 测试接口1: 导入菜品数据
    print("\n【测试1】导入菜品数据接口（JSON格式）")

    # 创建测试数据文件
    test_data = [
        {
            "id": "test_001",
            "name": "测试菜品-清蒸时蔬",
            "canteen": "家园食堂",
            "window": "粤菜",
            "price": 12,
            "cuisine": "粤",
            "flavor": ["鲜", "咸"],
            "cooking": "清蒸",
            "appearance": 4,
            "calories": 120,
            "protein": 5,
            "carbs": 15,
            "fat": 3,
            "fiber": 6,
            "prep_time": 5,
            "image": "",
            "tags": ["健康", "清淡"],
            "rating": 4.0,
            "rating_count": 10,
            "hours": {"lunch": True, "dinner": True, "late_night": False}
        }
    ]

    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False)
        test_file = f.name

    result = import_dish_data(test_file, "json")
    print(f"  导入结果: {'成功' if result['success'] else '失败'}")
    print(f"  导入数: {result['imported_count']}, 更新数: {result['updated_count']}")
    print(f"  错误: {result['errors'] if result['errors'] else '无'}")

    os.unlink(test_file)

    # 测试接口2: 连接菜品选择程序
    print("\n【测试2】连接菜品选择程序（内置引擎）")
    result = connect_dish_selector("internal", {"mode": "normal", "top_k": 1})
    print(f"  连接结果: {'成功' if result['success'] else '失败'}")
    if result["selected_dish"]:
        dish = result["selected_dish"]
        print(f"  选中菜品: {dish['name']} @ {dish['canteen']}  ¥{dish['price']}")
    print(f"  连接信息: {result['connection_info']}")

    print("\n【测试3】连接菜品选择程序（随机模式）")
    result = connect_dish_selector("random")
    print(f"  连接结果: {'成功' if result['success'] else '失败'}")
    if result["selected_dish"]:
        print(f"  随机选中: {result['selected_dish']['name']}")

    print("\n【测试4】预留接口（API模式 - 未启用）")
    result = connect_dish_selector("api", {"api_endpoint": "https://example.com/api"})
    print(f"  状态: {result['connection_info'].get('status', 'unknown')}")
    print(f"  说明: {result['connection_info'].get('note', '')}")

    # 清理
    import shutil
    if os.path.exists("test_data"):
        shutil.rmtree("test_data")
    if os.path.exists("data"):
        shutil.rmtree("data")

    print("\n所有接口测试完成!")


if __name__ == "__main__":
    test_interfaces()
