import os
import sys
import subprocess
import re
import time
import json
import concurrent.futures
import uuid
import shutil
import logging
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
import gradio as gr
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- External Tools Setup ---
def setup_external():
    # Clone TinyTroupe
    if not os.path.exists("external/TinyTroupe"):
        logger.info("Cloning TinyTroupe...")
        os.makedirs("external", exist_ok=True)
        subprocess.run([
            "git", "clone", "-b", "fix/jules-final-submission-branch",
            "https://github.com/JsonLord/TinyTroupe.git", "external/TinyTroupe"
        ])

    # Clone mkslides
    if not os.path.exists("external/mkslides"):
        logger.info("Cloning mkslides...")
        subprocess.run([
            "git", "clone", "--recursive",
            "https://github.com/MartenBE/mkslides.git", "external/mkslides"
        ])
        pyproject_path = "external/mkslides/pyproject.toml"
        if os.path.exists(pyproject_path):
            with open(pyproject_path, "r") as f: content = f.read()
            content = content.replace('requires-python = ">=3.13"', 'requires-python = ">=3.12"')
            with open(pyproject_path, "w") as f: f.write(content)
        subprocess.run(["pip", "install", "./external/mkslides"])

setup_external()

# Add external/TinyTroupe to sys.path
TINYTROUPE_PATH = os.path.join(os.getcwd(), "external", "TinyTroupe")
sys.path.append(TINYTROUPE_PATH)

# Configuration from environment variables
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_API_TOKEN") or os.environ.get("GITHUB_API_KEY")
JULES_API_KEY = os.environ.get("JULES_API_KEY")
BLABLADOR_API_KEY = os.environ.get("BLABLADOR_API_KEY")
BLABLADOR_BASE_URL = "https://api.helmholtz-blablador.fz-juelich.de/v1"
JULES_API_URL = "https://jules.googleapis.com/v1alpha"

from github import Github, Auth
from openai import OpenAI

# Initialize GitHub client
gh = None
if GITHUB_TOKEN:
    try:
        gh = Github(auth=Auth.Token(GITHUB_TOKEN))
    except Exception as e:
        logger.error(f"Failed to initialize GitHub client: {e}")

REPO_NAME = "JsonLord/tiny_web"

# --- Backend Logic ---

def get_repo_branches(repo_full_name):
    if not gh: return ["main"]
    try:
        repo = gh.get_repo(repo_full_name)
        branches = list(repo.get_branches())
        def fetch_date(b):
            try: return (b.name, repo.get_commit(b.commit.sha).commit.author.date)
            except: return (b.name, datetime.min)
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
            info = list(ex.map(fetch_date, branches))
        info.sort(key=lambda x: x[1], reverse=True)
        return [b[0] for b in info]
    except: return ["main"]

def generate_personas(theme, customer_profile, num_personas):
    final_personas = []
    for i in range(int(num_personas)):
        final_personas.append({
            "name": f"User_{uuid.uuid4().hex[:4]}",
            "minibio": f"Persona interested in {theme}",
            "persona": {"occupation": theme, "profile": customer_profile}
        })
    return final_personas

def generate_tasks(theme, customer_profile):
    return [f"Task {i+1} on {theme}" for i in range(10)]

def initiate_jules_session(persona, tasks, url, report_id):
    if not JULES_API_KEY: return {"error": "No API Key"}
    template_path = "jules_template.md"
    if not os.path.exists(template_path): return {"error": "Template missing"}

    with open(template_path, "r") as f: template = f.read()
    prompt = template.replace("{{persona_context}}", json.dumps(persona))
    prompt = prompt.replace("{{tasks_list}}", json.dumps(tasks))
    prompt = prompt.replace("{{url}}", url)
    prompt = prompt.replace("{{report_id}}", report_id)
    prompt = prompt.replace("{{blablador_api_key}}", BLABLADOR_API_KEY or "")

    headers = {"X-Goog-Api-Key": JULES_API_KEY, "Content-Type": "application/json"}
    data = {
        "prompt": prompt,
        "sourceContext": {"source": f"sources/github/{REPO_NAME}", "githubRepoContext": {"startingBranch": "main"}},
        "automationMode": "AUTO_CREATE_PR",
        "title": f"AUX ANALYSIS [{report_id}]"
    }
    return requests.post(f"{JULES_API_URL}/sessions", headers=headers, json=data).json()

