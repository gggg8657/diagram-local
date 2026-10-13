# 제3자 구성요소 (Third-party notices) — diagram-local

조사일 2026-10-12. 실제 파일(`static/`, `setup.sh`, `app.py` import, `ui.html`) 기준. 라이선스는 각 프로젝트의 LICENSE / npm·PyPI 메타데이터 / 모델 카드에서 확인했다.
이 표는 고지용 정리이며 법률 자문이 아니다. 상업 이용 전에는 원문을 다시 확인할 것.

## 동봉 (저장소에 들어 있음)

| 이름 | 버전 | 쓰임 | 라이선스 | 링크 | 상업 이용 | 비고 |
|---|---|---|---|---|---|---|
| mermaid | 11.17.2 | 동봉 `static/mermaid.min.js` (브라우저에서 다이어그램 렌더) | MIT | https://github.com/mermaid-js/mermaid | 가능 | 원문 `licenses/mermaid-LICENSE.txt`. 수정하지 않은 배포본 |
| └ mermaid 번들 안의 의존성 | mermaid 11.17.2 기준 | 위 파일 안에 함께 번들됨 | d3 (ISC), d3-sankey (BSD-3-Clause), dagre-d3-es · cytoscape · cytoscape-cose-bilkent · cytoscape-fcose · katex · khroma · marked · roughjs · stylis · dayjs · uuid · es-toolkit · lodash-es · langium · @mermaid-js/parser · @iconify/utils · @braintree/sanitize-url · @upsetjs/venn.js · ts-dedent · fastdom (MIT), chevrotain (Apache-2.0), DOMPurify (MPL-2.0 OR Apache-2.0) | https://www.npmjs.com/package/mermaid | 가능 | `npm view` 로 확인. DOMPurify 원문 `licenses/dompurify-LICENSE.txt`(Apache-2.0 선택) |

## 실행 환경 (동봉 안 함)

| 이름 | 버전 | 쓰임 | 라이선스 | 링크 | 상업 이용 | 비고 |
|---|---|---|---|---|---|---|
| Python 표준 라이브러리 | 3.9+ | 서버(`app.py`) — 외부 pip 패키지 없음 | PSF-2.0 | https://docs.python.org/3/license.html | 가능 | |
| Ollama | 설치 시점 최신 | `setup.sh` 가 없으면 설치(`ollama.com/install.sh`) — LLM 실행기 | MIT | https://github.com/ollama/ollama | 가능 | 다른 OpenAI 호환 서버(vLLM 등)로 바꿔도 됨 |

## 모델 가중치 (저장소에 없음 — 사용자가 내려받음)

| 이름 | 쓰임 | 라이선스 | 링크 | 상업 이용 | 비고 |
|---|---|---|---|---|---|
| Qwen3-8B (`qwen3:8b`) | `setup.sh` 기본 pull 모델(Ollama 에 모델이 없을 때) | Apache-2.0 | https://huggingface.co/Qwen/Qwen3-8B | 가능 | `MODEL=` 로 변경 |
| Gemma 4 31B (`gemma4:31b`) | 포털 배포 기본 모델 | Apache-2.0 | https://ai.google.dev/gemma/docs/gemma_4_license | 가능 | 모델 카드 `google/gemma-4-31B-it` license 필드 확인 |

## 확인 필요

없음 (2026-10-12 조사 기준). 다른 모델을 `MODEL=`/`LLM_MODEL=` 로 지정하면 그 모델의 라이선스를 따로 확인할 것.

## 이 저장소의 원저작물

`app.py`, `ui.html`, `goal-prompt.md`, `selftest.py`, `setup.sh`, `README.md` — DongJu Kim (gggg8657), PolyForm Noncommercial 1.0.0 (`LICENSE`).
