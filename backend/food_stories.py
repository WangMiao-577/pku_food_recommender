"""
food_stories.py - 美食故事（预设 + 用户收集，同等地位）
"""

import json
import os
import random
from datetime import datetime
from typing import Dict, List, Optional

from backend.paths import delete_user_story_image


class FoodStoryManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.preset_file = os.path.join(data_dir, "preset_food_stories.json")
        self.user_file = os.path.join(data_dir, "user_food_stories.json")
        self.presets = self._load(self.preset_file)
        self.user_stories = self._load(self.user_file)

    @staticmethod
    def _load(path: str) -> List:
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_user(self):
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.user_file, "w", encoding="utf-8") as f:
            json.dump(self.user_stories, f, ensure_ascii=False, indent=2)

    def all_stories(self) -> List[Dict]:
        merged = []
        for s in self.presets:
            item = dict(s)
            item["source"] = "official"
            merged.append(item)
        for s in self.user_stories:
            item = dict(s)
            item["source"] = "user"
            merged.append(item)
        return merged

    def random_story(self) -> Optional[Dict]:
        stories = self.all_stories()
        return random.choice(stories) if stories else None

    def add_user_story(
        self,
        title: str,
        summary: str,
        image: str = "",
        link: str = "",
        author: str = "我",
    ) -> Dict:
        story = {
            "story_id": f"user_{len(self.user_stories) + 1:03d}_{int(datetime.now().timestamp())}",
            "title": title.strip(),
            "summary": summary.strip(),
            "image": image.strip(),
            "link": link.strip(),
            "author": author,
            "created_at": datetime.now().isoformat(),
        }
        self.user_stories.insert(0, story)
        self._save_user()
        return story

    def get_user_story(self, story_id: str) -> Optional[Dict]:
        for s in self.user_stories:
            if s.get("story_id") == story_id:
                return dict(s)
        return None

    def update_user_story(
        self,
        story_id: str,
        title: str,
        summary: str,
        image: str = "",
        link: str = "",
        author: str = "我",
    ) -> Optional[Dict]:
        for s in self.user_stories:
            if s.get("story_id") != story_id:
                continue
            old_image = s.get("image", "")
            new_image = image.strip()
            s["title"] = title.strip()
            s["summary"] = summary.strip()
            s["image"] = new_image
            s["link"] = link.strip()
            s["author"] = author
            s["updated_at"] = datetime.now().isoformat()
            if old_image and old_image != new_image:
                delete_user_story_image(old_image)
            self._save_user()
            return dict(s)
        return None

    def delete_user_story(self, story_id: str) -> bool:
        removed = None
        kept = []
        for s in self.user_stories:
            if s.get("story_id") == story_id:
                removed = s
            else:
                kept.append(s)
        if removed is None:
            return False
        delete_user_story_image(removed.get("image", ""))
        self.user_stories = kept
        self._save_user()
        return True
