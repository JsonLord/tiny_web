import os
import sys
import subprocess
import re
import time
import json
import concurrent.futures

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

        # 1. Import concurrent.futures and add parallel helper to the class
        if "import concurrent.futures" not in content:
            content = "import concurrent.futures\n" + content

        # Add the parallel helper to OpenAIClient
        parallel_helper = """
    def _raw_model_call_parallel(self, model_names, chat_api_params):
        def make_call(m_name):
            try:
                p = chat_api_params.copy()
                p["model"] = m_name
                # Adjust for reasoning models if needed
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

        # 2. Ensure alias-large is used (revert any previous fast patches)
        content = content.replace('"alias-fast"', '"alias-large"')

        # 3. Handle 502 errors by waiting 35 seconds and setting a parallel retry flag
        # We need to modify the send_message loop

        # Inject parallel_retry = False before the loop
        content = content.replace("i = 0", "parallel_retry = False\n        i = 0")

        # Modify the model call inside the loop
        old_call = "response = self._raw_model_call(model, chat_api_params)"
        new_call = """if parallel_retry:
                        logger.info("Attempting parallel call to alias-large and alias-huge.")
                        response = self._raw_model_call_parallel(["alias-large", "alias-huge"], chat_api_params)
                        if isinstance(response, Exception):
                            raise response
                    else:
                        response = self._raw_model_call(model, chat_api_params)"""
        content = content.replace(old_call, new_call)

        # Update the 502 catch block
        pattern = r"if isinstance\(e, openai\.APIStatusError\) and e\.status_code == 502 and isinstance\(self, HelmholtzBlabladorClient\):.*?except Exception as fallback_e:.*?logger\.error\(f\"Fallback to OpenAI also failed: \{fallback_e\}\"\)"

        new_502_block = """if isinstance(e, openai.APIStatusError) and e.status_code == 502 and isinstance(self, HelmholtzBlabladorClient):
                    logger.warning("Helmholtz API returned a 502 error. Waiting 35 seconds and enabling parallel retry...")
                    parallel_retry = True
                    time.sleep(35)"""

        content = re.sub(pattern, new_502_block, content, flags=re.DOTALL)

        with open(path, "w") as f:
            f.write(content)
        print("TinyTroupe patched to handle 502 errors with 35s wait and parallel retries.")

clone_tinytroupe()

import gradio as gr
from github import Github
import requests
from openai import OpenAI
import logging

# Add external/TinyTroupe to sys.path
TINYTROUPE_PATH = os.path.join(os.getcwd(), "external", "TinyTroupe")
sys.path.append(TINYTROUPE_PATH)

# Try to import tinytroupe
try:
    import tinytroupe
    from tinytroupe.agent import TinyPerson
    from tinytroupe.factory.tiny_person_factory import TinyPersonFactory
    from tinytroupe import config_manager
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
REPO_NAME = "JsonLord/tiny_web"

# Global state for processed reports
processed_prs = set()
all_discovered_reports = ""

# Helper for parallel LLM calls
def call_llm_parallel(client, model_names, messages, **kwargs):
    def make_call(model_name):
        try:
            print(f"Parallel call attempting: {model_name}")
            return client.chat.completions.create(
                model=model_name,
                messages=messages,
                **kwargs
            )
        except Exception as e:
            print(f"Parallel call error from {model_name}: {e}")
            return e

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(model_names)) as executor:
        futures = {executor.submit(make_call, m): m for m in model_names}
        # Wait for the first success that isn't a 502/Proxy Error
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if not isinstance(res, Exception):
                print(f"Parallel call success from: {futures[future]}")
                # Try to cancel others (not always possible but good practice)
                return res
            else:
                # If it's an error, check if we should keep waiting or if all failed
                pass

    return Exception("All parallel calls failed")

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
    # Ensure alias-large is used
    config_manager.update("model", "alias-large")
    config_manager.update("reasoning_model", "alias-large")

    context = f"A company related to {theme}. Target customers: {customer_profile}"

    # Manually define sampling plan if LLM fails to generate one correctly
    try:
        factory = TinyPersonFactory(context=context)
        # Attempt to initialize sampling plan, if it fails or produces 0 samples, we'll manually add one
        try:
            factory.initialize_sampling_plan()
        except:
            pass

        if not factory.remaining_characteristics_sample or any("sampled_values" not in s for s in factory.remaining_characteristics_sample):
            print("Sampling plan generation failed or returned invalid samples. Creating manual sample.")
            factory.remaining_characteristics_sample = [{
                "name": f"User_{i}",
                "age": 25 + i,
                "gender": "unknown",
                "nationality": "unknown",
                "occupation": theme,
                "background": customer_profile
            } for i in range(int(num_personas))]
        else:
            # If it has sampled_values but it's nested (it should be flattened by factory)
            # Actually, the error shows it's a list of dictionaries that might be errors
            pass

        people = factory.generate_people(number_of_people=int(num_personas), verbose=True)
        if not people:
            print("TinyTroupe generated 0 people. Using fallback.")
            raise Exception("No people generated.")
    except Exception as e:
        print(f"Error in generate_personas: {e}")
        # Fallback: create dummy people if everything fails
        personas_data = []
        for i in range(int(num_personas)):
            personas_data.append({
                "name": f"User_{i}",
                "minibio": f"A simulated user interested in {theme}.",
                "persona": {"name": f"User_{i}", "occupation": theme, "background": customer_profile}
            })
        return personas_data

    personas_data = []
    if people:
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
    Return the tasks as a JSON list of strings in the format: {{"tasks": ["task1", "task2", ...]}}
    """

    # Try alias-large first, then alias-fast
    for model_name in ["alias-large", "alias-fast"]:
        try:
            # Handle potential 502 with wait
            response = None
            for attempt in range(3):
                try:
                    print(f"Attempting task generation with {model_name}, attempt {attempt+1}")
                    if attempt > 0:
                        # Parallel retry after first failure
                        print("Proxy error occurred previously. Attempting parallel call to alias-large and alias-huge.")
                        response = call_llm_parallel(client, ["alias-large", "alias-huge"], [{"role": "user", "content": prompt}])
                        if isinstance(response, Exception):
                            raise response
                    else:
                        response = client.chat.completions.create(
                            model=model_name,
                            messages=[{"role": "user", "content": prompt}]
                        )
                    break
                except Exception as e:
                    print(f"Error during task generation with {model_name}: {e}")
                    if "502" in str(e) or "Proxy Error" in str(e):
                        print(f"Waiting 35 seconds before retry...")
                        time.sleep(35)
                    else:
                        # For other errors, don't wait as long but still retry or move on
                        time.sleep(1)

            if not response or isinstance(response, Exception):
                print(f"Failed to get response from {model_name} after all attempts.")
                continue

            content = response.choices[0].message.content
            # Extract JSON from content (it might be wrapped in code blocks)
            json_str = re.search(r"\{.*\}", content, re.DOTALL)
            if json_str:
                tasks_json = json.loads(json_str.group())
                if "tasks" in tasks_json:
                    return tasks_json["tasks"]
                elif isinstance(tasks_json, list):
                    return tasks_json
                else:
                    return list(tasks_json.values())[0]
        except Exception as e:
            print(f"Error with model {model_name}: {e}")
            continue

    return [f"Task {i+1} for {theme} (Failed to generate)" for i in range(10)]

