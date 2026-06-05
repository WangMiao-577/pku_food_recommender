"""
canteen_import.py - 从食堂 Excel 导入菜品（农园等）
首列文字为详细档口位置，写入 location_hint / window / floor。
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

CANTEEN_META = {
    "农园食堂": {"canteen_id": "nongyuan", "cuisine_default": "融合"},
}

WINDOW_CUISINE = {
    "日韩料理": "日韩", "西北风味": "西北", "西式简餐": "西式",
    "清真": "清真", "家常菜": "融合", "粤菜": "粤",
    "东侧窗口": "湘", "西侧窗口": "湘", "水饺": "融合",
    "水果": "轻食", "铁板炒饭": "融合", "麻辣烫": "川",
}


def parse_price(raw) -> float:
    if raw is None:
        return 0.0
    s = str(raw).replace("元", "").strip()
    m = re.search(r"[\d.]+", s)
    return float(m.group()) if m else 0.0


def parse_location_hint(loc: str) -> Tuple[str, int, str]:
    """解析「农园二层，东侧窗口」-> floor, window, full hint"""
    loc = (loc or "").strip()
    floor = 1
    if "地下" in loc:
        floor = 0
    elif "二层" in loc or "二楼" in loc:
        floor = 2
    elif "三层" in loc or "三楼" in loc:
        floor = 3

    window = "综合"
    if "，" in loc:
        window = loc.split("，", 1)[1].strip()
    elif "," in loc:
        window = loc.split(",", 1)[1].strip()

    return window, floor, loc


def infer_flavor(name: str, ingredients: str) -> List[str]:
    text = name + ingredients
    flavors = []
    rules = [
        ("麻辣", "麻辣"), ("微辣", "微辣"), ("辣", "辣"), ("酸", "酸"),
        ("甜", "甜"), ("鲜", "鲜"), ("咸", "咸"), ("清淡", "清淡"),
    ]
    for kw, tag in rules:
        if kw in text and tag not in flavors:
            flavors.append(tag)
    if not flavors:
        if any(k in text for k in ("粉", "面", "饭")):
            flavors = ["咸", "鲜"]
        else:
            flavors = ["鲜"]
    return flavors[:3]


def infer_nutrition(calories: float) -> Dict[str, float]:
    cal = float(calories or 400)
    protein = round(cal * 0.12 / 4, 1)
    fat = round(cal * 0.28 / 9, 1)
    carbs = round(cal * 0.45 / 4, 1)
    return {"calories": int(cal), "protein": protein, "fat": fat, "carbs": carbs, "fiber": 2.0}


def infer_tags(name: str, window: str, price: float) -> List[str]:
    tags = []
    if price <= 10:
        tags.append("经济")
    if any(k in name for k in ("粉", "面", "饭", "饺")):
        tags.append("管饱")
    if "水果" in window:
        tags.append("健康")
    if any(k in name for k in ("牛肉", "鸡", "排骨", "肉")):
        tags.append("高蛋白")
    if "水饺" in window or "饺" in name:
        tags.append("经典")
    return tags or ["家常"]


def row_to_dish(row: Dict, dish_id: str, canteen: str, window_numbers: Dict[str, int]) -> Dict:
    window, floor, hint = parse_location_hint(row["location"])
    if window not in window_numbers:
        window_numbers[window] = len(window_numbers) + 1

    name = row["name"]
    ingredients = row.get("ingredients", "")
    price = parse_price(row.get("price_raw"))
    nutrition = infer_nutrition(row.get("calories", 400))
    cuisine = WINDOW_CUISINE.get(window, CANTEEN_META[canteen]["cuisine_default"])

    return {
        "id": dish_id,
        "name": name,
        "canteen": canteen,
        "canteen_id": CANTEEN_META[canteen]["canteen_id"],
        "window": window,
        "window_number": window_numbers[window],
        "floor": floor,
        "price": price,
        "cuisine": cuisine,
        "flavor": infer_flavor(name, ingredients),
        "cooking": "现做",
        "appearance": 3,
        "portion_size": "M" if price < 14 else "L",
        "prep_time": 5 if "水果" in window else 8,
        "image": "",
        "tags": infer_tags(name, window, price),
        "rating": 4.0,
        "rating_count": 0,
        "hours": {"lunch": True, "dinner": True, "late_night": False},
        "related_dishes": [],
        "location_hint": hint,
        "ingredients": ingredients,
        **nutrition,
    }


def load_nongyuan_from_excel(xlsx_path: str) -> List[Dict]:
    import openpyxl
    wb = openpyxl.load_workbook(xlsx_path, read_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = []
    loc = ""
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not any(c for c in row if c):
            continue
        if row[1]:
            loc = str(row[1]).strip()
        name = row[2] if len(row) > 2 else None
        if not name or str(name).strip() in ("菜品名称",):
            continue
        rows.append({
            "location": loc,
            "name": str(name).strip(),
            "price_raw": row[3] if len(row) > 3 else "",
            "ingredients": str(row[4] or "") if len(row) > 4 else "",
            "calories": row[5] if len(row) > 5 else 400,
        })
    return rows


def merge_nongyuan_dishes(
    dishes_file: str,
    xlsx_path: str,
    id_prefix: str = "ny",
    start_index: int = 1,
) -> Tuple[int, int]:
    """导入农园菜品并合并到 dishes.json，返回 (新增, 跳过)"""
    path = Path(dishes_file)
    existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    existing_names = {(d["canteen"], d["name"]) for d in existing}
    existing_ids = {d["id"] for d in existing}

    raw_rows = load_nongyuan_from_excel(xlsx_path)
    window_numbers: Dict[str, int] = {}
    added = 0
    skipped = 0
    idx = start_index

    for row in raw_rows:
        if row["location"] in ("图片来源", "") or not row["name"]:
            skipped += 1
            continue
        key = ("农园食堂", row["name"])
        if key in existing_names:
            skipped += 1
            continue
        dish_id = f"{id_prefix}{idx:03d}"
        while dish_id in existing_ids:
            idx += 1
            dish_id = f"{id_prefix}{idx:03d}"
        dish = row_to_dish(row, dish_id, "农园食堂", window_numbers)
        existing.append(dish)
        existing_names.add(key)
        existing_ids.add(dish_id)
        added += 1
        idx += 1

    path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    return added, skipped
