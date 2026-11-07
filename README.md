# sme_ai_helper (AI-Bridge)

대전환 챌린지용 **AX 지원 후속업무** Streamlit MVP입니다.

**진단 본업은 K-Doctor**입니다. [AX 자가진단](https://kdoctor.kosmes.or.kr/aiself/ai_intro.do) **결과 보고서를 업로드**하거나, 같은 흐름의 간이 체크로 **어디에 AI를 적용할지**를 잡은 뒤, 중진공 AX 지원 문서로 이어갑니다.

### 실행 순서 (토스형 5스텝)
1. **기초체력보기** — 보고서 업로드 또는 업종→영역→문제→사업·데이터·운영 체크
2. **과업지시서 작성** — 선택한 적용 영역을 반영한 AX 과업지시서 초안
3. **업체 탐색** — 적용 영역·과업 키워드로 AI 공급사 추천
4. **견적비교** — 공급사 견적 비교
5. **정책연계** — 기술자금·스마트화·지역주도형 AI 대전환 등

시연용 예시 보고서: `samples/한빛정밀_AX자가진단_결과보고서.txt`

### 1단계 고도화 (국민제안 접점)
- **AX 자가진단형 기초체력** — 보고서 업로드 또는 매뉴얼 기반 체크 → 교육 링크
- **표준 CSV 검증** (필수 컬럼·숫자형·파일명 `기업명_사업명_문서종류`)
- 견적 CSV 표준 컬럼 검사

### 정책·공급사
- 결과 후 **정책자금·사업 추천** (`src/policies.py`)
- **AI 공급사 추천** 24개 카탈로그 (`src/vendors.py`) — 적용 영역 가중

### 보조 (더보기)
- K-Doctor 진단 결과 연동(시연: 합성 데이터)
- 기존 시스템 분석 · 모델 A/B 비교 · CSV 검증

- 웹: Streamlit
- AI: 상용 LLM API 2종 (Solar / Gemini) — `src/config.py`의 `MODELS`로 교체
- 문서: PDF·DOCX·CSV·XLSX·TXT
- 데이터: K-Doctor 진단 완료를 가정한 가상 기업 (`samples/` + `COMPANIES.kdoctor`)
- DB 없음, 업로드 비영구 처리
- GitLab: https://gitlab.aigov.go.kr/kosme2512042/sme_ai_helper

## 로컬 실행

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env 에 SOLAR_API_KEY / GEMINI_API_KEY 입력
streamlit run app.py
```

브라우저: http://localhost:8501

키가 없으면 해당 모델은 Mock으로 시연됩니다.

## 배포

### Streamlit Community Cloud (권장)

- 앱 URL: https://sme-ai-helper.streamlit.app
- 진입점: `streamlit_app.py` (또는 `app.py`)
- GitHub: https://github.com/kosme-ax/ai-bridge
- Secrets에 `SOLAR_API_KEY` 등 등록 (`.streamlit/secrets.toml.example` 참고)

도메인에 밑줄(`_`)은 쓸 수 없어 `sme_ai_helper` → `sme-ai-helper` 로 배포합니다.

### GitLab

- 코드 호스팅: https://gitlab.aigov.go.kr/kosme2512042/sme_ai_helper
- CI: SAST + Secret Detection + 앱 스모크 테스트 (`.gitlab-ci.yml`)
- **GitLab Pages는 정적 호스팅이라 Streamlit에 부적합**
- 실행 URL은 Streamlit Cloud를 사용합니다.

## 보안 원칙 (대회)

- API 키는 서버 secrets / 환경변수만 (깃에 올리지 않음)
- 실제 민감 기업자료 금지 → `samples/` 가상 데이터
- 파일 영구 저장·DB 없음
