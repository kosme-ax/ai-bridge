from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from src.analysis import analyze_systems, compare_models, compare_quotations, diagnose, generate_rfp
from src.config import MODELS, model_status, runtime_settings
from src.docs import load_sample, read_upload
from src.reports import to_docx_bytes, to_pdf_bytes
from src.sample_data import COMPANIES, sample_files

st.set_page_config(
    page_title="AI-Bridge | 중소기업 AX 도입 도우미",
    layout="wide",
)

NOTICE = (
    "본 앱은 대회 시연용입니다. 실제 기업의 민감 자료 대신 **가상·합성 데이터**만 사용하십시오. "
    "업로드 파일은 세션 메모리에서만 처리하며 영구 저장하지 않습니다. "
    "API 키는 서버 secrets/환경변수에만 두십시오."
)


def init_state() -> None:
    st.session_state.setdefault("company_key", "한빛정밀")
    st.session_state.setdefault("last_result", None)
    st.session_state.setdefault("last_title", "")
    settings = runtime_settings()
    st.session_state.setdefault("model_name", settings["default_model"])


def sidebar() -> str:
    with st.sidebar:
        st.markdown("### AI-Bridge")
        st.caption("공공 기업지원 · AX 도입 업무보조 MVP")
        st.info(NOTICE)

        settings = runtime_settings()
        model_name = st.selectbox(
            "분석 모델",
            options=list(MODELS.keys()),
            index=list(MODELS.keys()).index(st.session_state.model_name)
            if st.session_state.model_name in MODELS
            else 0,
            help="모델 이름은 설정(MODELS)으로만 관리합니다.",
        )
        st.session_state.model_name = model_name

        st.markdown("#### 모델 상태")
        for name in MODELS:
            status = model_status(name)
            badge = "🟢 live" if status["live"] else "🟡 mock"
            st.write(f"**{name}** · {status['model']} · {badge}")

        st.markdown("#### 가상 기업")
        company_key = st.selectbox("시연 기업", list(COMPANIES.keys()), index=0)
        st.session_state.company_key = company_key
        company = COMPANIES[company_key]
        st.write(f"{company['name']} / {company['industry']} / {company['employees']}명")
        st.caption(company["note"])

        default = settings["default_model"]
        st.caption(f"기본 모델 설정: {default}")
    return model_name


def company_form(company: dict) -> dict:
    st.subheader("기업 정보")
    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("기업명", company["name"])
        industry = st.text_input("업종", company["industry"])
        employees = st.number_input("인원", min_value=1, value=int(company["employees"]))
    with c2:
        main_tasks = st.text_area("주요 업무", company["main_tasks"], height=80)
        it_summary = st.text_area("IT 현황", company["it_summary"], height=80)
        pain_points = st.text_area("고충", company["pain_points"], height=80)
    return {
        "name": name,
        "industry": industry,
        "employees": employees,
        "main_tasks": main_tasks,
        "it_summary": it_summary,
        "pain_points": pain_points,
    }


