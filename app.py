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
from src.csv_validate import (
    COMPANY_METRICS_COLUMNS,
    validate_company_metrics,
    validate_quote_csv,
)
from src.docs import load_sample, read_upload
from src.fitness import (
    AI_AREAS,
    INDUSTRIES,
    KDOCTOR_AX_INTRO,
    KDOCTOR_LOGIN,
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

# 메인 실행 순서 (토스식 한 줄 플로우). 더보기는 보조.
STEPS = (
    "기초체력보기",
    "과업지시서 작성",
    "업체 탐색",
    "견적비교",
    "정책연계",
)
PAGES = STEPS + ("더보기",)

# 이전 세션/북마크용 별칭 → 정식 스텝명
_PAGE_ALIASES = {
    "기초체력": "기초체력보기",
    "과업지시서": "과업지시서 작성",
    "견적 비교": "견적비교",
}


def init_state() -> None:
    st.session_state.setdefault("company_key", "한빛정밀")
    st.session_state.setdefault("last_result", None)
    st.session_state.setdefault("last_title", "")
    st.session_state.setdefault("fitness", None)
    st.session_state.setdefault("page", "기초체력보기")
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
    # 구 페이지명 마이그레이션
    cur = st.session_state.get("page")
    if cur in _PAGE_ALIASES:
        st.session_state.page = _PAGE_ALIASES[cur]


def step_nav(prev: str | None, next_: str | None, *, key_prefix: str) -> None:
    """화면 하단 이전/다음 스텝 이동."""
    st.write("")
    cols = st.columns(2)
    if prev:
        if cols[0].button(f"← {prev}", use_container_width=True, key=f"{key_prefix}_prev"):
            navigate(prev)
    else:
        cols[0].write("")
    if next_:
        if cols[1].button(f"다음 · {next_}", type="primary", use_container_width=True, key=f"{key_prefix}_next"):
            navigate(next_)
    else:
        cols[1].write("")


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
                "실행 순서: ①기초체력보기 → ②과업지시서 작성 → ③업체 탐색 → ④견적비교 → ⑤정책연계. "
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
    soft_card("맞춤 교육 안내", fit["tip"])
    for link in fit.get("education") or []:
        st.link_button(link["title"], link["url"], use_container_width=True)


def render_vendor_recs(company: dict, *, key_prefix: str) -> None:
    wo = st.session_state.get("last_result") if st.session_state.get("last_title") == "AX과업지시서" else None
    fit = st.session_state.get("fitness")
    recs = recommend_vendors(company=company, work_order=wo, fitness=fit, limit=8)
    st.markdown("#### AI 공급사 추천")
    focus = " · ".join((fit or {}).get("ai_areas") or []) or "과업·진단"
    st.caption(
        f"{focus} 기준으로 {len(VENDORS)}개 카탈로그 중 골라 둔 참고 목록입니다. "
        "계약·단가 보증이 아니며 AI바우처 Pool·각사 공고를 확인하세요."
    )
    for i, v in enumerate(recs):
        vendor_card(v)
        st.link_button(
            f"{v['name']} 바로가기",
            v["url"],
            use_container_width=True,
            key=f"{key_prefix}_vendor_{v['id']}_{i}",
        )


def render_policy_recs(company: dict, *, context: str, key_prefix: str) -> None:
    fit = st.session_state.get("fitness")
    recs = recommend_policies(fitness=fit, company=company, context=context, limit=3)
    st.markdown("#### 중진공 정책 연계 추천")
    st.caption("결과 기준으로 골라 둔 안내입니다. 일정·조건은 공식 공고를 확인하세요.")
    for i, p in enumerate(recs):
        policy_card(p)
        b1, b2 = st.columns(2)
        b1.link_button(
            "신청·바로가기",
            p["apply_url"],
            use_container_width=True,
            key=f"{key_prefix}_apply_{p['id']}_{i}",
        )
        b2.link_button(
            "상세 안내",
            p["info_url"],
            use_container_width=True,
            key=f"{key_prefix}_info_{p['id']}_{i}",
        )
        st.write("")


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
    src = {
        "report": "보고서 업로드",
        "kdoctor": "보고서 업로드",
        "quiz": "AX 자가진단형 체크",
    }.get(str(fit.get("source")), "체크")
    st.metric("기초체력", f"{fit['label']}  {fit['total']}/{fit['max_score']}")
    st.caption(f"산출 경로: {src}")
    areas = fit.get("ai_areas") or []
    problems = fit.get("ai_problems") or []
    if areas:
        soft_card(
            "AI 적용 희망 영역",
            " · ".join(areas)
            + (f" · 업종 {fit.get('industry')}" if fit.get("industry") else ""),
        )
    if problems:
        soft_card("해결하고 싶은 문제", " · ".join(problems))
    st.write(fit["tip"])
    if fit.get("kdoctor_summary"):
        soft_card("진단 보고서 요약", fit["kdoctor_summary"])
    if fit.get("priority_tasks") and not problems:
        soft_card("우선 과제", " · ".join(fit["priority_tasks"]))
    render_education(fit)
    st.write("")
    soft_card("다음 단계", "선택한 AI 적용 영역을 반영해 과업지시서 초안을 작성하세요.")
    c1, c2 = st.columns(2)
    if c1.button("처음부터", use_container_width=True, key="fit_restart"):
        st.session_state.fitness = None
        st.session_state.fit_path = None
        _reset_quiz_state()
        st.rerun()
    if c2.button("다음 · 과업지시서 작성", type="primary", use_container_width=True, key="go_wo"):
        navigate("과업지시서 작성")


def _render_quiz_focus(step: int) -> None:
    """STEP 1: 업종 → AI 영역(최대2) → 문제(최대2)."""
    st.progress(step / TOTAL_QUIZ_STEPS, text=f"AX 자가진단 체크 {step + 1} / {TOTAL_QUIZ_STEPS}")

    if step == 0:
        soft_card("STEP 1 · AI 필요 분야", "귀사의 업종을 먼저 고르세요. (K-Doctor AX 자가진단과 같은 흐름)")
        industry = st.radio("귀사의 주요 업종은 무엇입니까?", INDUSTRIES, key="fit_ui_industry")
        c1, c2 = st.columns(2)
        if c1.button("이전 경로로", use_container_width=True, key="fit_quiz_back"):
            st.session_state.fit_path = None
            _reset_quiz_state()
            st.rerun()
        if c2.button("다음", type="primary", use_container_width=True, key="fit_quiz_next"):
            st.session_state.fit_industry = industry
            st.session_state.fit_step = 1
            st.rerun()
        return

    if step == 1:
        soft_card(
            "STEP 1 · AI 적용 영역",
            "어디에 AI를 적용하고 싶은지가 핵심입니다. 업무 영역에서 최대 2개까지 고르세요.",
        )
        areas = st.multiselect(
            "귀사에서는 어떤 영역에 AI를 적용하고 싶습니까? (최대 2개)",
            options=list(AI_AREAS),
            default=[a for a in (st.session_state.get("fit_areas") or []) if a in AI_AREAS][:2],
            max_selections=2,
            key="fit_ui_areas",
        )
        c1, c2 = st.columns(2)
        if c1.button("이전", use_container_width=True, key="fit_quiz_back"):
            st.session_state.fit_step = 0
            st.rerun()
        if c2.button("다음", type="primary", use_container_width=True, key="fit_quiz_next"):
            if not areas:
                st.warning("적용하고 싶은 영역을 1개 이상 골라 주세요.")
            else:
                st.session_state.fit_areas = list(areas)
                st.session_state.fit_problems = []
                st.session_state.fit_step = 2
                st.rerun()
        return

    # step == 2
    areas = list(st.session_state.get("fit_areas") or [])
    opts = problems_for_areas(areas)
    soft_card(
        "STEP 1 · 해결 문제",
        f"선택한 영역({ ' · '.join(areas) })에서 해결하고 싶은 문제를 최대 2개 고르세요.",
    )
    problems = st.multiselect(
        "해결하고 싶은 문제는 무엇입니까? (최대 2개)",
        options=opts,
        default=[p for p in (st.session_state.get("fit_problems") or []) if p in opts][:2],
        max_selections=2,
        key="fit_ui_problems",
    )
    c1, c2 = st.columns(2)
    if c1.button("이전", use_container_width=True, key="fit_quiz_back"):
        st.session_state.fit_step = 1
        st.rerun()
    if c2.button("다음", type="primary", use_container_width=True, key="fit_quiz_next"):
        if not problems:
            st.warning("해결하고 싶은 문제를 1개 이상 골라 주세요.")
        else:
            st.session_state.fit_problems = list(problems)
            st.session_state.fit_step = 3
            st.rerun()


def _render_quiz_likert(step: int) -> None:
    li = step - 3
    q = likert_at(li)
    st.progress(step / TOTAL_QUIZ_STEPS, text=f"AX 자가진단 체크 {step + 1} / {TOTAL_QUIZ_STEPS}")
    soft_card(q["step"], q["topic"])
    labels = [o[0] for o in q["options"]]
    scores = {o[0]: o[1] for o in q["options"]}
    choice = st.radio(q["text"], labels, key=f"fit_likert_{q['id']}")

    c1, c2 = st.columns(2)
    if c1.button("이전", use_container_width=True, key="fit_quiz_back"):
        st.session_state.fit_step = step - 1
        st.rerun()
    if c2.button(
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


def page_fitness() -> None:
    company = COMPANIES[st.session_state.company_key]

    page_header(
        "STEP 1",
        "어디에 AI를<br>쓰고 싶은가요?",
        "K-Doctor AX 자가진단 결과 보고서를 올리거나, 같은 흐름으로 여기서 바로 체크합니다.",
    )

    if st.session_state.get("fitness"):
        _render_fitness_result(company)
        return

    # --- Gate ---
    if st.session_state.fit_path is None:
        soft_card(
            "먼저 확인할게요",
            "중진공 K-Doctor AX 자가진단을 이미 하셨나요? 하셨다면 결과 보고서를 업로드하세요.",
        )
        a1, a2 = st.columns(2)
        if a1.button("네, 보고서 올릴게요", type="primary", use_container_width=True, key="fit_kd_yes"):
            st.session_state.fit_path = "report"
            st.rerun()
        if a2.button("아직 안 했어요 · 여기서 체크", use_container_width=True, key="fit_kd_no"):
            st.session_state.fit_path = "quiz"
            _reset_quiz_state()
            st.rerun()
        b1, b2 = st.columns(2)
        b1.link_button("AX 자가진단 시작", KDOCTOR_AX_INTRO, use_container_width=True)
        b2.link_button("K-Doctor 로그인", KDOCTOR_LOGIN, use_container_width=True)
        return

    # --- Path A: 보고서 업로드 ---
    if st.session_state.fit_path == "report":
        soft_card(
            "결과 보고서 업로드",
            "K-Doctor에서 받은 AX 자가진단 결과(텍스트·PDF·DOCX)를 올리면 적용 영역·과제를 읽어 기초체력을 산출합니다.",
        )
        sample_path = sample_files()["AX 자가진단 보고서"]
        if sample_path.exists():
            st.download_button(
                "시연용 예시 보고서 받기",
                data=sample_path.read_bytes(),
                file_name=sample_path.name,
                mime="text/plain",
                use_container_width=True,
                key="dl_ax_report_sample",
            )
        use_sample = st.toggle("샘플 보고서 사용 (심사 시연)", value=True, key="fit_report_sample")
        report_text = ""
        report_name = ""
        if use_sample and sample_path.exists():
            report_text = load_sample(sample_path)
            report_name = sample_path.name
            soft_card("샘플", report_name)
            with st.expander("미리보기"):
                st.text(report_text[:1500])
        else:
            uploaded = st.file_uploader(
                "AX 자가진단 결과 보고서",
                type=["txt", "md", "pdf", "docx"],
                key="fit_report_up",
            )
            if uploaded:
                report_name = uploaded.name
                report_text = read_upload(uploaded.name, uploaded.getvalue())
                soft_card("업로드됨", report_name)

        b1, b2 = st.columns(2)
        if b1.button("뒤로", use_container_width=True, key="fit_kd_back"):
            st.session_state.fit_path = None
            st.rerun()
        if b2.button("보고서로 기초체력 산출", type="primary", use_container_width=True, key="fit_report_run"):
            if not report_text.strip():
                st.warning("보고서를 올리거나 샘플을 켜 주세요.")
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
        return

    # 구 세션값 호환
    if st.session_state.fit_path == "kdoctor":
        st.session_state.fit_path = "report"
        st.rerun()
        return

    # --- Path B: AX 자가진단형 체크 ---
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
        "STEP 2",
        "과업지시서를<br>작성해요",
        "K-Doctor 진단과 기초체력 결과를 반영해 AX 지원 과업지시서 초안을 만듭니다.",
    )
    fit = st.session_state.get("fitness")
    if fit:
        areas = fit.get("ai_areas") or []
        soft_card(
            f"기초체력 · {fit['label']}",
            (f"AI 적용 희망: {' · '.join(areas)}. " if areas else "") + fit["tip"],
        )
        render_education(fit)
    else:
        soft_card("기초체력 미실시", "먼저 STEP 1 「기초체력보기」에서 AI 적용 영역을 고르면 과업 톤이 맞춰집니다.")

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
                {
                    "kdoctor": kd,
                    "fitness": fit,
                    **(st.session_state.get("last_result") or {}),
                },
            )
        show_result("AX과업지시서", result)
        st.session_state.work_order_done = True

    if st.session_state.get("work_order_done") or st.session_state.get("last_title") == "AX과업지시서":
        soft_card("다음 단계", "과업에 맞는 AI 공급사를 골라 보세요.")
        if st.button("다음 · 업체 탐색", type="primary", use_container_width=True, key="wo_to_vendors"):
            navigate("업체 탐색")
    else:
        step_nav("기초체력보기", None, key_prefix="wo")