def get_reports_in_branch(repo_name, branch, filter_type=None):
    if not gh: return []
    try:
        repo = gh.get_repo(repo_name)
        tree = repo.get_git_tree(branch, recursive=True).tree
        files = [e.path for e in tree if e.type == "blob" and e.path.endswith(".md")]
        if filter_type == "report": files = [f for f in files if "slide" not in f.lower()]
        elif filter_type == "slides": files = [f for f in files if "slide" in f.lower()]
        return files
    except: return []

def render_slides_html(repo_name, branch, path):
    try:
        repo = gh.get_repo(repo_name)
        content = repo.get_contents(path, ref=branch).decoded_content.decode("utf-8")
        uid = str(uuid.uuid4())[:8]
        work_dir, out_dir = f"work_{uid}", f"site_{uid}"
        os.makedirs(work_dir, exist_ok=True)
        with open(f"{work_dir}/index.md", "w") as f: f.write(content)
        subprocess.run(["mkslides", "build", work_dir, "--site-dir", out_dir])
        if os.path.exists(f"{out_dir}/index.html"):
            return f'<iframe src="/file={os.path.abspath(out_dir)}/index.html" width="100%" height="600px"></iframe>'
        return "Rendering failed."
    except Exception as e: return str(e)

def test_github_connection():
    global gh
    # Re-initialize in case token was added later or failed initially
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_API_TOKEN") or os.environ.get("GITHUB_API_KEY")
    if token:
        try:
            gh = Github(auth=Auth.Token(token))
            user = gh.get_user().login
            return f"✅ Connected as: {user}"
        except Exception as e:
            return f"❌ Connection failed: {str(e)}"
    return "❌ No GitHub Token found (tried GITHUB_TOKEN, GITHUB_API_TOKEN, GITHUB_API_KEY)."

# --- API Endpoints ---
api_app = FastAPI()

class AnalysisRequest(BaseModel):
    theme: str
    profile: str
    num_personas: int = 1
    url: str

@api_app.get("/health")
def health():
    return {"status": "running", "timestamp": datetime.now().isoformat()}

@api_app.post("/api/start_analysis")
def start_analysis_api(req: AnalysisRequest):
    report_id = str(uuid.uuid4())[:8]
    tasks = generate_tasks(req.theme, req.profile)
    personas = generate_personas(req.theme, req.profile, req.num_personas)
    session = initiate_jules_session(personas[0], tasks, req.url, report_id)
    return {"report_id": report_id, "session": session}

@api_app.get("/api/results/{report_id}")
def get_results_api(report_id: str):
    branches = get_repo_branches(REPO_NAME)
    for b in branches[:30]:
        reports = get_reports_in_branch(REPO_NAME, b, filter_type="report")
        for r in reports:
            if report_id in r:
                content = gh.get_repo(REPO_NAME).get_contents(r, ref=b).decoded_content.decode("utf-8")
                slides = get_reports_in_branch(REPO_NAME, b, filter_type="slides")
                slides_html = render_slides_html(REPO_NAME, b, slides[0]) if slides else "No slides found"
                return {"status": "ready", "report_md": content, "slides_html": slides_html}
    return {"status": "pending"}

# --- Gradio Interface ---
with gr.Blocks(title="AUX ANALYSIS BACKEND") as demo:
    gr.Markdown("# AUX ANALYSIS BACKEND")
    gr.Markdown("This space orchestrates AI-driven UX audits. API endpoints are available at `/api/...`")

    with gr.Row():
        status_json = gr.JSON(label="System Status", value={"api": "online", "github": "init..."})
        test_gh_btn = gr.Button("Test GitHub Connection")

    gh_output = gr.Markdown()

    test_gh_btn.click(test_github_connection, outputs=[gh_output])

    # Auto-run test on load
    demo.load(test_github_connection, outputs=[gh_output])

app = gr.mount_gradio_app(api_app, demo, path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
