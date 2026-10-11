import os, time

sessions = {}
collection = None

if os.getenv("MONGODB_URI"):
    from pymongo import MongoClient
    collection = MongoClient(os.getenv("MONGODB_URI")).step_outside.sessions


def save(session):
    session["updated_at"] = time.time()
    if collection is not None:
        collection.replace_one({"_id": session["id"]}, {**session, "_id": session["id"]}, upsert=True)
    else:
        sessions[session["id"]] = session


def get(session_id):
    if collection is not None:
        doc = collection.find_one({"_id": session_id})
        if doc:
            doc.pop("_id")
        return doc
    return sessions.get(session_id)


def recent_challenges(limit=10):
    if collection is not None:
        docs = collection.find({"challenge": {"$ne": None}}).sort("updated_at", -1).limit(limit)
        return [d["challenge"] for d in docs]
    return [s["challenge"] for s in sessions.values() if s["challenge"]][-limit:]
