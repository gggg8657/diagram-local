# diagram-local — 말로 설명하면 다이어그램 (Mermaid · 로컬 LLM)

> **한 줄 요약** — "결재 절차 그려줘"처럼 한국어로 설명하면 로컬 LLM이 Mermaid 소스를 쓰고 브라우저가 바로 그림으로 그려 주는 도구입니다.
> 순서도·시퀀스·조직도·간트·마인드맵·ER 등 9종, SVG/PNG 내려받기, "단계 하나 더 넣어줘" 식 다듬기, 파싱 오류 자동 수정 1회.
> 파이썬 표준 라이브러리만 쓰고 mermaid.js(MIT)를 폴더에 동봉해 CDN·외부 통신이 없습니다. 폴더 복사만으로 폐쇄망 배포, LLM은 Ollama/vLLM 환경변수로 지정.
> 보고서 삽도·시스템 구성도·과제 일정표 초안을 1분 안에 뽑는 용도입니다.

```bash
bash setup.sh                 # OS 감지 → Python → LLM 서버 탐색(없으면 Ollama 설치) → selftest → http://localhost:8768
bash setup.sh stop
python3 app.py                # 수동 실행
python3 app.py --cli "시료 채취 → 전처리 → 측정 → 보고서 순서" flowchart   # Mermaid 소스를 stdout에
python3 selftest.py           # LLM 없이 검증
```

| 환경변수 | 기본 | 설명 |
|---|---|---|
| `LLM_API` | `ollama` | `ollama` 또는 `openai`(vLLM·LM Studio·llama.cpp) |
| `LLM_BASE_URL` | `http://localhost:11434` / `http://localhost:8000/v1` | 서버 주소 |
| `LLM_MODEL` | `qwen3:8b` | UI에서 변경 가능 |
| `LLM_API_KEY` | (없음) | OpenAI 호환 서버 키 |
| `NUM_CTX` | `16384` | Ollama 컨텍스트 |
| `PORT` | `8768` | |

흐름: 설명 → `goal-prompt.md`(출력 계약: Mermaid만, 한글 라벨은 따옴표, 노드 id 영문) → LLM 1콜 → 서버 1차 검사(선언·괄호·따옴표) → 브라우저 mermaid 렌더 → 파싱 오류면 `/api/repair` 로 LLM 수정 1회.
다듬기 요청은 현재 소스를 함께 보내 전체 소스를 다시 받습니다. 결과는 `_workspace/<id>.json`.

폐쇄망: 이 폴더를 통째로 복사하면 끝 (`static/mermaid.min.js` 포함). 외부 통신은 LLM 서버 주소뿐.

## 출처·감사 (Credits)

- 동봉: [mermaid](https://github.com/mermaid-js/mermaid) 11.17.2 (`static/mermaid.min.js`, MIT, Copyright (c) 2014-2025 Knut Sveidqvist)
- **LLM 실행** — OpenAI 호환 API 로 호출합니다(모델 가중치는 동봉하지 않음). 기본 배포는 [Ollama](https://github.com/ollama/ollama) (MIT) 위의 Google [Gemma](https://ai.google.dev/gemma) `gemma4:31b` — 모델 이용 조건은 Gemma 배포처 참고.
- 이 도구는 [agent-page-portal](https://github.com/gggg8657/agent-page-portal) 에 연결해 쓰도록 만들었습니다(단독 실행도 됨).

저작권 표기·전체 목록은 `NOTICE` 를 보세요.
