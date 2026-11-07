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
from src.csv_validate import validate_company_metrics
from src.docs import load_sample, read_upload
from src.fitness import (
    AI_AREAS,
    INDUSTRIES,
    KDOCTOR_AX_INTRO,
    LIKERT_QUESTIONS,
    TOTAL_QUIZ_STEPS,
    fitness_from_report,
    likert_at,
    problems_for_areas,
    score_fitness,
)
from src.policies import POLICIES, recommend_policies
from src.reports import to_docx_bytes, to_pdf_bytes
from src.sample_data import COMPANIES, sample_files
from src.ui import inject_styles, page_header, policy_card, render_footer, soft_card, vendor_card
from src.vendors import VENDORS, recommend_vendors

st.set_page_config(
    page_title="AI-Bridge",
    page_icon="💠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# 상단 메뉴 = 단계 이동. 화면 안 다음/이전 CTA는 두지 않음.
STEPS = ("기초체력", "과업지시서", "업체", "견적", "정책")
PAGES = STEPS + ("더보기",)

_PAGE_ALIASES = {
    "기초체력보기": "기초체력",
    "과업지시서 작성": "과업지시서",
    "업체 탐색": "업체",
    "견적비교": "견적",
    "견적 비교": "견적",
    "정책연계": "정책",
}


def init_state() -> None:
    st.session_state.setdefault("company_key", "한빛정밀")
    st.session_state.setdefault("last_result", None)
    st.session_state.setdefault("last_title", "")
    st.session_state.setdefault("fitness", None)
    st.session_state.setdefault("page", "기초체력")
    st.session_state.setdefault("more_choice", "CSV 검증")
    if st.session_state.get("more_choice") == "K-Doctor 연동":
        st.session_state.more_choice = "보완 진단"
    st.session_state.setdefault("fit_path", None)  # None | report | quiz
    st.session_state.setdefault("fit_step", 0)  # 0 industry, 1 areas, 2 problems, 3+ likert
    st.session_state.setdefault("fit_answers", {})
    st.session_state.setdefault("fit_answer_log", [])
    st.session_state.setdefault("fit_industry", None)
    st.session_state.setdefault("fit_areas", [])
    st.session_state.setdefault("fit_problems", [])
    settings = runtime_settings()
    st.session_state.setdefault("model_name", settings["default_model"])
    cur = st.session_state.get("page")
    if cur in _PAGE_ALIASES:
        st.session_state.page = _PAGE_ALIASES[cur]


def navigate(page: str, *, more: str | None = None) -> None:
    """위젯 key에 직접 쓰지 말고, 다음 런 시작 전에 적용되도록 예약."""
    st.session_state["_nav_page"] = page
    if more is not None:
        st.session_state["_nav_more"] = more
    st.rerun()


def apply_pending_nav() -> None:
    """radio(key=page/more_choice) 생성 전에만 호출."""
    if "_nav_page" in st.session_state:
        st.session_state.page = st.session_state.pop("_nav_page")
    if "_nav_more" in st.session_state:
        st.session_state.more_choice = st.session_state.pop("_nav_more")


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

        fit = st.session_state.get("fitness")
        if fit:
            st.caption(f"기초체력 {fit['label']} · {fit['total']}/{fit['max_score']}")

        with st.expander("안내"):
            st.write(
                "상단 메뉴로 이동: 기초체력 → 과업지시서 → 업체 → 견적 → 정책. "
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
        "fitness": st.session_state.get("fitness"),
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


def render_education(fit: dict) -> None:
    if fit["level"] == "high":
        return
    links = fit.get("education") or []
    if not links:
        return
    with st.expander("교육 안내"):
        for link in links:
            st.link_button(link["title"], link["url"], use_container_width=True)


def render_vendor_recs(company: dict, *, key_prefix: str) -> None:
    wo = st.session_state.get("last_result") if st.session_state.get("last_title") == "AX과업지시서" else None
    fit = st.session_state.get("fitness")
    recs = recommend_vendors(company=company, work_order=wo, fitness=fit, limit=6)
    for i, v in enumerate(recs):
        vendor_card(v)
        st.link_button(
            v["name"],
            v["url"],
            use_container_width=True,
            key=f"{key_prefix}_vendor_{v['id']}_{i}",
        )


def render_policy_recs(company: dict, *, context: str, key_prefix: str) -> None:
    fit = st.session_state.get("fitness")
    recs = recommend_policies(fitness=fit, company=company, context=context, limit=3)
    for i, p in enumerate(recs):
        policy_card(p)
        st.link_button(
            "바로가기",
            p["apply_url"],
            use_container_width=True,
            key=f"{key_prefix}_apply_{p['id']}_{i}",
        )


def _reset_quiz_state() -> None:
    st.session_state.fit_step = 0
    st.session_state.fit_answers = {}
    st.session_state.fit_answer_log = []
    st.session_state.fit_industry = None
    st.session_state.fit_areas = []
    st.session_state.fit_problems = []


def _finish_quiz() -> None:
    used = [
        {"id": q["id"], "text": q["text"], "options": q["options"]}
        for q in LIKERT_QUESTIONS
    ]
    st.session_state.fitness = score_fitness(
        st.session_state.fit_answers,
        questions=used,
        source="quiz",
        extra={
            "industry": st.session_state.get("fit_industry"),
            "ai_areas": list(st.session_state.get("fit_areas") or []),
            "ai_problems": list(st.session_state.get("fit_problems") or []),
            "answer_log": st.session_state.fit_answer_log,
        },
    )


def _render_fitness_result(company: dict) -> None:
    fit = st.session_state.get("fitness")
    if not fit:
        return
    st.metric(fit["label"], f"{fit['total']}/{fit['max_score']}")
    areas = fit.get("ai_areas") or []
    problems = fit.get("ai_problems") or []
    if areas:
        soft_card("AI 적용 영역", " · ".join(areas))
    if problems:
        soft_card("해결 문제", " · ".join(problems))
    if fit.get("kdoctor_summary"):
        with st.expander("보고서 요약"):
            st.write(fit["kdoctor_summary"])
    render_education(fit)
    if st.button("다시하기", use_container_width=True, key="fit_restart"):
        st.session_state.fitness = None
        st.session_state.fit_path = None
        _reset_quiz_state()
        st.rerun()


def _render_quiz_focus(step: int) -> None:
    st.progress((step + 1) / TOTAL_QUIZ_STEPS)

    if step == 0:
        industry = st.radio("업종", INDUSTRIES, key="fit_ui_industry")
        if st.button("다음", type="primary", use_container_width=True, key="fit_quiz_next"):
            st.session_state.fit_industry = industry
            st.session_state.fit_step = 1
            st.rerun()
        if st.button("뒤로", use_container_width=True, key="fit_quiz_back"):
            st.session_state.fit_path = None
            _reset_quiz_state()
            st.rerun()
        return

    if step == 1:
        areas = st.multiselect(
            "AI 적용 영역 (최대 2)",
            options=list(AI_AREAS),
            default=[a for a in (st.session_state.get("fit_areas") or []) if a in AI_AREAS][:2],
            max_selections=2,
            key="fit_ui_areas",
        )
        if st.button("다음", type="primary", use_container_width=True, key="fit_quiz_next"):
            if not areas:
                st.warning("영역을 골라 주세요.")
            else:
                st.session_state.fit_areas = list(areas)
                st.session_state.fit_problems = []
                st.session_state.fit_step = 2
                st.rerun()
        if st.button("뒤로", use_container_width=True, key="fit_quiz_back"):
            st.session_state.fit_step = 0
            st.rerun()
        return

    areas = list(st.session_state.get("fit_areas") or [])
    opts = problems_for_areas(areas)
    problems = st.multiselect(
        "해결 문제 (최대 2)",
        options=opts,
        default=[p for p in (st.session_state.get("fit_problems") or []) if p in opts][:2],
        max_selections=2,
        key="fit_ui_problems",
    )
    if st.button("다음", type="primary", use_container_width=True, key="fit_quiz_next"):
        if not problems:
            st.warning("문제를 골라 주세요.")
        else:
            st.session_state.fit_problems = list(problems)
            st.session_state.fit_step = 3
            st.rerun()
    if st.button("뒤로", use_container_width=True, key="fit_quiz_back"):
        st.session_state.fit_step = 1
        st.rerun()


def _render_quiz_likert(step: int) -> None:
    li = step - 3
    q = likert_at(li)
    st.progress((step + 1) / TOTAL_QUIZ_STEPS)
    st.caption(q["step"])
    labels = [o[0] for o in q["options"]]
    scores = {o[0]: o[1] for o in q["options"]}
    choice = st.radio(q["text"], labels, key=f"fit_likert_{q['id']}")

    if st.button(
        "완료" if li >= len(LIKERT_QUESTIONS) - 1 else "다음",
        type="primary",
        use_container_width=True,
        key="fit_quiz_next",
    ):
        score = scores[choice]
        st.session_state.fit_answers[q["id"]] = score
        st.session_state.fit_answer_log.append(
            {
                "id": q["id"],
                "topic": q["topic"],
                "step": q["step"],
                "choice_label": choice,
                "score": score,
                "text": q["text"],
            }
        )
        st.session_state.fit_step = step + 1
        if st.session_state.fit_step >= TOTAL_QUIZ_STEPS:
            _finish_quiz()
        st.rerun()
    if st.button("뒤로", use_container_width=True, key="fit_quiz_back"):
        st.session_state.fit_step = step - 1
        st.rerun()


def page_fitness() -> None:
    company = COMPANIES[st.session_state.company_key]
    page_header("기초체력", "어디에 AI를<br>쓸까요?", "보고서를 올리거나 바로 체크하세요.")

    if st.session_state.get("fitness"):
        _render_fitness_result(company)
        return

    if st.session_state.fit_path is None:
        a1, a2 = st.columns(2)
        if a1.button("보고서 업로드", type="primary", use_container_width=True, key="fit_kd_yes"):
            st.session_state.fit_path = "report"
            st.rerun()
        if a2.button("여기서 체크", use_container_width=True, key="fit_kd_no"):
            st.session_state.fit_path = "quiz"
            _reset_quiz_state()
            st.rerun()
        st.link_button("K-Doctor AX 자가진단", KDOCTOR_AX_INTRO, use_container_width=True)
        return

    if st.session_state.fit_path == "report":
        sample_path = sample_files()["AX 자가진단 보고서"]
        use_sample = st.toggle("샘플 보고서", value=True, key="fit_report_sample")
        report_text = ""
        report_name = ""
        if use_sample and sample_path.exists():
            report_text = load_sample(sample_path)
            report_name = sample_path.name
            with st.expander("미리보기"):
                st.text(report_text[:1200])
                st.download_button(
                    "예시 파일",
                    data=sample_path.read_bytes(),
                    file_name=sample_path.name,
                    mime="text/plain",
                    key="dl_ax_report_sample",
                )
        else:
            uploaded = st.file_uploader(
                "결과 보고서",
                type=["txt", "md", "pdf", "docx"],
                key="fit_report_up",
            )
            if uploaded:
                report_name = uploaded.name
                report_text = read_upload(uploaded.name, uploaded.getvalue())

        if st.button("기초체력 산출", type="primary", use_container_width=True, key="fit_report_run"):
            if not report_text.strip():
                st.warning("보고서를 올려 주세요.")
            else:
                fit = fitness_from_report(report_text, company)
                st.session_state.last_result = {
                    "summary": fit.get("kdoctor_summary"),
                    "source": "report",
                    "diagnosis_id": fit.get("kdoctor_id"),
                    "priority_tasks": fit.get("priority_tasks"),
                    "ai_areas": fit.get("ai_areas"),
                    "filename": report_name,
                }
                st.session_state.last_title = "AX보고서"
                st.session_state.fitness = fit
                st.rerun()
        if st.button("뒤로", use_container_width=True, key="fit_kd_back"):
            st.session_state.fit_path = None
            st.rerun()
        return

    if st.session_state.fit_path == "kdoctor":
        st.session_state.fit_path = "report"
        st.rerun()
        return

    step = int(st.session_state.fit_step)
    if step >= TOTAL_QUIZ_STEPS:
        _finish_quiz()
        st.rerun()
        return
    if step < 3:
        _render_quiz_focus(step)
    else:
        _render_quiz_likert(step)


def page_work_order(model_name: str, company: dict) -> None:
    page_header("과업지시서", "과업지시서를<br>만들어요", "적용 영역을 반영한 초안입니다.")
    fit = st.session_state.get("fitness")
    if fit and (fit.get("ai_areas") or fit.get("label")):
        soft_card(
            fit.get("label") or "기초체력",
            " · ".join(fit.get("ai_areas") or []) or fit.get("tip", ""),
        )
    kd = company.get("kdoctor") or {}
    profile = company_form(company, "wo")
    if st.button("만들기", type="primary", use_container_width=True, key="wo_run"):
        with st.spinner("작성 중…"):
            result = generate_work_order(
                model_name,
                profile,
                {
                    "kdoctor": kd,
                    "fitness": fit,
                    **(st.session_state.get("last_result") or {}),
                },
            )
        show_result("AX과업지시서", result)
        st.session_state.work_order_done = True


def page_vendors(company: dict) -> None:
    st.session_state.vendors_viewed = True
    page_header("업체", "맞는 업체를<br>골라 보세요", "참고용 추천입니다.")
    render_vendor_recs(company, key_prefix="vd")
    with st.expander(f"전체 {len(VENDORS)}개"):
        for i, v in enumerate(VENDORS):
            item = dict(v)
            item["match_score"] = 0
            item["why"] = "카탈로그"
            vendor_card(item)
            st.link_button(v["name"], v["url"], use_container_width=True, key=f"vd_all_{v['id']}_{i}")


def page_quotes(model_name: str, company: dict) -> None:
    page_header("견적", "견적을<br>비교해요", "샘플 또는 파일을 넣으세요.")
    parts = []
    use_sample = st.toggle("샘플 견적", value=True, key="quote_sample")
    if use_sample:
        for key in ("견적 A", "견적 B"):
            path = sample_files()[key]
            if path.exists():
                parts.append(f"# {key}\n{load_sample(path)}")
    else:
        uploads = st.file_uploader(
            "견적 파일",
            type=["txt", "csv", "xlsx", "pdf", "docx"],
            accept_multiple_files=True,
            key="quote_up",
        )
        for f in uploads or []:
            raw = f.getvalue()
            parts.append(f"# {f.name}\n{read_upload(f.name, raw)}")

    if st.button("비교하기", type="primary", use_container_width=True, key="quote_run"):
        quote_text = "\n\n".join(parts)
        if not quote_text.strip():
            st.warning("견적 자료를 넣어 주세요.")
        else:
            with st.spinner("비교 중…"):
                result = compare_quotations(model_name, company, quote_text)
            show_result("견적비교", result)
            st.session_state.quotes_done = True


def page_csv_validate() -> None:
    page_header("CSV", "표준인지<br>검사해요", "필수 컬럼·파일명을 확인합니다.")
    tpl = sample_files()["표준 템플릿"]
    if tpl.exists():
        st.download_button(
            "템플릿",
            data=tpl.read_bytes(),
            file_name="템플릿_표준_기업현황.csv",
            mime="text/csv",
            use_container_width=True,
            key="dl_tpl",
        )
    use_sample = st.toggle("샘플 검사", value=True, key="metrics_sample")
    if use_sample:
        path = sample_files()["표준 기업현황"]
        data = path.read_bytes()
        name = path.name
    else:
        uploaded = st.file_uploader("CSV/XLSX", type=["csv", "xlsx"], key="metrics_up")
        if not uploaded:
            return
        data = uploaded.getvalue()
        name = uploaded.name
    if st.button("검사", type="primary", use_container_width=True, key="metrics_run"):
        st.session_state["csv_report"] = validate_company_metrics(name, data)
    report = st.session_state.get("csv_report")
    if not report:
        return
    if report["ok"]:
        st.success(f"통과 · {report['row_count']}행")
    else:
        st.error("미통과")
        for issue in report["issues"]:
            st.write(f"- {issue}")
    if report.get("preview") is not None:
        st.dataframe(report["preview"], use_container_width=True)


def page_policies(company: dict) -> None:
    st.session_state.policies_viewed = True
    page_header("정책", "맞는 정책을<br>이어가요", "공식 공고를 확인하세요.")
    render_policy_recs(company, context="work_order", key_prefix="pol_top")
    with st.expander("전체 카탈로그"):
        for i, p in enumerate(POLICIES):
            item = dict(p)
            item["why"] = "카탈로그"
            policy_card(item)
            st.link_button("바로가기", p["apply_url"], use_container_width=True, key=f"pol_a_{i}")


def page_more(model_name: str, company: dict) -> None:
    choice = st.radio(
        "선택",
        ("CSV 검증", "시스템 분석", "모델 비교", "보완 진단"),
        horizontal=True,
        label_visibility="collapsed",
        key="more_choice",
    )
    if choice == "CSV 검증":
        page_csv_validate()
        return

    page_header("더보기", "필요할 때만<br>쓰세요", "")

    if choice == "보완 진단":
        profile = company_form(company, "diag")
        if st.checkbox("합성 메모", value=True, key="diag_sample"):
            path = sample_files()["진단 메모"]
            extra = load_sample(path) if path.exists() else ""
        else:
            extra = ""
        if st.button("실행", type="primary", use_container_width=True, key="diag_run"):
            with st.spinner("실행 중…"):
                result = diagnose(model_name, profile, extra)
            show_result("보완진단", result)
    elif choice == "시스템 분석":
        doc_text = ""
        if st.toggle("샘플", value=True, key="sys_sample"):
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
        if st.button("분석", type="primary", use_container_width=True, key="sys_run"):
            if not doc_text.strip():
                st.warning("문서가 없습니다.")
            else:
                with st.spinner("분석 중…"):
                    result = analyze_systems(model_name, company, doc_text)
                show_result("시스템분석", result)
    else:
        names = list(MODELS.keys())
        a = st.selectbox("모델 A", names, index=0, key="cmp_a")
        b = st.selectbox("모델 B", names, index=min(1, len(names) - 1), key="cmp_b")
        question = st.text_input("질문", "우선 과업 3가지와 검수기준을 제시해 주세요.", key="cmp_q")
        if st.button("비교", type="primary", use_container_width=True, key="cmp_run"):
            with st.spinner("비교 중…"):
                result = compare_models(a, b, company, question)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**{result['model_a']['name']}**")
                st.write((result["model_a"]["result"] or {}).get("summary"))
            with c2:
                st.markdown(f"**{result['model_b']['name']}**")
                st.write((result["model_b"]["result"] or {}).get("summary"))


def main() -> None:
    init_state()
    apply_pending_nav()
    inject_styles()
    model_name, company = sidebar()

    current = st.session_state.get("page", STEPS[0])
    if current not in PAGES:
        current = STEPS[0]
        st.session_state.page = current

    page = st.pills(
        "메뉴",
        options=list(PAGES),
        default=current if current in PAGES else STEPS[0],
        key="page",
        label_visibility="collapsed",
    )
    if page is None:
        page = current
        st.session_state.page = page

    if page == "기초체력":
        page_fitness()
    elif page == "과업지시서":
        page_work_order(model_name, company)
    elif page == "업체":
        page_vendors(company)
    elif page == "견적":
        page_quotes(model_name, company)
    elif page == "정책":
        page_policies(company)
    else:
        page_more(model_name, company)

    render_footer()


if __name__ == "__main__":
    main()
