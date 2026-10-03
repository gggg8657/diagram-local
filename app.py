#!/usr/bin/env python3
"""diagram local — 말로 설명하면 Mermaid 다이어그램. 외부 의존성 없음(stdlib), CDN 없음(static/mermaid.min.js 동봉).

  python3 app.py                                   # http://localhost:8768
  LLM_MODEL=gpt-oss:20b python3 app.py
  LLM_API=openai LLM_BASE_URL=http://gpu:8000/v1 LLM_MODEL=Qwen3-32B python3 app.py
  python3 app.py --cli "사용자가 로그인하면 인증서버가 토큰을 발급" [flowchart]   # Mermaid 소스를 stdout에
"""
import datetime
import json
import os
import re
import secrets
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
WS = os.path.join(ROOT, "_workspace")
LLM_API = os.environ.get("LLM_API", "ollama")            # ollama | openai (vLLM·LM Studio·llama.cpp 등)
LLM_BASE = os.environ.get("LLM_BASE_URL", "http://localhost:8000/v1" if LLM_API == "openai" else "http://localhost:11434").rstrip("/")
MODEL = os.environ.get("LLM_MODEL", "qwen3:8b")
LLM_KEY = os.environ.get("LLM_API_KEY", "")
PORT = int(os.environ.get("PORT", "8768"))
NUM_CTX = int(os.environ.get("NUM_CTX", "16384"))
TYPES = {"auto": "", "flowchart": "flowchart TD", "sequence": "sequenceDiagram", "class": "classDiagram", "er": "erDiagram",
         "state": "stateDiagram-v2", "gantt": "gantt", "mindmap": "mindmap", "timeline": "timeline", "pie": "pie"}
HEADS = ("flowchart", "graph", "sequenceDiagram", "classDiagram", "erDiagram", "stateDiagram", "gantt", "mindmap", "timeline", "pie",
         "journey", "gitGraph", "quadrantChart", "xychart", "block", "sankey", "requirementDiagram", "C4Context")


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, s):
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)


# ── LLM ─────────────────────────────────────────────────────────────────
def _clean(out):
    out = re.sub(r"<think>.*?</think>", "", out, flags=re.S).strip()
    out = re.sub(r"^```\w*\s*\n", "", out)
    out = re.sub(r"\n?```\s*$", "", out)
    return out.strip()


def openai_chat(system, messages, model, on_token=None):
    body = {"model": model, "stream": True, "temperature": 0.2,
            "messages": [{"role": "system", "content": system}, *messages]}
    hdr = {"Content-Type": "application/json", **({"Authorization": f"Bearer {LLM_KEY}"} if LLM_KEY else {})}
    req = urllib.request.Request(LLM_BASE + "/chat/completions", json.dumps(body).encode(), hdr)
    buf = []
    try:
        with urllib.request.urlopen(req, timeout=3600) as r:
            for line in r:
                line = line.decode().strip()
                if not line.startswith("data:") or line == "data: [DONE]":
                    continue
                tok = (json.loads(line[5:])["choices"][0].get("delta") or {}).get("content") or ""
                if tok:
                    buf.append(tok)
                    if on_token:
                        on_token(tok)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"LLM HTTP {e.code}: {e.read().decode(errors='replace')[:300]}")
    return "".join(buf)


def ollama(system, messages, model, on_token=None):
    """Ollama /api/chat 스트리밍 (think:false 미지원 모델이면 재시도). LLM_API=openai 면 OpenAI 호환."""
    if LLM_API == "openai":
        return openai_chat(system, messages, model, on_token)
    body = {"model": model, "stream": True, "think": False, "options": {"temperature": 0.2, "num_ctx": NUM_CTX},
            "messages": [{"role": "system", "content": system}, *messages]}
    for attempt in (0, 1):
        try:
            req = urllib.request.Request(LLM_BASE + "/api/chat", json.dumps(body).encode(), {"Content-Type": "application/json"})
            buf = []
            with urllib.request.urlopen(req, timeout=3600) as r:
                for line in r:
                    if not line.strip():
                        continue
                    j = json.loads(line)
                    if "error" in j:
                        raise RuntimeError(j["error"])
                    tok = j.get("message", {}).get("content", "")
                    if tok:
                        buf.append(tok)
                        if on_token:
                            on_token(tok)
                    if j.get("done"):
                        break
            return "".join(buf)
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")
            if attempt == 0 and "think" in msg:
                body.pop("think")
                continue
            raise RuntimeError(f"Ollama HTTP {e.code}: {msg[:300]}")


def models():
    if LLM_API == "openai":
        req = urllib.request.Request(LLM_BASE + "/models", headers={"Authorization": f"Bearer {LLM_KEY}"} if LLM_KEY else {})
        with urllib.request.urlopen(req, timeout=10) as r:
            return [m["id"] for m in json.load(r)["data"]]
    with urllib.request.urlopen(LLM_BASE + "/api/tags", timeout=10) as r:
        return [m["name"] for m in json.load(r)["models"]]


