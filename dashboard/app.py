from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from typing import Any

import httpx
from fastapi import Depends, FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

REPO = os.getenv("GITHUB_REPO", "solgea/ai-trading-agent-research-v1")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
DASHBOARD_USER = os.getenv("DASHBOARD_USER", "owner")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")
SESSION_SECRET = os.getenv("SESSION_SECRET", secrets.token_urlsafe(32))

app = FastAPI(title="AI Trading Agent Control Dashboard")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET, https_only=True, same_site="lax")

HTML = """<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Trading Agent — Control Dashboard</title>
<style>
body{font-family:Inter,system-ui,sans-serif;background:#0b1020;color:#e8edf7;margin:0}.wrap{max-width:1200px;margin:auto;padding:28px}
h1{margin:0 0 6px}.muted{color:#9aa7bd}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px;margin:20px 0}
.card{background:#121a2b;border:1px solid #26334d;border-radius:14px;padding:18px}.ok{color:#63d69f}.warn{color:#ffcc66}.bad{color:#ff7185}
button{background:#2d6cdf;color:white;border:0;border-radius:9px;padding:10px 14px;cursor:pointer;font-weight:700}button.danger{background:#b83b50}button.secondary{background:#33415e}
button:disabled{opacity:.45;cursor:not-allowed}.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.phase{display:flex;justify-content:space-between;gap:12px;align-items:center}
pre{white-space:pre-wrap;background:#0a0f1c;padding:12px;border-radius:8px;color:#b9c5d9}.pill{padding:4px 9px;border-radius:99px;background:#26334d}.approval{border:1px solid #7d6328;background:#211d11}
</style></head><body><div class="wrap">
<h1>AI Trading Agent — Control Dashboard</h1><div class="muted">Human-in-the-loop control plane · GitHub source of truth · execution disabled</div>
<div id="app">Yükleniyor…</div></div>
<script>
async function api(path,opt={}){let r=await fetch(path,{credentials:'same-origin',...opt});if(r.status===401){location='/login';return null}let d=await r.json();if(!r.ok)throw Error(d.detail||'İşlem başarısız');return d}
function esc(x){return String(x??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
async function act(path,body){if(!confirm('Bu insan onayı GitHub üzerinde kayıt altına alınacak. Devam edilsin mi?'))return;try{await api(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});await load()}catch(e){alert(e.message)}}
async function load(){let d=await api('/api/state');if(!d)return;
let prs=d.open_prs.map(p=>'<div class="card"><div class="phase"><b>#'+p.number+' '+esc(p.title)+'</b><span class="pill">'+esc(p.draft?'DRAFT':'OPEN')+'</span></div><p class="muted">head: '+esc(p.head_sha.slice(0,12))+'</p><div class="row"><button onclick="act(\'/api/approve-pr\',{pr:'+p.number+'})">Approve PR</button><button class="secondary" onclick="act(\'/api/merge-pr\',{pr:'+p.number+',sha:\''+p.head_sha+'\'})">Merge PR</button></div></div>').join('')||'<div class="muted">Açık PR yok.</div>';
let runs=d.runs.slice(0,8).map(r=>'<div class="row"><span class="pill">'+esc(r.status)+' / '+esc(r.conclusion||'—')+'</span><span>'+esc(r.name)+'</span><span class="muted">'+esc(r.head_sha?.slice(0,10))+'</span></div>').join('');
let issues=d.issues.slice(0,8).map(i=>'<div><b>#'+i.number+'</b> '+esc(i.title)+' <span class="muted">('+esc(i.state)+')</span></div>').join('');
document.getElementById('app').innerHTML=
'<div class="grid"><div class="card"><div class="muted">Repository</div><b>'+esc(d.repo.full_name)+'</b><p>main: <code>'+esc(d.repo.default_branch_sha.slice(0,12))+'</code></p></div>'+
'<div class="card"><div class="muted">Execution</div><b class="ok">LOCKED</b><p>Dashboard doğrudan emir çalıştırmaz.</p></div>'+
'<div class="card '+(d.at3_authorized?'':'approval')+'"><div class="muted">AT-3 Gate</div><b class="'+(d.at3_authorized?'ok':'warn')+'">'+(d.at3_authorized?'AUTHORIZED':'HUMAN APPROVAL REQUIRED')+'</b><p>'+(d.at3_authorized?'GitHub audit kaydı mevcut.':'AT-3 başlamadan önce aşağıdaki butonla açık onay gerekir.')+'</p><button '+(d.at3_authorized?'disabled':'')+' onclick="act(\'/api/authorize-at3\',{})">'+(d.at3_authorized?'Onaylandı':'AT-3 Başlatmayı Onayla')+'</button></div></div>'+
'<h2>Onay bekleyen GitHub işlemleri</h2><div class="grid">'+prs+'</div>'+
'<h2>CI / Workflow</h2><div class="card">'+runs+'</div>'+
'<h2>Son GitHub kayıtları</h2><div class="card">'+issues+'</div>'+
'<p class="muted">Son yenileme: '+new Date().toLocaleString('tr-TR')+' · <a href="/logout" style="color:#9bbcff">Çıkış</a></p>'}
load();setInterval(load,15000)
</script></body></html>"""

