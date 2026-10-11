# Step Outside - the web server. Run with: uvicorn main:app --reload
import os, time, uuid
from dotenv import load_dotenv

load_dotenv()

import sentry_sdk
if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), traces_sample_rate=1.0)

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import ai, db, extras

app = FastAPI()
ENOUGH = "Enough. Put your phone away."

def get_open_session(session_id, expected_state=None):
    session = db.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if session["state"] == "ended":
        raise HTTPException(410, ENOUGH)
    if expected_state and session["state"] != expected_state:
        raise HTTPException(409, "Wrong step")
    return session


@app.post("/api/start")
def start(minutes: float = 20):
    if not 0.25 <= minutes <= 240:
        raise HTTPException(400, "Choose between 0.25 and 240 minutes")
    session = {
        "id": uuid.uuid4().hex,
        "state": "idle",
        "started_at": time.time(),
        "idle_seconds": round(minutes * 60),
        "challenge": None,
        "reply": None,
        "subject": None,
    }
    db.save(session)
    return {"id": session["id"], "idle_seconds": session["idle_seconds"]}


@app.post("/api/{session_id}/challenge")
def challenge(session_id: str):
    session = get_open_session(session_id, "idle")
    with sentry_sdk.start_transaction(op="ai", name="make_challenge"):
        session["challenge"] = ai.make_challenge(db.recent_challenges())
        session["seconds_on_page"] = round(time.time() - session["started_at"])
        session["state"] = "challenged"
        db.save(session)
    return {"challenge": session["challenge"]}


@app.post("/api/{session_id}/photo")
async def photo(session_id: str, file: UploadFile = File(...)):
    session = get_open_session(session_id, "challenged")
    image = await file.read()
    if not file.content_type.startswith("image/") or len(image) > 15_000_000:
        raise HTTPException(400, "Upload one image under 15MB")
    with sentry_sdk.start_transaction(op="ai", name="react_to_photo"):
        session["reply"], session["subject"] = ai.react_to_photo(session["challenge"], image)
        session["state"] = "responded"
        db.save(session)
    return {"reply": session["reply"], "closing": ENOUGH}


@app.post("/api/{session_id}/end")
def end(session_id: str):
    session = get_open_session(session_id, "responded")
    session["state"] = "ended"
    db.save(session)
    return {"message": ENOUGH}


@app.get("/api/{session_id}/info")
def info(session_id: str):
    session = db.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return extras.lookup(session["subject"])


@app.get("/")
def home():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")