def page_vendors(company: dict) -> None:
    st.session_state.vendors_viewed = True
    page_header(
        "STEP 3",
        "맞는 업체를<br>찾아볼게요",
        "과업·진단 키워드로 공급사 카탈로그를 골라 드립니다. 계약·단가 보증은 아닙니다.",
    )
    wo = st.session_state.get("last_result") if st.session_state.get("last_title") == "AX과업지시서" else None
    if not wo:
        soft_card("과업지시서 권장", "STEP 2에서 과업지시서를 만들면 매칭이 더 정확해집니다.")
    render_vendor_recs(company, key_prefix="vd")
    with st.expander(f"전체 카탈로그 ({len(VENDORS)}개)"):
        for i, v in enumerate(VENDORS):
            item = dict(v)
            item["match_score"] = 0
            item["why"] = "카탈로그"
            vendor_card(item)
            st.link_button(v["name"], v["url"], use_container_width=True, key=f"vd_all_{v['id']}_{i}")
    soft_card("다음 단계", "후보 업체의 견적을 받아 비교하세요.")
    step_nav("과업지시서 작성", "견적비교", key_prefix="vd")


def page_quotes(model_name: str, company: dict) -> None:
    page_header(
        "STEP 4",
        "견적을<br>비교해요",
        "과업 범위에 맞춰 공급사 견적을 정리합니다. CSV면 표준 컬럼도 함께 검사해요.",
    )
    parts = []
    use_sample = st.toggle("샘플 견적 사용", value=True, key="quote_sample")
    if use_sample:
        for key in ("견적 A", "견적 B"):
            path = sample_files()[key]
            if path.exists():
                parts.append(f"# {key}\n{load_sample(path)}")
                report = validate_quote_csv(path.name, path.read_bytes(), check_name=False)
                if report["ok"]:
                    st.caption(f"{key}: 표준 컬럼 OK · {report['row_count']}행")
                else:
                    st.caption(f"{key}: {', '.join(report['issues'])}")
        soft_card("샘플 견적 A / B", "합성 데이터로 비교 흐름만 보여줍니다.")
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
            if f.name.lower().endswith((".csv", ".xlsx")):
                report = validate_quote_csv(f.name, raw, check_name=False)
                if report["ok"]:
                    st.success(f"{f.name}: 표준 컬럼 OK")
                else:
                    st.warning(f"{f.name}: {'; '.join(report['issues']) or '검사 실패'}")

    st.write("")
    if st.button("비교하기", type="primary", use_container_width=True, key="quote_run"):
        quote_text = "\n\n".join(parts)
        if not quote_text.strip():
            st.warning("견적 자료를 넣어 주세요.")
        else:
            with st.spinner("비교 중…"):
                result = compare_quotations(model_name, company, quote_text)
            show_result("견적비교", result)
            st.session_state.quotes_done = True

    if st.session_state.get("quotes_done") or st.session_state.get("last_title") == "견적비교":
        soft_card("다음 단계", "견적·과업에 맞는 중진공 정책·자금을 확인하세요.")
        if st.button("다음 · 정책연계", type="primary", use_container_width=True, key="qt_to_pol"):
            navigate("정책연계")
    else:
        step_nav("업체 탐색", None, key_prefix="qt")


