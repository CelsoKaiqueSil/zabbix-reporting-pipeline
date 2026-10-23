from pathlib import Path
import pandas as pd
from zabbix_reporting.pipeline import load_metrics, summarize_peaks, build_report, _summary_by_client


def test_invalid_rows_have_reason_and_reconcile(tmp_path):
    path = tmp_path / 'metrics.csv'
    pd.DataFrame([
        ['Demo', 'host-a', 'CPU', '2026-01-01T00:00:00Z', '10'],
        ['Demo', 'host-a', 'CPU', 'bad', '10'],
        ['Demo', 'host-a', 'CPU', '2026-01-01T00:00:00Z', 'inf'],
    ], columns=['client', 'host', 'item_name', 'timestamp', 'value']).to_csv(path, index=False)
    frame = load_metrics(path)
    assert frame.attrs['quality'] == {'input_rows': 3, 'accepted_rows': 1, 'rejected_rows': 2}
    assert frame.attrs['rejected']['rejection_reason'].str.len().min() > 0


def test_units_do_not_get_averaged_together():
    frame = pd.DataFrame({'client': ['Demo']*2, 'metric_group': ['Tráfego']*2,
        'item_name': ['WAN']*2, 'unit': ['bps', 'Bps'], 'value': [8, 1]})
    result = _summary_by_client(frame)
    assert len(result) == 2
    assert set(result['unit']) == {'bps', 'Bps'}


def test_empty_input_still_produces_control_and_rejections(tmp_path):
    path = tmp_path / 'empty.csv'
    path.write_text('client,host,item_name,timestamp,value\n', encoding='utf-8')
    frame = load_metrics(path)
    assert summarize_peaks(frame).empty
    output = build_report(path, tmp_path / 'report.xlsx')
    with pd.ExcelFile(output) as book:
        assert 'Rejeitados' in book.sheet_names
