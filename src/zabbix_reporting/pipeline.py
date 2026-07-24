"""Create an auditable Excel report from synthetic Zabbix metric samples."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {"client", "host", "item_name", "timestamp", "value"}


def classify_metric(item_name: str) -> str:
    """Classify an item while prioritizing explicit memory terms over processor."""
    name = item_name.casefold()
    if any(term in name for term in ("memory", "memória", "memoria", "ram")):
        return "Memória"
    if any(term in name for term in ("cpu", "processor", "load")):
        return "CPU"
    if any(term in name for term in ("traffic", "tráfego", "trafego", "bits", "bytes")):
        return "Tráfego"
    return "Outros"


def load_metrics(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    frame = frame.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame["metric_group"] = frame["item_name"].map(classify_metric)
    frame = frame.dropna(subset=["timestamp", "value"])
    return frame.sort_values(["client", "host", "item_name", "timestamp"]).reset_index(drop=True)


def summarize_peaks(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    keys = ["client", "host", "item_name", "metric_group"]
    for key, group in frame.groupby(keys, dropna=False, sort=True):
        maximum = group["value"].max()
        peak_rows = group.loc[group["value"].eq(maximum)].sort_values("timestamp")
        rows.append(
            {
                "client": key[0],
                "host": key[1],
                "item_name": key[2],
                "metric_group": key[3],
                "average": group["value"].mean(),
                "maximum": maximum,
                "first_peak_at": peak_rows.iloc[0]["timestamp"],
                "peak_count": int(len(peak_rows)),
                "sample_count": int(len(group)),
            }
        )
    return pd.DataFrame(rows)


def _summary_by_client(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.groupby(["client", "metric_group"], as_index=False)
        .agg(samples=("value", "size"), average=("value", "mean"), maximum=("value", "max"))
        .sort_values(["client", "metric_group"])
    )


def _excel_safe(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a copy whose datetime columns are compatible with Excel."""
    result = frame.copy()
    for column in result.columns:
        if isinstance(result[column].dtype, pd.DatetimeTZDtype):
            result[column] = result[column].dt.tz_convert("UTC").dt.tz_localize(None)
    return result


def build_report(input_path: str | Path, output_path: str | Path) -> Path:
    frame = load_metrics(input_path)
    peaks = summarize_peaks(frame)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    control = pd.DataFrame(
        [
            {"control": "generated_at_utc", "value": datetime.now(timezone.utc).isoformat()},
            {"control": "source", "value": "synthetic_csv"},
            {"control": "rows", "value": len(frame)},
            {"control": "clients", "value": frame["client"].nunique()},
            {"control": "read_only", "value": True},
        ]
    )

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        _summary_by_client(frame).to_excel(writer, sheet_name="Resumo", index=False)
        _excel_safe(peaks).to_excel(writer, sheet_name="Picos", index=False)
        for metric in ("CPU", "Memória", "Tráfego"):
            _excel_safe(frame.loc[frame["metric_group"].eq(metric)]).to_excel(
                writer, sheet_name=metric, index=False
            )
        control.to_excel(writer, sheet_name="Controle", index=False)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/sample_metrics.csv")
    parser.add_argument("--output", default="output/zabbix_report.xlsx")
    args = parser.parse_args()
    path = build_report(args.input, args.output)
    print(path)


if __name__ == "__main__":
    main()
