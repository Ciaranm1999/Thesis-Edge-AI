"""
Thesis figure generation — Ciaran Maher, 2025/2026
Energy Profiling of TinyML Frameworks for Autonomous Mould Detection
Chapter 5 (Research Results) — 8 publication-quality figures

Figures produced
----------------
  fig_data_overview.png        — dataset readings + TVOC saturation per batch
  fig_sensor_trends.png        — Batch 3 representative 4-panel time series
  fig_onset_alignment.png      — TVOC traces aligned to mould onset (Batches 1, 3, 5)
  fig_class_comparison.png     — mean pre vs post mould comparison (2x2 bar chart)
  fig_power_breakdown.png      — component power pies (current vs MOSFET+MEMS improved)
  fig_ml_comparison.png        — energy / latency / accuracy 3-panel bar chart
  fig_tradeoff.png             — accuracy vs ML-energy trade-off scatter
  fig_battery_lifetime.png     — battery runtime across 3 hardware scenarios
"""

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE = "C:/Users/cmahe/OneDrive/Desktop/SSE Masters/Thesis/Code/Thesis-Edge-AI/"
OUT  = BASE + "ThesisReport/template/images/"
CSV  = BASE + "RaspberryPi/RaspberryPiData/analysis_exports/all_batches_ml_curated.csv"

# ── Consistent colour palette ─────────────────────────────────────────────────
C_N1     = '#1565C0'   # Node 1 (beside produce)
C_N2     = '#E65100'   # Node 2 (below produce)
C_MASTER = '#757575'   # Master node (ambient)
C_ONSET  = '#C62828'   # Mould-onset line
C_PRE    = '#90CAF9'   # Pre-mould fill
C_POST   = '#FFAB91'   # Post-mould fill

C_FW = ['#1565C0', '#0288D1', '#E65100', '#B71C1C']   # AIfES, TFLM, TinyOL, AIfES Full

# Batch colours for the onset-alignment plot
C_BATCHES = {'Batch1': '#1565C0', 'batch3': '#E65100', 'batch5': '#2E7D32'}
B_NAMES   = {'Batch1': 'Batch 1 (High-temp)', 'batch3': 'Batch 3 (High-temp)',
             'batch5': 'Batch 5 (Low-temp / test)'}

SAT_THR = 59_000

plt.rcParams.update({
    'font.family':        'DejaVu Sans',
    'font.size':          11,
    'axes.titlesize':     12,
    'axes.labelsize':     11,
    'legend.fontsize':    10,
    'axes.spines.top':    False,
    'axes.spines.right':  False,
    'axes.grid':          True,
    'grid.alpha':         0.25,
    'grid.linestyle':     '--',
    'savefig.dpi':        200,
    'savefig.bbox':       'tight',
    'figure.dpi':         110,
})

# ── Load data ─────────────────────────────────────────────────────────────────
df = pd.read_csv(CSV, parse_dates=['timestamp', 'mould_start'])
print(f"Loaded {len(df)} rows — batches: {list(df['batch'].unique())}")

BATCHES  = ['Batch1', 'batch2', 'batch3', 'batch4', 'batch5']
B_LABELS = [
    'Batch 1\n(High-temp)', 'Batch 2\n(High-temp)', 'Batch 3\n(High-temp)',
    'Batch 4\n(Low-temp)',  'Batch 5\n(Low-temp)',
]


def _onset_h(sub):
    """Return elapsed_hours of mould onset for a batch subset, or None."""
    mask = sub['mould_start'].notna()
    if not mask.any():
        return None
    t_onset = sub.loc[mask, 'mould_start'].iloc[0]
    after   = sub[sub['timestamp'] >= t_onset]['elapsed_hours']
    return float(after.min()) if len(after) else None


# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 1 — Dataset Overview
# ═══════════════════════════════════════════════════════════════════════════════
def fig_data_overview():
    # Batch 4 onset confirmed post-collection — not in raw CSV, patched in ML pipeline
    B4_ONSET_TS = pd.Timestamp('2026-03-11 14:42:21')

    pre_c, post_c, sat1, sat2 = [], [], [], []
    for b in BATCHES:
        sub = df[df['batch'] == b]
        if b == 'batch4':
            t_on = B4_ONSET_TS
            pre  = int((sub['timestamp'] < t_on).sum())
            post = int((sub['timestamp'] >= t_on).sum())
        else:
            mask = sub['mould_start'].notna()
            if mask.any():
                t_on = sub.loc[mask, 'mould_start'].iloc[0]
                pre  = int((sub['timestamp'] < t_on).sum())
                post = int((sub['timestamp'] >= t_on).sum())
            else:
                pre, post = len(sub), 0
        pre_c.append(pre);  post_c.append(post)
        sat1.append(int((sub['node1_tvoc'] >= SAT_THR).sum()))
        sat2.append(int((sub['node2_tvoc'] >= SAT_THR).sum()))

    x = np.arange(5)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))
    fig.suptitle('Collected Dataset Overview — Five Experimental Batches',
                 fontsize=13, fontweight='bold', y=1.02)

    ax1.bar(x, pre_c,  0.55, label='Pre-mould (Label 0)',
            color=C_PRE,  edgecolor=C_N1,   linewidth=1.0)
    ax1.bar(x, post_c, 0.55, bottom=pre_c,
            label='Post-onset (Label 1)',
            color=C_POST, edgecolor=C_ONSET, linewidth=1.0)

    for i, (pre, post) in enumerate(zip(pre_c, post_c)):
        total = pre + post
        ax1.text(x[i], total + 6, str(total), ha='center', va='bottom',
                 fontsize=9.5, fontweight='bold', color='#333')
        if post > 0:
            ax1.text(x[i], pre + post / 2, str(post),
                     ha='center', va='center', fontsize=8.5,
                     color='white', fontweight='bold')

    ax1.set_xticks(x);  ax1.set_xticklabels(B_LABELS, fontsize=10)
    ax1.set_ylabel('Number of Readings')
    ax1.set_title('Readings per Batch by Mould Label', fontweight='bold')
    ax1.legend(fontsize=10, loc='upper right')
    ax1.set_ylim(0, max(a + b for a, b in zip(pre_c, post_c)) * 1.22)
    ax1.yaxis.grid(True, alpha=0.3);  ax1.set_axisbelow(True)
    ax1.annotate(
        'Onset confirmed post-collection\n(~47 h); withheld from all\nbackbone training',
        xy=(3, pre_c[3] + 8), xytext=(3.6, pre_c[3] * 0.55 + 15),
        fontsize=8, color='#555',
        arrowprops=dict(arrowstyle='->', color='#888', lw=1.1))

    w  = 0.35
    b1 = ax2.bar(x - w / 2, sat1, w, label='Node 1 — beside produce',
                 color=C_N1, edgecolor='#0D47A1', linewidth=1)
    b2 = ax2.bar(x + w / 2, sat2, w, label='Node 2 — below produce',
                 color=C_N2, edgecolor='#BF360C', linewidth=1)
    for bar_grp, col in [(b1, C_N1), (b2, C_N2)]:
        for bar in bar_grp:
            h = bar.get_height()
            if h > 0:
                ax2.text(bar.get_x() + bar.get_width() / 2, h + 3, str(int(h)),
                         ha='center', va='bottom', fontsize=9,
                         color=col, fontweight='bold')
    ax2.set_xticks(x);  ax2.set_xticklabels(B_LABELS, fontsize=10)
    ax2.set_ylabel('Saturated Readings  (TVOC \u2265 59,000 ppb)')
    ax2.set_title('TVOC Sensor Saturation per Batch\n'
                  '(saturated readings imputed with batch median for ML training)',
                  fontweight='bold')
    ax2.legend(fontsize=10)
    top = max(max(sat1), max(sat2)) if max(sat1 + sat2) > 0 else 10
    ax2.set_ylim(0, top * 1.32)
    ax2.yaxis.grid(True, alpha=0.3);  ax2.set_axisbelow(True)
    ax2.annotate(
        'Entire Batch 2\nsaturated — excluded\nfrom all training',
        xy=(1, sat1[1] + 5), xytext=(1.65, sat1[1] * 0.55 + 30),
        fontsize=8.5, color=C_N2,
        arrowprops=dict(arrowstyle='->', color=C_N2, lw=1.2))

    plt.tight_layout()
    plt.savefig(OUT + 'fig_data_overview.png')
    plt.close()
    print('  Saved: fig_data_overview.png')


# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 2 — Batch 3 Representative Sensor Time Series
# ═══════════════════════════════════════════════════════════════════════════════
def fig_sensor_trends():
    """
    Batch 3: best representative because temperature and humidity were held
    consistently stable, and all four channels show clean, unambiguous trends.
    """
    b = df[df['batch'] == 'batch3'].copy().sort_values('elapsed_hours')
    onset_h = _onset_h(b)

    channels = [
        ('node1_temp',    'node2_temp',    'master_temp',    'Temperature (\u00b0C)'),
        ('node1_hum',     'node2_hum',     'master_hum',     'Relative Humidity (%)'),
        ('node1_tvoc',    'node2_tvoc',    'master_tvoc',    'TVOC (ppb)'),
        ('node1_mq3_ppm', 'node2_mq3_ppm', 'master_mq3_ppm', 'Ethanol (ppm)'),
    ]

    fig, axes = plt.subplots(4, 1, figsize=(13, 11), sharex=True)
    fig.suptitle(
        'Batch 3 \u2014 Sensor Readings Over Time  (High-Temperature Regime)',
        fontsize=13, fontweight='bold', y=1.005,
    )

    for ax, (c1, c2, cm, ylabel) in zip(axes, channels):
        ax.plot(b['elapsed_hours'], b[cm], color=C_MASTER, lw=1.2, alpha=0.7, zorder=2)
        ax.plot(b['elapsed_hours'], b[c1], color=C_N1, lw=1.8, zorder=3)
        ax.plot(b['elapsed_hours'], b[c2], color=C_N2, lw=1.8, zorder=3)
        if onset_h is not None:
            ax.axvline(onset_h, color=C_ONSET, linestyle='--', lw=1.8, zorder=4)
        ax.set_ylabel(ylabel, fontsize=10.5)
        ax.yaxis.grid(True, alpha=0.25);  ax.xaxis.grid(True, alpha=0.25)

    # TVOC: zoom to show the actual signal, not the full range up to saturation
    tvoc_max = max(b['node1_tvoc'].max(), b['node2_tvoc'].max(), b['master_tvoc'].max())
    axes[2].set_ylim(0, tvoc_max * 1.15)

    if onset_h is not None:
        ylim = axes[0].get_ylim()
        axes[0].text(onset_h + 0.7, ylim[0] + (ylim[1] - ylim[0]) * 0.88,
                     f'Mould onset\n({onset_h:.1f} h)',
                     color=C_ONSET, fontsize=9, va='top', fontweight='bold')

    axes[-1].set_xlabel('Elapsed Time (hours)', fontsize=11)

    legend_handles = [
        mpatches.Patch(color=C_N1,     label='Node 1 \u2014 beside produce'),
        mpatches.Patch(color=C_N2,     label='Node 2 \u2014 below produce'),
        mpatches.Patch(color=C_MASTER, label='Master \u2014 ambient (outside)'),
        Line2D([0], [0], color=C_ONSET, linestyle='--', lw=1.8, label='Mould onset'),
    ]
    fig.legend(handles=legend_handles, loc='lower center', ncol=4,
               fontsize=10.5, bbox_to_anchor=(0.5, -0.022),
               frameon=True, framealpha=0.92)
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(OUT + 'fig_sensor_trends.png')
    plt.close()
    print('  Saved: fig_sensor_trends.png')


# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 3 — TVOC Onset Alignment (Batches 1, 3, 5)
# ═══════════════════════════════════════════════════════════════════════════════
def fig_onset_alignment():
    """
    TVOC Node 1 traces aligned to the mould-onset event for all 5 batches.
    Node 1 (beside produce) is used here because Node 2 has more saturation
    issues, making Node 1 a cleaner cross-batch comparison.
    Batch 4's onset (~46.7 h) is derived from the batch_analysis notebook
    metadata (mould_start = 2026-03-11 14:42:21) since the CSV export
    does not include a mould_start timestamp for Batch 4.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))
    fig.suptitle(
        'TVOC Signal Aligned to Mould Onset \u2014 All Five Batches\n'
        '(Node 1 \u2014 beside produce)',
        fontsize=13, fontweight='bold', y=1.02,
    )

    WINDOW_PRE  = 15   # hours before onset to show
    WINDOW_POST = 25   # hours after onset to show

    # Batch 4 onset derived from batch_analysis.ipynb metadata
    B4_ONSET_TS = pd.Timestamp('2026-03-11 14:42:21')

    # Colour per batch (5 distinct colours)
    batch_styles = [
        ('Batch1', '#1565C0', 'Batch 1 (High-temp)'),
        ('batch2', '#9E9E9E', 'Batch 2 (High-temp, saturated)'),
        ('batch3', '#E65100', 'Batch 3 (High-temp)'),
        ('batch4', '#7B1FA2', 'Batch 4 (Low-temp, onset \u224847 h)'),
        ('batch5', '#2E7D32', 'Batch 5 (Low-temp / test set)'),
    ]

    for batch_key, col, lbl in batch_styles:
        sub = df[df['batch'] == batch_key].copy().sort_values('elapsed_hours')
        if len(sub) == 0:
            continue

        # Determine onset hour
        mask = sub['mould_start'].notna()
        if mask.any():
            t_onset = sub.loc[mask, 'mould_start'].iloc[0]
            onset_h = float(sub[sub['timestamp'] >= t_onset]['elapsed_hours'].min())
        elif batch_key == 'batch4':
            # Use known timestamp from batch_analysis notebook metadata
            first_ts = pd.Timestamp(sub['timestamp'].iloc[0])
            onset_h  = (B4_ONSET_TS - first_ts).total_seconds() / 3600
        else:
            continue  # skip if no onset known

        sub['rel_h'] = sub['elapsed_hours'] - onset_h
        window = sub[(sub['rel_h'] >= -WINDOW_PRE) & (sub['rel_h'] <= WINDOW_POST)]

        # Normalise: divide by mean of last 10 readings before onset
        pre_vals = sub[sub['rel_h'] < 0]['node1_tvoc'].dropna()
        baseline = pre_vals.iloc[-10:].mean() if len(pre_vals) >= 10 else pre_vals.mean()
        if baseline == 0 or pd.isna(baseline) or baseline < 100:
            baseline = max(pre_vals.mean(), 500)  # avoid div-by-zero for very low baselines

        ls = ':' if batch_key == 'batch2' else '-'
        alpha = 0.6 if batch_key == 'batch2' else 0.95
        norm_tvoc = window['node1_tvoc'] / baseline
        ax1.plot(window['rel_h'], norm_tvoc, color=col, lw=2.0,
                 linestyle=ls, alpha=alpha, label=lbl)
        ax2.plot(window['rel_h'], window['node1_tvoc'] / 1000,
                 color=col, lw=2.0, linestyle=ls, alpha=alpha, label=lbl)

    for ax in (ax1, ax2):
        ax.axvline(0, color=C_ONSET, linestyle='--', lw=1.8, alpha=0.85,
                   label='Mould onset (t = 0)')
        ax.axvspan(0, WINDOW_POST, alpha=0.04, color=C_ONSET)
        ax.set_xlabel('Time Relative to Mould Onset (hours)', fontsize=11)
        ax.legend(fontsize=9.0, loc='upper left')
        ax.xaxis.grid(True, alpha=0.3);  ax.yaxis.grid(True, alpha=0.3)

    ax1.set_ylabel('TVOC Node 1  (normalised to pre-onset baseline)', fontsize=11)
    ax1.set_title('Normalised TVOC Rise\n(1.0 = pre-onset mean)', fontweight='bold')
    ax1.axhline(1.0, color='#9E9E9E', linestyle=':', lw=1.2)
    ax1.text(WINDOW_PRE * -0.9, 1.03, 'Baseline\n(1.0)', fontsize=8.5, color='#757575')

    ax2.set_ylabel('TVOC Node 1  (thousands of ppb)', fontsize=11)
    ax2.set_title('Raw TVOC Signal\n(absolute values)', fontweight='bold')

    plt.tight_layout()
    plt.savefig(OUT + 'fig_onset_alignment.png')
    plt.close()
    print('  Saved: fig_onset_alignment.png')


# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 4 — Class Comparison (replaces box plots)
# ═══════════════════════════════════════════════════════════════════════════════
def fig_class_comparison():
    """
    1x2 grouped bar chart: mean +/- 1 SD for TVOC at Node 1 and Node 2,
    split by mould class (pre-mould vs post-onset).
    TVOC is the primary discriminating feature; the two panels show how it
    separates by class at each node position.
    """
    df_ml = df[df['keep_for_ml'] == True].copy()
    df_ml['label'] = 0
    mask = df_ml['mould_start'].notna()
    df_ml.loc[mask, 'label'] = (
        df_ml.loc[mask, 'timestamp'] >= df_ml.loc[mask, 'mould_start']
    ).astype(int)

    channels = [
        ('node1_tvoc', 'TVOC — Node 1\n(beside produce)'),
        ('node2_tvoc', 'TVOC — Node 2\n(below produce)'),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(11, 6))
    fig.suptitle(
        'TVOC Class Separability — Pre-mould vs Post-mould Onset\n'
        '(ML training dataset, error bars = \u00b11 standard deviation)',
        fontsize=12, fontweight='bold',
    )
    axes_flat = axes.flatten()

    for ax, (col, title) in zip(axes_flat, channels):
        pre  = df_ml[df_ml['label'] == 0][col].dropna()
        post = df_ml[df_ml['label'] == 1][col].dropna()

        means  = [pre.mean(),  post.mean()]
        stds   = [pre.std(),   post.std()]
        colors = [C_PRE,       C_POST]
        edge_c = [C_N1,        C_ONSET]
        labels = [f'Pre-mould\n(Label 0)\nn={len(pre)}',
                  f'Post-onset\n(Label 1)\nn={len(post)}']

        x = np.array([0, 1])
        bars = ax.bar(x, means, 0.52, color=colors,
                      edgecolor=edge_c, linewidth=1.2, zorder=3)
        ax.errorbar(x, means, yerr=stds, fmt='none',
                    ecolor='#333', elinewidth=1.5, capsize=5, capthick=1.5, zorder=4)

        # Annotate bar tops with the mean value
        for xi, (m, s) in enumerate(zip(means, stds)):
            unit = 'ppb' if 'tvoc' in col else 'ppm'
            ax.text(xi, m + s + max(means) * 0.03,
                    f'{m:,.0f} {unit}',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')

        ax.set_xticks(x);  ax.set_xticklabels(labels, fontsize=10)
        ax.set_title(title, fontsize=11, fontweight='bold', pad=8)
        ax.set_ylabel(title.split('\n')[1].strip('()'), fontsize=10)
        ax.yaxis.grid(True, alpha=0.3);  ax.set_axisbelow(True)
        ax.set_ylim(0, max(means) + max(stds) * 1.5 + max(means) * 0.15)

    plt.tight_layout()
    plt.savefig(OUT + 'fig_class_comparison.png')
    plt.close()
    print('  Saved: fig_class_comparison.png')


# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 5 — Power Breakdown Pie Charts
# Improved hardware = MOSFET gate on SGP30 + MEMS sensor replacing MQ3 only.
# No custom PCB changes — those are future work.
# ═══════════════════════════════════════════════════════════════════════════════
def fig_power_breakdown():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 7))
    fig.suptitle(
        'Slave Node Power Breakdown \u2014 Current vs Improved Hardware\n'
        '(Average current per 15-minute duty cycle at 3.3 V)',
        fontsize=12, fontweight='bold', y=1.03,
    )

    # ── Left: current hardware ────────────────────────────────────────────────
    vals_cur = [103.3, 48.0, 10.0, 6.75]
    pct_cur  = [100 * v / sum(vals_cur) for v in vals_cur]
    lbl_cur  = [
        f'MQ3 Heater  ({pct_cur[0]:.1f}%)\n103.3 mA \u2014 continuous resistive heater',
        f'SGP30 VOC Sensor  ({pct_cur[1]:.1f}%)\n48.0 mA \u2014 no gating in current design',
        f'DevKit Board  ({pct_cur[2]:.1f}%)\n10.0 mA \u2014 LDO + USB-UART bridge',
        f'ESP32 + DHT22  ({pct_cur[3]:.1f}%)\n6.75 mA avg \u2014 cycles active/sleep',
    ]
    cols_cur = ['#C62828', '#1565C0', '#FFA000', '#43A047']

    ax1.pie(vals_cur, colors=cols_cur,
            explode=(0.07, 0.02, 0.02, 0.02), startangle=130,
            wedgeprops={'edgecolor': 'white', 'linewidth': 2.2})
    ax1.legend(
        handles=[mpatches.Patch(color=c, label=l) for c, l in zip(cols_cur, lbl_cur)],
        loc='lower center', bbox_to_anchor=(0.5, -0.42),
        fontsize=9, frameon=True, framealpha=0.92, ncol=1)
    ax1.set_title(
        f'Current Hardware\n'
        f'Total avg current \u2248 {sum(vals_cur):.0f} mA',
        fontsize=12, fontweight='bold', pad=10)

    # ── Right: improved hardware (MOSFET + MEMS only, no custom PCB) ──────────
    # SGP30 MOSFET-gated: 48 mA × (45 s / 900 s) = 2.4 mA avg
    # MEMS sensor (replaces MQ3): 3.6 mA active × (45 s / 900 s) ≈ 0.18 mA avg
    # Board overhead: 10.0 mA — UNCHANGED (still DevKit board)
    # ESP32 + DHT22: 6.75 mA avg — UNCHANGED
    mems_avg  = 3.6 * (45 / 900)   # 0.18 mA
    sgp30_avg = 48.0 * (45 / 900)  # 2.40 mA
    board     = 10.0
    esp32     = 6.75
    vals_imp  = [mems_avg, sgp30_avg, board, esp32]
    tot_imp   = sum(vals_imp)
    pct_imp   = [100 * v / tot_imp for v in vals_imp]
    lbl_imp   = [
        f'MEMS Sensor  ({pct_imp[0]:.1f}%)\n{mems_avg:.2f} mA avg \u2014 replaces MQ3',
        f'SGP30 (MOSFET-gated)  ({pct_imp[1]:.1f}%)\n{sgp30_avg:.2f} mA avg \u2014 5% on-time',
        f'DevKit Board  ({pct_imp[2]:.1f}%)\n{board:.1f} mA \u2014 next optimisation target',
        f'ESP32 + DHT22  ({pct_imp[3]:.1f}%)\n{esp32:.2f} mA avg \u2014 unchanged',
    ]
    cols_imp  = ['#C62828', '#1565C0', '#FFA000', '#43A047']
    # Use slightly desaturated red for MEMS (tiny slice, not a problem anymore)
    cols_imp[0] = '#EF9A9A'

    ax2.pie(vals_imp, colors=cols_imp,
            startangle=110,
            wedgeprops={'edgecolor': 'white', 'linewidth': 2.2})
    ax2.legend(
        handles=[mpatches.Patch(color=c, label=l) for c, l in zip(cols_imp, lbl_imp)],
        loc='lower center', bbox_to_anchor=(0.5, -0.42),
        fontsize=9, frameon=True, framealpha=0.92, ncol=1)
    ax2.set_title(
        f'Improved Hardware (MOSFET + MEMS)\n'
        f'Total avg current \u2248 {tot_imp:.1f} mA  (\u2212{(1 - tot_imp/sum(vals_cur))*100:.1f}%)',
        fontsize=12, fontweight='bold', pad=10)

    plt.tight_layout(w_pad=5)
    plt.subplots_adjust(bottom=0.32)
    plt.savefig(OUT + 'fig_power_breakdown.png')
    plt.close()
    print('  Saved: fig_power_breakdown.png')


# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 6 — ML Framework Comparison
# ═══════════════════════════════════════════════════════════════════════════════
def fig_ml_comparison():
    fw_labels = ['AIfES\nInference', 'TF Lite\nMicro', 'TinyOL\nUpdate', 'AIfES\nFull Training']
    energy_uj = [6.305,  8.881,   1.810,  194.816]
    lat_us    = [45.7,   73.2,    13.1,   1914.0]
    accuracy  = [94.0,   93.7,    86.1,    77.1]

    x = np.arange(4)
    fig, axes = plt.subplots(1, 3, figsize=(14, 5.5))
    fig.suptitle('TinyML Framework Comparison \u2014 ESP32 @ 240 MHz',
                 fontsize=13, fontweight='bold')

    # Energy (log)
    ax = axes[0]
    bars = ax.bar(x, energy_uj, color=C_FW, edgecolor='white',
                  linewidth=1.2, width=0.58, alpha=0.92)
    ax.set_yscale('log')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: (f'{v:.0f} \u00b5J' if v >= 1 else f'{v*1000:.0f} nJ')))
    for bar, val in zip(bars, energy_uj):
        label = f'{val:.3f} \u00b5J' if val < 10 else f'{val:.0f} \u00b5J'
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() * 1.6, label,
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax.set_xticks(x); ax.set_xticklabels(fw_labels, fontsize=9.5)
    ax.set_ylabel('ML-only Energy per Operation (\u00b5J)')
    ax.set_title('Energy\n(log scale)', fontweight='bold')
    ax.yaxis.grid(True, alpha=0.3, which='both'); ax.set_axisbelow(True)

    # Latency (log)
    ax = axes[1]
    bars = ax.bar(x, lat_us, color=C_FW, edgecolor='white',
                  linewidth=1.2, width=0.58, alpha=0.92)
    ax.set_yscale('log')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: (f'{v/1000:.1f} ms' if v >= 1000 else f'{v:.0f} \u00b5s')))
    for bar, val in zip(bars, lat_us):
        label = f'{val/1000:.2f} ms' if val >= 1000 else f'{val:.1f} \u00b5s'
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() * 1.6, label,
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax.set_xticks(x); ax.set_xticklabels(fw_labels, fontsize=9.5)
    ax.set_ylabel('Latency per Operation')
    ax.set_title('Latency\n(log scale)', fontweight='bold')
    ax.yaxis.grid(True, alpha=0.3, which='both'); ax.set_axisbelow(True)

    # Accuracy (horizontal bars, top to bottom = highest to lowest)
    ax = axes[2]
    fw_rev  = fw_labels[::-1]
    acc_rev = accuracy[::-1]
    col_rev = C_FW[::-1]
    yr = np.arange(4)
    bars = ax.barh(yr, acc_rev, color=col_rev, edgecolor='white',
                   linewidth=1.2, height=0.55, alpha=0.92)
    for bar, val in zip(bars, acc_rev):
        ax.text(val + 0.4, bar.get_y() + bar.get_height() / 2,
                f'{val:.1f}%', ha='left', va='center',
                fontsize=10, fontweight='bold')
    ax.set_yticks(yr); ax.set_yticklabels(fw_rev, fontsize=9.5)
    ax.set_xlabel('Test-set Accuracy (%)')
    ax.set_title('Prediction Accuracy\n(332 held-out test samples)', fontweight='bold')
    ax.set_xlim(65, 102)
    ax.axvline(90, color='#9E9E9E', linestyle='--', lw=1.3, alpha=0.8)
    ax.text(90.4, -0.6, '90%', fontsize=8.5, color='#757575')
    ax.xaxis.grid(True, alpha=0.3); ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(OUT + 'fig_ml_comparison.png')
    plt.close()
    print('  Saved: fig_ml_comparison.png')


# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 7 — Accuracy vs Energy Trade-off
# ═══════════════════════════════════════════════════════════════════════════════
def fig_tradeoff():
    fw_names  = ['AIfES Inference\n(Method 1)', 'TF Lite Micro\n(Method 1)',
                 'TinyOL Update\n(Method 2)',   'AIfES Full Training\n(Method 3)']
    energy_uj = [6.305,  8.881,  1.810, 194.816]
    accuracy  = [94.0,   93.7,   86.1,   77.1]
    params    = [0,      0,      17,     193]

    min_sz = 140
    sz     = [min_sz + p * 5.5 for p in params]
    offsets = [(-0.55, 1.8), (0.18, 1.8), (0.18, -3.0), (-0.62, -3.0)]

    fig, ax = plt.subplots(figsize=(9, 6.5))
    for i, (e, a, p, lbl, (ox, oy)) in enumerate(
            zip(energy_uj, accuracy, params, fw_names, offsets)):
        ax.scatter(e, a, s=sz[i], color=C_FW[i], zorder=5,
                   edgecolors='white', linewidths=1.8, alpha=0.92)
        xe = e * (2 ** ox) if abs(ox) > 0.3 else e
        ax.annotate(lbl, xy=(e, a), xytext=(xe, a + oy),
                    fontsize=10, color=C_FW[i], fontweight='bold',
                    arrowprops=dict(arrowstyle='-', color=C_FW[i], lw=0.9)
                    if abs(ox) > 0.2 or abs(oy) > 1.5 else None)

    ax.annotate('Increasing on-device autonomy \u2192',
                xy=(energy_uj[0] * 0.5, 73.5), fontsize=9,
                color='#757575', style='italic')

    ax.text(energy_uj[2] * 0.45, 98.5,
            '\u2190  Ideal: high accuracy, low energy',
            fontsize=8.5, color='#2E7D32', style='italic')

    ax.set_xscale('log')
    ax.set_xlabel('ML-only Energy per Operation (\u00b5J)  [log scale]', fontsize=11)
    ax.set_ylabel('Accuracy on Held-out Test Set (%)', fontsize=11)
    ax.set_title(
        'Accuracy vs Energy Trade-off \u2014 ESP32 On-Device ML\n'
        '(Bubble size \u221d on-device trainable parameters)',
        fontsize=12, fontweight='bold')
    ax.set_ylim(70, 100)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f'{v:.0f}' if v >= 1 else f'{v:.2f}'))
    ax.yaxis.grid(True, alpha=0.3);  ax.xaxis.grid(True, alpha=0.3, which='both')
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(OUT + 'fig_tradeoff.png')
    plt.close()
    print('  Saved: fig_tradeoff.png')


# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE 8 — Battery Lifetime: 3 Hardware Scenarios
# ═══════════════════════════════════════════════════════════════════════════════
def fig_battery_lifetime():
    """
    Three scenarios (3-node mesh, 85% battery efficiency, 15-min duty cycle):

    Current hardware (MQ3 included — all three MQ3s measured at 310 mA total → 103.3 mA each):
      Master: 88.79 mA (measured, no MQ3) + 103.3 mA (MQ3) = 192.1 mA
      Slave 1: 64.75 mA (measured) + 103.3 mA (MQ3) = 168.05 mA
      Slave 2: 66.14 mA (measured) + 103.3 mA (MQ3) = 169.44 mA
      Total mesh: 529.6 mA → approx 528 mA → [0.13, 0.34, 0.67, 1.34] days

    MOSFET + MEMS (MQ3 replaced, SGP30 gated at 5% duty):
      Per slave: 0.18 (MEMS) + 2.40 (SGP30 gated) + 10.0 (DevKit) + 6.75 (ESP32) = 19.33 mA
      Master (SGP30 also gated): 88.79 - 45.6 = 43.19 mA
      Total mesh: 2×19.33 + 43.19 ≈ 81.85 mA → [0.84, 2.1, 4.2, 8.4] days

    Full redesign (+ custom PCB replaces DevKit on all nodes):
      Per slave: ~9.33 mA (DevKit 10 → 1 mA with efficient LDO)
      Master redesigned: ~33.19 mA
      Total mesh: 2×9.33 + 33.19 ≈ 51.85 mA → [1.4, 3.6, 7.1, 14.3] days
    """
    battery_labels = ['2,000 mAh', '5,000 mAh', '10,000 mAh', '20,000 mAh']
    # Corrected: each MQ3 = 310 mA / 3 = 103.3 mA; total mesh ≈ 528 mA
    runtime_cur    = [0.13, 0.34, 0.67, 1.34]
    runtime_mosfet = [0.84, 2.1,  4.2,  8.4 ]   # MOSFET gate + MEMS, no PCB redesign
    runtime_full   = [1.4,  3.6,  7.1, 14.3 ]   # full improvements inc. custom PCB

    x = np.arange(4)
    w = 0.26

    fig, ax = plt.subplots(figsize=(12, 6.5))

    b_cur = ax.bar(x - w, runtime_cur, w,
                   label='Current hardware (inc. MQ3 external)',
                   color='#FFCDD2', edgecolor='#C62828', linewidth=1.2)
    b_mos = ax.bar(x,     runtime_mosfet, w,
                   label='Improved: MOSFET gate + MEMS sensor',
                   color='#FFF9C4', edgecolor='#F57F17', linewidth=1.2)
    b_ful = ax.bar(x + w, runtime_full, w,
                   label='Full redesign: MOSFET + MEMS + custom PCB',
                   color='#C8E6C9', edgecolor='#2E7D32', linewidth=1.2)

    for bars, col in [(b_cur, '#C62828'), (b_mos, '#E65100'), (b_ful, '#2E7D32')]:
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.12, f'{h:.1f}d',
                    ha='center', va='bottom', fontsize=9,
                    fontweight='bold', color=col)

    for days, col, ls, lbl in [
        (1,  '#F57F17', '--', '1 day'),
        (7,  '#1565C0', '--', '7 days (1 week)'),
        (30, '#43A047', ':',  '30 days (1 month)'),
    ]:
        ax.axhline(days, color=col, linestyle=ls, lw=1.4, alpha=0.85, label=lbl)

    ax.set_xticks(x);  ax.set_xticklabels(battery_labels, fontsize=11)
    ax.set_ylabel('Estimated Runtime (days)', fontsize=11)
    ax.set_xlabel('Battery Capacity (mAh)', fontsize=11)
    ax.set_title(
        'Estimated Battery Lifetime \u2014 Three Hardware Scenarios\n'
        '(3-node mesh, 15-minute duty cycle, 3.3 V, 85% efficiency)',
        fontsize=12, fontweight='bold')
    ax.legend(fontsize=9.5, loc='upper left')
    ax.set_ylim(0, max(runtime_full) * 1.30)
    ax.yaxis.grid(True, alpha=0.3);  ax.set_axisbelow(True)

    ax.text(0.99, 0.04,
            'ML framework choice does not affect runtime\n'
            '(ML overhead \u2264 0.01% of daily energy budget)',
            transform=ax.transAxes, ha='right', va='bottom',
            fontsize=8.5, color='#616161', style='italic',
            bbox=dict(boxstyle='round,pad=0.4',
                      facecolor='#FAFAFA', edgecolor='#BDBDBD'))

    plt.tight_layout()
    plt.savefig(OUT + 'fig_battery_lifetime.png')
    plt.close()
    print('  Saved: fig_battery_lifetime.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Run all
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("Generating thesis figures...\n")
    fig_data_overview()
    fig_sensor_trends()
    fig_onset_alignment()
    fig_class_comparison()
    fig_power_breakdown()
    fig_ml_comparison()
    fig_tradeoff()
    fig_battery_lifetime()
    print(f"\nDone. All figures saved to: {OUT}")
