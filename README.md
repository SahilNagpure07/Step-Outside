# 🌱 Step Outside
An app that gets you OFF your screen: nudge → challenge → one photo → "Enough. Put your phone away."

## Run it
Create a `.env` file in the project root, next to `main.py`. Add the keys for the integrations you want to use:

```env
GEMINI_API_KEY=your_gemini_api_key
SERPAPI_KEY=your_serpapi_key
MONGODB_URI=your_mongodb_connection_string
SENTRY_DSN=your_sentry_dsn
```
```
pip install -r requirements.txt
uvicorn main:app --reload
```
Open http://localhost:8000

**Reminder time:** pick it on the start screen (in minutes). For a quick demo, enter `0.25` (= 15 seconds).

**Session flow:** `idle → challenged → responded → ended`. After "Enough.", a **Start again** button returns to the start screen.

## Files
| File | What it does |
|---|---|
| `main.py` | Web server + API routes |
| `ai.py` | Gemma: makes challenges, reacts to photos |
| `db.py` | MongoDB Atlas storage |
| `extras.py` | SerpApi info about what you found |
| `static/` | The web page (HTML, CSS, JS) |

## Deploy
Push to GitHub → Render. Add your keys as env vars.