def page_csv_validate() -> None:
    page_header(
        "부가 · CSV",
        "표준 CSV인지<br>바로 검사해요",
        "필수 컬럼·숫자형·파일명(기업명_사업명_문서종류)을 확인합니다.",
    )
    soft_card(
        "필수 컬럼",
        ", ".join(COMPANY_METRICS_COLUMNS),
    )
    tpl = sample_files()["표준 템플릿"]
    if tpl.exists():
        st.download_button(
            "빈 표준 템플릿 받기",
            data=tpl.read_bytes(),
            file_name="템플릿_표준_기업현황.csv",
            mime="text/csv",
            use_container_width=True,
            key="dl_tpl",
        )

    use_sample = st.toggle("샘플 기업현황 검사", value=True, key="metrics_sample")
    if use_sample:
        path = sample_files()["표준 기업현황"]
        data = path.read_bytes()
        name = path.name
    else:
        uploaded = st.file_uploader("기업현황 CSV/XLSX", type=["csv", "xlsx"], key="metrics_up")
        if not uploaded:
            return
        data = uploaded.getvalue()
        name = uploaded.name

    if st.button("검사하기", type="primary", use_container_width=True, key="metrics_run"):
        report = validate_company_metrics(name, data)
        st.session_state["csv_report"] = report

    report = st.session_state.get("csv_report")
    if not report:
        return

    if report["ok"]:
        st.success(f"통과 · {report['row_count']}행 · {report['filename']}")
    else:
        st.error("미통과 — 아래를 고쳐 다시 올려 주세요.")
        for issue in report["issues"]:
            st.write(f"- {issue}")

    st.caption(report["filename_check"]["message"])
    if report.get("preview") is not None:
        st.dataframe(report["preview"], use_container_width=True)

    if report["ok"] and st.button("과업지시서 작성으로", type="primary", use_container_width=True):
        navigate("과업지시서 작성")


