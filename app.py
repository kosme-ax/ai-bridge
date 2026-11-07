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
from src.ui import inject_styles, page_header, render_footer, soft_card

st.set_page_config(
    page_title="AI-Bridge",
    page_icon="💠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

PAGES = ("과업지시서", "견적 비교", "더보기")


def init_state() -> None:
    st.session_state.setdefault("company_key", "한빛정밀")
    st.session_state.setdefault("last_result", None)
    st.session_state.setdefault("last_title", "")
    st.session_state.setdefault("page", "과업지시서")
    settings = runtime_settings()
    st.session_state.setdefault("model_name", settings["default_model"])


def sidebar() -> tuple[str, dict]:
    with st.sidebar:
        st.markdown("**AI-Bridge**")
        st.caption("AX 지원 문서 도우미")

        company_key = st.selectbox("기업", list(COMPANIES.keys()), label_visibility="collapsed")
        st.session_state.company_key = company_key
        company = COMPANIES[company_key]
        kd = company.get("kdoctor") or {}
        st.caption(f"{company['name']} · {kd.get('status', '')}")

        model_name = st.selectbox(
            "모델",
            options=list(MODELS.keys()),
            index=list(MODELS.keys()).index(st.session_state.model_name)
            if st.session_state.model_name in MODELS
            else 0,
        )
        st.session_state.model_name = model_name
        status = model_status(model_name)
        st.caption(("live" if status["live"] else "mock") + f" · {status['model']}")

        with st.expander("안내"):
            st.write(
                "진단은 K-Doctor에서 합니다. 여기서는 과업지시서와 견적 비교가 핵심입니다. "
                "시연은 합성 데이터만 사용합니다."
            )
    return model_name, company


def company_form(company: dict, key_prefix: str) -> dict:
    name = st.text_input("기업명", company["name"], key=f"{key_prefix}_name")
    industry = st.text_input("업종", company["industry"], key=f"{key_prefix}_industry")
    employees = st.number_input(
        "인원",
        min_value=1,
        value=int(company["employees"]),
        key=f"{key_prefix}_employees",
    )
    with st.expander("상세 정보", expanded=False):
        main_tasks = st.text_area(
            "주요 업무", company["main_tasks"], height=70, key=f"{key_prefix}_main_tasks"
        )
        it_summary = st.text_area(
            "IT 현황", company["it_summary"], height=70, key=f"{key_prefix}_it_summary"
        )
        pain_points = st.text_area(
            "고충", company["pain_points"], height=70, key=f"{key_prefix}_pain_points"
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
    st.success(f"완료 · {meta.get('model_name')} · {meta.get('mode')}")
    if result.get("summary"):
        st.write(result["summary"])
    with st.expander("전체 결과"):
        st.json({k: v for k, v in result.items() if k != "_meta"})
    pdf = to_pdf_bytes(title, result)
    docx = to_docx_bytes(title, result)
    safe = title.replace(" ", "_")
    b1, b2 = st.columns(2)
    b1.download_button(
        "PDF",
        data=pdf,
        file_name=f"{title}.pdf",
        mime="application/pdf",
        key=f"dl_pdf_{safe}",
        use_container_width=True,
    )
    b2.download_button(
        "DOCX",
        data=docx,
        file_name=f"{title}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        key=f"dl_docx_{safe}",
        use_container_width=True,
    )


def page_work_order(model_name: str, company: dict) -> None:
    page_header(
        "핵심 기능",
        "과업지시서를<br>바로 작성해요",
        "K-Doctor 진단을 바탕으로 AX 지원 과업지시서 초안을 만듭니다.",
    )
    kd = company.get("kdoctor") or {}
    soft_card(
        kd.get("diagnosis_id", "진단 연동"),
        kd.get("summary", "연동된 진단 요약이 없습니다."),
    )
    profile = company_form(company, "wo")
    st.write("")
    if st.button("과업지시서 만들기", type="primary", use_container_width=True, key="wo_run"):
        with st.spinner("작성 중…"):
            result = generate_work_order(
                model_name,
                profile,
                {"kdoctor": kd, **(st.session_state.get("last_result") or {})},
            )
        show_result("AX과업지시서", result)


def page_quotes(model_name: str, company: dict) -> None:
    page_header(
        "핵심 기능",
        "견적을<br>비교해요",
        "과업 범위에 맞춰 공급사 견적을 정리합니다. 단가 차이만으로 판단하지 않아요.",
    )
    parts = []
    use_sample = st.toggle("샘플 견적 사용", value=True, key="quote_sample")
    if use_sample:
        for key in ("견적 A", "견적 B"):
            path = sample_files()[key]
            if path.exists():
                parts.append(f"# {key}\n{load_sample(path)}")
        soft_card("샘플 견적 A / B", "합성 데이터로 비교 흐름만 보여줍니다.")
    else:
        uploads = st.file_uploader(
            "견적 파일",
            type=["txt", "csv", "xlsx", "pdf", "docx"],
            accept_multiple_files=True,
            key="quote_up",
        )
        for f in uploads or []:
            parts.append(f"# {f.name}\n{read_upload(f.name, f.getvalue())}")

    st.write("")
    if st.button("비교하기", type="primary", use_container_width=True, key="quote_run"):
        quote_text = "\n\n".join(parts)
        if not quote_text.strip():
            st.warning("견적 자료를 넣어 주세요.")
        else:
            with st.spinner("비교 중…"):
                result = compare_quotations(model_name, company, quote_text)
            show_result("견적비교", result)


def page_more(model_name: str, company: dict) -> None:
    page_header(
        "부가 기능",
        "필요할 때만<br>꺼내 쓰세요",
        "진단 연동 보완, 시스템 분석, 모델 비교는 여기 모아 두었습니다.",
    )

    choice = st.radio(
        "선택",
        ("K-Doctor 연동", "시스템 분석", "모델 비교"),
        horizontal=True,
        label_visibility="collapsed",
        key="more_choice",
    )

    if choice == "K-Doctor 연동":
        kd = company.get("kdoctor") or {}
        soft_card(str(kd.get("diagnosis_id", "-")), kd.get("summary", ""))
        if st.button("이 결과 불러오기", type="primary", use_container_width=True, key="kd_link"):
            st.session_state.last_result = {
                "summary": kd.get("summary"),
                "source": "kdoctor",
                "diagnosis_id": kd.get("diagnosis_id"),
                "priority_tasks": kd.get("priority_tasks"),
                "ax_level": kd.get("ax_level"),
            }
            st.success("불러왔어요. 과업지시서 화면으로 이동해 작성하세요.")
            st.session_state.page = "과업지시서"
            st.rerun()

        with st.expander("보완 진단(선택)"):
            profile = company_form(company, "diag")
            if st.checkbox("합성 메모 사용", value=True, key="diag_sample"):
                path = sample_files()["진단 메모"]
                extra = load_sample(path) if path.exists() else ""
            else:
                extra = ""
            if st.button("보완 진단 실행", key="diag_run", use_container_width=True):
                with st.spinner("실행 중…"):
                    result = diagnose(model_name, profile, extra)
                show_result("보완진단", result)

    elif choice == "시스템 분석":
        soft_card("시스템 현황", "과업 범위를 정할 때 참고하는 보조 기능입니다.")
        doc_text = ""
        if st.toggle("샘플 목록 사용", value=True, key="sys_sample"):
            path = sample_files()["시스템 목록"]
            if path.exists():
                doc_text = load_sample(path)
        else:
            uploaded = st.file_uploader(
                "문서",
                type=["txt", "pdf", "docx", "csv", "xlsx"],
                key="sys_up",
            )
            if uploaded:
                doc_text = read_upload(uploaded.name, uploaded.getvalue())
        if st.button("분석하기", type="primary", use_container_width=True, key="sys_run"):
            if not doc_text.strip():
                st.warning("문서가 없습니다.")
            else:
                with st.spinner("분석 중…"):
                    result = analyze_systems(model_name, company, doc_text)
                show_result("시스템분석", result)

    else:
        soft_card("모델 비교", "같은 질문에 두 모델을 동시에 돌려 교체 가능성을 확인합니다.")
        names = list(MODELS.keys())
        a = st.selectbox("모델 A", names, index=0, key="cmp_a")
        b = st.selectbox("모델 B", names, index=min(1, len(names) - 1), key="cmp_b")
        question = st.text_input(
            "질문",
            "우선 과업 3가지와 검수기준을 제시해 주세요.",
            key="cmp_q",
        )
        if st.button("비교 실행", type="primary", use_container_width=True, key="cmp_run"):
            with st.spinner("비교 중…"):
                result = compare_models(a, b, company, question)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**{result['model_a']['name']}**")
                st.write((result["model_a"]["result"] or {}).get("summary"))
            with c2:
                st.markdown(f"**{result['model_b']['name']}**")
                st.write((result["model_b"]["result"] or {}).get("summary"))
            st.download_button(
                "JSON 저장",
                data=json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"),
                file_name="model_compare.json",
                mime="application/json",
                key="cmp_dl",
                use_container_width=True,
            )


def main() -> None:
    init_state()
    inject_styles()
    model_name, company = sidebar()

    page = st.radio(
        "메뉴",
        PAGES,
        horizontal=True,
        label_visibility="collapsed",
        key="page",
    )

    if page == "과업지시서":
        page_work_order(model_name, company)
    elif page == "견적 비교":
        page_quotes(model_name, company)
    else:
        page_more(model_name, company)

    render_footer()


if __name__ == "__main__":
    main()
