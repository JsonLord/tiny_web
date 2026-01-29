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
from gradio_client import Client
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import uvicorn
import gradio as gr

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Logic to clone TinyTroupe on startup if not present
def clone_tinytroupe():
    if not os.path.exists("external/TinyTroupe"):
        print("Cloning TinyTroupe...")
        os.makedirs("external", exist_ok=True)
        subprocess.run([
            "git", "clone", "-b", "fix/jules-final-submission-branch",
            "https://github.com/JsonLord/TinyTroupe.git", "external/TinyTroupe"
        ])
        patch_tinytroupe()
    else:
        print("TinyTroupe already present.")
        patch_tinytroupe()

def patch_tinytroupe():
    path = "external/TinyTroupe/tinytroupe/openai_utils.py"
    if os.path.exists(path):
        with open(path, "r") as f:
            content = f.read()

        if "import concurrent.futures" not in content:
            content = "import concurrent.futures\n" + content

        parallel_helper = """
    def _raw_model_call_parallel(self, model_names, chat_api_params):
        def make_call(m_name):
            try:
                p = chat_api_params.copy()
                p["model"] = m_name
                if self._is_reasoning_model(m_name):
                    if "max_tokens" in p:
                        p["max_completion_tokens"] = p.pop("max_tokens")
                    p.pop("temperature", None)
                    p.pop("top_p", None)
                    p.pop("frequency_penalty", None)
                    p.pop("presence_penalty", None)
                    p.pop("stream", None)
                return self.client.chat.completions.create(**p)
            except Exception as e:
                return e

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(model_names)) as executor:
            futures = {executor.submit(make_call, m): m for m in model_names}
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if not isinstance(res, Exception):
                    return res
        return Exception("All parallel calls failed")
"""
        if "_raw_model_call_parallel" not in content:
            content = content.replace("class OpenAIClient:", "class OpenAIClient:" + parallel_helper)

        content = content.replace('"alias-fast"', '"alias-large"')
        content = content.replace("i = 0", "parallel_retry = False\n        i = 0")

        old_call = "response = self._raw_model_call(model, chat_api_params)"
        new_call = """if parallel_retry:
                        logger.info("Attempting parallel call to alias-large and alias-huge.")
                        response = self._raw_model_call_parallel(["alias-large", "alias-huge"], chat_api_params)
                        if isinstance(response, Exception):
                            raise response
                    else:
                        response = self._raw_model_call(model, chat_api_params)"""
        content = content.replace(old_call, new_call)

        pattern = r"if isinstance\(e, openai\.APIStatusError\) and e\.status_code == 502 and isinstance\(self, HelmholtzBlabladorClient\):.*?except Exception as fallback_e:.*?logger\.error\(f\"Fallback to OpenAI also failed: \{fallback_e\}\"\)"
        new_502_block = """if isinstance(e, openai.APIStatusError) and e.status_code == 502 and isinstance(self, HelmholtzBlabladorClient):
                    logger.warning("Helmholtz API returned a 502 error. Waiting 35 seconds and enabling parallel retry...")
                    parallel_retry = True
                    time.sleep(35)"""
        content = re.sub(pattern, new_502_block, content, flags=re.DOTALL)

        with open(path, "w") as f:
            f.write(content)

clone_tinytroupe()

def setup_mkslides():
    if not os.path.exists("external/mkslides"):
        os.makedirs("external", exist_ok=True)
        subprocess.run(["git", "clone", "--recursive", "https://github.com/MartenBE/mkslides.git", "external/mkslides"])
        pyproject_path = "external/mkslides/pyproject.toml"
        if os.path.exists(pyproject_path):
            with open(pyproject_path, "r") as f: content = f.read()
            content = content.replace('requires-python = ">=3.13"', 'requires-python = ">=3.12"')
            with open(pyproject_path, "w") as f: f.write(content)
        subprocess.run(["pip", "install", "./external/mkslides"])

setup_mkslides()

from github import Github, Auth
from openai import OpenAI

# Add external/TinyTroupe to sys.path
TINYTROUPE_PATH = os.path.join(os.getcwd(), "external", "TinyTroupe")
sys.path.append(TINYTROUPE_PATH)

try:
    import tinytroupe
    from tinytroupe.agent import TinyPerson
    from tinytroupe.factory.tiny_person_factory import TinyPersonFactory
    from tinytroupe import config_manager
except ImportError:
    pass

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_API_TOKEN")
JULES_API_KEY = os.environ.get("JULES_API_KEY")
BLABLADOR_API_KEY = os.environ.get("BLABLADOR_API_KEY")
BLABLADOR_BASE_URL = "https://api.helmholtz-blablador.fz-juelich.de/v1"
JULES_API_URL = "https://jules.googleapis.com/v1alpha"

gh = Github(auth=Auth.Token(GITHUB_TOKEN)) if GITHUB_TOKEN else None
REPO_NAME = "JsonLord/tiny_web"

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
    with open("jules_template.md", "r") as f: template = f.read()
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

# FastAPI
api_app = FastAPI()

class AnalysisRequest(BaseModel):
    theme: str
    profile: str
    num_personas: int = 1
    url: str

@api_app.get("/health")
def health(): return {"status": "running"}

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
    for b in branches[:20]:
        reports = get_reports_in_branch(REPO_NAME, b, filter_type="report")
        for r in reports:
            if report_id in r:
                content = gh.get_repo(REPO_NAME).get_contents(r, ref=b).decoded_content.decode("utf-8")
                slides = get_reports_in_branch(REPO_NAME, b, filter_type="slides")
                slides_html = render_slides_html(REPO_NAME, b, slides[0]) if slides else "No slides"
                return {"status": "ready", "report_md": content, "slides_html": slides_html}
    return {"status": "pending"}

# Gradio
with gr.Blocks(title="AUX ANALYSIS BACKEND") as demo:
    gr.Markdown("# AUX ANALYSIS BACKEND")
    gr.JSON(value={"status": "online"})

app = gr.mount_gradio_app(api_app, demo, path="/")
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
