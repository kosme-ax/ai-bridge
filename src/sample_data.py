from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples"

# K-Doctor(기업진단) 완료 기업을 가정한 합성 연동 데이터.
# 실제 API 연동 전 시연용이며, 본 앱의 핵심은 진단 자체가 아니라
# 진단 결과를 받아 AX 지원 과업지시서·견적 비교로 이어가는 후속 업무다.
COMPANIES = {
    "한빛정밀": {
        "name": "(합성) 한빛정밀",
        "industry": "자동차 부품 가공",
        "employees": 85,
        "main_tasks": "CNC 가공, 외관 검사, 출하, 월마감",
        "it_summary": "ERP + 현장 엑셀 + 구형 수주 프로그램",
        "pain_points": "월마감 수기 집계, 검사 숙련자 의존, 생산-영업 데이터 단절",
        "note": "K-Doctor 진단 완료를 가정한 시연용 가상 기업입니다.",
        "kdoctor": {
            "source": "https://kdoctor.kosmes.or.kr/main.do?v=f",
            "diagnosis_id": "KD-SIM-HB-2025-001",
            "status": "진단완료",
            "ax_level": "중간",
            "summary": (
                "내부역량·외부환경 진단 결과, 생산-영업 데이터 단절과 검사 숙련 의존이 "
                "성장 저해 요인으로 도출됨. AX 우선과제는 품질검사 보조와 월마감 자동화."
            ),
            "priority_tasks": [
                "외관검사 AI 보조 도입 범위 정의",
                "ERP-현장 데이터 연계 과업 명세",
                "월마감 자동화 PoC 과업지시서 작성",
            ],
        },
    },
    "푸른식품": {
        "name": "(합성) 푸른식품",
        "industry": "식품 제조",
        "employees": 60,
        "main_tasks": "배합, 품질검사, 출고, 거래처 정산",
        "it_summary": "MES 일부 + 엑셀 정산",
        "pain_points": "라벨 수작업, 재고 실사 오차, 거래처별 단가표 분산",
        "note": "K-Doctor 진단 완료를 가정한 시연용 가상 기업입니다.",
        "kdoctor": {
            "source": "https://kdoctor.kosmes.or.kr/main.do?v=f",
            "diagnosis_id": "KD-SIM-PR-2025-014",
            "status": "진단완료",
            "ax_level": "초기",
            "summary": (
                "라벨·재고·거래처 단가의 수기 비중이 높아 내부 효율 저하. "
                "AX 지원은 라벨 자동화와 정산 데이터 표준화 과업이 우선."
            ),
            "priority_tasks": [
                "라벨 자동화 과업 범위·검수기준 작성",
                "재고 실사 오차 개선 과업지시서",
                "거래처 단가표 통합 RFP/견적 비교",
            ],
        },
    },
}


def sample_files() -> dict[str, Path]:
    return {
        "진단 메모": SAMPLES / "hanbit_diagnosis.txt",
        "시스템 목록": SAMPLES / "hanbit_systems.csv",
        "견적 A": SAMPLES / "quote_a.csv",
        "견적 B": SAMPLES / "quote_b.csv",
    }