LOGIN = """<!doctype html><html lang="tr"><body style="font-family:system-ui;max-width:420px;margin:80px auto;background:#0b1020;color:white;padding:30px">
<h2>Control Dashboard</h2><form method="post"><input name="username" placeholder="Kullanıcı" style="width:100%;padding:12px;margin:8px 0">
<input name="password" type="password" placeholder="Şifre" style="width:100%;padding:12px;margin:8px 0"><button style="padding:12px 20px">Giriş</button></form></body></html>"""

def auth(request: Request) -> None:
    if not request.session.get("auth"):
        raise HTTPException(401, "authentication required")

async def gh(method: str, path: str, **kwargs: Any) -> Any:
    if not GITHUB_TOKEN:
        raise HTTPException(503, "GITHUB_TOKEN yapılandırılmamış")
    headers={"Authorization":f"Bearer {GITHUB_TOKEN}","Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"}
    async with httpx.AsyncClient(timeout=15) as c:
        r=await c.request(method, f"https://api.github.com{path}", headers=headers, **kwargs)
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text[:500])
    return r.json() if r.content else {}

@app.get("/health")
async def health(): return {"status":"ok","execution":"locked"}

@app.get("/login", response_class=HTMLResponse)
async def login(): return LOGIN

@app.post("/login")
async def do_login(request: Request, username: str=Form(...), password: str=Form(...)):
    if not (hmac.compare_digest(username,DASHBOARD_USER) and hmac.compare_digest(password,DASHBOARD_PASSWORD)):
        raise HTTPException(401,"invalid credentials")
    request.session["auth"]=True; r=RedirectResponse("/",status_code=303); return r

@app.get("/logout")
async def logout(request: Request):
    request.session.clear(); return RedirectResponse("/login",303)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    auth(request); return HTML

@app.get("/api/state")
async def state(request: Request):
    auth(request)
    repo=await gh("GET",f"/repos/{REPO}")
    prs=await gh("GET",f"/repos/{REPO}/pulls",params={"state":"open","per_page":20})
    issues=await gh("GET",f"/repos/{REPO}/issues",params={"state":"all","per_page":12,"sort":"updated","direction":"desc"})
    runs=await gh("GET",f"/repos/{REPO}/actions/runs",params={"per_page":12})
    comments=await gh("GET",f"/repos/{REPO}/issues/5/comments",params={"per_page":50}) if REPO=="solgea/ai-trading-agent-research-v1" else []
    at3=any("HUMAN_APPROVAL: AT-3" in c.get("body","") for c in comments)
    return {"repo":{"full_name":repo["full_name"],"default_branch_sha":(await gh("GET",f"/repos/{REPO}/git/ref/heads/{repo['default_branch']}"))["object"]["sha"]},
            "open_prs":[{"number":p["number"],"title":p["title"],"draft":p["draft"],"head_sha":p["head"]["sha"]} for p in prs],
            "issues":[{"number":i["number"],"title":i["title"],"state":i["state"]} for i in issues],
            "runs":[{"name":r["name"],"status":r["status"],"conclusion":r["conclusion"],"head_sha":r["head_sha"]} for r in runs["workflow_runs"]],
            "at3_authorized":at3}

@app.post("/api/approve-pr")
async def approve_pr(request: Request):
    auth(request); body=await request.json(); pr=int(body["pr"])
    return await gh("POST",f"/repos/{REPO}/pulls/{pr}/reviews",json={"event":"APPROVE","body":"Human approval via Control Dashboard."})

@app.post("/api/merge-pr")
async def merge_pr(request: Request):
    auth(request); body=await request.json(); pr=int(body["pr"]); sha=body["sha"]
    return await gh("PUT",f"/repos/{REPO}/pulls/{pr}/merge",json={"sha":sha,"merge_method":"squash","commit_title":f"Merge PR #{pr} via Control Dashboard"})

@app.post("/api/authorize-at3")
async def authorize_at3(request: Request):
    auth(request)
    return await gh("POST",f"/repos/{REPO}/issues/5/comments",json={"body":"HUMAN_APPROVAL: AT-3\nApproved via Control Dashboard by repository owner.\nExecution authority: NONE. This approval authorizes only the AT-3 engineering phase to be proposed/implemented under the existing safety gates."})
