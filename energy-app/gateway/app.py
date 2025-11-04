from fastapi import FastAPI, Request, Response
from starlette.responses import JSONResponse
import os, httpx, jwt
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

AUTH_URL = os.getenv("AUTH_URL", "http://127.0.0.1:8001")
USERS_URL = os.getenv("USERS_URL", "http://127.0.0.1:8002")
DEVICES_URL = os.getenv("DEVICES_URL", "http://127.0.0.1:8003")
JWT_SECRET = os.getenv("JWT_SECRET", "changeme")

app = FastAPI(
    title="E Gateway",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

TARGETS = {
    "/api/auth/": AUTH_URL,
    "/api/users": USERS_URL,
    "/api/devices": DEVICES_URL,
}

def required_role(path: str, method: str):
    # Public
    if path.startswith("/api/auth/"):
        return None
    # Client
    if path == "/api/devices/mine" and method == "GET":
        return "client"
    # Admin
    if path.startswith("/api/users"):
        return "admin"
    if path.startswith("/api/devices"):
        return "admin"
    return None

def pick_target(path: str) -> Optional[str]:
    for prefix, base in TARGETS.items():
        if path.startswith(prefix.rstrip("/")):
            return base
    return None

@app.middleware("http")
async def guard_and_proxy(request: Request, call_next):
    path = request.url.path
    method = request.method
    need = required_role(path, method)
    if path == "/api/health" or path.startswith("/api/docs") or path == "/api/openapi.json":
        return await call_next(request)
    user_id = None
    role = None
    if need is not None:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return JSONResponse({"detail":"Missing bearer token"}, status_code=401)
        token = auth.split(" ",1)[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user_id = payload.get("sub")
            role = payload.get("role")
        except jwt.PyJWTError:
            return JSONResponse({"detail":"Invalid token"}, status_code=401)
        if need == "admin" and role != "admin":
            return JSONResponse({"detail":"Forbidden"}, status_code=403)

    target = pick_target(path)
    if not target:
        return JSONResponse({"detail":"No route"}, status_code=404)

    async with httpx.AsyncClient(timeout=30.0) as client:
        proxied_url = target + path.replace("/api", "")
        headers = dict(request.headers)
        headers.pop("host", None)
        if user_id:
            headers["X-User-Id"] = user_id
            headers["X-User-Role"] = role or ""
        body = await request.body()
        resp = await client.request(method, proxied_url, content=body, headers=headers, params=request.query_params)
        clean_headers = {k:v for k,v in resp.headers.items() if k.lower() != "content-encoding"}
        return Response(content=resp.content, status_code=resp.status_code, headers=clean_headers)

@app.get("/api/health")
def health():
    return {"status":"ok"}
