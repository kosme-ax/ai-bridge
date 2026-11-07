# AI-Bridge

대전환 챌린지용 **중소기업 AX 도입 도우미** MVP입니다.

- 웹: Streamlit
- AI: 상용 LLM API 2종 (Solar / Gemini) — 설정으로 교체
- 문서: PDF·DOCX·CSV·XLSX·TXT
- 데이터: 가상·합성 기업 샘플만 사용
- DB 없음, 업로드 비영구 처리

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

## 모델 설정

`src/config.py`의 `MODELS`만 수정하면 UI·분석 코드를 다시 짤 필요가 없습니다.

```python
MODELS = {
    "Solar": {"provider": "upstage", "model": "solar-pro4", ...},
    "Gemini": {"provider": "google", "model": "gemini-2.0-flash", ...},
}
```

## 배포

### Streamlit Community Cloud (권장)

1. 저장소 푸시 (GitHub 연동이 가장 단순)
2. [share.streamlit.io](https://share.streamlit.io)에서 `app.py` 지정
3. Secrets에 API 키 등록 (`.streamlit/secrets.toml.example` 참고)

### GitLab

- 코드 호스팅: GitLab
- **GitLab Pages는 정적 사이트용이라 Streamlit에 부적합**
- 선택지: (1) GitHub 미러 후 Streamlit Cloud (2) GitLab CI + 컨테이너 호스팅

`/.gitlab-ci.yml`에 린트·패키지 검사 파이프라인을 포함했습니다.

## 보안 원칙 (대회)

- API 키는 서버 secrets / 환경변수만
- 실제 민감 기업자료 금지 → `samples/` 가상 데이터
- 파일 영구 저장·DB 없음
