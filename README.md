---
title: AUX ANALYSIS BACKEND
emoji: ⚙️
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 4.44.1
app_file: app.py
python_version: "3.10"
pinned: false
---

# AUX ANALYSIS BACKEND

Exposes API endpoints for orchestrating and retrieving UX analysis reports.

## API Usage
- `GET /health`: Health check.
- `POST /api/start_analysis`: Initiate a session.
- `GET /api/results/{report_id}`: Fetch results once ready.
