# """
# LeetCode Automated Solver & Submitter
# FastAPI Backend — main.py
# Run:
# uvicorn main:app --reload --port 8000 --log-level debug
# """

# from dotenv import load_dotenv
# load_dotenv()

# import os, re, time, logging
# from datetime import datetime
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import FileResponse
# from pydantic import BaseModel
# import sqlite3
# import requests

# # ─── Optional imports ──────────────────────────────────────────────
# try:
#     import undetected_chromedriver as uc
#     from selenium.webdriver.common.by import By
#     from selenium.webdriver.support.ui import WebDriverWait
#     from selenium.webdriver.support import expected_conditions as EC
#     SELENIUM_AVAILABLE = True
# except ImportError:
#     SELENIUM_AVAILABLE = False

# try:
#     from openai import OpenAI
#     OPENAI_AVAILABLE = True
# except ImportError:
#     OPENAI_AVAILABLE = False

# # ─── Environment Config ────────────────────────────────────────────
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# LEETCODE_EMAIL = os.getenv("LEETCODE_EMAIL")
# LEETCODE_PASSWORD = os.getenv("LEETCODE_PASSWORD")
# CHROME_PROFILE_PATH = os.getenv("CHROME_PROFILE_PATH")

# # ─── Logging Setup ──────────────────────────────────────────────────
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
# logger = logging.getLogger(__name__)

# # ─── FastAPI Setup ──────────────────────────────────────────────────
# app = FastAPI(title="LeetCode Automator", version="2.0.0")
# app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# # ─── Database Setup ─────────────────────────────────────────────────
# def init_db():
#     conn = sqlite3.connect("results.db")
#     conn.execute("""
#         CREATE TABLE IF NOT EXISTS submissions (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             problem_number TEXT,
#             problem_title TEXT,
#             problem_slug TEXT,
#             solution TEXT,
#             status TEXT,
#             runtime TEXT,
#             memory TEXT,
#             timestamp TEXT
#         )
#     """)
#     conn.commit()
#     conn.close()

# init_db()

# def save_result(data: dict):
#     conn = sqlite3.connect("results.db")
#     conn.execute("""
#         INSERT INTO submissions (problem_number, problem_title, problem_slug,
#             solution, status, runtime, memory, timestamp)
#         VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#     """, (
#         data.get("problem_number"),
#         data.get("title"),
#         data.get("slug"),
#         data.get("solution"),
#         data.get("status"),
#         data.get("runtime"),
#         data.get("memory"),
#         datetime.now().isoformat()
#     ))
#     conn.commit()
#     conn.close()

# # ─── LeetCode API ───────────────────────────────────────────────────
# def get_problem_slug(problem_number: int) -> dict:
#     url = "https://leetcode.com/graphql"
#     query = """
#     query questionData($titleSlug: String!) {
#       question(titleSlug: $titleSlug) {
#         questionFrontendId
#         title
#         titleSlug
#         difficulty
#         isPaidOnly
#       }
#     }
#     """

#     # First get slug list via public API
#     list_url = "https://leetcode.com/api/problems/all/"
#     try:
#         resp = requests.get(list_url, timeout=10)
#         data = resp.json()

#         for item in data.get("stat_status_pairs", []):
#             if str(item["stat"]["frontend_question_id"]) == str(problem_number):
#                 slug = item["stat"]["question__title_slug"]
#                 title = item["stat"]["question__title"]
#                 difficulty = ["Easy", "Medium", "Hard"][item["difficulty"]["level"] - 1]
#                 return {
#                     "slug": slug,
#                     "title": title,
#                     "difficulty": difficulty,
#                     "paid_only": item.get("paid_only", False)
#                 }

#         return None

#     except Exception as e:
#         logger.error(f"Slug fetch error: {e}")
#         return None

# # ─── GPT Solution Generator ─────────────────────────────────────────
# def generate_solution(problem_number: int, title: str, description: str, snippet: str) -> str:
#     if not OPENAI_AVAILABLE:
#         return snippet + "\n        pass"

