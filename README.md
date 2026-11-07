# sme_ai_helper (AI-Bridge)

대전환 챌린지용 **AX 지원 후속업무** Streamlit MVP입니다.

**진단은 하지 않습니다.** [K-Doctor](https://kdoctor.kosmes.or.kr/main.do?v=f)에서 끝난 기업진단 데이터를 연동 입력으로 받아, 중진공 AX 지원에 필요한 문서를 만듭니다.

### 핵심
1. **AX 과업지시서 작성**
2. **공급사 견적 비교**

### 1단계 고도화 (국민제안 접점)
- **Data Fitness 자가진단** (8문항) → 등급·연수원/K-Doctor 교육 링크
- **표준 CSV 검증** (필수 컬럼·숫자형·파일명 `기업명_사업명_문서종류`)
- 견적 CSV 표준 컬럼 검사

### 정책 킥 (중진공 연계)
- 기초체력·과업지시서·견적 결과 후 **정책자금·사업 추천**
- 기술자금(개발기술사업화), 제조현장스마트화, 지역주도형 AI 대전환, K-Doctor, 연수 안내
- 개요·일정·신청방법·담당/문의·바로가기 (`src/policies.py`)

### 보조
- K-Doctor 진단 결과 연동(시연: 합성 데이터)
- 기존 시스템 분석
- 모델 A/B 비교

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
