from __future__ import annotations

from enum import StrEnum


class IssueSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    REVIEW = "REVIEW"
    BLOCKING = "BLOCKING"
    FAILURE = "FAILURE"


class IssueScope(StrEnum):
    DOCUMENT = "DOCUMENT"
    TABLE = "TABLE"
    FACT = "FACT"


SEVERITY_RANK = {
    IssueSeverity.BLOCKING: 0,
    IssueSeverity.FAILURE: 1,
    IssueSeverity.REVIEW: 2,
    IssueSeverity.WARNING: 3,
    IssueSeverity.INFO: 4,
}

TABLES_WITHOUT_FACTS_WARNING = 0.35
TABLES_WITHOUT_FACTS_REVIEW = 0.60

ROW_WITHOUT_LABEL_REVIEW = 0.20

PERIOD_WARNING = 0.50
PERIOD_REVIEW = 0.10

UNIT_WARNING = 0.20
UNIT_REVIEW = 0.02

MIN_FACTS_FOR_SEMANTIC_COVERAGE = 50
MIN_FACTS_FOR_CORE_STATEMENT_CHECK = 100

RECONCILIATION_RELATIVE_TOLERANCE = "0.0005"
RECONCILIATION_ABSOLUTE_TOLERANCE = "1"


BALANCE_ASSET_ALIASES = (
    "资产总计",
    "总资产",
    "total assets",
)
BALANCE_LIABILITY_ALIASES = (
    "负债合计",
    "总负债",
    "total liabilities",
)
BALANCE_EQUITY_ALIASES = (
    "所有者权益合计",
    "股东权益合计",
    "权益合计",
    "total equity",
    "shareholders equity",
    "shareholders' equity",
)

INCOME_ALIASES = (
    "营业收入",
    "营业总收入",
    "收入",
    "revenue",
)
PROFIT_ALIASES = (
    "净利润",
    "年度利润",
    "profit for the year",
    "net profit",
)

CASH_OPERATING_ALIASES = (
    "经营活动产生的现金流量净额",
    "net cash generated from operating activities",
    "net cash from operating activities",
)
CASH_INCREASE_ALIASES = (
    "现金及现金等价物净增加额",
    "net increase in cash and cash equivalents",
)
CASH_END_ALIASES = (
    "期末现金及现金等价物余额",
    "cash and cash equivalents at end",
    "cash and cash equivalents at the end",
)
CASH_BEGIN_ALIASES = (
    "期初现金及现金等价物余额",
    "cash and cash equivalents at beginning",
    "cash and cash equivalents at the beginning",
)
