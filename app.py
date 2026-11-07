from __future__ import annotations

import json

import streamlit as st

from src.analysis import (
    analyze_systems,
    compare_models,
    compare_quotations,
    diagnose,
    generate_work_order,
)
from src.config import MODELS, model_status, runtime_settings
from src.docs import load_sample, read_upload
from src.reports import to_docx_bytes, to_pdf_bytes
from src.sample_data import COMPANIES, sample_files
from src.ui import inject_styles, render_footer, render_hero, render_top

st.set_page_config(
    page_title="AI-Bridge | AX 과업지시서·견적비교",
    page_icon="🔵",
    layout="wide",
    initial_sidebar_state="expanded",
)

NOTICE = (
    "본 앱의 **핵심은 진단이 아닙니다.** "
    "[K-Doctor](https://kdoctor.kosmes.or.kr/main.do?v=f) 진단 결과를 연동 입력으로 받아 "
    "**AX 과업지시서**와 **견적 비교**를 작성하는 업무보조 MVP입니다. "
    "시연은 가상·합성 데이터만 사용하며, 업로드는 세션 메모리에서만 처리합니다."
)


def init_state() -> None:
    st.session_state.setdefault("company_key", "한빛정밀")
    st.session_state.setdefault("last_result", None)
    st.session_state.setdefault("last_title", "")
    st.session_state.setdefault("kdoctor_linked", False)
    settings = runtime_settings()
    st.session_state.setdefault("model_name", settings["default_model"])


def sidebar() -> str:
    with st.sidebar:
        st.markdown("### 설정")
        st.caption("핵심: 과업지시서 · 견적비교")
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

        st.markdown("#### K-Doctor 진단 기업(시연)")
        company_key = st.selectbox("연동 기업", list(COMPANIES.keys()), index=0)
        st.session_state.company_key = company_key
        company = COMPANIES[company_key]
        kd = company.get("kdoctor") or {}
        st.write(f"{company['name']} / {company['industry']} / {company['employees']}명")
        st.caption(f"진단ID `{kd.get('diagnosis_id', '-')}` · {kd.get('status', '-')}")
        st.caption(company["note"])

        default = settings["default_model"]
        st.caption(f"기본 모델 설정: {default}")
    return model_name