#     logger.info("Generating solution using GPT...")

#     client = OpenAI(api_key=OPENAI_API_KEY)

#     prompt = f"""Solve LeetCode Problem #{problem_number}: {title}

# Description:
# {description}

# Template:
# {snippet}

# Return ONLY valid Python code.
# """

#     try:
#         response = client.chat.completions.create(
#             model="gpt-4o",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.1,
#             max_tokens=1500
#         )
#         code = response.choices[0].message.content.strip()
#         code = re.sub(r"```.*?\n", "", code)
#         code = code.replace("```", "")
#         return code.strip()
#     except Exception as e:
#         logger.error(f"GPT Error: {e}")
#         return snippet + "\n        pass"

# # ─── Selenium Submitter (DEBUG MODE) ───────────────────────────────
# def auto_submit(slug: str, solution: str) -> dict:
#     if not SELENIUM_AVAILABLE:
#         return {"status": "SELENIUM_NOT_INSTALLED"}

#     if not CHROME_PROFILE_PATH:
#         logger.warning("No CHROME_PROFILE_PATH set in .env")

#     options = uc.ChromeOptions()
#     if CHROME_PROFILE_PATH:
#         options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")

#     options.add_argument("--no-sandbox")

#     driver = uc.Chrome(options=options)
#     logger.info("Chrome launched successfully")

#     result = {"status": "UNKNOWN", "runtime": "N/A", "memory": "N/A"}

#     try:
#         url = f"https://leetcode.com/problems/{slug}/"
#         logger.info(f"Opening problem page: {url}")
#         driver.get(url)
#         time.sleep(4)

#         logger.info(f"Current URL: {driver.current_url}")
#         logger.info(f"Page Title: {driver.title}")

#         # Wait for Monaco editor
#         WebDriverWait(driver, 20).until(
#             EC.presence_of_element_located((By.CLASS_NAME, "monaco-editor"))
#         )
#         logger.info("Monaco editor detected")

#         logger.info(f"Injecting solution (length={len(solution)})")
#         driver.execute_script("""
#             var editor = monaco.editor.getModels()[0];
#             editor.setValue(arguments[0]);
#         """, solution)

#         time.sleep(2)

#         submit_btn = WebDriverWait(driver, 15).until(
#             EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Submit')]"))
#         )
#         submit_btn.click()

#         logger.info("Submit button clicked. Waiting for verdict...")

#         # 🔥 POLLING VERDICT (Stable Method)
#         timeout = 60
#         start = time.time()

#         while time.time() - start < timeout:
#             page = driver.page_source

#             if "Accepted" in page:
#                 result["status"] = "Accepted"
#                 break
#             elif "Wrong Answer" in page:
#                 result["status"] = "Wrong Answer"
#                 break
#             elif "Time Limit Exceeded" in page:
#                 result["status"] = "Time Limit Exceeded"
#                 break

#             logger.info("Polling for verdict...")
#             time.sleep(3)
#         else:
#             logger.error("Verdict timeout after 60s")
#             result["status"] = "VERDICT_TIMEOUT"

#     except Exception as e:
#         logger.error(f"Selenium error: {e}")
#         result["status"] = f"ERROR: {str(e)}"

#     finally:
#         logger.info("Browser kept open for debugging")
#         # driver.quit()   # Keep disabled for debugging

#     return result

# # ─── API ────────────────────────────────────────────────────────────
# class SolveRequest(BaseModel):
#     problem_number: int

# @app.post("/api/solve")
# async def solve_problem(req: SolveRequest):
#     n = req.problem_number

#     meta = get_problem_slug(n)
#     if not meta:
#         raise HTTPException(404, "Problem not found")

#     solution = generate_solution(n, meta["title"], "Auto-fetched description", "")

#     submission = auto_submit(meta["slug"], solution)

#     record = {
#         "problem_number": str(n),
#         "title": meta["title"],
#         "slug": meta["slug"],
#         "solution": solution,
#         **submission
#     }
#     save_result(record)

