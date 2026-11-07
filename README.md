# sme_ai_helper (AI-Bridge)

대전환 챌린지용 **중소기업 AX 도입 도우미** Streamlit MVP입니다.

- 웹: Streamlit
- AI: 상용 LLM API 2종 (Solar / Gemini) — `src/config.py`의 `MODELS`로 교체
- 문서: PDF·DOCX·CSV·XLSX·TXT
- 데이터: 가상·합성 기업 샘플 (`samples/`)
- DB 없음, 업로드 비영구 처리
- GitLab: https://gitlab.aigov.go.kr/kosme2512042/sme_ai_helper

## 시연 기능

1. 기업 AI 도입 진단
2. 기존 시스템 분석
3. RFP 자동 생성
4. 견적 비교 분석
5. 동일 입력 모델 A/B 비교

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

1. 이 저장소를 Streamlit Cloud에 연결 (`app.py`)
2. Secrets에 API 키 등록 (`.streamlit/secrets.toml.example` 참고)

### GitLab

- 코드 호스팅: 이 프로젝트
- CI: SAST + Secret Detection + 앱 스모크 테스트 (`.gitlab-ci.yml`)
- **GitLab Pages는 정적 호스팅이라 Streamlit에 부적합**
- 선택지: Streamlit Cloud, 또는 Docker 이미지 수동 배포

## 보안 원칙 (대회)

- API 키는 서버 secrets / 환경변수만 (깃에 올리지 않음)
- 실제 민감 기업자료 금지 → `samples/` 가상 데이터
- 파일 영구 저장·DB 없음
