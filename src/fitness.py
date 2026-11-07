"""AX Data Fitness — K-Doctor 연동 분기 + 적응형 문항."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

# 주제별 난이도 변형 (낮음=쉬운 말 / 높음=디지털·AX 용어)
QUESTION_BANK: list[dict[str, Any]] = [
    {
        "id": "q1",
        "topic": "디지털 기록",
        "levels": {
            "easy": {
                "text": "매출·비용·재고 같은 숫자를 노트·카톡이 아니라 엑셀이나 컴퓨터 파일로 남겨 두나요?",
                "options": [("자주 파일로 남김", 2), ("가끔", 1), ("거의 안 함", 0)],
            },
            "normal": {
                "text": "매출·비용·재고 등 핵심 숫자를 엑셀·ERP 등 디지털로 기록하나요?",
                "options": [("항상", 2), ("가끔", 1), ("거의 안 함", 0)],
            },
            "hard": {
                "text": "핵심 경영지표가 ERP/BI 등 시스템에서 자동 집계되고 있나요?",
                "options": [("자동 집계", 2), ("일부 수동", 1), ("대부분 수기", 0)],
            },
        },
    },
    {
        "id": "q2",
        "topic": "고객 데이터",
        "levels": {
            "easy": {
                "text": "거래처 이름·연락처·주문 내용을 어딘가 파일로 모아 두나요?",
                "options": [("파일로 모아 둠", 2), ("일부만", 1), ("거의 기억/수첩", 0)],
            },
            "normal": {
                "text": "고객·거래처 데이터를 파일이나 시스템으로 모아 두고 있나요?",
                "options": [("체계적으로", 2), ("부분적으로", 1), ("거의 없음", 0)],
            },
            "hard": {
                "text": "고객·거래 이력이 CRM·DB로 통합되어 조회 가능한가요?",
                "options": [("통합됨", 2), ("분산됨", 1), ("없음", 0)],
            },
        },
    },
    {
        "id": "q3",
        "topic": "현장 데이터",
        "levels": {
            "easy": {
                "text": "불량·출하·작업 내용을 나중에 볼 수 있게 적어 두나요?",
                "options": [("꼬박꼬박", 2), ("가끔", 1), ("거의 안 적음", 0)],
            },
            "normal": {
                "text": "공정·품질·출하 등 현장 데이터를 주기적으로 남기나요?",
                "options": [("주기적", 2), ("필요할 때만", 1), ("수기/기억", 0)],
            },
            "hard": {
                "text": "현장 센서·설비 로그가 수집·저장되고 있나요?",
                "options": [("수집 중", 2), ("일부", 1), ("없음", 0)],
            },
        },
    },
    {
        "id": "q4",
        "topic": "양식 표준",
        "levels": {
            "easy": {
                "text": "직원끼리 비슷한 엑셀 양식으로 자료를 주고받나요?",
                "options": [("비슷한 양식 씀", 2), ("사람마다 다름", 1), ("양식 없음", 0)],
            },
            "normal": {
                "text": "직원 간에 같은 양식(템플릿)으로 자료를 주고받나요?",
                "options": [("표준 양식 있음", 2), ("부서마다 다름", 1), ("없음", 0)],
            },
            "hard": {
                "text": "마스터 데이터·코드 체계가 전사 표준으로 관리되나요?",
                "options": [("표준 관리", 2), ("부분", 1), ("없음", 0)],
            },
        },
    },
    {
        "id": "q5",
        "topic": "데이터 계획",
        "levels": {
            "easy": {
                "text": "새 설비·사업을 할 때 '나중에 뭐라도 기록해 둘까' 생각해 본 적 있나요?",
                "options": [("생각해 봄", 2), ("조금", 1), ("아직 없음", 0)],
            },
            "normal": {
                "text": "설비·사업 확장 시 '어떤 데이터를 모을지'를 미리 생각해 본 적 있나요?",
                "options": [("계획 있음", 2), ("생각해 봄", 1), ("아직 없음", 0)],
            },
            "hard": {
                "text": "투자·설비 도입 시 데이터 수집·활용 KPI가 문서화되어 있나요?",
                "options": [("문서화", 2), ("구두 수준", 1), ("없음", 0)],
            },
        },
    },
    {
        "id": "q6",
        "topic": "파일 정리",
        "levels": {
            "easy": {
                "text": "파일 이름을 알아볼 수 있게 짓나요? (예: 회사명_견적_날짜)",
                "options": [("규칙 있게", 2), ("가끔", 1), ("제각각", 0)],
            },
            "normal": {
                "text": "파일 이름·폴더를 규칙 있게 정리하나요? (예: 기업명_사업명_재무)",
                "options": [("규칙 준수", 2), ("가끔", 1), ("제각각", 0)],
            },
            "hard": {
                "text": "문서·데이터 자산의 네이밍·보관 정책이 있나요?",
                "options": [("정책 있음", 2), ("관행만", 1), ("없음", 0)],
            },
        },
    },
    {
        "id": "q7",
        "topic": "AX 인식",
        "levels": {
            "easy": {
                "text": "AI가 꼭 비싼 큰 컴퓨터여야 한다고 생각하나요, 아니면 작은 기록 습관부터도 된다고 보나요?",
                "options": [("작은 습관부터", 2), ("잘 모르겠음", 1), ("큰 것만 AI", 0)],
            },
            "normal": {
                "text": "AI·디지털 전환을 '수억 원 대형 시스템'이 아니라 작은 데이터 습관으로도 볼 수 있나요?",
                "options": [("그렇게 봄", 2), ("반반", 1), ("대형만 생각", 0)],
            },
            "hard": {
                "text": "AX 로드맵에 데이터 기반 과제와 PoC 우선순위가 정리되어 있나요?",
                "options": [("정리됨", 2), ("초안만", 1), ("없음", 0)],
            },
        },
    },
    {
        "id": "q8",
        "topic": "기계판독",
        "levels": {
            "easy": {
                "text": "고용·매출 숫자를 한글(HWP) 표가 아니라 엑셀로도 뽑아 줄 수 있나요?",
                "options": [("엑셀로 가능", 2), ("일부 가능", 1), ("어려움", 0)],
            },
            "normal": {
                "text": "정량 지표(고용·매출 등)를 HWP 표가 아닌 CSV/엑셀로 제출할 준비가 되어 있나요?",
                "options": [("가능", 2), ("일부 가능", 1), ("어려움", 0)],
            },
            "hard": {
                "text": "정량 지표를 표준 스키마(CSV)로 반복 제출할 수 있는 프로세스가 있나요?",
                "options": [("프로세스 있음", 2), ("수작업 변환", 1), ("없음", 0)],
            },
        },
    },
]

EDUCATION_LINKS: list[dict[str, str]] = [
    {"title": "중진공 연수원 · 교육과정 안내", "url": "https://www.kosmes.or.kr/", "when": "low"},
    {"title": "K-Doctor AI진단 (현황 점검)", "url": "https://kdoctor.kosmes.or.kr/main.do?v=f", "when": "all"},
]

# 하위 호환: 기본(normal) 문항 목록
FITNESS_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": q["id"],
        "text": q["levels"]["normal"]["text"],
        "options": q["levels"]["normal"]["options"],
        "topic": q["topic"],
    }
    for q in QUESTION_BANK
]


def update_difficulty(current: str, last_score: int) -> str:
    """직전 답 점수로 난이도 조절. 0→쉽게, 2→어렵게."""
    order = ["easy", "normal", "hard"]
    idx = order.index(current) if current in order else 1
    if last_score <= 0:
        idx = max(0, idx - 1)
    elif last_score >= 2:
        idx = min(2, idx + 1)
    return order[idx]


def question_at(index: int, difficulty: str) -> dict[str, Any]:
    bank = QUESTION_BANK[index]
    level = difficulty if difficulty in bank["levels"] else "normal"
    payload = bank["levels"][level]
    return {
        "id": bank["id"],
        "topic": bank["topic"],
        "difficulty": level,
        "text": payload["text"],
        "options": payload["options"],
        "index": index,
        "total": len(QUESTION_BANK),
    }


def adapt_question_with_ai(
    question: dict[str, Any],
    *,
    previous_answers: list[dict[str, Any]],
    company_name: str,
    model_name: str,
    chat_fn: Callable[..., str] | None = None,
) -> dict[str, Any]:
    """AI가 문항 문구를 다듬음. 실패·무키면 원문 유지."""
    if chat_fn is None:
        return question
    hist = "\n".join(
        f"- {a.get('topic')}: {a.get('choice_label')} (난이도 {a.get('difficulty')})"
        for a in previous_answers[-3:]
    ) or "(없음)"
    prompt = (
        f"기업: {company_name}\n"
        f"현재 난이도: {question['difficulty']}\n"
        f"직전 응답: {hist}\n"
        f"원문 문항: {question['text']}\n"
        f"선택지: {[o[0] for o in question['options']]}\n\n"
        "위 문항을 같은 의미·같은 3개 선택지 점수로, 응답자가 이해하기 쉽게 "
        "한 문장으로만 다시 쓰세요. 선택지 문구는 바꾸지 마세요. "
        "설명·따옴표·접두어 없이 문항 문장만 출력하세요."
    )
    try:
        rewritten = chat_fn(model_name, [], prompt, "{}").strip()
        if 8 < len(rewritten) < 120 and "\n" not in rewritten:
            out = deepcopy(question)
            out["text"] = rewritten.lstrip("-• ").strip()
            out["ai_rewritten"] = True
            return out
    except Exception:
        pass
    return question


def score_fitness(
    answers: dict[str, int],
    *,
    questions: list[dict[str, Any]] | None = None,
    source: str = "quiz",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    qs = questions or FITNESS_QUESTIONS
    max_score = sum(max(o[1] for o in q["options"]) for q in qs) or 1
    total = sum(int(answers.get(q["id"], 0)) for q in qs)
    ratio = total / max_score
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
        if x["when"] == "all" or level in ("low", "mid") and x["when"] == "low"
    ]
    result = {
        "total": total,
        "max_score": max_score,
        "ratio": round(ratio, 3),
        "level": level,
        "label": label,
        "tip": tip,
        "education": links,
        "answers": answers,
        "source": source,
    }
    if extra:
        result.update(extra)
    return result


def fitness_from_kdoctor(kdoctor: dict[str, Any], company: dict[str, Any]) -> dict[str, Any]:
    """K-Doctor 연동(합성) 데이터 → 기초체력 결과로 변환."""
    df = kdoctor.get("data_fitness") or {}
    answers = {
        "q1": int(df.get("digital_record", 1)),
        "q2": int(df.get("customer_data", 1)),
        "q3": int(df.get("shopfloor_data", 1)),
        "q4": int(df.get("template_std", 1)),
        "q5": int(df.get("data_plan", 1)),
        "q6": int(df.get("naming", 1)),
        "q7": int(df.get("ax_mindset", 1)),
        "q8": int(df.get("machine_readable", 1)),
    }
    tip_map = {
        "초기": "K-Doctor AX수준이 초기입니다. 기초 기록 습관·교육 연계를 권합니다.",
        "중간": "K-Doctor 진단 완료·AX 중간 수준입니다. 과업지시서로 우선과제를 문서화하세요.",
        "높음": "K-Doctor 기준 준비가 양호합니다. 견적·정책자금 연계로 실행하세요.",
    }
    ax = str(kdoctor.get("ax_level") or "")
    result = score_fitness(
        answers,
        source="kdoctor",
        extra={
            "kdoctor_id": kdoctor.get("diagnosis_id"),
            "kdoctor_summary": kdoctor.get("summary"),
            "priority_tasks": kdoctor.get("priority_tasks") or [],
            "company_name": company.get("name"),
            "pulled_at": kdoctor.get("pulled_at"),
            "tip": tip_map.get(ax) or tip_map["중간"],
        },
    )
    # ax_level로 label 보정 (데이터 점수와 함께)
    if ax == "초기" and result["level"] == "high":
        result["level"], result["label"] = "mid", "보완 필요"
    return result
