import os
import threading
import time
import httpx
import gradio as gr
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, HTMLResponse

# 1. Start our standard python server on port 8000 in a background thread
def start_backend():
    print("Starting backend http.server on port 8000...")
    from server import run_server
    run_server(8000)

backend_thread = threading.Thread(target=start_backend, daemon=True)
backend_thread.start()

# Wait for backend to start
time.sleep(2)

# 2. Define Gradio Interface (serves the iframe)
with gr.Blocks(title="Linkedin Resume Agent") as demo:
    gr.HTML("<iframe src='/dashboard/index.html' style='width:100%; height:95vh; border:none; margin:0; padding:0;'></iframe>")

# 3. Get Gradio's internal FastAPI app
app = demo.app

# 4. Mount static files directory directly on Gradio's FastAPI app
app.mount("/dashboard", StaticFiles(directory="static"), name="dashboard")

# 5. Route API requests to backend http.server on port 8000
@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_api(request: Request, path: str = ""):
    try:
        target_url = f"http://127.0.0.1:8000/api/{path}"
        if request.url.query:
            target_url += f"?{request.url.query}"
            
        async with httpx.AsyncClient() as client:
            req_headers = {k.lower(): v for k, v in request.headers.items()}
            for h in ["host", "content-length", "connection", "transfer-encoding", "accept-encoding"]:
                req_headers.pop(h, None)
                
            req_body = await request.body()
            
            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=req_headers,
                content=req_body,
                timeout=60.0
            )
            
            resp_headers = {k: v for k, v in resp.headers.items()}
            resp_headers.pop("content-length", None)
            resp_headers.pop("transfer-encoding", None)
            
            return StreamingResponse(
                resp.aiter_bytes(),
                status_code=resp.status_code,
                headers=resp_headers
            )
    except Exception as proxy_err:
        print(f"[Proxy Exception] Failed to proxy API {request.method} /api/{path}: {proxy_err}")
        return HTMLResponse(content=f"API Proxy error: {proxy_err}", status_code=500)

# 6. Launch the Gradio web server natively (so the Hugging Face supervisor detects it and keeps it alive)
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
