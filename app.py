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
from src.chatbot import build_context, reply_chat
from src.fitness import (
    QUESTION_BANK,
    adapt_question_with_ai,
    fitness_from_kdoctor,
    question_at,
    score_fitness,
    update_difficulty,
)
from src.policies import POLICIES, recommend_policies
from src.reports import to_docx_bytes, to_pdf_bytes
from src.sample_data import COMPANIES, sample_files
from src.ui import inject_styles, page_header, policy_card, render_footer, soft_card

st.set_page_config(
    page_title="AI-Bridge",
    page_icon="💠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

PAGES = ("기초체력", "과업지시서", "견적 비교", "정책연계", "더보기")


def init_state() -> None:
    st.session_state.setdefault("company_key", "한빛정밀")
    st.session_state.setdefault("last_result", None)
    st.session_state.setdefault("last_title", "")
    st.session_state.setdefault("fitness", None)
    st.session_state.setdefault("page", "기초체력")
    st.session_state.setdefault("more_choice", "CSV 검증")
    st.session_state.setdefault("chat_messages", [])
    st.session_state.setdefault("fit_path", None)  # None | kdoctor | quiz
    st.session_state.setdefault("fit_step", 0)
    st.session_state.setdefault("fit_difficulty", "normal")
    st.session_state.setdefault("fit_answers", {})
    st.session_state.setdefault("fit_answer_log", [])
    st.session_state.setdefault("fit_current_q", None)
    settings = runtime_settings()
    st.session_state.setdefault("model_name", settings["default_model"])


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
                "국민제안의 접수·서식(기시행) 위에, 기초체력 체크·CSV 검증·과업지시서·견적비교를 "
                "잇는 실행 레이어입니다. 시연은 합성 데이터만 사용합니다."
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


def render_chat_panel(model_name: str, company: dict, page: str) -> None:
    with st.expander("AI 상담 · 기초체력 · 과업 · 견적 · 정책", expanded=False):
        st.caption("자세히 묻고 싶을 때 여기서 이어가세요. 화면 메뉴와 같이 쓰면 좋아요.")
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        c1, c2, c3, c4 = st.columns(4)
        quick = None
        if c1.button("기초체력", use_container_width=True, key="chat_q_fit"):
            quick = "기초체력 결과가 어떻게 나왔고, 다음에 뭘 하면 좋을까요?"
        if c2.button("과업지시서", use_container_width=True, key="chat_q_wo"):
            quick = "과업지시서에 넣을 우선 과업을 짧게 잡아 주세요."
        if c3.button("견적", use_container_width=True, key="chat_q_qt"):
            quick = "견적 비교할 때 어떤 항목을 보면 되나요?"
        if c4.button("정책자금", use_container_width=True, key="chat_q_pol"):
            quick = "지금 기업에 맞는 중진공 기술자금이나 지역 AI 대전환을 알려 주세요."

        prompt = st.chat_input("궁금한 점을 입력하세요")
        user_text = quick or prompt
        if not user_text:
            return

        st.session_state.chat_messages.append({"role": "user", "content": user_text})
        context = build_context(
            company=company,
            fitness=st.session_state.get("fitness"),
            last_title=st.session_state.get("last_title") or "",
            last_result=st.session_state.get("last_result"),
            page=page,
        )
        history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.chat_messages[:-1]
            if m["role"] in ("user", "assistant")
        ]
        with st.spinner("답변 작성 중…"):
            answer = reply_chat(model_name, history, user_text, context)
        st.session_state.chat_messages.append({"role": "assistant", "content": answer})
        st.rerun()


def render_education(fit: dict) -> None:
    if fit["level"] == "high":
        return
    soft_card("맞춤 교육 안내", fit["tip"])
    for link in fit.get("education") or []:
        st.link_button(link["title"], link["url"], use_container_width=True)


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
    st.session_state.fit_difficulty = "normal"
    st.session_state.fit_answers = {}
    st.session_state.fit_answer_log = []
    st.session_state.fit_current_q = None


