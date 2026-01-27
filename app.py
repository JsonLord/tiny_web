import os
import sys
import subprocess

# Logic to clone TinyTroupe on startup if not present
def clone_tinytroupe():
    if not os.path.exists("external/TinyTroupe"):
        print("Cloning TinyTroupe...")
        os.makedirs("external", exist_ok=True)
        subprocess.run([
            "git", "clone", "-b", "fix/jules-final-submission-branch",
            "https://github.com/JsonLord/TinyTroupe.git", "external/TinyTroupe"
        ])
    else:
        print("TinyTroupe already present.")

clone_tinytroupe()

import gradio as gr
from github import Github
import requests
from openai import OpenAI
import time
import json
import logging
import re

# Add external/TinyTroupe to sys.path
TINYTROUPE_PATH = os.path.join(os.getcwd(), "external", "TinyTroupe")
sys.path.append(TINYTROUPE_PATH)

# Try to import tinytroupe
try:
    import tinytroupe
    from tinytroupe.agent import TinyPerson
    from tinytroupe.factory.tiny_person_factory import TinyPersonFactory
    print("TinyTroupe imported successfully")
except ImportError as e:
    print(f"Error importing TinyTroupe: {e}")

# Configuration from environment variables
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
JULES_API_KEY = os.environ.get("JULES_API_KEY")
BLABLADOR_API_KEY = os.environ.get("BLABLADOR_API_KEY")
BLABLADOR_BASE_URL = "https://api.helmholtz-blablador.fz-juelich.de/v1"
JULES_API_URL = "https://jules.googleapis.com/v1alpha"

# GitHub Client
gh = Github(GITHUB_TOKEN) if GITHUB_TOKEN else None

# BLABLADOR Client for task generation
def get_blablador_client():
    if not BLABLADOR_API_KEY:
        return None
    return OpenAI(
        api_key=BLABLADOR_API_KEY,
        base_url=BLABLADOR_BASE_URL
    )

def get_user_repos():
    if not gh:
        return ["JsonLord/tiny_web"]
    try:
        user = gh.get_user()
        repos = [repo.full_name for repo in user.get_repos()]
        if "JsonLord/tiny_web" not in repos:
            repos.append("JsonLord/tiny_web")
        return sorted(repos)
    except Exception as e:
        print(f"Error fetching repos: {e}")
        return ["JsonLord/tiny_web"]

def get_repo_branches(repo_full_name):
    if not gh or not repo_full_name:
        return ["main"]
    try:
        repo = gh.get_repo(repo_full_name)
        branches = [branch.name for branch in repo.get_branches()]
        return branches
    except Exception as e:
        print(f"Error fetching branches: {e}")
        return ["main"]

def generate_personas(theme, customer_profile, num_personas):
    context = f"A company related to {theme}. Target customers: {customer_profile}"
    factory = TinyPersonFactory(context=context)
    people = factory.generate_people(number_of_people=int(num_personas), verbose=True)

    personas_data = []
    for person in people:
        personas_data.append({
            "name": person.name,
            "minibio": person.minibio(),
            "persona": person._persona
        })
    return personas_data