def page_policies(company: dict) -> None:
    st.session_state.policies_viewed = True
    page_header(
        "STEP 5",
        "정책·자금을<br>이어가요",
        "기술자금·스마트화 융자, 지역주도형 AI 대전환 등 개요·일정·신청·담당을 안내합니다.",
    )
    fit = st.session_state.get("fitness")
    if fit:
        soft_card(f"현재 기초체력 · {fit['label']}", fit["tip"])
    else:
        soft_card("기초체력 미실시", "STEP 1을 먼저 하면 추천이 더 정확해집니다.")

    render_policy_recs(company, context="work_order", key_prefix="pol_top")

    st.markdown("#### 정책 전체 카탈로그")
    for i, p in enumerate(POLICIES):
        item = dict(p)
        item["why"] = "카탈로그 — 필요 시 직접 확인하세요."
        policy_card(item)
        b1, b2 = st.columns(2)
        b1.link_button("신청·바로가기", p["apply_url"], use_container_width=True, key=f"pol_a_{i}")
        b2.link_button("상세 안내", p["info_url"], use_container_width=True, key=f"pol_i_{i}")

    soft_card("완료", "다섯 스텝을 모두 봤어요. 필요하면 처음부터 다시 진행하거나 더보기에서 CSV·진단을 보완하세요.")
    step_nav("견적비교", None, key_prefix="pol")


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

    page_header(
        "부가 기능",
        "필요할 때만<br>꺼내 쓰세요",
        "CSV 검증, 시스템 분석, 모델 비교를 모아 두었습니다. AX 보고서는 기초체력보기에서 업로드하세요.",
    )

    if choice == "보완 진단":
        soft_card("보완 진단", "보고서 업로드 외에 짧은 메모로 보완이 필요할 때만 쓰세요.")
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

    if page == "기초체력보기":
        page_fitness()
    elif page == "과업지시서 작성":
        page_work_order(model_name, company)
    elif page == "업체 탐색":
        page_vendors(company)
    elif page == "견적비교":
        page_quotes(model_name, company)
    elif page == "정책연계":
        page_policies(company)
    else:
        page_more(model_name, company)

    render_footer()


if __name__ == "__main__":
    main()
