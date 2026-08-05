import os
import threading
import time
import httpx
import gradio as gr
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from server import run_server

# 1. Start our standard python server on port 8000 in a background thread
def start_backend():
    print("Starting backend http.server on port 8000...")
    run_server(8000)

backend_thread = threading.Thread(target=start_backend, daemon=True)
backend_thread.start()

# Wait for backend
time.sleep(2)

# 2. Define custom routes and proxy on the FastAPI app
# Gradio mounts the FastAPI app and exposes it under demo.app
with gr.Blocks(title="Linkedin Resume Agent") as demo:
    gr.HTML("<iframe src='/dashboard/' style='width:100%; height:95vh; border:none; margin:0; padding:0;'></iframe>")

# Get FastAPI app from Gradio
app = demo.app

@app.api_route("/dashboard/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_backend(request: Request, path: str = ""):
    url_path = request.url.path
    if url_path in ["/dashboard", "/dashboard/"]:
        url_path = "/dashboard/index.html"
        
    target_path = url_path
    if target_path.startswith("/dashboard/"):
        target_path = "/" + target_path[len("/dashboard/"):]
        
    target_url = f"http://127.0.0.1:8000{target_path}"
    if request.url.query:
        target_url += f"?{request.url.query}"
        
    async with httpx.AsyncClient() as client:
        req_headers = dict(request.headers)
        req_headers.pop("host", None)
        req_body = await request.body()
        
        resp = await client.request(
            method=request.method,
            url=target_url,
            headers=req_headers,
            content=req_body,
            timeout=60.0
        )
        
        return StreamingResponse(
            resp.aiter_bytes(),
            status_code=resp.status_code,
            headers=dict(resp.headers)
        )

# 5. Launch the Gradio web server in blocking mode
demo.launch(server_name="0.0.0.0", server_port=7860)
