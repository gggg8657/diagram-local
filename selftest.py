#!/usr/bin/env python3
"""LLM 없이 검증: 유형 힌트 주입 → 정리(코드펜스·think 제거) → 서버 측 sanity → repair 경로 → CLI → ui.html 로컬 자산만.
python3 selftest.py"""
import os, re, subprocess, sys
import app

GOOD = 'flowchart TD\n  A["연구원 기안"] --> B["팀장 검토"]\n  B --> C{"금액 1천만원 이상?"}\n  C -->|"예"| D["원장 결재"]\n  C -->|"아니오"| E["부서장 승인"]'
BAD = 'flowchart TD\n  A["연구원 기안" --> B["팀장 검토"]'   # 괄호 불일치
seen = []
def fake(system, messages, model, on_token=None):
    seen.append(messages)
    out = FAKE
    if on_token: on_token(out)
    return out
app.ollama = fake

# 1) 코드펜스·think 가 벗겨지고, 유형 힌트가 마지막 user 메시지에 붙는다
FAKE = "<think>생각</think>```mermaid\n" + GOOD + "\n```"
src = app.diagram([{"role": "user", "content": "결재 절차"}], "flowchart")
assert src == GOOD, src
assert "[유형] flowchart TD" in seen[-1][-1]["content"] and app.sanity(src) is None
# auto 는 힌트 없음
app.diagram([{"role": "user", "content": "x"}], "auto"); assert "[유형]" not in seen[-1][-1]["content"]

# 2) sanity 가 깨진 소스를 잡고, repair 가 고친 소스를 돌려준다
assert app.sanity(BAD) and "괄호" in app.sanity(BAD)
assert app.sanity("안녕하세요 다이어그램입니다") and "선언" in app.sanity("안녕하세요 다이어그램입니다")
FAKE = GOOD
fixed = app.repair(BAD, "Parse error on line 2")
assert fixed == GOOD and "[파싱 오류]" in seen[-1][-1]["content"] and BAD in seen[-1][-1]["content"]

# 3) 저장·목록
rid = app.save([{"role": "user", "content": "결재 절차"}, {"role": "assistant", "content": GOOD}], "flowchart", GOOD, "fake")
assert app.list_runs()[0]["id"] == rid and app.list_runs()[0]["head"] == "결재 절차"

# 4) CLI (LLM 없이 실행하면 연결 실패 → exit 1 이어야 하고, 스택트레이스가 아닌 에러로 끝나지 않아도 됨) — 여기선 --help 성격만: 모듈 임포트 확인
r = subprocess.run([sys.executable, "-c", "import app; print(app.TYPES['gantt'])"], capture_output=True, text=True, cwd=app.ROOT)
assert r.stdout.strip() == "gantt", r

# 5) ui.html 은 로컬 자산만 참조 (폐쇄망)
ui = app.read(os.path.join(app.ROOT, "ui.html"))
assert not re.search(r'<(script|link)[^>]+(src|href)="https?://', ui), "외부 CDN 참조 있음"
assert os.path.exists(os.path.join(app.ROOT, "static", "mermaid.min.js"))
# 저작권 표기: 서버가 화면에 붙이는 코드가 있어야 한다 (LICENSE·NOTICE)
_src = open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "app.py"), encoding="utf-8").read()
assert "wqkgMjAyNiDquYDrj5nso7wgwrcgZG9uZ2p1a2ltLmRldkBnbWFpbC5jb20=" in _src and "signed(" in _src and "X-Author" in _src, "저작권 표기 누락"

print("selftest OK")
