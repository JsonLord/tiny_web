import gradio as gr
import requests
import os
import time
import json
from datetime import datetime, timedelta

# Default Backend Configuration
DEFAULT_BACKEND_URL = "https://harvesthealth-xxg-backup.hf.space"
# Try to get token from env, otherwise leave empty for manual entry
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
    font-size: 3.5rem;
    font-weight: 800;
    background: linear-gradient(90deg, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 10px;
}

.glass-card {
    background: var(--panel-bg) !important;
    backdrop-filter: blur(12px);
    border: 1px solid var(--border-color) !important;
    border-radius: 24px !important;
    padding: 32px !important;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5) !important;
}

.primary-btn {
    background: var(--accent-gradient) !important;
    border: none !important;
    color: white !important;
    font-weight: 700 !important;
    padding: 12px 24px !important;
    border-radius: 12px !important;
    transition: all 0.3s ease !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.primary-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(139, 92, 246, 0.5) !important;
}

/* Customizing Gradio Components */
.gr-text-input, .gr-textarea, .gr-slider {
    background: rgba(15, 23, 42, 0.6) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
    color: white !important;
}

.error-box {
    color: #ef4444;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid #ef4444;
    padding: 10px;
    border-radius: 8px;
    margin: 10px 0;
}
"""

def get_headers(token):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

def start_analysis(theme, profile, url, num_personas, backend_url, token):
    if not theme or not profile or not url:
        return None, "### ⚠️ Please fill in all fields.", gr.update()

    try:
        payload = {
            "theme": theme,
            "profile": profile,
            "url": url,
            "num_personas": int(num_personas)
        }
        # Ensure url ends correctly
        base = backend_url.rstrip("/")
        resp = requests.post(f"{base}/api/start_analysis", json=payload, headers=get_headers(token), timeout=30)

        if resp.status_code == 200:
            data = resp.json()
            # If we got HTML back, it means auth failed
            if isinstance(data, str) and "<title>" in data:
                return None, "### ❌ Authentication Failed\nBackend returned Hugging Face login page. Please check your Token in the Settings tab.", gr.update()

            report_id = data.get("report_id")
            eta = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")
            return report_id, f"### ✅ Analysis Initialized\n**Session ID:** `{report_id}`\n\nETA: Approximately {eta} (1 hour)", gr.update(selected="results")

        err_msg = resp.text[:500]
        if "<title>" in err_msg:
            return None, "### ❌ Connection Error\nBackend is unreachable or private. Ensure the HF Token is correct in the Settings tab.", gr.update()

        return None, f"### ❌ Error ({resp.status_code})\n{err_msg}", gr.update()
    except Exception as e:
        return None, f"### ❌ Connection Error\n{str(e)}", gr.update()

def fetch_results(report_id, backend_url, token):
    if not report_id:
        return gr.update(visible=False), gr.update(visible=False), "### ⚠️ Enter a Session ID"

    try:
        base = backend_url.rstrip("/")
        resp = requests.get(f"{base}/api/results/{report_id}", headers=get_headers(token), timeout=30)

        if resp.status_code == 200:
            # Check if response is JSON
            try:
                data = resp.json()
            except:
                if "<title>" in resp.text:
                    return gr.update(visible=False), "", "", "### ❌ Authentication Error\nCannot reach backend results. Check Token."
                return gr.update(visible=False), "", "", "### ❌ Invalid Response from Backend"

            if data.get("status") == "ready":
                return gr.update(visible=True), data.get("slides_html"), data.get("report_md"), ""
            return gr.update(visible=False), "", "", "### ⏳ Still Processing...\nThe audit is currently being performed. Please check back in a while."

        return gr.update(visible=False), "", "", f"### ❌ Error ({resp.status_code})"
    except Exception as e:
        return gr.update(visible=False), "", "", f"### ❌ Connection Error\n{str(e)}"

with gr.Blocks(css=CSS, title="AUX ANALYSIS") as demo:
    gr.HTML("""
    <div class='hero-section'>
        <h1 class='hero-title'>AUX ANALYSIS</h1>
    </div>
    """)

    with gr.Tabs() as tabs:
        with gr.Tab("Launch Audit", id="launch"):
            with gr.Column(elem_classes="glass-card"):
                with gr.Row():
                    with gr.Column():
                        theme = gr.Textbox(label="Analysis Theme", placeholder="e.g. E-commerce Checkout Flow", info="What core experience should be audited?")
                        profile = gr.TextArea(label="Target User Profile", placeholder="e.g. Tech-savvy millennials looking for sustainable coffee...", info="Who is the persona to simulate?")
                    with gr.Column():
                        url = gr.Textbox(label="Target URL", value="https://", info="The website to interact with.")
                        personas = gr.Slider(label="Persona Intensity", minimum=1, maximum=3, step=1, value=1, info="Number of unique user simulations.")

                launch_btn = gr.Button("🚀 Start AI Deep Scan", elem_classes="primary-btn")
                launch_status = gr.Markdown()

        with gr.Tab("Results Portal", id="results"):
            with gr.Column(elem_classes="glass-card"):
                gr.Markdown("### 🔍 Retrieve Your Audit")
                report_id_input = gr.Textbox(label="Session ID", placeholder="Paste your Session ID here...")
                check_btn = gr.Button("⚡ Fetch Analysis Results", elem_classes="primary-btn")

                status_msg = gr.Markdown()

                with gr.Column(visible=False) as output_container:
                    with gr.Tabs() as result_view_tabs:
                        with gr.Tab("Presentation Slides"):
                            slides_frame = gr.HTML()
                            skip_btn = gr.Button("View Full Written Report →")
                        with gr.Tab("Full Strategic Report"):
                            report_markdown = gr.Markdown()

        with gr.Tab("Settings", id="settings"):
            with gr.Column(elem_classes="glass-card"):
                gr.Markdown("### ⚙️ Backend Configuration")
                backend_url_input = gr.Textbox(label="Backend URL", value=DEFAULT_BACKEND_URL)
                token_input = gr.Textbox(label="Hugging Face Token", placeholder="hf_...", type="password", value=ENV_TOKEN)
                gr.Markdown("_This token is used to authenticate with the private backend space._")

    # Logic
    launch_btn.click(
        start_analysis,
        inputs=[theme, profile, url, personas, backend_url_input, token_input],
        outputs=[report_id_input, launch_status, tabs]
    )

    check_btn.click(
        fetch_results,
        inputs=[report_id_input, backend_url_input, token_input],
        outputs=[output_container, slides_frame, report_markdown, status_msg]
    )

if __name__ == "__main__":
    demo.launch()
