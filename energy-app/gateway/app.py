import os
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import Response
import httpx
import jwt
from typing import Optional

JWT_SECRET = os.getenv("JWT_SECRET", "secret-key")
AUTH_URL = os.getenv("AUTH_URL", "http://auth:8001")
USERS_URL = os.getenv("USERS_URL", "http://users:8002")
DEVICES_URL = os.getenv("DEVICES_URL", "http://devices:8003")
MONITORING_URL = os.getenv("MONITORING_URL", "http://monitoring:8004")

app = FastAPI(title="API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


TARGETS = {
    "/api/auth": (AUTH_URL, "/api"),
    "/api/users": (USERS_URL, "/api"),
    "/api/devices/mine": (DEVICES_URL, "/api"),
    "/api/devices": (DEVICES_URL, "/api"),
    "/api/device-users": (DEVICES_URL, "/api"),
    "/api/monitoring": (MONITORING_URL, "/api"),  
}

def required_role(path: str, method: str):
    # Public
    if path.startswith("/api/auth"):
        return None
    # Client
    if path == "/api/devices/mine" and method == "GET":
        return "client" 
    if path.startswith("/api/monitoring/devices/") and "/day/" in path and method == "GET":
        return "client" 
    # Admin
    if path.startswith("/api/monitoring/devices") and method == "GET":
       
        if path.endswith("/devices"):
            return "admin"
    if path.startswith("/api/users"):
        return "admin"
    if path.startswith("/api/devices"):
        return "admin"
    return None

def pick_target(path: str):
    
    for prefix in sorted(TARGETS.keys(), key=len, reverse=True):
        if path.startswith(prefix):
            target_url, strip_prefix = TARGETS[prefix]
            service_path = path.replace(strip_prefix, "", 1)
            return target_url + service_path
    return None

@app.middleware("http")
async def guard_and_proxy(request: Request, call_next):
    path = request.url.path
    method = request.method
    
    print(f"Gateway received: {method} {path}")  
    
   
    if path == "/api/health" or path.startswith("/api/docs") or path == "/api/openapi.json":
        return await call_next(request)
    
    
    if method == "OPTIONS":
        proxied_url = pick_target(path)
        if not proxied_url:
            return JSONResponse({"detail":"No route"}, status_code=404)
        
        print(f"Proxying OPTIONS to: {proxied_url}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                headers = dict(request.headers)
                headers.pop("host", None)
                resp = await client.options(proxied_url, headers=headers)
                clean_headers = {k:v for k,v in resp.headers.items() if k.lower() not in ["content-encoding", "content-length", "transfer-encoding"]}
                return Response(content=resp.content, status_code=resp.status_code, headers=clean_headers)
            except Exception as e:
                print(f"Error proxying OPTIONS to {proxied_url}: {e}")
                return JSONResponse({"detail": f"Service unavailable: {str(e)}"}, status_code=503)
    
    need = required_role(path, method)
    user_id = None
    role = None
    
   
    if need is not None:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            print(f"Missing bearer token for {path}")
            return JSONResponse({"detail":"Missing bearer token"}, status_code=401)
        
        token = auth.split(" ",1)[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user_id = payload.get("sub")
            role = payload.get("role")
            print(f"Authenticated user: {user_id}, role: {role}")
        except jwt.PyJWTError as e:
            print(f"Invalid token: {e}")
            return JSONResponse({"detail":"Invalid token"}, status_code=401)
        
       
        if need == "admin" and role != "admin":
            print(f"Access denied: need admin, got {role}")
            return JSONResponse({"detail":"Forbidden"}, status_code=403)
        
        
        if need == "client" and role not in ["client", "admin"]:
            print(f"Access denied: need client or admin, got {role}")
            return JSONResponse({"detail":"Forbidden"}, status_code=403)

    proxied_url = pick_target(path)
    if not proxied_url:
        print(f"No target found for {path}")
        return JSONResponse({"detail":"No route"}, status_code=404)
    
    print(f"Proxying to: {proxied_url}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            headers = dict(request.headers)
            headers.pop("host", None)
            if user_id:
                headers["X-User-Id"] = user_id
                headers["X-User-Role"] = role or ""
            body = await request.body()
            resp = await client.request(method, proxied_url, content=body, headers=headers, params=request.query_params)
            clean_headers = {k:v for k,v in resp.headers.items() if k.lower() not in ["content-encoding", "content-length", "transfer-encoding"]}
            print(f"Response: {resp.status_code}")
            return Response(content=resp.content, status_code=resp.status_code, headers=clean_headers)
        except Exception as e:
            print(f"Error proxying to {proxied_url}: {e}")
            return JSONResponse({"detail": f"Service unavailable: {str(e)}"}, status_code=503)

@app.get("/api/health")
def health():
    return {"status":"ok"}
