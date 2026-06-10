"""
paths.py - 应用路径解析（开发环境 / PyInstaller 打包环境）
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Optional

APP_NAME = "PKUFoodRecommender"
APP_DISPLAY_NAME = "今天吃什么？"
APP_VERSION = "2.0.0"

# 首次安装时从包内复制到用户目录的种子数据（不覆盖已有文件）
SEED_DATA_FILES = (
    "dishes.json",
    "preset_combos.json",
    "preset_food_stories.json",
)

# 始终属于用户的数据文件
USER_DATA_FILES = (
    "user_profile.json",
    "history.json",
    "reviews.json",
    "settings.json",
    "food_footprint.json",
    "user_food_stories.json",
    "footprint_favorites.json",
)


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def project_root() -> Path:
    """源码项目根目录；打包后为 exe 所在目录"""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def bundle_root() -> Path:
    """只读资源根目录（PyInstaller _MEIPASS 或项目根）"""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", project_root()))
    return project_root()


def user_data_dir() -> Path:
    """可写的用户数据目录"""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".local" / "share"
    path = base / APP_NAME / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def bundled_data_dir() -> Path:
    return bundle_root() / "data"


def images_dir() -> Path:
    return bundle_root() / "images"


def pku_map_dir() -> Path:
    return bundle_root() / "pku_map"


def resource_path(*parts: str) -> Path:
    return bundle_root().joinpath(*parts)


def icon_path() -> Path:
    for candidate in (project_root() / "my_logo.ico", bundle_root() / "my_logo.ico"):
        if candidate.exists():
            return candidate
    return project_root() / "my_logo.ico"


def ensure_user_data_seeded() -> Path:
    """将包内种子 JSON 复制到用户目录（仅缺失时）"""
    user_dir = user_data_dir()
    seed_dir = bundled_data_dir()
    if seed_dir.exists():
        for name in SEED_DATA_FILES:
            src = seed_dir / name
            dst = user_dir / name
            if src.exists() and not dst.exists():
                shutil.copy2(src, dst)
    return user_dir


def get_data_dir() -> str:
    """DataManager 使用的数据目录"""
    if is_frozen():
        return str(ensure_user_data_seeded())
    dev_dir = project_root() / "data"
    dev_dir.mkdir(parents=True, exist_ok=True)
    return str(dev_dir)


def dish_image_path(filename: str) -> Path:
    return images_dir() / filename


def user_story_images_dir() -> Path:
    """用户上传的美食故事配图（可写）"""
    if is_frozen():
        path = user_data_dir().parent / "story_images"
    else:
        path = project_root() / "images" / "stories" / "user"
    path.mkdir(parents=True, exist_ok=True)
    return path


def story_image_path(filename: str) -> Path:
    return images_dir() / "stories" / filename


def is_user_story_image(filename: str) -> bool:
    """是否为 stories/user/ 下的用户上传配图"""
    if not filename:
        return False
    return filename.replace("\\", "/").strip().startswith("stories/user/")


def delete_user_story_image(filename: str) -> bool:
    """删除用户上传的故事配图（仅 stories/user/ 路径）"""
    if not is_user_story_image(filename):
        return False
    p = user_story_images_dir() / Path(filename.replace("\\", "/")).name
    if p.exists():
        p.unlink()
        return True
    return False


def resolve_story_image(filename: str) -> Optional[Path]:
    """解析故事配图路径（预设资源或用户上传）"""
    if not filename:
        return None
    name = filename.replace("\\", "/").strip()
    if name.startswith("stories/user/"):
        p = user_story_images_dir() / Path(name).name
        return p if p.exists() else None
    if name.startswith("stories/"):
        p = images_dir() / name
        return p if p.exists() else None
    for candidate in (
        images_dir() / "stories" / name,
        user_story_images_dir() / name,
        Path(name),
    ):
        if candidate.exists():
            return candidate
    return None
