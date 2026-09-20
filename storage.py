#All data stored on MongoDB Atlas


import os
import time
from pymongo import MongoClient

MONGODB_URI = os.getenv("MONGODB_URI")

client = MongoClient(MONGODB_URI)
db = client["mandrabot"]

honor_col  = db["honor"]
stone_col  = db["stone"]
blocked_col = db["blocked"]

COOLDOWN_SECONDS = 4 * 60 * 60  # 4 hours

#DM blocked users 
def load_blocked_users() -> set:
    try:
        doc = blocked_col.find_one({"_id": "blocked"})
        return set(doc["users"]) if doc else set()
    except Exception as e:
        print(f"load_blocked_users error: {e}")
        return set()
    #saving blocked users
def save_blocked_users(blocked_users: set):
    try:
        blocked_col.update_one(
            {"_id": "blocked"},
            {"$set": {"users": list(blocked_users)}},
            upsert=True
        )
    except Exception as e:
        print(f"save_blocked_users error: {e}")


# Stone leaderboard
def load_stone_data() -> dict:
    try:
        doc = stone_col.find_one({"_id": "scores"})
        return doc["scores"] if doc else {}
    except Exception as e:
        print(f"load_stone_data error: {e}")
        return {}

def save_stone_data(scores: dict):
    try:
        stone_col.update_one(
            {"_id": "scores"},
            {"$set": {"scores": scores}},
            upsert=True
        )
    except Exception as e:
        print(f"save_stone_data error: {e}")


#Honor/karma system
def _get_honor_doc(user_id: str) -> dict | None:
    return honor_col.find_one({"_id": user_id})

def _ensure_honor_user(user_id: str):
    honor_col.update_one(
        {"_id": user_id},
        {"$setOnInsert": {"karma": 0, "cooldowns": {}}},
        upsert=True
    )

def get_honor_user(user_id: int) -> dict | None:
    try:
        return _get_honor_doc(str(user_id))
    except Exception as e:
        print(f"get_honor_user error: {e}")
        return None

def add_honor(target_id: int, voter_id: int) -> tuple[bool, str]:
    try:
        tid, vid = str(target_id), str(voter_id)

        if tid == vid:
            return False, "You can't rep yourself."

        _ensure_honor_user(tid)
        doc = _get_honor_doc(tid)

        last = doc["cooldowns"].get(vid, 0)
        remaining = COOLDOWN_SECONDS - (time.time() - last)
        if remaining > 0:
            hours   = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            return False, f"You can +rep this user again in **{hours}h {minutes}m**."

        honor_col.update_one(
            {"_id": tid},
            {
                "$inc": {"karma": 1},
                "$set": {f"cooldowns.{vid}": time.time()}
            }
        )
        new_karma = doc["karma"] + 1
        return True, f"+rep! They now have **{new_karma}** karma"

    except Exception as e:
        print(f"add_honor error: {e}")
        return False, f"Something went wrong: {e}"

def remove_honor(target_id: int, voter_id: int) -> tuple[bool, str]:
    try:
        tid, vid = str(target_id), str(voter_id)

        if tid == vid:
            return False, "You can't rep yourself."

        _ensure_honor_user(tid)
        doc = _get_honor_doc(tid)

        last = doc["cooldowns"].get(vid, 0)
        remaining = COOLDOWN_SECONDS - (time.time() - last)
        if remaining > 0:
            hours   = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            return False, f"You can -rep this user again in **{hours}h {minutes}m**."

        honor_col.update_one(
            {"_id": tid},
            {
                "$inc": {"karma": -1},
                "$set": {f"cooldowns.{vid}": time.time()}
            }
        )
        new_karma = doc["karma"] - 1
        return True, f"-rep. That fool now has **{new_karma}** karma"

    except Exception as e:
        print(f"remove_honor error: {e}")
        return False, f"Something went wrong: {e}"

def get_honor_leaderboard(top_n: int = 10) -> list[tuple[str, int]]:
    try:
        docs = honor_col.find().sort("karma", -1).limit(top_n)
        return [(doc["_id"], doc["karma"]) for doc in docs]
    except Exception as e:
        print(f"get_honor_leaderboard error: {e}")
        return []