def company_form(company: dict, key_prefix: str) -> dict:
    st.subheader("기업 정보")
    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("기업명", company["name"], key=f"{key_prefix}_name")
        industry = st.text_input("업종", company["industry"], key=f"{key_prefix}_industry")
        employees = st.number_input(
            "인원",
            min_value=1,
            value=int(company["employees"]),
            key=f"{key_prefix}_employees",
        )
    with c2:
        main_tasks = st.text_area(
            "주요 업무", company["main_tasks"], height=80, key=f"{key_prefix}_main_tasks"
        )
        it_summary = st.text_area(
            "IT 현황", company["it_summary"], height=80, key=f"{key_prefix}_it_summary"
        )
        pain_points = st.text_area(
            "고충", company["pain_points"], height=80, key=f"{key_prefix}_pain_points"
        )
    return {
        "name": name,
        "industry": industry,
        "employees": employees,
        "main_tasks": main_tasks,
        "it_summary": it_summary,
        "pain_points": pain_points,
        "kdoctor": company.get("kdoctor") or {},
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
    safe = title.replace(" ", "_")
    b1, b2 = st.columns(2)
    b1.download_button(
        "PDF 다운로드",
        data=pdf,
        file_name=f"{title}.pdf",
        mime="application/pdf",
        key=f"dl_pdf_{safe}",
    )
    b2.download_button(
        "DOCX 다운로드",
        data=docx,
        file_name=f"{title}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        key=f"dl_docx_{safe}",
    )


def tab_work_order(model_name: str, company: dict) -> None:
    st.markdown("### 핵심① AX 지원 과업지시서")
    st.caption(
        "K-Doctor 진단 결과를 입력으로 받아, 지원사업에 바로 쓸 **과업지시서** 초안을 작성합니다. "
        "진단 재실행이 목적이 아닙니다."
    )
    kd = company.get("kdoctor") or {}
    if kd:
        st.success(
            f"연동 진단 `{kd.get('diagnosis_id')}` · {kd.get('status')} · AX수준 {kd.get('ax_level')}"
        )
        st.write(kd.get("summary", ""))
        if kd.get("priority_tasks"):
            st.markdown("**진단에서 넘긴 우선 과제**")
            for t in kd["priority_tasks"]:
                st.write(f"- {t}")

    profile = company_form(company, "wo")
    use_extra = st.checkbox("추가 진단 메모 반영(선택)", value=False, key="wo_extra")
    extra_diag = st.session_state.get("last_result") if use_extra else {"kdoctor": kd}
    if st.button("과업지시서 작성", type="primary", key="wo_run"):
        with st.spinner("과업지시서 작성 중…"):
            result = generate_work_order(model_name, profile, extra_diag)
        show_result("AX과업지시서", result)
        for key in (
            "objectives",
            "scope",
            "deliverables",
            "schedule_phases",
            "roles",
            "acceptance_criteria",
        ):
            if result.get(key):
                st.markdown(f"**{key}**")
                st.write(result[key])
        sections = result.get("sections") or {}
        if isinstance(sections, dict):
            for k, v in sections.items():
                st.markdown(f"**{k}**")
                st.write(v)


def tab_quotes(model_name: str, company: dict) -> None:
    st.markdown("### 핵심② 견적 비교")
    st.caption(
        "과업지시서 범위에 맞춰 공급사 견적을 항목·범위 적합도 중심으로 비교합니다. "
        "단가 차이만으로 부적정 단정하지 않습니다."
    )
    parts = []
    if st.checkbox("합성 견적 A/B 불러오기", value=True, key="quote_sample"):
        for key in ("견적 A", "견적 B"):
            path = sample_files()[key]
            if path.exists():
                parts.append(f"# {key}\n{load_sample(path)}")
                st.markdown(f"**{key}**")
                st.dataframe(__import__("pandas").read_csv(path), key=f"quote_df_{key}")
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


def tab_kdoctor(model_name: str, company: dict) -> None:
    st.markdown("### 입력 · K-Doctor 진단 연동")
    st.caption(
        "진단은 [K-Doctor](https://kdoctor.kosmes.or.kr/main.do?v=f)에서 수행합니다. "
        "여기서는 진단 완료 기업 데이터를 **불러와** 과업지시서·견적비교에 넘깁니다."
    )
    kd = company.get("kdoctor") or {}
    c1, c2, c3 = st.columns(3)
    c1.metric("진단ID", kd.get("diagnosis_id", "-"))
    c2.metric("상태", kd.get("status", "-"))
    c3.metric("AX 수준", kd.get("ax_level", "-"))
    st.write(kd.get("summary", ""))
    if kd.get("priority_tasks"):
        st.markdown("**우선 과제(진단 산출)**")
        for t in kd["priority_tasks"]:
            st.write(f"- {t}")

    if st.button("이 진단 결과 연동하기", type="primary", key="kd_link"):
        st.session_state.kdoctor_linked = True
        st.session_state.last_result = {
            "summary": kd.get("summary"),
            "source": "kdoctor",
            "diagnosis_id": kd.get("diagnosis_id"),
            "priority_tasks": kd.get("priority_tasks"),
            "ax_level": kd.get("ax_level"),
        }
        st.session_state.last_title = "K-Doctor연동"
        st.success("연동됨 → 상단 **과업지시서 / 견적 비교** 탭에서 이어서 작성하세요.")

    st.divider()
    st.markdown("#### (보조) 로컬 보완 진단")
    st.caption("실연동 전 시연용. 핵심 업무가 아니며, 과업지시서 보강 입력으로만 씁니다.")
    profile = company_form(company, "diag")
    use_sample = st.checkbox("합성 진단 메모 불러오기", value=True, key="diag_sample")
    extra = ""
    if use_sample:
        path = sample_files()["진단 메모"]
        if path.exists():
            extra = load_sample(path)
            st.text_area("진단 메모(미리보기)", extra, height=120, key="diag_memo_preview")
    uploaded = st.file_uploader(
        "추가 자료 업로드 (txt/pdf/docx/csv)",
        type=["txt", "pdf", "docx", "csv"],
        key="diag_up",
    )
    if uploaded:
        extra = (extra + "\n\n" + read_upload(uploaded.name, uploaded.getvalue())).strip()
    if st.button("보완 진단 실행", key="diag_run"):
        with st.spinner("보완 진단 중…"):
            result = diagnose(model_name, profile, extra)
        show_result("보완진단", result)


def tab_systems(model_name: str, company: dict) -> None:
    st.markdown("### 보조 · 기존 시스템 분석")
    st.caption("과업지시서 범위 확정을 돕는 보조 기능입니다.")
    doc_text = ""
    if st.checkbox("합성 시스템 목록 불러오기", value=True, key="sys_sample"):
        path = sample_files()["시스템 목록"]
        if path.exists():
            doc_text = load_sample(path)
            st.dataframe(__import__("pandas").read_csv(path), key="sys_sample_df")
    uploaded = st.file_uploader(
        "시스템/업무 문서",
        type=["txt", "pdf", "docx", "csv", "xlsx"],
        key="sys_up",
    )
    if uploaded:
        doc_text = read_upload(uploaded.name, uploaded.getvalue())
        st.text_area("추출 텍스트", doc_text[:4000], height=160, key="sys_extracted")
    if st.button("시스템 분석 실행", type="primary", key="sys_run"):
        if not doc_text.strip():
            st.warning("분석할 문서가 없습니다.")
        else:
            with st.spinner("분석 중…"):
                result = analyze_systems(model_name, company, doc_text)
            show_result("시스템분석", result)


def tab_compare(model_name: str, company: dict) -> None:
    st.markdown("### 모델 비교 시연")
    st.caption("동일 과업지시서/견적 질문을 모델 A·B에 넣어 교체 가능성을 보여줍니다.")
    names = list(MODELS.keys())
    a = st.selectbox("모델 A", names, index=0, key="cmp_a")
    b = st.selectbox("모델 B", names, index=min(1, len(names) - 1), key="cmp_b")
    question = st.text_input(
        "동일 질문",
        "이 기업의 AX 지원 과업지시서에 우선 넣을 과업 3가지와 검수기준을 제시하라.",
        key="cmp_q",
    )
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
            key="cmp_dl",
        )


