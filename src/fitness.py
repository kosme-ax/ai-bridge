"""AX Data Fitness 자가진단 — 국민제안 '기초 체력 체크리스트' 실행 레이어."""

from __future__ import annotations

from typing import Any

# 거창한 기술평가가 아니라 데이터 기록·수집 습관만 묻는다.
FITNESS_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "q1",
        "text": "매출·비용·재고 등 핵심 숫자를 엑셀·ERP 등 디지털로 기록하나요?",
        "options": [("항상", 2), ("가끔", 1), ("거의 안 함", 0)],
    },
    {
        "id": "q2",
        "text": "고객·거래처 데이터를 파일이나 시스템으로 모아 두고 있나요?",
        "options": [("체계적으로", 2), ("부분적으로", 1), ("거의 없음", 0)],
    },
    {
        "id": "q3",
        "text": "공정·품질·출하 등 현장 데이터를 주기적으로 남기나요?",
        "options": [("주기적", 2), ("필요할 때만", 1), ("수기/기억", 0)],
    },
    {
        "id": "q4",
        "text": "직원 간에 같은 양식(템플릿)으로 자료를 주고받나요?",
        "options": [("표준 양식 있음", 2), ("부서마다 다름", 1), ("없음", 0)],
    },
    {
        "id": "q5",
        "text": "설비·사업 확장 시 '어떤 데이터를 모을지'를 미리 생각해 본 적 있나요?",
        "options": [("계획 있음", 2), ("생각해 봄", 1), ("아직 없음", 0)],
    },
    {
        "id": "q6",
        "text": "파일 이름·폴더를 규칙 있게 정리하나요? (예: 기업명_사업명_재무)",
        "options": [("규칙 준수", 2), ("가끔", 1), ("제각각", 0)],
    },
    {
        "id": "q7",
        "text": "AI·디지털 전환을 '수억 원 대형 시스템'이 아니라 작은 데이터 습관으로도 볼 수 있나요?",
        "options": [("그렇게 봄", 2), ("반반", 1), ("대형만 생각", 0)],
    },
    {
        "id": "q8",
        "text": "정량 지표(고용·매출 등)를 HWP 표가 아닌 CSV/엑셀로 제출할 준비가 되어 있나요?",
        "options": [("가능", 2), ("일부 가능", 1), ("어려움", 0)],
    },
]

# 중진공 연수원·디지털 역량 안내 (시연용 공개 링크)
EDUCATION_LINKS: list[dict[str, str]] = [
    {
        "title": "중진공 연수원 · 교육과정 안내",
        "url": "https://www.kosmes.or.kr/",
        "when": "low",
    },
    {
        "title": "K-Doctor AI진단 (현황 점검)",
        "url": "https://kdoctor.kosmes.or.kr/main.do?v=f",
        "when": "all",
    },
]


def score_fitness(answers: dict[str, int]) -> dict[str, Any]:
    max_score = sum(max(o[1] for o in q["options"]) for q in FITNESS_QUESTIONS)
    total = sum(int(answers.get(q["id"], 0)) for q in FITNESS_QUESTIONS)
    ratio = total / max_score if max_score else 0.0
    if ratio >= 0.75:
        level, label = "high", "준비됨"
        tip = "데이터 기초 체력이 양호합니다. 과업지시서·견적비교로 바로 이어가세요."
    elif ratio >= 0.45:
        level, label = "mid", "보완 필요"
        tip = "기록·수집은 시작됐지만 표준화·계획이 부족합니다. 짧은 교육 후 과업을 구체화하세요."
    else:
        level, label = "low", "기초 다지기"
        tip = "거창한 AI보다 엑셀·표준파일부터입니다. 아래 무료 교육으로 인식을 먼저 맞추세요."
    links = [
        x
        for x in EDUCATION_LINKS
        if x["when"] == "all" or (level == "low" and x["when"] == "low") or (level == "mid" and x["when"] == "low")
    ]
    return {
        "total": total,
        "max_score": max_score,
        "ratio": round(ratio, 3),
        "level": level,
        "label": label,
        "tip": tip,
        "education": links,
        "answers": answers,
    }