def generate_tasks(theme, customer_profile):
    client = get_blablador_client()
    if not client:
        return [f"Task {i+1} for {theme} (BLABLADOR_API_KEY not set)" for i in range(10)]

    prompt = f"""
    Generate 10 sequential tasks for a user to perform on a website related to the theme: {theme}.
    The user profile is: {customer_profile}.

    The tasks should cover:
    1. Communication
    2. Purchase decisions
    3. Custom Search / Information gathering
    4. Emotional connection to the persona and content/styling

    The tasks must be in sequential order.
    Return the tasks as a JSON list of strings.
    """

    response = client.chat.completions.create(
        model="alias-large",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    try:
        content = response.choices[0].message.content
        tasks_json = json.loads(content)
        if "tasks" in tasks_json:
            return tasks_json["tasks"]
        elif isinstance(tasks_json, list):
            return tasks_json
        else:
            return list(tasks_json.values())[0]
    except Exception as e:
        print(f"Error parsing tasks: {e}")
        return [f"Task {i+1} for {theme}" for i in range(10)]

def handle_generate(theme, customer_profile, num_personas):
    try:
        yield "Generating tasks...", None, None
        tasks = generate_tasks(theme, customer_profile)

        yield "Generating personas...", tasks, None
        personas = generate_personas(theme, customer_profile, num_personas)

        yield "Generation complete!", tasks, personas
    except Exception as e:
        yield f"Error during generation: {str(e)}", None, None

def start_and_monitor_sessions(repo_name, branch_name, personas, tasks, url):
    if not JULES_API_KEY:
        yield "Error: JULES_API_KEY not set.", ""
        return

    with open("jules_template.md", "r") as f:
        template = f.read()

    sessions = []
    for persona in personas:
        # Format prompt
        prompt = template.replace("{{persona_context}}", json.dumps(persona))
        prompt = prompt.replace("{{tasks_list}}", json.dumps(tasks))
        prompt = prompt.replace("{{url}}", url)

        # Call Jules API
        headers = {
            "X-Goog-Api-Key": JULES_API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "prompt": prompt,
            "sourceContext": {
                "source": f"sources/github/{repo_name}",
                "githubRepoContext": {
                    "startingBranch": branch_name
                }
            },
            "automationMode": "AUTO_CREATE_PR",
            "title": f"UX Analysis for {persona['name']}"
        }

        response = requests.post(f"{JULES_API_URL}/sessions", headers=headers, json=data)
        if response.status_code == 200:
            sessions.append(response.json())
        else:
            yield f"Error creating session for {persona['name']}: {response.text}", ""
            return

    # Monitoring
    all_reports = ""
    while sessions:
        for i, session in enumerate(sessions):
            session_id = session['id']
            res = requests.get(f"{JULES_API_URL}/sessions/{session_id}", headers=headers)
            if res.status_code == 200:
                current_session = res.json()
                yield f"Monitoring sessions... Status of {current_session.get('title')}: {current_session.get('state', 'UNKNOWN')}", all_reports

                # Check for PR in outputs
                outputs = current_session.get("outputs", [])
                pr_url = None
                for out in outputs:
                    if "pullRequest" in out:
                        pr_url = out["pullRequest"]["url"]
                        break

                if pr_url:
                    yield f"PR created for {current_session.get('title')}: {pr_url}. Pulling report...", all_reports
                    report_content = pull_report_from_pr(pr_url)
                    all_reports += f"\n\n# Report for {current_session.get('title')}\n\n{report_content}"
                    sessions.pop(i)
                    break # Restart loop since we modified the list
            else:
                print(f"Error polling session {session_id}: {res.text}")

        if sessions:
            time.sleep(30) # Poll every 30 seconds

    yield "All sessions complete!", all_reports

def pull_report_from_pr(pr_url):
    if not gh:
        return "Error: GITHUB_TOKEN not set."

    try:
        # Extract repo and PR number from URL
        match = re.search(r"github\.com/([^/]+/[^/]+)/pull/(\d+)", pr_url)
        if not match:
            return "Error: Could not parse PR URL."

        repo_full_name = match.group(1)
        pr_number = int(match.group(2))

        repo = gh.get_repo(repo_full_name)
        pr = repo.get_pull(pr_number)
        branch_name = pr.head.ref

        # Fetch the report.md file
        file_path = "user_experience_reports/report.md"
        file_content = repo.get_contents(file_path, ref=branch_name)
        return file_content.decoded_content.decode("utf-8")

    except Exception as e:
        print(f"Error pulling report: {e}")
        return f"Error pulling report: {str(e)}"

# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("# Jules UX Analysis Orchestrator")

    with gr.Row():
        with gr.Column():
            theme_input = gr.Textbox(label="Theme", placeholder="e.g., Communication, Purchase decisions, Information gathering")
            profile_input = gr.Textbox(label="Customer Profile Description", placeholder="Describe the target customer...")
            num_personas_input = gr.Number(label="Number of Personas", value=1, precision=0)
            url_input = gr.Textbox(label="Target URL", value="https://example.com")

            repo_selector = gr.Dropdown(label="GitHub Repository", choices=get_user_repos(), value="JsonLord/tiny_web")
            branch_selector = gr.Dropdown(label="Branch", choices=["main"], value="main")

            repo_selector.change(fn=get_repo_branches, inputs=repo_selector, outputs=branch_selector)

            generate_btn = gr.Button("Generate Personas & Tasks")

        with gr.Column():
            status_output = gr.Textbox(label="Status", interactive=False)
            task_list_display = gr.JSON(label="Tasks")
            persona_display = gr.JSON(label="Personas")

    with gr.Row():
        start_session_btn = gr.Button("Start Jules Session", variant="primary")

    with gr.Row():
        report_output = gr.Markdown(label="Final Reports")

    # Event handlers
    generate_btn.click(
        fn=handle_generate,
        inputs=[theme_input, profile_input, num_personas_input],
        outputs=[status_output, task_list_display, persona_display]
    )

    start_session_btn.click(
        fn=start_and_monitor_sessions,
        inputs=[repo_selector, branch_selector, persona_display, task_list_display, url_input],
        outputs=[status_output, report_output]
    )

if __name__ == "__main__":
    demo.launch()