def handle_generate(theme, customer_profile, num_personas):
    try:
        yield "Generating tasks...", None, None
        tasks = generate_tasks(theme, customer_profile)

        yield "Generating personas...", tasks, None
        personas = generate_personas(theme, customer_profile, num_personas)

        yield "Generation complete!", tasks, personas
    except Exception as e:
        yield f"Error during generation: {str(e)}", None, None

def start_and_monitor_sessions(personas, tasks, url):
    repo_name = "JsonLord/tiny_web"
    branch_name = "main"

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
        prompt = prompt.replace("{{blablador_api_key}}", BLABLADOR_API_KEY if BLABLADOR_API_KEY else "YOUR_API_KEY")

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
        try:
            file_content = repo.get_contents(file_path, ref=branch_name)
            content = file_content.decoded_content.decode("utf-8")
            # Mark as processed
            processed_prs.add(pr_number)
            return content
        except:
            return "Report not found yet in this branch."

    except Exception as e:
        print(f"Error pulling report: {e}")
        return f"Error pulling report: {str(e)}"

def monitor_repo_for_reports():
    global all_discovered_reports
    if not gh:
        return all_discovered_reports

    try:
        repo = gh.get_repo(REPO_NAME)
        # List open PRs
        prs = repo.get_pulls(state='open', sort='created', direction='desc')

        new_content_found = False
        for pr in prs:
            if pr.number not in processed_prs:
                # Check if it has the report
                try:
                    file_path = "user_experience_reports/report.md"
                    file_content = repo.get_contents(file_path, ref=pr.head.ref)
                    content = file_content.decoded_content.decode("utf-8")

                    processed_prs.add(pr.number)
                    report_header = f"\n\n## Discovered Report: {pr.title} (PR #{pr.number})\n\n"
                    all_discovered_reports = report_header + content + "\n\n---\n\n" + all_discovered_reports
                    new_content_found = True
                except:
                    # Report not in this PR or not yet created
                    continue

        return all_discovered_reports
    except Exception as e:
        print(f"Error monitoring repo: {e}")
        return all_discovered_reports

# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("# Jules UX Analysis Orchestrator")

    with gr.Row():
        with gr.Column():
            theme_input = gr.Textbox(label="Theme", placeholder="e.g., Communication, Purchase decisions, Information gathering")
            profile_input = gr.Textbox(label="Customer Profile Description", placeholder="Describe the target customer...")
            num_personas_input = gr.Number(label="Number of Personas", value=1, precision=0)
            url_input = gr.Textbox(label="Target URL", value="https://example.com")


            generate_btn = gr.Button("Generate Personas & Tasks")

        with gr.Column():
            status_output = gr.Textbox(label="Status", interactive=False)
            task_list_display = gr.JSON(label="Tasks")
            persona_display = gr.JSON(label="Personas")

    with gr.Row():
        start_session_btn = gr.Button("Start Jules Session", variant="primary")

    with gr.Row():
        with gr.Tab("Active Session Reports"):
            report_output = gr.Markdown(label="Final Reports")
        with gr.Tab("Global Repo Feed"):
            gr.Markdown("### Live Monitoring of JsonLord/tiny_web for new UX reports")
            refresh_btn = gr.Button("Refresh Feed Now")
            global_feed = gr.Markdown(value="Waiting for new reports...")
            # Use a Timer to poll every 60 seconds
            timer = gr.Timer(value=60)
            timer.tick(fn=monitor_repo_for_reports, outputs=global_feed)
            refresh_btn.click(fn=monitor_repo_for_reports, outputs=global_feed)

    # Event handlers
    generate_btn.click(
        fn=handle_generate,
        inputs=[theme_input, profile_input, num_personas_input],
        outputs=[status_output, task_list_display, persona_display]
    )

    start_session_btn.click(
        fn=start_and_monitor_sessions,
        inputs=[persona_display, task_list_display, url_input],
        outputs=[status_output, report_output]
    )

if __name__ == "__main__":
    demo.launch()
