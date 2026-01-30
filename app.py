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
import gradio as gr
import requests
from github import Github, Auth

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
JULES_API_KEY = os.environ.get("JULES_API_KEY")
BLABLADOR_API_KEY = os.environ.get("BLABLADOR_API_KEY")
JULES_API_URL = "https://jules.googleapis.com/v1alpha"
REPO_NAME = "JsonLord/tiny_web"

gh_client = None
def init_gh():
    global gh_client
    if GITHUB_TOKEN:
        try:
            gh_client = Github(auth=Auth.Token(GITHUB_TOKEN))
            return True
        except: return False
    return False

MKSLIDES_READY = False
def setup_mkslides():
    global MKSLIDES_READY
    if MKSLIDES_READY: return
    try:
        if not os.path.exists("external/mkslides"):
            os.makedirs("external", exist_ok=True)
            subprocess.run(["git", "clone", "--recursive", "https://github.com/MartenBE/mkslides.git", "external/mkslides"], check=True)
            pyproject = "external/mkslides/pyproject.toml"
            if os.path.exists(pyproject):
                with open(pyproject, "r") as f: content = f.read()
                content = re.sub(r'requires-python = ">=3.13"', 'requires-python = ">=3.10"', content)
                with open(pyproject, "w") as f: f.write(content)
            subprocess.run([sys.executable, "-m", "pip", "install", "./external/mkslides"], check=True)
        MKSLIDES_READY = True
    except Exception as e:
        print(f"mkslides setup error: {e}")

def api_get_branches():
    if not gh_client: init_gh()
    try:
        repo = gh_client.get_repo(REPO_NAME)
        return [b.name for b in repo.get_branches()]
    except:
        return ["main"]

def api_start_analysis(theme, profile, num, url):
    if not JULES_API_KEY: return {"error": "No API Key"}
    report_id = str(uuid.uuid4())[:8]
    try:
        with open("jules_template.md", "r") as f: template = f.read()
        persona = {"name": "Auditor", "minibio": f"Expert for {theme}", "persona": {"profile": profile}}
        tasks = [f"Audit {theme} at {url}"]
        prompt = template.replace("{{persona_context}}", json.dumps(persona)).replace("{{tasks_list}}", json.dumps(tasks)).replace("{{url}}", url).replace("{{report_id}}", report_id).replace("{{blablador_api_key}}", BLABLADOR_API_KEY or "")

        headers = {"X-Goog-Api-Key": JULES_API_KEY, "Content-Type": "application/json"}
        data = {
            "prompt": prompt,
            "sourceContext": {"source": f"sources/github/{REPO_NAME}", "githubRepoContext": {"startingBranch": "main"}},
            "automationMode": "AUTO_CREATE_PR",
            "title": f"AUX ANALYSIS [{report_id}]"
        }
        resp = requests.post(f"{JULES_API_URL}/sessions", headers=headers, json=data)
        return {"report_id": report_id, "session": resp.json()}
    except Exception as e:
        return {"error": str(e)}

def api_get_results(report_id, branch_manual):
    if not gh_client: init_gh()
    setup_mkslides()
    work_dir = None
    out_dir = None
    try:
        repo = gh_client.get_repo(REPO_NAME)
        branches = [branch_manual] if branch_manual and branch_manual != "Auto-detect" else api_get_branches()[:10]
        for b in branches:
            try:
                tree = repo.get_git_tree(b, recursive=True).tree
                reports = [e.path for e in tree if report_id in e.path and e.path.endswith(".md") and "slides/" not in e.path]
                if reports:
                    content = repo.get_contents(reports[0], ref=b).decoded_content.decode("utf-8")

                    # Slides
                    slide_files = sorted([e.path for e in tree if e.path.startswith("user_experience_reports/slides/") and e.path.endswith(".md")])
                    slides_html = ""
                    if slide_files:
                        uid = str(uuid.uuid4())[:8]
                        work_dir, out_dir = f"work_{uid}", f"site_{uid}"
                        os.makedirs(work_dir, exist_ok=True)
                        for sf in slide_files:
                            sc = repo.get_contents(sf, ref=b).decoded_content.decode("utf-8")
                            with open(os.path.join(work_dir, os.path.basename(sf)), "w") as f: f.write(sc)

                        subprocess.run([sys.executable, "-m", "mkslides", "build", work_dir, "--site-dir", out_dir], check=False)
                        if os.path.exists(f"{out_dir}/index.html"):
                            with open(f"{out_dir}/index.html", "r") as f: slides_html = f.read()

                    return {"status": "ready", "branch": b, "report_md": content, "slides_html": slides_html}
            except: continue
        return {"status": "pending"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if work_dir and os.path.exists(work_dir): shutil.rmtree(work_dir)
        if out_dir and os.path.exists(out_dir): shutil.rmtree(out_dir)

with gr.Blocks() as demo:
    gr.Markdown("# AUX ANALYSIS BACKEND")

    with gr.Row():
        b_btn = gr.Button("Get Branches")
        b_out = gr.JSON()
        b_btn.click(api_get_branches, outputs=b_out, api_name="get_branches")

    with gr.Row():
        t1 = gr.Textbox(label="Theme")
        t2 = gr.Textbox(label="Profile")
        n1 = gr.Number(label="Personas")
        t3 = gr.Textbox(label="URL")
        s_btn = gr.Button("Start Analysis")
        s_out = gr.JSON()
        s_btn.click(api_start_analysis, inputs=[t1, t2, n1, t3], outputs=s_out, api_name="start_analysis")

    with gr.Row():
        r1 = gr.Textbox(label="Report ID")
        r2 = gr.Textbox(label="Branch")
        r_btn = gr.Button("Get Results")
        r_out = gr.JSON()
        r_btn.click(api_get_results, inputs=[r1, r2], outputs=r_out, api_name="get_results")

init_gh()
demo.launch()