#     return {
#     "problem_number": n,
#     "title": meta["title"],
#     "difficulty": meta["difficulty"],
#     "submission_status": submission["status"],
#     "runtime": submission.get("runtime", "N/A"),
#     "memory": submission.get("memory", "N/A"),
#     "leetcode_url": f"https://leetcode.com/problems/{meta['slug']}/"
# }

# @app.get("/")
# async def root():
#     return FileResponse("index.html")

# @app.get("/api/history")
# async def get_history():
#     conn = sqlite3.connect("results.db")
#     conn.row_factory = sqlite3.Row
#     rows = conn.execute("SELECT * FROM submissions ORDER BY id DESC LIMIT 50").fetchall()
#     conn.close()
#     return [dict(r) for r in rows]

# @app.get("/api/stats")
# async def get_stats():
#     conn = sqlite3.connect("results.db")
#     total = conn.execute("SELECT COUNT(*) FROM submissions").fetchone()[0]
#     accepted = conn.execute("SELECT COUNT(*) FROM submissions WHERE status='Accepted'").fetchone()[0]
#     conn.close()
#     return {
#         "total": total,
#         "accepted": accepted,
#         "success_rate": f"{(accepted/total*100):.1f}%" if total else "0%"
#     }



# """
# LeetCode Automated Solver & Submitter
# Stable Version - Selenium Fixed
# """

# from dotenv import load_dotenv
# load_dotenv()

# import os
# import re
# import time
# import logging
# import sqlite3
# import requests
# from datetime import datetime

# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import FileResponse
# from pydantic import BaseModel

# # ─────────────────────────────────────────────────────────────
# # SAFE IMPORTS
# # ─────────────────────────────────────────────────────────────

# try:
#     from selenium import webdriver
#     from selenium.webdriver.common.by import By
#     from selenium.webdriver.support.ui import WebDriverWait
#     from selenium.webdriver.support import expected_conditions as EC
#     from selenium.webdriver.chrome.service import Service
#     SELENIUM_AVAILABLE = True
# except Exception as e:
#     print("Selenium import error:", e)
#     SELENIUM_AVAILABLE = False

# try:
#     from openai import OpenAI
#     OPENAI_AVAILABLE = True
# except:
#     OPENAI_AVAILABLE = False

# # ─────────────────────────────────────────────────────────────
# # ENV CONFIG
# # ─────────────────────────────────────────────────────────────

# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# LEETCODE_EMAIL = os.getenv("LEETCODE_EMAIL")
# LEETCODE_PASSWORD = os.getenv("LEETCODE_PASSWORD")
# CHROME_PROFILE_PATH = os.getenv("CHROME_PROFILE_PATH")

# # ─────────────────────────────────────────────────────────────
# # LOGGING
# # ─────────────────────────────────────────────────────────────

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # ─────────────────────────────────────────────────────────────
# # FASTAPI
# # ─────────────────────────────────────────────────────────────

# app = FastAPI(title="LC Auto Stable", version="3.0")
# app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# # ─────────────────────────────────────────────────────────────
# # DATABASE
# # ─────────────────────────────────────────────────────────────

# def init_db():
#     conn = sqlite3.connect("results.db")
#     conn.execute("""
#         CREATE TABLE IF NOT EXISTS submissions (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             problem_number TEXT,
#             problem_title TEXT,
#             problem_slug TEXT,
#             solution TEXT,
#             status TEXT,
#             runtime TEXT,
#             memory TEXT,
#             timestamp TEXT
#         )
#     """)
#     conn.commit()
#     conn.close()

# init_db()

# def save_result(data: dict):
#     conn = sqlite3.connect("results.db")
#     conn.execute("""
#         INSERT INTO submissions
#         (problem_number, problem_title, problem_slug,
#          solution, status, runtime, memory, timestamp)
#         VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#     """, (
#         data.get("problem_number"),
#         data.get("title"),
#         data.get("slug"),
#         data.get("solution"),
#         data.get("status"),
#         data.get("runtime"),
#         data.get("memory"),
#         datetime.now().isoformat()
#     ))
#     conn.commit()
#     conn.close()

