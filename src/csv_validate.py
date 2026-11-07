"""중진공 표준 CSV/파일명 검증 — 기계판독(Machine-Readable) 강제 레이어."""

from __future__ import annotations

import io
import re
from typing import Any

import pandas as pd

# 국민제안: 기업개요·재무·고용 등 정량 지표 표준 컬럼
COMPANY_METRICS_COLUMNS = [
    "기업명",
    "사업자등록번호",
    "업종",
    "상시근로자수",
    "매출액_백만원",
    "영업이익_백만원",
    "수출액_백만원",
    "기준연도",
]

QUOTE_COLUMNS = ["공급사", "항목", "수량", "단위", "공급가액", "부가세", "합계"]

# 예: 한빛정밀_AX도입_재무현황.csv
FILENAME_PATTERN = re.compile(
    r"^[A-Za-z0-9가-힣()._-]+_[A-Za-z0-9가-힣()._-]+_[A-Za-z0-9가-힣()._-]+\.(csv|xlsx|pdf)$",
    re.IGNORECASE,
)


def check_filename(name: str) -> dict[str, Any]:
    ok = bool(FILENAME_PATTERN.match(name.strip()))
    return {
        "ok": ok,
        "filename": name,
        "message": (
            "파일명 규칙 충족 (기업명_사업명_문서종류.확장자)"
            if ok
            else "권장 형식: 기업명_사업명_문서종류.csv 예) 한빛정밀_AX지원_기업현황.csv"
        ),
    }


def _read_table(filename: str, data: bytes) -> pd.DataFrame:
    lower = filename.lower()
    if lower.endswith(".xlsx"):
        return pd.read_excel(io.BytesIO(data))
    return pd.read_csv(io.BytesIO(data))


def validate_table(
    filename: str,
    data: bytes,
    required_columns: list[str],
    *,
    check_name: bool = True,
) -> dict[str, Any]:
    issues: list[str] = []
    name_result = check_filename(filename) if check_name else {"ok": True, "message": "파일명 검사 생략"}
    if check_name and not name_result["ok"]:
        issues.append(name_result["message"])

    try:
        df = _read_table(filename, data)
    except Exception as exc:  # noqa: BLE001 — 시연용 친절 메시지
        return {
            "ok": False,
            "filename": filename,
            "filename_check": name_result,
            "missing_columns": required_columns,
            "extra_columns": [],
            "row_count": 0,
            "issues": [f"파일을 읽을 수 없습니다: {exc}"],
            "preview": None,
        }

    cols = [str(c).strip() for c in df.columns]
    missing = [c for c in required_columns if c not in cols]
    extra = [c for c in cols if c not in required_columns]
    if missing:
        issues.append(f"필수 컬럼 누락: {', '.join(missing)}")
    if df.empty:
        issues.append("데이터 행이 없습니다.")

    # 숫자열 간단 검사
    numeric_hints = [c for c in required_columns if any(x in c for x in ("수", "액", "연도"))]
    for col in numeric_hints:
        if col in df.columns:
            coerced = pd.to_numeric(df[col], errors="coerce")
            bad = int(coerced.isna().sum()) - int(df[col].isna().sum())
            if bad > 0:
                issues.append(f"'{col}'에 숫자로 읽히지 않는 값 {bad}개")

    return {
        "ok": len(missing) == 0 and not df.empty and (name_result["ok"] if check_name else True),
        "filename": filename,
        "filename_check": name_result,
        "missing_columns": missing,
        "extra_columns": extra,
        "row_count": int(len(df)),
        "issues": issues,
        "preview": df.head(5),
    }


def validate_company_metrics(filename: str, data: bytes) -> dict[str, Any]:
    return validate_table(filename, data, COMPANY_METRICS_COLUMNS)


def validate_quote_csv(filename: str, data: bytes, *, check_name: bool = False) -> dict[str, Any]:
    return validate_table(filename, data, QUOTE_COLUMNS, check_name=check_name)
