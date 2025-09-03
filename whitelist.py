# whitelist.py
import json
import os

WHITELIST_PATH = "whitelist.json"


def load_whitelist():
    if not os.path.exists(WHITELIST_PATH):
        return {}
    with open(WHITELIST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_whitelist(data):
    with open(WHITELIST_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_whitelisted(user_id):
    data = load_whitelist()
    return user_id in data


def get_user_info(user_id):
    data = load_whitelist()
    return data.get(user_id)


def get_user_plan_list(user_id):
    info = get_user_info(user_id)
    if not info:
        return []
    return info.get("plan_list", [])


def get_user_role(user_id):
    info = get_user_info(user_id)
    return info.get("role", "unknown") if info else "unknown"


def update_user_plan_list(user_id, plan_list):
    data = load_whitelist()
    if user_id in data:
        data[user_id]["plan_list"] = plan_list
        save_whitelist(data)
        return True
    return False


def get_all_users_by_role(role):
    data = load_whitelist()
    return {uid: info for uid, info in data.items() if info.get("role") == role}