def main() -> None:
    init_state()
    inject_styles()
    model_name = sidebar()
    company = COMPANIES[st.session_state.company_key]

    render_top()
    render_hero()

    if st.session_state.get("kdoctor_linked"):
        st.caption("✓ K-Doctor 진단 결과 연동됨 — 과업지시서·견적비교에 반영 가능")

    # 핵심 탭을 앞으로
    tabs = st.tabs(
        [
            "① 과업지시서",
            "② 견적 비교",
            "K-Doctor 연동",
            "시스템 분석",
            "모델 비교",
            "사용 안내",
        ]
    )
    with tabs[0]:
        tab_work_order(model_name, company)
    with tabs[1]:
        tab_quotes(model_name, company)
    with tabs[2]:
        tab_kdoctor(model_name, company)
    with tabs[3]:
        tab_systems(model_name, company)
    with tabs[4]:
        tab_compare(model_name, company)
    with tabs[5]:
        st.markdown(
            """
### 이 프로젝트의 위치
1. **진단** → [K-Doctor](https://kdoctor.kosmes.or.kr/main.do?v=f) (기존 중진공 서비스)
2. **과업지시서 작성** → AI-Bridge **핵심**
3. **견적 비교** → AI-Bridge **핵심**
4. 시스템 분석·모델 비교 → 보조

### 로컬 실행
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

### Streamlit Community Cloud
- 진입점: `streamlit_app.py` · App URL: `sme-ai-helper`
- Secrets에 API 키 등록

### 보안
- 실제 민감 기업자료 대신 `samples/` 가상·합성 K-Doctor 연동 데이터를 사용합니다.
- 업로드는 세션 처리만 하고 DB/영구 저장을 쓰지 않습니다.
"""
        )
    render_footer()


if __name__ == "__main__":
    main()
