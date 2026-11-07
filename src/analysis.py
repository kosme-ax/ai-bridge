from __future__ import annotations

from typing import Any

from src.llm import generate_json
from src.prompt_templates import build_fitness_context, quotation_prompt, work_order_prompt


def diagnose(model_name: str, company: dict[str, Any], extra_text: str = "") -> dict[str, Any]:
    profile = "\n".join(
        [
            f"기업명: {company.get('name')}",
            f"업종: {company.get('industry')}",
            f"인원: {company.get('employees')}",
            f"주요업무: {company.get('main_tasks')}",
            f"IT현황: {company.get('it_summary')}",
            f"고충: {company.get('pain_points')}",
            extra_text[:12000],
        ]
    )
    prompt = f"""키워드: diagnosis
다음 가상/합성 기업 자료를 바탕으로 AX 도입 진단을 수행하십시오.

{profile}

JSON 키: summary, ax_readiness(high|medium|low|unknown), problems(title,detail,severity), candidate_tasks, data_gaps, human_review_risks
"""
    return generate_json(model_name, "diagnosis", prompt, profile)


def analyze_systems(model_name: str, company: dict[str, Any], doc_text: str) -> dict[str, Any]:
    context = f"기업: {company.get('name')}\n자료:\n{doc_text[:14000]}"
    prompt = f"""키워드: systems
기존 시스템/업무 문서를 분석하십시오.

{context}

JSON 키: summary, duplicate_functions, manual_work, data_silos, legacy_risks, ai_applicable_work, integration_needs, human_review_risks
"""
    return generate_json(model_name, "systems", prompt, context)


def generate_work_order(
    model_name: str,
    company: dict[str, Any],
    diagnosis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """표준 RFP/과업지시서 초안. 상세 프롬프트는 UI에 노출하지 않음."""
    kdoctor = company.get("kdoctor") or {}
    fitness = company.get("fitness") or (diagnosis or {}).get("fitness") or {}
    ai_areas = list(fitness.get("ai_areas") or kdoctor.get("ai_areas") or [])
    ai_problems = list(fitness.get("ai_problems") or kdoctor.get("ai_problems") or [])
    extra = {
        k: v
        for k, v in (diagnosis or {}).items()
        if k not in {"fitness", "kdoctor"} and not str(k).startswith("_")
    }
    context = "\n".join(
        [
            f"기업명: {company.get('name')}",
            f"업종: {company.get('industry')}",
            f"인원: {company.get('employees')}",
            f"주요업무: {company.get('main_tasks')}",
            f"IT현황: {company.get('it_summary')}",
            f"고충: {company.get('pain_points')}",
            f"K-Doctor: {kdoctor.get('diagnosis_id')} / AX수준 {kdoctor.get('ax_level')}",
            f"K-Doctor요약: {kdoctor.get('summary')}",
            f"K-Doctor우선과제: {kdoctor.get('priority_tasks')}",
            build_fitness_context(fitness),
            f"추가입력키: {list(extra.keys())}",
        ]
    )
    # 프롬프트 본문은 생성에만 사용 · 반환 JSON에 넣지 않음
    prompt = work_order_prompt(context=context, ai_areas=ai_areas, ai_problems=ai_problems)
    result = generate_json(model_name, "work_order", prompt, context)
    # 안전: 프롬프트 키가 섞여 있으면 제거
    for key in ("_prompt", "prompt", "raw_prompt", "system_prompt"):
        result.pop(key, None)
    result.setdefault("document_type", "표준RFP/과업지시서")
    result.setdefault(
        "fitness_basis",
        {
            "industry": fitness.get("industry") or company.get("industry"),
            "ai_areas": ai_areas,
            "ai_problems": ai_problems,
            "level": fitness.get("level"),
            "label": fitness.get("label"),
            "tip": fitness.get("tip"),
        },
    )
    result.setdefault("target_ai_areas", ai_areas)
    result.setdefault("target_problems", ai_problems)
    return result


def generate_rfp(
    model_name: str,
    company: dict[str, Any],
    diagnosis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return generate_work_order(model_name, company, diagnosis)


def compare_quotations(model_name: str, company: dict[str, Any], quote_text: str) -> dict[str, Any]:
    context = (
        f"기업: {company.get('name')}\n"
        f"K-Doctor 연계 우선과제: {(company.get('kdoctor') or {}).get('priority_tasks')}\n"
        f"기초체력: {build_fitness_context(company.get('fitness'))}\n"
        f"견적자료:\n{quote_text[:14000]}"
    )
    prompt = quotation_prompt(context=context)
    result = generate_json(model_name, "quotation", prompt, context)
    for key in ("_prompt", "prompt", "raw_prompt", "system_prompt"):
        result.pop(key, None)
    return result


def compare_models(model_a: str, model_b: str, company: dict[str, Any], question: str) -> dict[str, Any]:
    context = f"기업: {company}\n질문: {question}"
    a = generate_json(
        model_a,
        "compare",
        f"키워드: multimodel\n동일 질문에 답하십시오.\n{context}\nJSON 키: summary, final_opinion, human_review_risks",
        context,
    )
    b = generate_json(
        model_b,
        "compare",
        f"키워드: multimodel\n동일 질문에 답하십시오.\n{context}\nJSON 키: summary, final_opinion, human_review_risks",
        context,
    )
    return {
        "question": question,
        "model_a": {"name": model_a, "result": a},
        "model_b": {"name": model_b, "result": b},
        "note": "동일 입력에 대한 두 모델 결과입니다. 최종 판단은 담당자가 합니다.",
    }
