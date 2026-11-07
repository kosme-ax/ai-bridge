from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples"

COMPANIES = {
    "한빛정밀": {
        "name": "(합성) 한빛정밀",
        "industry": "자동차 부품 가공",
        "employees": 85,
        "main_tasks": "CNC 가공, 외관 검사, 출하, 월마감",
        "it_summary": "ERP + 현장 엑셀 + 구형 수주 프로그램",
        "pain_points": "월마감 수기 집계, 검사 숙련자 의존, 생산-영업 데이터 단절",
        "note": "대회 시연용 가상 기업입니다. 실제 기업 정보가 아닙니다.",
    },
    "푸른식품": {
        "name": "(합성) 푸른식품",
        "industry": "식품 제조",
        "employees": 60,
        "main_tasks": "배합, 품질검사, 출고, 거래처 정산",
        "it_summary": "MES 일부 + 엑셀 정산",
        "pain_points": "라벨 수작업, 재고 실사 오차, 거래처별 단가표 분산",
        "note": "대회 시연용 가상 기업입니다. 실제 기업 정보가 아닙니다.",
    },
}


def sample_files() -> dict[str, Path]:
    return {
        "진단 메모": SAMPLES / "hanbit_diagnosis.txt",
        "시스템 목록": SAMPLES / "hanbit_systems.csv",
        "견적 A": SAMPLES / "quote_a.csv",
        "견적 B": SAMPLES / "quote_b.csv",
    }
