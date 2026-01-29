import gradio as gr
import requests
import os
import time
import json
from datetime import datetime, timedelta

# Default Backend Configuration
DEFAULT_BACKEND_URL = "https://harvesthealth-xxg-backup.hf.space"
# Try to get token from env
ENV_TOKEN = os.environ.get("HF_TOKEN") or os.environ.get("GITHUB_API_TOKEN")

# Modern SaaS CSS
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800&display=swap');

:root {
    --bg-color: #020617;
    --panel-bg: rgba(30, 41, 59, 0.5);
    --accent-gradient: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --border-color: rgba(255, 255, 255, 0.1);
}

body, .gradio-container {
    background-color: var(--bg-color) !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--text-primary) !important;
}

.hero-section {
    text-align: center;
    padding: 60px 20px;
}

.hero-title {
    font-size: 4rem;
    font-weight: 800;
    background: linear-gradient(90deg, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 20px;
}

.glass-card {
    background: var(--panel-bg) !important;
    backdrop-filter: blur(12px);
    border: 1px solid var(--border-color) !important;
    border-radius: 24px !important;
    padding: 32px !important;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5) !important;
    margin-bottom: 20px;
}

.primary-btn {
    background: var(--accent-gradient) !important;
    border: none !important;
    color: white !important;
    font-weight: 700 !important;
    padding: 14px 28px !important;
    border-radius: 12px !important;
    transition: all 0.3s ease !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    cursor: pointer;
}

.primary-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(139, 92, 246, 0.5) !important;
}

.secondary-btn {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid var(--border-color) !important;
    color: white !important;
    padding: 10px 20px !important;
    border-radius: 10px !important;
}