def _render_fitness_result(company: dict) -> None:
    fit = st.session_state.get("fitness")
    if not fit:
        return
    src = "K-Doctor 연동" if fit.get("source") == "kdoctor" else "적응형 문항"
    st.metric("기초체력", f"{fit['label']}  {fit['total']}/{fit['max_score']}")
    st.caption(f"산출 경로: {src}")
    st.write(fit["tip"])
    if fit.get("kdoctor_summary"):
        soft_card("K-Doctor 요약", fit["kdoctor_summary"])
    if fit.get("priority_tasks"):
        soft_card("우선 과제", " · ".join(fit["priority_tasks"]))
    render_education(fit)
    render_policy_recs(company, context="fitness", key_prefix="fit")
    st.write("")
    soft_card("다음 단계", "표준 CSV를 검증하거나 과업지시서를 작성하세요.")
    c1, c2, c3 = st.columns(3)
    if c1.button("처음부터", use_container_width=True, key="fit_restart"):
        st.session_state.fitness = None
        st.session_state.fit_path = None
        _reset_quiz_state()
        st.rerun()
    if c2.button("CSV 검증으로", use_container_width=True, key="go_csv"):
        navigate("더보기", more="CSV 검증")
    if c3.button("과업지시서로", type="primary", use_container_width=True, key="go_wo"):
        navigate("과업지시서")


def page_fitness() -> None:
    company = COMPANIES[st.session_state.company_key]
    model_name = st.session_state.model_name

    page_header(
        "고도화 ①",
        "기초 체력,<br>진단부터 확인할게요",
        "K-Doctor를 했으면 데이터를 불러오고, 아니면 수준에 맞춰 문항이 달라집니다.",
    )

    if st.session_state.get("fitness"):
        _render_fitness_result(company)
        return

    # --- Gate: K-Doctor 여부 ---
    if st.session_state.fit_path is None:
        soft_card(
            "먼저 확인할게요",
            "중진공 K-Doctor(AI진단)를 이미 하셨나요? 하셨다면 합성 연동 데이터로 불러옵니다.",
        )
        a1, a2 = st.columns(2)
        if a1.button("네, 진단했어요", type="primary", use_container_width=True, key="fit_kd_yes"):
            st.session_state.fit_path = "kdoctor"
            st.rerun()
        if a2.button("아직 안 했어요", use_container_width=True, key="fit_kd_no"):
            st.session_state.fit_path = "quiz"
            _reset_quiz_state()
            st.rerun()
        st.link_button(
            "K-Doctor 바로가기",
            "https://kdoctor.kosmes.or.kr/main.do?v=f",
            use_container_width=True,
        )
        return

    # --- Path A: K-Doctor pull (test data) ---
    if st.session_state.fit_path == "kdoctor":
        kd = company.get("kdoctor") or {}
        soft_card(
            f"연동 준비 · {kd.get('diagnosis_id', '-')}",
            f"{company['name']} / AX수준 {kd.get('ax_level')} / {kd.get('status')}",
        )
        st.write(kd.get("summary", ""))
        if kd.get("priority_tasks"):
            st.markdown("**우선 과제**")
            for t in kd["priority_tasks"]:
                st.write(f"- {t}")
        st.caption(
            f"시연용 테스트 데이터입니다. (pulled_at: {kd.get('pulled_at', '-')}) "
            "실 API 연동 전 단계예요."
        )
        b1, b2 = st.columns(2)
        if b1.button("뒤로", use_container_width=True, key="fit_kd_back"):
            st.session_state.fit_path = None
            st.rerun()
        if b2.button("이 진단으로 기초체력 산출", type="primary", use_container_width=True, key="fit_kd_pull"):
            st.session_state.last_result = {
                "summary": kd.get("summary"),
                "source": "kdoctor",
                "diagnosis_id": kd.get("diagnosis_id"),
                "priority_tasks": kd.get("priority_tasks"),
                "ax_level": kd.get("ax_level"),
            }
            st.session_state.last_title = "K-Doctor연동"
            st.session_state.fitness = fitness_from_kdoctor(kd, company)
            st.rerun()
        return

    # --- Path B: adaptive quiz (one question at a time) ---
    step = int(st.session_state.fit_step)
    total = len(QUESTION_BANK)
    if step >= total:
        # safety
        qs = [question_at(i, "normal") for i in range(total)]
        st.session_state.fitness = score_fitness(st.session_state.fit_answers, questions=qs, source="quiz")
        st.rerun()
        return

    if st.session_state.fit_current_q is None:
        q = question_at(step, st.session_state.fit_difficulty)
        q = adapt_question_with_ai(
            q,
            previous_answers=st.session_state.fit_answer_log,
            company_name=company.get("name", ""),
            model_name=model_name,
            chat_fn=reply_chat,
        )
        st.session_state.fit_current_q = q
    else:
        q = st.session_state.fit_current_q

    st.progress((step) / total, text=f"문항 {step + 1} / {total} · 난이도 {q['difficulty']}")
    soft_card(q["topic"], "직전 답에 맞춰 질문 수준을 조정했어요." if step else "첫 문항부터 시작해 볼게요.")
    if q.get("ai_rewritten"):
        st.caption("AI가 문항 문구를 다듬었습니다.")

    labels = [o[0] for o in q["options"]]
    scores = {o[0]: o[1] for o in q["options"]}
    choice = st.radio(q["text"], labels, horizontal=True, key=f"fit_step_{step}_{q['difficulty']}")

    c1, c2 = st.columns(2)
    if c1.button("이전 경로로", use_container_width=True, key="fit_quiz_back"):
        st.session_state.fit_path = None
        _reset_quiz_state()
        st.rerun()
    if c2.button("다음", type="primary", use_container_width=True, key="fit_quiz_next"):
        score = scores[choice]
        st.session_state.fit_answers[q["id"]] = score
        st.session_state.fit_answer_log.append(
            {
                "id": q["id"],
                "topic": q["topic"],
                "difficulty": q["difficulty"],
                "choice_label": choice,
                "score": score,
                "text": q["text"],
            }
        )
        st.session_state.fit_difficulty = update_difficulty(st.session_state.fit_difficulty, score)
        st.session_state.fit_step = step + 1
        st.session_state.fit_current_q = None
        if st.session_state.fit_step >= total:
            used = [
                {
                    "id": row["id"],
                    "text": row["text"],
                    "options": next(
                        b["levels"][row["difficulty"]]["options"]
                        for b in QUESTION_BANK
                        if b["id"] == row["id"]
                    ),
                }
                for row in st.session_state.fit_answer_log
            ]
            st.session_state.fitness = score_fitness(
                st.session_state.fit_answers,
                questions=used,
                source="quiz",
                extra={"answer_log": st.session_state.fit_answer_log},
            )
        st.rerun()


