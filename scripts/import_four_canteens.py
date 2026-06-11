"""
导入佟园 / 学一+勺园 / 松林 食堂数据

用法:
    python scripts/import_four_canteens.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.canteen_import import (
    merge_tongyuan_csv,
    merge_xueyi_shaoyuan_excel,
    merge_songlin_excel,
)

DISHES_FILE = str(ROOT / "data" / "dishes.json")

SOURCES = {
    "佟园": {
        "path": r"d:\Edgedownload\佟园.csv",
        "fn": lambda p: merge_tongyuan_csv(DISHES_FILE, p, replace_existing=True),
    },
    "学一+勺园": {
        "path": r"d:\学一食堂 勺园食堂.xlsx",
        "fn": lambda p: merge_xueyi_shaoyuan_excel(DISHES_FILE, p, replace_existing=True),
    },
    "松林": {
        "path": r"d:\Edgedownload\松林快餐.xlsx",
        "fn": lambda p: merge_songlin_excel(DISHES_FILE, p, replace_existing=True),
    },
}


def main():
    for label, cfg in SOURCES.items():
        src = Path(cfg["path"])
        if not src.exists():
            print(f"[跳过] {label}: 文件不存在 {src}")
            continue
        result = cfg["fn"](str(src))
        print(f"[{label}] {result} <- {src}")

    dishes = json.loads(Path(DISHES_FILE).read_text(encoding="utf-8"))
    for name in ("佟园", "学一食堂", "勺园", "松林"):
        items = [d for d in dishes if d.get("canteen") == name]
        weekday = [d for d in items if d.get("available_weekdays")]
        print(f"  {name}: {len(items)} 道（按星期供应 {len(weekday)} 道）")
    print("总计:", len(dishes))


if __name__ == "__main__":
    main()
