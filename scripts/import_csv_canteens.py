"""
从 CSV 批量导入食堂菜品到 data/dishes.json

用法:
    python scripts/import_csv_canteens.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.canteen_import import merge_csv_canteen

DISHES_FILE = str(ROOT / "data" / "dishes.json")

IMPORTS = [
    {
        "csv": r"d:\Edgedownload\家园二层.csv",
        "canteen": "家园食堂",
        "prefix": "家园二层",
        "id_prefix": "jy2",
        "loader": "nutrition",
        "floor": 2,
    },
    {
        "csv": r"d:\燕南美食.csv",
        "canteen": "燕南美食",
        "prefix": "燕南地上",
        "id_prefix": "ynu",
        "loader": "nutrition",
        "floor": 1,
    },
    {
        "csv": r"d:\Edgedownload\畅春园.csv",
        "canteen": "畅春园",
        "prefix": "畅春园",
        "id_prefix": "ccy",
        "loader": "changchun",
        "floor": 1,
    },
]


def main():
    results = {}
    for item in IMPORTS:
        csv_path = item["csv"]
        if not Path(csv_path).exists():
            print(f"[跳过] 文件不存在: {csv_path}")
            continue
        added, skipped = merge_csv_canteen(
            DISHES_FILE,
            csv_path,
            target_canteen=item["canteen"],
            location_prefix=item["prefix"],
            id_prefix=item["id_prefix"],
            loader=item["loader"],
            floor_override=item.get("floor"),
            replace_existing=False,
        )
        results[item["canteen"]] = {"added": added, "skipped": skipped, "file": csv_path}
        print(f"[{item['canteen']}] 新增 {added}，跳过重复 {skipped} <- {csv_path}")

    dishes = json.loads(Path(DISHES_FILE).read_text(encoding="utf-8"))
    summary = {}
    for canteen in ("家园食堂", "燕南美食", "畅春园"):
        items = [d for d in dishes if d.get("canteen") == canteen]
        summary[canteen] = len(items)
    print("\n导入后各食堂菜品数:", summary)
    print("总计:", len(dishes))
    return results


if __name__ == "__main__":
    main()