# ── Mermaid 처리 ───────────────────────────────────────────────────────
def sanity(src):
    """서버 측 1차 검사 — 진짜 파싱은 브라우저의 mermaid 가 한다. 실패 사유 문자열 또는 None."""
    lines = [l for l in src.strip().splitlines() if l.strip() and not l.strip().startswith("%%")]
    if not lines:
        return "빈 출력"
    if not lines[0].strip().startswith(HEADS):
        return f"첫 줄이 다이어그램 선언이 아님: {lines[0][:40]!r}"
    for a, b in ("[]", "()", "{}"):
        if src.count(a) != src.count(b):
            return f"괄호 불일치 {a}{b}"
    if src.count('"') % 2:
        return "큰따옴표 홀수"
    return None


def diagram(messages, dtype="auto", model=MODEL, on_token=None):
    """messages: [{role, content}] 대화. 마지막 user 메시지에 유형 힌트를 붙여 LLM 호출 → Mermaid 소스."""
    system = read(os.path.join(ROOT, "goal-prompt.md"))
    msgs = [dict(m) for m in messages]
    hint = TYPES.get(dtype, "")
    if hint and msgs and msgs[-1]["role"] == "user":
        msgs[-1]["content"] += f"\n\n[유형] {hint} 로 그린다."
    src = _clean(ollama(system, msgs, model, on_token))
    return src


def repair(src, error, model=MODEL):
    system = read(os.path.join(ROOT, "goal-prompt.md"))
    user = f"[파싱 오류]\n{error}\n\n[소스]\n{src}"
    return _clean(ollama(system, [{"role": "user", "content": user}], model))


def save(messages, dtype, src, model):
    os.makedirs(WS, exist_ok=True)
    rid = f"{datetime.date.today()}-{secrets.token_hex(2)}"
    head = next((m["content"] for m in messages if m["role"] == "user"), "")[:60]
    write(os.path.join(WS, rid + ".json"), json.dumps({"id": rid, "type": dtype, "model": model, "messages": messages, "source": src,
                                                        "head": head, "ts": datetime.datetime.now().isoformat(timespec="seconds")},
                                                       ensure_ascii=False, indent=1))
    return rid


def list_runs():
    if not os.path.isdir(WS):
        return []
    out = []
    for n in sorted(os.listdir(WS), reverse=True)[:50]:
        if n.endswith(".json"):
            try:
                j = json.load(open(os.path.join(WS, n), encoding="utf-8"))
                out.append({k: j.get(k) for k in ("id", "type", "model", "head", "ts")})
            except Exception:
                pass
    return out


# ── HTTP ───────────────────────────────────────────────────────────────
HTML = read(os.path.join(ROOT, "ui.html")) if os.path.exists(os.path.join(ROOT, "ui.html")) else "ui.html 없음"


class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *a):
        if "/api/diagram" in (a[0] if a else "") or "/api/repair" in (a[0] if a else ""):
            super().log_message(fmt, *a)

    def _send(self, body, ctype="application/json", code=200):
        b = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        try:
            if self.path == "/api/models":
                return self._send(models())
            if self.path == "/api/runs":
                return self._send(list_runs())
            m = re.fullmatch(r"/api/runs/(\d{4}-\d{2}-\d{2}-[0-9a-f]{4})", self.path)
            if m:
                return self._send(read(os.path.join(WS, m.group(1) + ".json")).encode())
            if self.path == "/static/mermaid.min.js":
                with open(os.path.join(ROOT, "static", "mermaid.min.js"), "rb") as f:
                    return self._send(f.read(), "application/javascript")
            self._send(HTML.replace("%MODEL%", json.dumps(MODEL)).encode(), "text/html; charset=utf-8")
        except FileNotFoundError:
            self._send({"error": "없음"}, code=404)
        except Exception as e:
            self._send({"error": f"{type(e).__name__}: {e}"}, code=500)

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        model = req.get("model") or MODEL
        if self.path == "/api/repair":
            try:
                src = repair(req.get("source", ""), req.get("error", ""), model)
                return self._send({"source": src, "sanity": sanity(src)})
            except Exception as e:
                return self._send({"error": f"{type(e).__name__}: {e}"}, code=500)
        messages = [m for m in req.get("messages", []) if m.get("role") in ("user", "assistant") and (m.get("content") or "").strip()]
        if not messages:
            return self._send({"error": "빈 입력"}, code=400)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        def emit(ev):
            self.wfile.write(f"data: {json.dumps(ev, ensure_ascii=False)}\n\n".encode())
            self.wfile.flush()

        try:
            dtype = req.get("type") or "auto"
            src = diagram(messages, dtype, model, on_token=lambda t: emit({"token": t}))
            rid = save(messages + [{"role": "assistant", "content": src}], dtype, src, model)
            emit({"done": {"id": rid, "source": src, "sanity": sanity(src)}})
        except Exception as e:
            emit({"error": f"{type(e).__name__}: {e}"})


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        text = sys.argv[2] if len(sys.argv) > 2 else sys.stdin.read()
        dtype = sys.argv[3] if len(sys.argv) > 3 else "auto"
        src = diagram([{"role": "user", "content": text}], dtype, MODEL)
        bad = sanity(src)
        if bad:
            print(f"[경고] {bad}", file=sys.stderr)
        print(src)
        sys.exit(1 if bad else 0)
    print(f"diagram local → http://localhost:{PORT}  (model={MODEL}, llm={LLM_API} {LLM_BASE})")
    ThreadingHTTPServer(("", PORT), H).serve_forever()
