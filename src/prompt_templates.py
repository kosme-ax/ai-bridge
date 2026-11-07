"""내부 생성 프롬프트 — UI·다운로드·로그에 노출하지 않음."""

from __future__ import annotations

from typing import Any


def work_order_prompt(*, context: str, ai_areas: list[str], ai_problems: list[str]) -> str:
    areas = ", ".join(ai_areas) if ai_areas else "(미선택)"
    problems = ", ".join(ai_problems) if ai_problems else "(미선택)"
    return f"""키워드: work_order
역할: 중진공 AX 지원 담당자의 업무보조. 진단은 다시 하지 말고, 입력된 기초체력·보고서 결과만 반영한다.
출력: 국민제안에서 요구하는 **표준 RFP(제안요청서) / 과업지시서** 초안. 한국어. 시장가·임의 단가 금지.

핵심 입력(반드시 본문에 구체 반영):
- AI 적용 희망 영역: {areas}
- 해결하고 싶은 문제: {problems}

문서 구성(표준 RFP 항목 — sections에 아래 키로 상세 서술, 각 항목 3~8문장 수준):
1) 사업개요
2) 추진배경및필요성
3) 현황및문제점 — 기초체력 설문·보고서의 영역/문제를 인용해 작성
4) 기초체력진단요약 — 업종, 적용영역, 해결문제, 사업·데이터·운영 준비도 요지
5) 사업목표 — 측정 가능한 목표(정성·정량 후보, 수치 단정 금지)
6) 과업범위 — In/Out of Scope 구분
7) 세부과업내용 — 단계별 과업(착수·설계·구축·시험·이관)
8) 기능요구사항
9) 데이터요구사항 — 수집·품질·반출·학습데이터
10) 보안요구사항
11) 추진일정 — 단계·주 단위 초안(가정 명시)
12) 역할분담 — 발주(기업)·수행(공급사)·검수(중진공/기업)
13) 산출물
14) 검수및테스트기준
15) 제안요청및평가기준 — 기술·보안·유지보수·범위 적합도 (단가만으로 평가 금지)
16) 제출서류

추가 JSON 키:
- title, summary, document_type("표준RFP/과업지시서")
- target_ai_areas, target_problems
- objectives(list), scope(object: in_scope, out_of_scope)
- deliverables(list), schedule_phases(list of {{phase,weeks,tasks}})
- roles(object), acceptance_criteria(list)
- fitness_basis(object: industry, ai_areas, ai_problems, level, tip)
- linked_diagnosis_points(list), assumptions(list), human_review_risks(list)
- sections(object: 위 1~16 키)

입력 컨텍스트:
{context}
"""


def quotation_prompt(*, context: str) -> str:
    return f"""키워드: quotation
AX 지원 표준 RFP/과업지시서 이행을 위한 공급사 견적을 비교하십시오.
단가 차이만으로 부적정이라고 단정하지 마십시오. 확인되지 않은 시장가를 만들지 마십시오.
과업 범위·산출물·검수기준·보안·유지보수 관점에서 비교하십시오.

{context}

JSON 키: summary, currency, vendors(name,supply_amount,vat_amount,total_amount,notes),
scope_fit, comparison_notes, open_questions, recommendation, human_review_risks
"""


def build_fitness_context(fitness: dict[str, Any] | None) -> str:
    if not fitness:
        return "기초체력: 미실시"
    answers = fitness.get("answers") or {}
    answer_log = fitness.get("answer_log") or []
    lines = [
        f"등급: {fitness.get('label')} ({fitness.get('total')}/{fitness.get('max_score')})",
        f"업종: {fitness.get('industry')}",
        f"AI적용영역: {fitness.get('ai_areas')}",
        f"해결문제: {fitness.get('ai_problems')}",
        f"우선과제: {fitness.get('priority_tasks')}",
        f"요약팁: {fitness.get('tip')}",
        f"보고서요약: {fitness.get('kdoctor_summary')}",
        f"문항점수: {answers}",
    ]
    if answer_log:
        lines.append("문항응답:")
        for row in answer_log:
            lines.append(
                f"- {row.get('id')} {row.get('topic')}: {row.get('choice_label')} ({row.get('score')})"
            )
    return "\n".join(str(x) for x in lines)
