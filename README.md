# sme-ax-helper

**2026년 공공 AI 대전환 챌린지 · 세션 1(자유주제)**  
중진공 AX 지원 **후속업무** Streamlit MVP — 진단·접수(**기시행**) 이후 구간.

**진단 본업은 K-Doctor**입니다. [AX 자가진단](https://kdoctor.kosmes.or.kr/aiself/ai_intro.do) 결과 보고서를 업로드하거나 같은 흐름으로 **우리 회사 AX 수준**을 확인한 뒤, 표준 RFP·업체·견적·정책으로 이어갑니다.

### 실행 순서 (상단 메뉴)
**기초체력 → 과업지시서 → 업체 → 견적 → 정책**

1. **기초체력** — 우리 회사 AX 수준 진단  
2. **과업지시서** — 설문 기반 표준 RFP/과업지시서 (16항목, 프롬프트 비공개, 한글 PDF)  
3. **업체** — AI 공급사 추천  
4. **견적** — 공급사 견적 비교  
5. **정책** — 기술자금·스마트화·지역주도형 AI 대전환 등  

시연용 예시 보고서: `samples/한빛정밀_AX자가진단_결과보고서.txt`

### 대회 규칙 정합
- 합성·비민감 데이터만 사용 · 업로드 비영구 · DB 없음  
- Solar / Gemini **모델 교체 가능** (`src/config.py`)  
- API 키는 secrets/환경변수만 (깃 금지)

## 로컬 실행

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

## 배포

- 시연: https://sme-ai-helper.streamlit.app  
- GitHub: https://github.com/kosme-ax/sme-ax-helper  
- GitLab: https://gitlab.aigov.go.kr/kosme2512042/sme_ai_helper  
