"""Render sample metrics without mixing distinct item units."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from zabbix_reporting.pipeline import load_metrics, summarize_peaks

ROOT = Path(__file__).resolve().parents[1]
frame = load_metrics(ROOT / 'data/sample_metrics.csv')
peaks = summarize_peaks(frame)
fig = plt.figure(figsize=(13, 7), facecolor='#f6f8f9')
fig.text(.06, .93, 'Zabbix Reporting Pipeline', fontsize=24, weight='bold', color='#173631')
fig.text(.06, .86, f"{len(frame)} amostras | {frame.host.nunique()} hosts sinteticos | {len(peaks)} series | 0 rejeitados", color='#52636b', fontsize=13)
ax = fig.add_axes([.08, .22, .84, .50], facecolor='#f6f8f9')
sample = frame.loc[(frame.host == 'edge-a') & (frame.item_name == 'Processor: CPU utilization')]
ax.plot(sample.timestamp.dt.strftime('%H:%M'), sample.value, color='#147e57', marker='o', linewidth=3)
for i, value in enumerate(sample.value): ax.annotate(str(value), (i, value), xytext=(0, 12), textcoords='offset points', ha='center')
ax.set_title('edge-a | Processor: CPU utilization', loc='left', pad=20)
ax.set_ylabel('Valor do item sintetico (unidade nao declarada)')
ax.set_xlabel('01 jul 2026 | UTC')
ax.set_ylim(0, 100)
ax.spines[['top', 'right']].set_visible(False)
fig.text(.06, .07, 'Previa Python. Picos e amostras ficam auditaveis no Excel; unidades desconhecidas nao sao presumidas.', fontsize=11, color='#52636b')
output = ROOT / 'docs/images/preview.png'
output.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output, dpi=140)
plt.close(fig)
