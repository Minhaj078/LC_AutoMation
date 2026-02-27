# LC Auto — LeetCode Automated Solver

## Quick Setup

### 1. Install dependencies
```bash
pip install fastapi uvicorn selenium undetected-chromedriver openai requests
```

### 2. Set environment variables
```bash
export OPENAI_API_KEY="sk-your-key-here"
export LEETCODE_EMAIL="your@email.com"
export LEETCODE_PASSWORD="yourpassword"
export CHROME_PROFILE_PATH="./chrome_profile"   # persists login session
```
Or edit the constants directly in `main.py`.

### 3. Run the server
```bash
uvicorn main:app --reload --port 8000
```

### 4. Open the UI
Open `index.html` in your browser **or** visit `http://localhost:8000` (FastAPI serves it automatically).

---

## How it works

```
User enters #  →  FastAPI  →  LeetCode GraphQL (fetch problem)
                           →  OpenAI GPT-4o (generate solution)
                           →  Selenium Chrome (inject + submit)
                           →  SQLite (log result)
                           →  JSON response  →  Frontend UI
```

## System Modules

| Module | File / Component |
|--------|-----------------|
| 1. Navigation & Automation | `auto_submit()` in main.py |
| 2. Problem Extraction | `get_problem_details()` + GraphQL |
| 3. GPT Integration | `generate_solution()` — GPT-4o |
| 4. Solution Formatting | regex strip + snippet injection |
| 5. Auto-Submission | Selenium Monaco editor injection |
| 6. Analytics & Logging | SQLite + `/api/history` + `/api/stats` |

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/solve` | Full pipeline: fetch → generate → submit |
| GET | `/api/history` | Past 50 submissions |
| GET | `/api/stats` | Total / accepted / success rate |

## Notes
- **Chrome Profile**: On first run, log into LeetCode manually in the Selenium browser window. The profile is saved to `./chrome_profile/`, so future runs stay logged in without re-authentication.
- **GPT-4o key**: Get one from https://platform.openai.com/api-keys
- The frontend polls the single `/api/solve` endpoint and shows live step animation while it processes.