# # ─────────────────────────────────────────────────────────────
# # GET PROBLEM META
# # ─────────────────────────────────────────────────────────────

# def get_problem_slug(problem_number: int):
#     try:
#         resp = requests.get("https://leetcode.com/api/problems/all/", timeout=10)
#         data = resp.json()

#         for item in data["stat_status_pairs"]:
#             if str(item["stat"]["frontend_question_id"]) == str(problem_number):
#                 return {
#                     "slug": item["stat"]["question__title_slug"],
#                     "title": item["stat"]["question__title"],
#                     "difficulty": ["Easy", "Medium", "Hard"][item["difficulty"]["level"] - 1],
#                     "paid_only": item.get("paid_only", False)
#                 }
#     except Exception as e:
#         logger.error("Slug fetch error:", e)

#     return None

# # ─────────────────────────────────────────────────────────────
# # GPT GENERATOR (SAFE MODE)
# # ─────────────────────────────────────────────────────────────

# def generate_solution(problem_number, title):
#     if not OPENAI_AVAILABLE or not OPENAI_API_KEY:
#         logger.warning("GPT disabled — returning dummy solution")
#         return "class Solution:\n    def solve(self):\n        pass"

#     client = OpenAI(api_key=OPENAI_API_KEY)

#     try:
#         response = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[{
#                 "role": "user",
#                 "content": f"Solve LeetCode Problem #{problem_number}: {title}. Return only Python code."
#             }],
#             temperature=0.1
#         )
#         code = response.choices[0].message.content.strip()
#         code = re.sub(r"```.*?\n", "", code)
#         return code.replace("```", "").strip()

#     except Exception as e:
#         logger.error("GPT error:", e)
#         return "class Solution:\n    def solve(self):\n        pass"

# # ─────────────────────────────────────────────────────────────
# # SELENIUM SUBMITTER (STABLE)
# # ─────────────────────────────────────────────────────────────

# def auto_submit(slug, solution):
#     if not SELENIUM_AVAILABLE:
#         return {"status": "SELENIUM_IMPORT_FAILED"}

#     options = webdriver.ChromeOptions()

#     if CHROME_PROFILE_PATH:
#         options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")

#     options.add_argument("--start-maximized")

#     driver = webdriver.Chrome(options=options)
#     result = {"status": "UNKNOWN", "runtime": "N/A", "memory": "N/A"}

#     try:
#         url = f"https://leetcode.com/problems/{slug}/"
#         driver.get(url)
#         logger.info("Opened problem page")

#         # wait for editor
#         WebDriverWait(driver, 30).until(
#             EC.presence_of_element_located((By.CLASS_NAME, "monaco-editor"))
#         )

#         logger.info("Editor detected")

#         driver.execute_script("""
#             var editor = monaco.editor.getModels()[0];
#             editor.setValue(arguments[0]);
#         """, solution)

#         time.sleep(2)

#         submit_btn = WebDriverWait(driver, 20).until(
#             EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Submit')]"))
#         )

#         submit_btn.click()
#         logger.info("Submit clicked")

#         # verdict polling
#         start = time.time()
#         while time.time() - start < 60:
#             page = driver.page_source

#             if "Accepted" in page:
#                 result["status"] = "Accepted"
#                 break
#             elif "Wrong Answer" in page:
#                 result["status"] = "Wrong Answer"
#                 break
#             elif "Time Limit Exceeded" in page:
#                 result["status"] = "Time Limit Exceeded"
#                 break

#             time.sleep(3)
#         else:
#             result["status"] = "VERDICT_TIMEOUT"

#     except Exception as e:
#         logger.error("Selenium error:", e)
#         result["status"] = f"ERROR: {str(e)}"

#     finally:
#         # comment this if you want browser to stay open
#         driver.quit()

#     return result

# # ─────────────────────────────────────────────────────────────
# # API
# # ─────────────────────────────────────────────────────────────

# class SolveRequest(BaseModel):
#     problem_number: int

