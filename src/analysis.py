from __future__ import annotations

from typing import Any

from src.llm import generate_json


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
    """AX 지원용 과업지시서(핵심 산출물). 진단은 입력, 본 함수가 본업."""
    kdoctor = company.get("kdoctor") or {}
    context = (
        f"기업: {company}\n"
        f"K-Doctor 진단 연동: {kdoctor}\n"
        f"추가 진단/분석 결과: {diagnosis or {}}"
    )
    prompt = f"""키워드: work_order
당신은 중진공 AX 지원 담당자의 업무보조 AI입니다.
K-Doctor 등에서 이미 끝난 '기업진단'을 다시 하지 말고,
그 결과를 바탕으로 **AX 지원 과업지시서** 초안을 작성하십시오.
시장가격·임의 단가를 만들지 마십시오.

반드시 강조할 것:
- 과업 목적, 범위, 산출물, 일정(단계), 역할(발주/수행/검수), 검수기준, 위험·가정
- 진단 결과에서 도출된 우선 과제와의 연결

{context}

JSON 키: title, summary, objectives, scope, deliverables, schedule_phases,
roles, acceptance_criteria, assumptions, linked_diagnosis_points,
sections(객체), human_review_risks
"""
    return generate_json(model_name, "work_order", prompt, context)


def generate_rfp(
    model_name: str,
    company: dict[str, Any],
    diagnosis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """하위 호환: 과업지시서 생성으로 위임."""
    return generate_work_order(model_name, company, diagnosis)


def compare_quotations(model_name: str, company: dict[str, Any], quote_text: str) -> dict[str, Any]:
    context = (
        f"기업: {company.get('name')}\n"
        f"K-Doctor 연계 우선과제: {(company.get('kdoctor') or {}).get('priority_tasks')}\n"
        f"견적자료:\n{quote_text[:14000]}"
    )
    prompt = f"""키워드: quotation
AX 지원 과업지시서 이행을 위한 공급사 견적을 비교하십시오.
본 서비스의 핵심 산출물 중 하나입니다.
단가 차이만으로 부적정이라고 단정하지 마십시오. 확인되지 않은 시장가를 만들지 마십시오.
과업 범위·산출물·검수기준 관점에서 비교 포인트를 제시하십시오.

{context}

JSON 키: summary, currency, vendors(name,supply_amount,vat_amount,total_amount,notes),
scope_fit, comparison_notes, open_questions, recommendation, human_review_risks
"""
    return generate_json(model_name, "quotation", prompt, context)


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
