import os
import threading
import time
import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse

# 1. Start our standard python server on port 8000 in a background thread
def start_backend():
    print("Starting backend http.server on port 8000...")
    from server import run_server
    run_server(8000)

backend_thread = threading.Thread(target=start_backend, daemon=True)
backend_thread.start()

# Wait for backend
time.sleep(2)

# 2. Create FastAPI app
app = FastAPI()

# 3. Mount static files directory at /dashboard
app.mount("/dashboard", StaticFiles(directory="static"), name="dashboard")

# 4. Route root '/' to serve index.html directly
@app.get("/")
def read_root():
    return FileResponse("static/index.html")

# 5. Route /styles.css and /app.js to serve directly from static folder
@app.get("/styles.css")
def get_css():
    return FileResponse("static/styles.css")

@app.get("/app.js")
def get_js():
    return FileResponse("static/app.js")

# 6. Proxy API requests to backend http.server on port 8000
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

# 7. Start Uvicorn directly
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    print(f"Booting Uvicorn Server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
