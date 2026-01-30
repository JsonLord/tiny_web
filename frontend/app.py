import gradio as gr
from gradio_client import Client
import json
import os
import time
import base64
import traceback

# Styling
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
body { font-family: 'Inter', sans-serif; background-color: #0d1117; color: #c9d1d9; }
.glass { background: rgba(22, 27, 34, 0.8); backdrop-filter: blur(10px); border: 1px solid #30363d; border-radius: 12px; padding: 20px; }
.btn-primary { background: linear-gradient(135deg, #238636, #2ea043) !important; color: white !important; border: none !important; }
.status-badge { padding: 4px 8px; border-radius: 6px; font-size: 0.8em; font-weight: 600; }
.badge-ready { background: #23863622; color: #3fb950; border: 1px solid #3fb950; }
.badge-pending { background: #d2992222; color: #d29922; border: 1px solid #d29922; }
iframe { border: 1px solid #30363d; border-radius: 8px; background: white; }
"""

# State
SESSION_STATE = {
    "report_id": None,
    "backend_url": "harvesthealth/xxg_backup",
    "token": None
}

def get_client():
    url = SESSION_STATE["backend_url"]
    token = SESSION_STATE["token"] if SESSION_STATE["token"] else None
    return Client(url, token=token)

def run_diagnostic():
    try:
        client = get_client()
        res = client.predict(api_name="/get_branches")
        return {"status": "Connected", "branches": res}
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}

def fetch_branches():
    try:
        client = get_client()
        branches = client.predict(api_name="/get_branches")
        return gr.update(choices=["Auto-detect"] + branches)
    except Exception as e:
        return gr.update(choices=["Auto-detect", "Error: " + str(e)])

def launch_audit(theme, profile, num, url):
    try:
        client = get_client()
        res = client.predict(theme, profile, num, url, api_name="/start_analysis")
        if isinstance(res, str):
            res = json.loads(res)

        rid = res.get("report_id")
        if rid:
            SESSION_STATE["report_id"] = rid
            return gr.update(visible=True), rid, f"Audit started! ID: **{rid}**"
        return gr.update(visible=False), None, f"Failed: {res}"
    except Exception as e:
        return gr.update(visible=False), None, f"Error: {str(e)}"

def refresh_portal(rid, branch):
    try:
        client = get_client()
        res = client.predict(rid, branch, api_name="/get_results")
        if isinstance(res, str):
            res = json.loads(res)

        if res.get("status") == "ready":
            md = res.get("report_md")
            html = res.get("slides_html")
            found_b = res.get("branch")

            if html and "<html>" in html.lower():
                b64 = base64.b64encode(html.encode('utf-8')).decode('utf-8')
                slides_iframe = f'<iframe src="data:text/html;base64,{b64}" width="100%" height="600px"></iframe>'
            else:
                slides_iframe = f"<div>{html if html else 'No slides rendered.'}</div>"

            badge = '<span class="status-badge badge-ready">READY</span>'
            return badge, md, slides_iframe, f"Found in branch: `{found_b}`"

        badge = '<span class="status-badge badge-pending">PENDING</span>'
        return badge, "Waiting for agent to complete analysis...", "...", "*Scanning branches...*"
    except Exception as e:
        return "ERROR", f"Failed to fetch: {str(e)}", "...", None

with gr.Blocks(css=CSS, title="AUX ANALYSIS") as demo:
    gr.Markdown("# 🛡️ AUX ANALYSIS")

    with gr.Tabs() as main_tabs:
        with gr.Tab("Launch Audit", id=0):
            with gr.Row():
                with gr.Column(scale=2):
                    theme_in = gr.Textbox(label="Theme", placeholder="E-commerce Checkout")
                    profile_in = gr.Textbox(label="User Profile", placeholder="Busy parents")
                    url_in = gr.Textbox(label="URL", value="https://www.harvesthealth.life")
                with gr.Column(scale=1):
                    num_in = gr.Slider(1, 5, 1, step=1, label="Personas")
                    launch_btn = gr.Button("🚀 Start Audit", variant="primary")

            with gr.Row(visible=False) as status_row:
                status_md = gr.Markdown()
                portal_btn = gr.Button("Go to Results")

        with gr.Tab("Results Portal", id=1):
            with gr.Row():
                rid_input = gr.Textbox(label="Report ID")
                branch_select = gr.Dropdown(label="Branch", choices=["Auto-detect"], value="Auto-detect")
                refresh_b = gr.Button("🔄 Branches")
                fetch_btn = gr.Button("🔍 Fetch Results", variant="primary")

            with gr.Row():
                status_badge = gr.HTML('<span class="status-badge badge-pending">IDLE</span>')
                active_branch = gr.Markdown()

            with gr.Row():
                with gr.Tab("Strategic Report"):
                    report_out = gr.Markdown("No report loaded.")
                with gr.Tab("Interactive Slides"):
                    slides_out = gr.HTML("Slides will appear here.")

        with gr.Tab("Settings"):
            with gr.Group():
                b_url = gr.Textbox(label="Backend Space URL / ID", value=SESSION_STATE["backend_url"])
                h_token = gr.Textbox(label="HF Token (Optional)", type="password")
                save_btn = gr.Button("Save Configuration")

            diag_btn = gr.Button("🔍 Test Backend Connection")
            diag_out = gr.JSON(label="Diagnostic Log")

    # Events
    def save_config(u, t):
        SESSION_STATE["backend_url"] = u
        SESSION_STATE["token"] = t
        return f"✅ Config saved. Target: {u}"

    save_btn.click(save_config, [b_url, h_token], diag_out)
    diag_btn.click(run_diagnostic, outputs=diag_out)

    launch_btn.click(launch_audit, [theme_in, profile_in, num_in, url_in], [status_row, rid_input, status_md])
    portal_btn.click(lambda: gr.Tabs(selected=1), outputs=main_tabs)

    refresh_b.click(fetch_branches, outputs=branch_select)
    fetch_btn.click(refresh_portal, [rid_input, branch_select], [status_badge, report_out, slides_out, active_branch])

if __name__ == "__main__":
    demo.launch()
