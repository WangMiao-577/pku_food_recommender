"""
campus_navigation.py - 校园地图导航服务
整合节点图、A* 路径规划与地图可视化渲染。
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union

from backend.campus_graph import CampusGraph

PKU_MAP_DIR = Path(__file__).parent.parent / "pku_map"
if str(PKU_MAP_DIR) not in sys.path:
    sys.path.insert(0, str(PKU_MAP_DIR))

from pku_map_mapper import PKUMapMapper  # noqa: E402


# 食堂 -> 最近地图节点
CANTEEN_NODE_MAP = {
    "家园食堂": 4,       # 东南门附近
    "农园食堂": 10,      # 图书馆
    "学一食堂": 6,       # 西南门
    "学五食堂": 7,       # 西侧门
    "燕南美食": 12,      # 百周年纪念讲堂
    "佟园": 19,          # 勺园
    "畅春园": 24,
    "艺园": 29,          # 五四体育场
    "勺园": 19,
    "勺中": 19,
    "勺西": 19,
    "成府园": 3,         # 东门
    "松林": 6,
    "快餐车": 41,        # 二教
    "二教地下3W": 41,
}

# 旧版区域名 -> 默认节点（兼容）
REGION_NODE_FALLBACK = {
    "东南门/东门附近": 4,
    "西南门附近": 6,
    "西北门/西门附近": 1,
    "中部教学区": 10,
    "北部生活区": 8,
    "图书馆附近": 10,
}

CATEGORY_LABELS = {
    "gate": "校门",
    "landmark": "地标",
    "building": "建筑",
    "garden": "园林",
    "landscape": "景观",
    "sports": "体育",
}


class CampusNavigationService:
    """校园导航：定位解析、A* 规划、地图渲染"""

    _instance = None

    def __init__(self):
        self.graph = CampusGraph()
        map_path = PKU_MAP_DIR / "pku_campus_map_hd.png"
        nodes_csv = PKU_MAP_DIR / "pku_nodes.csv"
        self.mapper = PKUMapMapper(str(map_path), str(nodes_csv))
        self._temp_dir = Path(tempfile.gettempdir()) / "pku_food_nav"
        self._temp_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_instance(cls) -> "CampusNavigationService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def list_nodes(self) -> List[Dict]:
        return [self.graph.nodes[nid].copy() for nid in sorted(self.graph.nodes)]

    def list_nodes_by_category(self) -> Dict[str, List[Dict]]:
        grouped: Dict[str, List[Dict]] = {}
        for node in self.list_nodes():
            cat = node["category"]
            grouped.setdefault(cat, []).append(node)
        return grouped

    def get_node(self, node_id: int) -> Optional[Dict]:
        n = self.graph.nodes.get(node_id)
        return n.copy() if n else None

    def resolve_node(self, query: Union[int, str, None]) -> Optional[int]:
        if query is None:
            return None
        if isinstance(query, int):
            return query if query in self.graph.nodes else None
        if isinstance(query, str) and query.isdigit():
            nid = int(query)
            return nid if nid in self.graph.nodes else None

        text = str(query).strip()
        if not text:
            return None

        if text in REGION_NODE_FALLBACK:
            return REGION_NODE_FALLBACK[text]

        info = self.mapper.query_node(text)
        if info:
            return int(info["node_id"])

        for nid, node in self.graph.nodes.items():
            if text == node["name"] or text in node["name"] or text.lower() in node["name_en"].lower():
                return nid
        return None

    def canteen_to_node(self, canteen_name: str) -> Optional[int]:
        if canteen_name in CANTEEN_NODE_MAP:
            return CANTEEN_NODE_MAP[canteen_name]
        for name, nid in CANTEEN_NODE_MAP.items():
            if name in canteen_name or canteen_name in name:
                return nid
        return None

    def plan_route(self, start: Union[int, str], goal: Union[int, str]) -> Optional[Dict]:
        start_id = self.resolve_node(start) if not isinstance(start, int) else start
        goal_id = self.resolve_node(goal) if not isinstance(goal, int) else goal
        if start_id is None or goal_id is None:
            return None

        path = self.graph.astar(start_id, goal_id)
        if not path:
            return None

        dist = self.graph.path_distance(path)
        walk_minutes = max(1, int(dist * 1200 / 80))  # 相对距离换算约步行分钟
        steps = [self.graph.nodes[nid]["name"] for nid in path]

        return {
            "start_id": start_id,
            "goal_id": goal_id,
            "start_name": self.graph.nodes[start_id]["name"],
            "goal_name": self.graph.nodes[goal_id]["name"],
            "path_ids": path,
            "path_names": steps,
            "distance": round(dist, 4),
            "walk_minutes": walk_minutes,
            "route_text": " → ".join(steps),
        }

    def plan_route_to_canteen(self, start: Union[int, str], canteen_name: str) -> Optional[Dict]:
        goal_id = self.canteen_to_node(canteen_name)
        if goal_id is None:
            return None
        route = self.plan_route(start, goal_id)
        if route:
            route["canteen"] = canteen_name
            route["goal_name"] = canteen_name
        return route

    def render_route_image(
        self,
        path_ids: List[int],
        highlight_start: Optional[int] = None,
        highlight_goal: Optional[int] = None,
    ) -> str:
        """渲染路径地图，返回图片绝对路径"""
        out = self._temp_dir / f"route_{'_'.join(map(str, path_ids))}.png"
        self.mapper.draw_path(
            node_ids=path_ids,
            output_path=str(out),
            path_color="#FF0066",
            path_width=6,
            show_direction=True,
        )
        return str(out)

    def graph_distance_to_canteen(self, start_id: int, canteen_name: str) -> Optional[float]:
        goal_id = self.canteen_to_node(canteen_name)
        if goal_id is None or start_id not in self.graph.nodes:
            return None
        path = self.graph.astar(start_id, goal_id)
        if not path:
            return None
        return self.graph.path_distance(path)

    def location_score_for_canteen(self, start_id: Optional[int], canteen_name: str) -> tuple:
        """返回 (0-100 分数, 描述)"""
        if start_id is None:
            return 70.0, "未指定位置"
        dist = self.graph_distance_to_canteen(start_id, canteen_name)
        if dist is None:
            return 60.0, "一般距离"
        if dist <= 0.08:
            return 100.0, f"步行约{max(1, int(dist * 1200 / 80))}分钟"
        if dist <= 0.15:
            return 80.0, f"步行约{max(1, int(dist * 1200 / 80))}分钟"
        if dist <= 0.25:
            return 55.0, f"步行约{max(1, int(dist * 1200 / 80))}分钟"
        return 35.0, f"较远，约{max(1, int(dist * 1200 / 80))}分钟"
