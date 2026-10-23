from pathlib import Path

import pandas as pd

from zabbix_reporting.pipeline import build_report, classify_metric, load_metrics, summarize_peaks
from zabbix_reporting.readonly import ensure_read_only


ROOT = Path(__file__).resolve().parents[1]


def test_memory_classification_wins_over_processor() -> None:
    assert classify_metric("Processor: Memory utilization") == "Memória"


def test_peak_timestamp_and_recurrence() -> None:
    frame = load_metrics(ROOT / "data" / "sample_metrics.csv")
    peaks = summarize_peaks(frame)
    row = peaks.loc[
        (peaks["host"] == "edge-a")
        & (peaks["item_name"] == "Processor: CPU utilization")
    ].iloc[0]
    assert row["maximum"] == 81
    assert row["peak_count"] == 2
    assert str(row["first_peak_at"]) == "2026-07-01 10:00:00+00:00"


def test_report_contains_expected_sheets(tmp_path: Path) -> None:
    output = build_report(ROOT / "data" / "sample_metrics.csv", tmp_path / "report.xlsx")
    assert set(pd.ExcelFile(output).sheet_names) == {
        "Resumo",
        "Picos",
        "CPU",
        "Memória",
        "Tráfego",
        "Controle",
        "Rejeitados",
    }


def test_read_only_guard_fails_closed() -> None:
    assert ensure_read_only("trend.get") == "trend.get"
    try:
        ensure_read_only("host.create")
    except PermissionError:
        pass
    else:
        raise AssertionError("write method should have been blocked")
