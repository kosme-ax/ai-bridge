from __future__ import annotations

import streamlit as st

from src.analysis import compare_quotations, generate_work_order
from src.config import runtime_settings
from src.docs import read_upload
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
from src.reports import RFP_SECTION_ORDER, to_docx_bytes, to_pdf_bytes
from src.sample_data import COMPANIES
from src.ui import inject_styles, page_header, policy_card, render_footer, soft_card, vendor_card
from src.vendors import VENDORS, recommend_vendors

st.set_page_config(
    page_title="sme-ax-helper",
    page_icon="💠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# 상단 메뉴 = 단계 이동. 화면 안 다음/이전 CTA는 두지 않음.
STEPS = ("기초체력", "과업지시서", "업체", "견적", "정책")

_PAGE_ALIASES = {
    "기초체력보기": "기초체력",
    "과업지시서 작성": "과업지시서",
    "업체 탐색": "업체",
    "견적비교": "견적",
    "견적 비교": "견적",
    "정책연계": "정책",
    "더보기": "기초체력",
}


def init_state() -> None:
    st.session_state.setdefault("company_key", "한빛정밀")
    st.session_state.setdefault("last_result", None)
    st.session_state.setdefault("last_title", "")
    st.session_state.setdefault("fitness", None)
    st.session_state.setdefault("page", "기초체력")
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


def active_model() -> str:
    """모델은 UI가 아니라 DEFAULT_MODEL / src/config.py MODELS로만 교체."""
    settings = runtime_settings()
    name = settings["default_model"]
    st.session_state.model_name = name
    return name


def active_company() -> dict:
    key = st.session_state.get("company_key") or "한빛정밀"
    if key not in COMPANIES:
        key = next(iter(COMPANIES))
        st.session_state.company_key = key
    return COMPANIES[key]


def company_form(company: dict, key_prefix: str) -> dict:
    """입력칸은 비워 두고, 시연·현장에서 직접 기입. company는 폴백용."""
    name = st.text_input("기업명", value="", placeholder="예: 한빛정밀", key=f"{key_prefix}_name")
    industry = st.text_input("업종", value="", placeholder="예: 제조업", key=f"{key_prefix}_industry")
    employees = st.number_input(
        "인원",
        min_value=1,
        value=1,
        key=f"{key_prefix}_employees",
    )
    with st.expander("상세 정보", expanded=False):
        main_tasks = st.text_area(
            "주요 업무", value="", height=70, key=f"{key_prefix}_main_tasks"
        )
        it_summary = st.text_area(
            "IT 현황", value="", height=70, key=f"{key_prefix}_it_summary"
        )
        pain_points = st.text_area(
            "고충", value="", height=70, key=f"{key_prefix}_pain_points"
        )

    return {
        "name": name or company.get("name", ""),
        "industry": industry or company.get("industry", ""),
        "employees": int(employees) if employees else int(company.get("employees") or 1),
        "main_tasks": main_tasks or company.get("main_tasks", ""),
        "it_summary": it_summary or company.get("it_summary", ""),
        "pain_points": pain_points or company.get("pain_points", ""),
        "kdoctor": company.get("kdoctor") or {},
        "fitness": st.session_state.get("fitness"),
    }


def show_result(title: str, result: dict) -> None:
    st.session_state.last_title = title
    # 프롬프트·내부 키는 세션/화면에서 제외
    clean = {
        k: v
        for k, v in result.items()
        if k not in {"_prompt", "prompt", "raw_prompt", "system_prompt"}
    }
    st.session_state.last_result = clean
    meta = clean.get("_meta") or {}
    st.success(f"완료 · {meta.get('model_name')} · {meta.get('mode')}")
    if clean.get("summary"):
        st.write(clean["summary"])

    basis = clean.get("fitness_basis") or {}
    if basis.get("ai_areas") or basis.get("ai_problems"):
        soft_card(
            "기초체력 반영",
            " · ".join(
                [
                    x
                    for x in [
                        " · ".join(basis.get("ai_areas") or []) or "",
                        " / ".join(basis.get("ai_problems") or []) or "",
                    ]
                    if x
                ]
            ),
        )

    sections = clean.get("sections") or {}
    if isinstance(sections, dict) and sections:
        for key, heading in RFP_SECTION_ORDER:
            body = sections.get(key)
            if not body:
                continue
            with st.expander(heading, expanded=(key in {"사업개요", "현황및문제점", "기초체력진단요약"})):
                if isinstance(body, (list, dict)):
                    st.write(body)
                else:
                    st.write(body)
    else:
        # 견적 등: 요약 외 주요 필드만 (원본 JSON·프롬프트 비공개)
        for key in ("recommendation", "comparison_notes", "open_questions", "human_review_risks"):
            val = clean.get(key)
            if not val:
                continue
            if isinstance(val, list):
                soft_card(key, " · ".join(str(x) for x in val)[:800])
            else:
                soft_card(key, str(val)[:800])

    pdf = to_pdf_bytes(title, clean)
    docx = to_docx_bytes(title, clean)
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
    page_header(
        "기초체력",
        "우리 회사의<br>AX 수준 진단",
        "K-Doctor 보고서를 올리거나, 같은 흐름으로 바로 체크하세요.",
    )

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
        uploaded = st.file_uploader(
            "결과 보고서",
            type=["txt", "md", "pdf", "docx"],
            key="fit_report_up",
        )
        report_text = ""
        report_name = ""
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
    page_header(
        "과업지시서",
        "표준 RFP를<br>만들어요",
        "기초체력 설문·보고서를 반영한 국민제안형 표준 과업지시서입니다.",
    )
    fit = st.session_state.get("fitness")
    if fit and (fit.get("ai_areas") or fit.get("label")):
        soft_card(
            fit.get("label") or "기초체력",
            " · ".join(fit.get("ai_areas") or []) or fit.get("tip", ""),
        )
    else:
        soft_card("기초체력 권장", "상단 「기초체력」에서 설문·보고서를 먼저 하면 RFP가 더 구체적입니다.")
    kd = company.get("kdoctor") or {}
    profile = company_form(company, "wo")
    if st.button("표준 RFP 만들기", type="primary", use_container_width=True, key="wo_run"):
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
    page_header("견적", "견적을<br>비교해요", "견적 파일을 올려 주세요.")
    uploads = st.file_uploader(
        "견적 파일",
        type=["txt", "csv", "xlsx", "pdf", "docx"],
        accept_multiple_files=True,
        key="quote_up",
    )
    parts = []
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


def main() -> None:
    init_state()
    inject_styles()
    model_name = active_model()
    company = active_company()

    current = st.session_state.get("page", STEPS[0])
    if current not in STEPS:
        current = STEPS[0]
        st.session_state.page = current

    page = st.pills(
        "메뉴",
        options=list(STEPS),
        default=current if current in STEPS else STEPS[0],
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
    else:
        page_policies(company)

    render_footer()


if __name__ == "__main__":
    main()