# @app.post("/api/solve")
# async def solve_problem(req: SolveRequest):
#     n = req.problem_number

#     meta = get_problem_slug(n)
#     if not meta:
#         raise HTTPException(404, "Problem not found")

#     solution = generate_solution(n, meta["title"])
#     submission = auto_submit(meta["slug"], solution)

#     record = {
#         "problem_number": str(n),
#         "title": meta["title"],
#         "slug": meta["slug"],
#         "solution": solution,
#         **submission
#     }
#     save_result(record)

#     return {
#         "problem_number": n,
#         "title": meta["title"],
#         "difficulty": meta["difficulty"],
#         "submission_status": submission["status"],
#         "runtime": submission.get("runtime", "N/A"),
#         "memory": submission.get("memory", "N/A"),
#         "leetcode_url": f"https://leetcode.com/problems/{meta['slug']}/"
#     }

# @app.get("/")
# async def root():
#     return FileResponse("index.html")

# @app.get("/api/history")
# async def get_history():
#     conn = sqlite3.connect("results.db")
#     conn.row_factory = sqlite3.Row
#     rows = conn.execute("SELECT * FROM submissions ORDER BY id DESC LIMIT 50").fetchall()
#     conn.close()
#     return [dict(r) for r in rows]

# @app.get("/api/stats")
# async def get_stats():
#     conn = sqlite3.connect("results.db")
#     total = conn.execute("SELECT COUNT(*) FROM submissions").fetchone()[0]
#     accepted = conn.execute("SELECT COUNT(*) FROM submissions WHERE status='Accepted'").fetchone()[0]
#     conn.close()

#     return {
#         "total": total,
#         "accepted": accepted,
#         "success_rate": f"{(accepted/total*100):.1f}%" if total else "0%"
#     }

"""
LeetCode Automated Solver & Submitter
Production Stable Version
"""

from dotenv import load_dotenv
load_dotenv()

import os
import re
import time
import logging
import sqlite3
import requests
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# ─────────────────────────────────────────────
# SAFE IMPORTS
# ─────────────────────────────────────────────

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except Exception as e:
    print("Selenium import error:", e)
    SELENIUM_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except:
    OPENAI_AVAILABLE = False

# ─────────────────────────────────────────────
# ENV CONFIG
# ─────────────────────────────────────────────

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROME_PROFILE_PATH = os.getenv("CHROME_PROFILE_PATH")
CHROME_PROFILE_DIR = os.getenv("CHROME_PROFILE_DIR")  # optional (Profile 1, Profile 2)

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# FASTAPI
# ─────────────────────────────────────────────