def show_result(title: str, result: dict) -> None:
    st.session_state.last_title = title
    st.session_state.last_result = result
    meta = result.get("_meta") or {}
    st.success(f"{title} 완료 · 모델 `{meta.get('model_name')}` · 모드 `{meta.get('mode')}`")
    if result.get("summary"):
        st.markdown("#### 요약")
        st.write(result["summary"])
    with st.expander("전체 JSON", expanded=False):
        st.json({k: v for k, v in result.items() if k != "_meta"})
    pdf = to_pdf_bytes(title, result)
    docx = to_docx_bytes(title, result)
    b1, b2 = st.columns(2)
    b1.download_button("PDF 다운로드", data=pdf, file_name=f"{title}.pdf", mime="application/pdf")
    b2.download_button(
        "DOCX 다운로드",
        data=docx,
        file_name=f"{title}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


def tab_diagnosis(model_name: str, company: dict) -> None:
    st.markdown("### 1. 기업 AI 도입 진단")
    st.caption("기업정보를 바탕으로 맞춤형 도입 과제를 도출합니다.")
    profile = company_form(company)
    use_sample = st.checkbox("합성 진단 메모 불러오기", value=True)
    extra = ""
    if use_sample:
        path = sample_files()["진단 메모"]
        if path.exists():
            extra = load_sample(path)
            st.text_area("진단 메모(미리보기)", extra, height=120)
    uploaded = st.file_uploader("추가 자료 업로드 (txt/pdf/docx/csv)", type=["txt", "pdf", "docx", "csv"], key="diag_up")
    if uploaded:
        extra = (extra + "\n\n" + read_upload(uploaded.name, uploaded.getvalue())).strip()
    if st.button("진단 실행", type="primary", key="diag_run"):
        with st.spinner("진단 중…"):
            result = diagnose(model_name, profile, extra)
        show_result("AX도입진단", result)


def tab_systems(model_name: str, company: dict) -> None:
    st.markdown("### 2. 기존 시스템 분석")
    st.caption("기존 문서 업로드 및 현황 분석")
    doc_text = ""
    if st.checkbox("합성 시스템 목록 불러오기", value=True):
        path = sample_files()["시스템 목록"]
        if path.exists():
            doc_text = load_sample(path)
            st.dataframe(__import__("pandas").read_csv(path))
    uploaded = st.file_uploader("시스템/업무 문서", type=["txt", "pdf", "docx", "csv", "xlsx"], key="sys_up")
    if uploaded:
        doc_text = read_upload(uploaded.name, uploaded.getvalue())
        st.text_area("추출 텍스트", doc_text[:4000], height=160)
    if st.button("시스템 분석 실행", type="primary", key="sys_run"):
        if not doc_text.strip():
            st.warning("분석할 문서가 없습니다.")
        else:
            with st.spinner("분석 중…"):
                result = analyze_systems(model_name, company, doc_text)
            show_result("시스템분석", result)


def tab_rfp(model_name: str, company: dict) -> None:
    st.markdown("### 3. RFP 자동 생성")
    st.caption("AI 도입 요구사항과 제안요청서 초안")
    profile = company_form(company)
    if st.button("RFP 초안 생성", type="primary", key="rfp_run"):
        with st.spinner("RFP 작성 중…"):
            result = generate_rfp(model_name, profile, st.session_state.get("last_result"))
        show_result("RFP초안", result)
        sections = result.get("sections") or {}
        if isinstance(sections, dict):
            for k, v in sections.items():
                st.markdown(f"**{k}**")
                st.write(v)


def tab_quotes(model_name: str, company: dict) -> None:
    st.markdown("### 4. 견적 비교 분석")
    st.caption("견적서 항목 분류 및 비용 검토 (단가 차이 ≠ 부적정)")
    parts = []
    if st.checkbox("합성 견적 A/B 불러오기", value=True):
        for key in ("견적 A", "견적 B"):
            path = sample_files()[key]
            if path.exists():
                parts.append(f"# {key}\n{load_sample(path)}")
                st.markdown(f"**{key}**")
                st.dataframe(__import__("pandas").read_csv(path))
    uploads = st.file_uploader(
        "견적 파일 (복수 가능)",
        type=["txt", "csv", "xlsx", "pdf", "docx"],
        accept_multiple_files=True,
        key="quote_up",
    )
    for f in uploads or []:
        parts.append(f"# {f.name}\n{read_upload(f.name, f.getvalue())}")
    quote_text = "\n\n".join(parts)
    if st.button("견적 비교 실행", type="primary", key="quote_run"):
        if not quote_text.strip():
            st.warning("견적 자료가 없습니다.")
        else:
            with st.spinner("비교 중…"):
                result = compare_quotations(model_name, company, quote_text)
            show_result("견적비교", result)


def tab_compare(model_name: str, company: dict) -> None:
    st.markdown("### 모델 비교 시연")
    st.caption("동일 자료를 모델 A·B에 각각 분석시켜 교체가 실제로 작동함을 보여줍니다.")
    names = list(MODELS.keys())
    a = st.selectbox("모델 A", names, index=0, key="cmp_a")
    b = st.selectbox("모델 B", names, index=min(1, len(names) - 1), key="cmp_b")
    question = st.text_input("동일 질문", "이 기업의 우선 AX 과제는 무엇인가? 근거와 위험을 포함해 답하라.")
    if st.button("두 모델 동시 분석", type="primary", key="cmp_run"):
        with st.spinner("비교 분석 중…"):
            result = compare_models(a, b, company, question)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"#### {result['model_a']['name']}")
            st.write((result["model_a"]["result"] or {}).get("summary") or result["model_a"]["result"])
            st.caption((result["model_a"]["result"].get("_meta") or {}).get("mode"))
        with c2:
            st.markdown(f"#### {result['model_b']['name']}")
            st.write((result["model_b"]["result"] or {}).get("summary") or result["model_b"]["result"])
            st.caption((result["model_b"]["result"].get("_meta") or {}).get("mode"))
        st.info(result["note"])
        st.download_button(
            "비교 결과 JSON",
            data=json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="model_compare.json",
            mime="application/json",
        )


def main() -> None:
    init_state()
    model_name = sidebar()
    company = COMPANIES[st.session_state.company_key]

    st.title("AI-Bridge")
    st.markdown("중소기업 **AX(AI 전환) 도입**을 위한 공공 기업지원 업무보조 MVP")
    st.caption("Streamlit · 상용 LLM API 2종 · 가상 기업 시연 · 파일 비영구 처리")

    tabs = st.tabs(["진단", "시스템 분석", "RFP", "견적 비교", "모델 비교", "사용 안내"])
    with tabs[0]:
        tab_diagnosis(model_name, company)
    with tabs[1]:
        tab_systems(model_name, company)
    with tabs[2]:
        tab_rfp(model_name, company)
    with tabs[3]:
        tab_quotes(model_name, company)
    with tabs[4]:
        tab_compare(model_name, company)
    with tabs[5]:
        st.markdown(
            """
### 로컬 실행
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # SOLAR_API_KEY / GEMINI_API_KEY
streamlit run app.py
```

### Streamlit Community Cloud
1. 이 저장소를 GitHub/GitLab에 푸시
2. Streamlit Cloud에서 앱 생성 → `app.py`
3. Secrets에 API 키 등록 (`.streamlit/secrets.toml.example` 참고)

### GitLab
- 소스는 GitLab에 올립니다.
- Streamlit Community Cloud는 GitHub 연동이 가장 단순합니다. GitLab만 쓰면 CI로 컨테이너 배포하거나 GitHub 미러를 쓰십시오.
- **GitLab Pages는 정적 호스팅이라 이 Streamlit 앱에 적합하지 않습니다.**

### 보안
- API 키는 브라우저/프론트에 넣지 않습니다.
- 실제 민감 기업자료 대신 `samples/` 가상 데이터를 사용합니다.
- 업로드는 세션 처리만 하고 DB/영구 저장을 쓰지 않습니다.
"""
        )


if __name__ == "__main__":
    main()