.gr-text-input, .gr-textarea, .gr-slider {
    background: rgba(15, 23, 42, 0.6) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
    color: white !important;
}
"""

def get_headers(token):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

def start_analysis(theme, profile, url, num_personas, backend_url, token):
    if not theme or not profile or not url:
        return None, "### ⚠️ Please fill in all fields.", gr.update(), "Error: Missing fields"

    try:
        payload = {
            "theme": theme,
            "profile": profile,
            "url": url,
            "num_personas": int(num_personas)
        }
        base = backend_url.rstrip("/")
        endpoint = f"{base}/api/start_analysis"
        resp = requests.post(endpoint, json=payload, headers=get_headers(token), timeout=30)

        log = f"POST {endpoint} -> {resp.status_code}\n"
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, str) and "<title>" in data:
                return None, "### ❌ Auth Failed: Check Token in Settings", gr.update(), log + "Response contains HTML (Redirect)"

            report_id = data.get("report_id")
            eta = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")
            return report_id, f"### ✅ Audit Initiated\n**ID:** `{report_id}`\n\nETA: ~1 hour (come back at {eta})", gr.update(selected="results"), log + json.dumps(data, indent=2)

        return None, f"### ❌ Error {resp.status_code}\nCheck connection/token.", gr.update(), log + resp.text[:1000]
    except Exception as e:
        return None, f"### ❌ Connection Error\n{str(e)}", gr.update(), f"Exception: {str(e)}"

def fetch_results(report_id, backend_url, token):
    if not report_id:
        return gr.update(visible=False), "", "", "### ⚠️ Enter a Session ID", "Error: No ID"

    try:
        base = backend_url.rstrip("/")
        endpoint = f"{base}/api/results/{report_id}"
        resp = requests.get(endpoint, headers=get_headers(token), timeout=30)

        log = f"GET {endpoint} -> {resp.status_code}\n"
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "ready":
                return gr.update(visible=True), data.get("slides_html"), data.get("report_md"), "", log + "Results Ready"
            return gr.update(visible=False), "", "", "### ⏳ Still Working...\nThe AI agent is currently performing the analysis. Please check back later.", log + "Status: Pending"

        return gr.update(visible=False), "", "", f"### ❌ Error {resp.status_code}", log + resp.text[:1000]
    except Exception as e:
        return gr.update(visible=False), "", "", f"### ❌ Connection Error\n{str(e)}", f"Exception: {str(e)}"

def test_connection(backend_url, token):
    try:
        base = backend_url.rstrip("/")
        endpoint = f"{base}/health"
        resp = requests.get(endpoint, headers=get_headers(token), timeout=10)
        if resp.status_code == 200:
            return "✅ Backend Connected Successfully!", f"GET {endpoint} -> 200 OK\n{resp.text}"
        return f"❌ Connection failed ({resp.status_code})", f"GET {endpoint} -> {resp.status_code}\n{resp.text}"
    except Exception as e:
        return f"❌ Connection Error: {str(e)}", f"Exception: {str(e)}"

with gr.Blocks(css=CSS, title="AUX ANALYSIS") as demo:
    gr.HTML("""
    <div class='hero-section'>
        <h1 class='hero-title'>AUX ANALYSIS</h1>
        <p style='color: #94a3b8; font-size: 1.1rem;'>Professional AI-Driven User Experience Audits</p>
    </div>
    """)

    with gr.Tabs() as tabs:
        with gr.Tab("Launch Audit", id="launch"):
            with gr.Column(elem_classes="glass-card"):
                with gr.Row():
                    with gr.Column():
                        theme = gr.Textbox(label="Analysis Focus", placeholder="e.g. Mobile Signup Flow", info="What core experience should be analyzed?")
                        profile = gr.TextArea(label="Persona Background", placeholder="e.g. Professional photographer looking for cloud storage...", info="Who is the simulated user?")
                    with gr.Column():
                        url = gr.Textbox(label="Audit URL", value="https://", info="The destination for the AI scan.")
                        personas = gr.Slider(label="Simulated Sessions", minimum=1, maximum=3, step=1, value=1)

                launch_btn = gr.Button("🔥 Start AI Analysis", elem_classes="primary-btn")
                launch_status = gr.Markdown()

        with gr.Tab("Results Portal", id="results"):
            with gr.Column(elem_classes="glass-card"):
                gr.Markdown("### 🔍 Fetch Strategic Report")
                report_id_input = gr.Textbox(label="Session ID", placeholder="Paste your Session ID here...")
                check_btn = gr.Button("⚡ Retrieve Deliverables", elem_classes="primary-btn")

                status_msg = gr.Markdown()

                with gr.Column(visible=False) as output_container:
                    with gr.Tabs() as result_view_tabs:
                        with gr.Tab("Presentation"):
                            slides_frame = gr.HTML()
                        with gr.Tab("Written Report"):
                            report_markdown = gr.Markdown()

        with gr.Tab("Settings", id="settings"):
            with gr.Column(elem_classes="glass-card"):
                gr.Markdown("### ⚙️ System Configuration")
                backend_url_input = gr.Textbox(label="Backend Orchestrator URL", value=DEFAULT_BACKEND_URL)
                token_input = gr.Textbox(label="Access Token", placeholder="hf_...", type="password", value=ENV_TOKEN)
                test_btn = gr.Button("Test Backend Connection", elem_classes="secondary-btn")
                test_status = gr.Markdown()

                gr.Markdown("### 🛠️ Debug Logs")
                debug_output = gr.Code(label="Last Transaction Log", language="json")

    # Bindings
    launch_btn.click(
        start_analysis,
        inputs=[theme, profile, url, personas, backend_url_input, token_input],
        outputs=[report_id_input, launch_status, tabs, debug_output]
    )

    check_btn.click(
        fetch_results,
        inputs=[report_id_input, backend_url_input, token_input],
        outputs=[output_container, slides_frame, report_markdown, status_msg, debug_output]
    )

    test_btn.click(
        test_connection,
        inputs=[backend_url_input, token_input],
        outputs=[test_status, debug_output]
    )

if __name__ == "__main__":
    demo.launch()