app = FastAPI(title="LC Auto Stable", version="4.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ─────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect("results.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_number TEXT,
            problem_title TEXT,
            problem_slug TEXT,
            solution TEXT,
            status TEXT,
            runtime TEXT,
            memory TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def save_result(data: dict):
    conn = sqlite3.connect("results.db")
    conn.execute("""
        INSERT INTO submissions
        (problem_number, problem_title, problem_slug,
         solution, status, runtime, memory, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("problem_number"),
        data.get("title"),
        data.get("slug"),
        data.get("solution"),
        data.get("status"),
        data.get("runtime"),
        data.get("memory"),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

# ─────────────────────────────────────────────
# FETCH PROBLEM META
# ─────────────────────────────────────────────

def get_problem_slug(problem_number: int):
    try:
        resp = requests.get("https://leetcode.com/api/problems/all/", timeout=10)
        data = resp.json()

        for item in data["stat_status_pairs"]:
            if str(item["stat"]["frontend_question_id"]) == str(problem_number):
                return {
                    "slug": item["stat"]["question__title_slug"],
                    "title": item["stat"]["question__title"],
                    "difficulty": ["Easy", "Medium", "Hard"][item["difficulty"]["level"] - 1],
                }
    except Exception as e:
        logger.error("Slug fetch error:", e)

    return None

# ─────────────────────────────────────────────
# GPT GENERATOR (SAFE)
# ─────────────────────────────────────────────

def generate_solution(problem_number, title):
    if not OPENAI_AVAILABLE or not OPENAI_API_KEY:
        logger.warning("GPT disabled — returning dummy solution")
        return "class Solution:\n    def solve(self):\n        pass"

    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"Solve LeetCode Problem #{problem_number}: {title}. Return only valid Python code."
            }],
            temperature=0.1
        )

        code = response.choices[0].message.content.strip()
        code = re.sub(r"```.*?\n", "", code)
        return code.replace("```", "").strip()

    except Exception as e:
        logger.error("GPT error:", e)
        return "class Solution:\n    def solve(self):\n        pass"

# ─────────────────────────────────────────────
# SELENIUM SUBMITTER (CRASH SAFE)
# ─────────────────────────────────────────────

def auto_submit(slug, solution):

    if not SELENIUM_AVAILABLE:
        return {"status": "SELENIUM_IMPORT_FAILED"}

    options = webdriver.ChromeOptions()

    # profile support
    if CHROME_PROFILE_PATH:
        options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")

    if CHROME_PROFILE_DIR:
        options.add_argument(f"--profile-directory={CHROME_PROFILE_DIR}")

    options.add_argument("--start-maximized")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        logger.error("Driver launch error:", e)
        return {"status": "CHROMEDRIVER_ERROR"}

    result = {"status": "UNKNOWN", "runtime": "N/A", "memory": "N/A"}

    try:
        url = f"https://leetcode.com/problems/{slug}/"
        driver.get(url)
        logger.info("Opened problem page")

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "monaco-editor"))
        )

        logger.info("Editor detected")

        driver.execute_script("""
            var editor = monaco.editor.getModels()[0];
            editor.setValue(arguments[0]);
        """, solution)

        time.sleep(2)

        submit_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Submit')]"))
        )

        submit_btn.click()
        logger.info("Submit clicked")

        # verdict polling
        start = time.time()
        while time.time() - start < 60:
            page = driver.page_source

            if "Accepted" in page:
                result["status"] = "Accepted"
                break
            elif "Wrong Answer" in page:
                result["status"] = "Wrong Answer"
                break
            elif "Time Limit Exceeded" in page:
                result["status"] = "Time Limit Exceeded"
                break

            time.sleep(3)
        else:
            result["status"] = "VERDICT_TIMEOUT"

    except Exception as e:
        logger.error("Selenium runtime error:", e)
        result["status"] = f"ERROR: {str(e)}"

    finally:
        driver.quit()

    return result

# ─────────────────────────────────────────────
# API
# ─────────────────────────────────────────────

class SolveRequest(BaseModel):
    problem_number: int

@app.post("/api/solve")
async def solve_problem(req: SolveRequest):
    n = req.problem_number

    meta = get_problem_slug(n)
    if not meta:
        raise HTTPException(404, "Problem not found")

    solution = generate_solution(n, meta["title"])
    submission = auto_submit(meta["slug"], solution)

    record = {
        "problem_number": str(n),
        "title": meta["title"],
        "slug": meta["slug"],
        "solution": solution,
        **submission
    }
    save_result(record)

    return {
        "problem_number": n,
        "title": meta["title"],
        "difficulty": meta["difficulty"],
        "submission_status": submission["status"],
        "runtime": submission.get("runtime", "N/A"),
        "memory": submission.get("memory", "N/A"),
        "leetcode_url": f"https://leetcode.com/problems/{meta['slug']}/"
    }

@app.get("/")
async def root():
    return FileResponse("index.html")

@app.get("/api/history")
async def get_history():
    conn = sqlite3.connect("results.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM submissions ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/stats")
async def get_stats():
    conn = sqlite3.connect("results.db")
    total = conn.execute("SELECT COUNT(*) FROM submissions").fetchone()[0]
    accepted = conn.execute("SELECT COUNT(*) FROM submissions WHERE status='Accepted'").fetchone()[0]
    conn.close()

    return {
        "total": total,
        "accepted": accepted,
        "success_rate": f"{(accepted/total*100):.1f}%" if total else "0%"
    }