def page_work_order(model_name: str, company: dict) -> None:
    page_header(
        "핵심 기능",
        "과업지시서를<br>바로 작성해요",
        "K-Doctor 진단과 기초체력 결과를 반영해 AX 지원 과업지시서 초안을 만듭니다.",
    )
    fit = st.session_state.get("fitness")
    if fit:
        soft_card(f"기초체력 · {fit['label']}", fit["tip"])
        render_education(fit)
    else:
        soft_card("기초체력 미실시", "먼저 「기초체력」에서 8문항을 체크하면 과업 톤이 맞춰집니다.")

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

    if st.session_state.get("last_title") == "AX과업지시서":
        render_policy_recs(company, context="work_order", key_prefix="wo")


def page_quotes(model_name: str, company: dict) -> None:
    page_header(
        "핵심 기능",
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

    if st.session_state.get("last_title") == "견적비교":
        render_policy_recs(company, context="quote", key_prefix="qt")


def page_csv_validate() -> None:
    page_header(
        "고도화 ②",
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
        navigate("과업지시서")


def page_policies(company: dict) -> None:
    page_header(
        "정책 킥",
        "결과에 맞는<br>중진공 사업을 이어가요",
        "기술자금·스마트화 융자, 지역주도형 AI 대전환 등 개요·일정·신청·담당을 안내합니다.",
    )
    fit = st.session_state.get("fitness")
    if fit:
        soft_card(f"현재 기초체력 · {fit['label']}", fit["tip"])
    else:
        soft_card("기초체력 미실시", "기초체력을 먼저 하면 추천이 더 정확해집니다.")

    render_policy_recs(company, context="work_order", key_prefix="pol_top")

    st.markdown("#### 전체 카탈로그")
    for i, p in enumerate(POLICIES):
        item = dict(p)
        item["why"] = "카탈로그 — 필요 시 직접 확인하세요."
        policy_card(item)
        b1, b2 = st.columns(2)
        b1.link_button("신청·바로가기", p["apply_url"], use_container_width=True, key=f"pol_a_{i}")
        b2.link_button("상세 안내", p["info_url"], use_container_width=True, key=f"pol_i_{i}")


def page_more(model_name: str, company: dict) -> None:
    choice = st.radio(
        "선택",
        ("CSV 검증", "K-Doctor 연동", "시스템 분석", "모델 비교"),
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
        "진단 연동, 시스템 분석, 모델 비교를 모아 두었습니다.",
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
            navigate("과업지시서")

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
    apply_pending_nav()
    inject_styles()
    model_name, company = sidebar()

    page = st.radio(
        "메뉴",
        PAGES,
        horizontal=True,
        label_visibility="collapsed",
        key="page",
    )

    render_chat_panel(model_name, company, page)

    if page == "기초체력":
        page_fitness()
    elif page == "과업지시서":
        page_work_order(model_name, company)
    elif page == "견적 비교":
        page_quotes(model_name, company)
    elif page == "정책연계":
        page_policies(company)
    else:
        page_more(model_name, company)

    render_footer()


if __name__ == "__main__":
    main()
