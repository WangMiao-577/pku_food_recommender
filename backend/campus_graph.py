"""
campus_graph.py - 校园地图图结构与 A* 路径规划
节点来自 pku_nodes.csv，边由近邻连接构建，启发函数为欧氏距离。
"""

import csv
import heapq
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class CampusGraph:
    """校园路网图（相对坐标 0-1）"""

    def __init__(self, nodes_csv: Optional[str] = None, k_neighbors: int = 6, max_edge_dist: float = 0.14):
        base = Path(__file__).parent.parent / "pku_map"
        self.nodes_csv = nodes_csv or str(base / "pku_nodes.csv")
        self.k_neighbors = k_neighbors
        self.max_edge_dist = max_edge_dist
        self.nodes: Dict[int, Dict] = {}
        self.adj: Dict[int, List[Tuple[int, float]]] = {}
        self._load_nodes()
        self._build_edges()

    def _load_nodes(self):
        with open(self.nodes_csv, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                nid = int(row["node_id"])
                self.nodes[nid] = {
                    "node_id": nid,
                    "name": row["name"],
                    "name_en": row["name_en"],
                    "category": row["category"],
                    "x": float(row["x"]),
                    "y": float(row["y"]),
                    "description": row.get("description", ""),
                }

    @staticmethod
    def euclidean(n1: Dict, n2: Dict) -> float:
        return math.hypot(n1["x"] - n2["x"], n1["y"] - n2["y"])

    def _build_edges(self):
        ids = list(self.nodes.keys())
        for nid in ids:
            neighbors = []
            for oid in ids:
                if oid == nid:
                    continue
                d = self.euclidean(self.nodes[nid], self.nodes[oid])
                if d <= self.max_edge_dist:
                    neighbors.append((oid, d))
            neighbors.sort(key=lambda x: x[1])
            neighbors = neighbors[: self.k_neighbors]
            self.adj[nid] = neighbors

        self._ensure_connectivity()

    def _ensure_connectivity(self):
        """若图不连通，补充最近跨分量边"""
        if not self.nodes:
            return
        start = next(iter(self.nodes))
        visited = set()
        queue = [start]
        while queue:
            cur = queue.pop(0)
            if cur in visited:
                continue
            visited.add(cur)
            for nb, _ in self.adj.get(cur, []):
                if nb not in visited:
                    queue.append(nb)

        if len(visited) == len(self.nodes):
            return

        unvisited = [i for i in self.nodes if i not in visited]
        for uid in unvisited:
            best = None
            best_d = float("inf")
            for vid in visited:
                d = self.euclidean(self.nodes[uid], self.nodes[vid])
                if d < best_d:
                    best_d = d
                    best = vid
            if best is not None:
                self.adj.setdefault(uid, []).append((best, best_d))
                self.adj.setdefault(best, []).append((uid, best_d))
                visited.add(uid)

    def heuristic(self, a_id: int, b_id: int) -> float:
        return self.euclidean(self.nodes[a_id], self.nodes[b_id])

    def astar(self, start_id: int, goal_id: int) -> Optional[List[int]]:
        if start_id not in self.nodes or goal_id not in self.nodes:
            return None
        if start_id == goal_id:
            return [start_id]

        open_heap = [(0.0, start_id)]
        came_from: Dict[int, int] = {}
        g_score = {start_id: 0.0}
        closed: set = set()

        while open_heap:
            _, current = heapq.heappop(open_heap)
            if current in closed:
                continue
            if current == goal_id:
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path

            closed.add(current)
            for neighbor, cost in self.adj.get(current, []):
                if neighbor in closed:
                    continue
                tentative = g_score[current] + cost
                if tentative < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative
                    f = tentative + self.heuristic(neighbor, goal_id)
                    heapq.heappush(open_heap, (f, neighbor))

        return None

    def path_distance(self, path: List[int]) -> float:
        if not path or len(path) < 2:
            return 0.0
        total = 0.0
        for i in range(len(path) - 1):
            total += self.euclidean(self.nodes[path[i]], self.nodes[path[i + 1]])
        return total

    def find_nearest_node(self, x: float, y: float) -> int:
        best_id = next(iter(self.nodes))
        best_d = float("inf")
        for nid, node in self.nodes.items():
            d = math.hypot(node["x"] - x, node["y"] - y)
            if d < best_d:
                best_d = d
                best_id = nid
        return best_id
