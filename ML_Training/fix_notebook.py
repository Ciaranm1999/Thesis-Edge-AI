"""
Fix:
  1. TinyOL window detection  – peak-finding (was: falling back to middle 60% of trace)
  2. AIfES Full window detection – pre-training idle reference (was: 40th pct = training zone)
  3. Plot cleanup – remove error bars, fix overlapping text, drop radar chart
"""
import json

with open('energy_analysis.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

def set_src(i, text):
    nb['cells'][i]['source'] = [text]
    nb['cells'][i]['outputs'] = []
    nb['cells'][i]['execution_count'] = None

# ─────────────────────────────────────────────────────────────────────────────
# Cell 12 — TinyOL: spike detection using peak-finding + threshold expansion
# ─────────────────────────────────────────────────────────────────────────────
set_src(12, """\
tinyol_files = sorted(TINYOL_DIR.glob('*.csv'))
print(f'Found {len(tinyol_files)} TinyOL files: {[f.name for f in tinyol_files]}')

tinyol_results = []
fig, axes = plt.subplots(len(tinyol_files), 1, figsize=(13, 4*len(tinyol_files)), squeeze=False)

for idx, fpath in enumerate(tinyol_files):
    print(f'\\n--- Run {idx+1}: {fpath.name} ---')
    df = load_ppk2_csv(fpath)

    # ── Window detection for short spike (~38 ms) ──────────────────────────
    # Standard detect_benchmark_window requires min_duration=0.5s and uses
    # a 50ms smooth_window — both too large for a ~38ms spike. Instead:
    #  1. Smooth with 50-sample (0.5ms) window to preserve the spike shape
    #  2. Use the first 0.5s of the trace as the idle reference
    #  3. Find all regions above idle*1.08 and pick the one containing the peak
    smooth    = df['current_uA'].rolling(window=50, center=True, min_periods=1).mean()
    idle_uA   = float(np.percentile(smooth.iloc[:50_000], 50))   # first 0.5 s @ 100 kHz
    threshold = idle_uA * 1.08
    peak_idx  = int(smooth.idxmax())
    peak_t    = df['time_s'].iloc[peak_idx]

    above   = smooth > threshold
    changes = above.astype(int).diff().fillna(0)
    starts  = df['time_s'][changes ==  1].values
    ends    = df['time_s'][changes == -1].values
    if len(ends) < len(starts):
        ends = np.append(ends, df['time_s'].iloc[-1])

    t_start = t_end = None
    for s, e in zip(starts, ends):
        if s <= peak_t <= e:
            t_start, t_end = float(s), float(e)
            break
    if t_start is None:                         # fallback: ±30 ms around peak
        t_start = max(df['time_s'].iloc[0],  peak_t - 0.030)
        t_end   = min(df['time_s'].iloc[-1], peak_t + 0.030)

    window_s          = t_end - t_start
    energy_uJ         = calc_energy_uJ(df, t_start, t_end)
    idle_energy_uJ    = IDLE_POWER_W * window_s * 1e6
    ml_energy_uJ      = energy_uJ - idle_energy_uJ
    energy_per_upd_nJ = (energy_uJ   / N_UPDATES) * 1000
    ml_energy_per_upd_nJ = (ml_energy_uJ / N_UPDATES) * 1000
    us_per_upd        = (window_s * 1e6) / N_UPDATES

    tinyol_results.append({
        'run': idx+1, 'file': fpath.name, 'window_s': window_s,
        'total_energy_uJ': energy_uJ,
        'energy_per_upd_nJ':    energy_per_upd_nJ,
        'ml_energy_per_upd_nJ': ml_energy_per_upd_nJ,
        'us_per_upd': us_per_upd,
    })
    print(f'  Window (spike)    : {t_start:.3f} - {t_end:.3f} s  ({window_s*1000:.1f} ms)')
    print(f'  idle ref          : {idle_uA/1000:.1f} mA, threshold: {threshold/1000:.1f} mA, peak: {smooth.iloc[peak_idx]/1000:.1f} mA')
    print(f'  Energy (raw)      : {energy_per_upd_nJ:.1f} nJ/update')
    print(f'  Energy (ML-only)  : {ml_energy_per_upd_nJ:.1f} nJ/update')
    print(f'  Latency           : {us_per_upd:.1f} us/update')

    ax = axes[idx][0]
    ds = df.iloc[::20]
    ax.plot(ds['time_s'], ds['current_uA']/1000, lw=0.5, color='mediumorchid', alpha=0.7, label='Current (mA)')
    ax.axvspan(t_start, t_end, alpha=0.35, color='gold', label=f'Training spike ({window_s*1000:.1f} ms)')
    ax.axvline(t_start, color='darkgoldenrod', lw=1.5, ls='--')
    ax.axvline(t_end,   color='darkgoldenrod', lw=1.5, ls='--')
    ax.set_title(f'TinyOL | {fpath.name} | {ml_energy_per_upd_nJ:.0f} nJ ML-only/upd | {us_per_upd:.1f} us/upd')
    ax.set_xlabel('Time (s)'); ax.set_ylabel('Current (mA)'); ax.legend(fontsize=9)
    y_lo = df['current_uA'].quantile(0.002)/1000; y_hi = df['current_uA'].quantile(0.998)/1000
    ax.set_ylim(y_lo - (y_hi-y_lo)*0.15, y_hi + (y_hi-y_lo)*0.5)

plt.suptitle('TinyOL On-Device Learning (Method 2) -- PPK2 Traces\\n'
             'Training spike ~38 ms | LED HIGH during benchmark window',
             fontsize=11, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(RESULTS_DIR/'tinyol_traces.png', bbox_inches='tight', dpi=130)
plt.show()
""")

# ─────────────────────────────────────────────────────────────────────────────
# Cell 14 — AIfES Full: use pre-training idle (first 2 s) as baseline reference
# ─────────────────────────────────────────────────────────────────────────────
set_src(14, """\
aifes_full_files = sorted(AIFES_FULL_DIR.glob('*.csv'))
print(f'Found {len(aifes_full_files)} AIfES Full Training files: {[f.name for f in aifes_full_files]}')

aifes_full_results = []

if len(aifes_full_files) == 0:
    print(f'No CSV files yet -- save PPK2 CSVs to: {AIFES_FULL_DIR}')
    aifes_full_df = pd.DataFrame(columns=['run','window_s','total_energy_uJ',
                                           'energy_per_upd_nJ','ml_energy_per_upd_nJ','us_per_upd'])
else:
    fig, axes = plt.subplots(len(aifes_full_files), 1,
                             figsize=(13, 4*len(aifes_full_files)), squeeze=False)
    for idx, fpath in enumerate(aifes_full_files):
        print(f'\\n--- Run {idx+1}: {fpath.name} ---')
        df = load_ppk2_csv(fpath)
        duration_s  = df['time_s'].iloc[-1] - df['time_s'].iloc[0]
        sample_rate = len(df) / duration_s if duration_s > 0 else 10_000
        sw = max(50, int(sample_rate * 0.05))   # 50 ms smoothing
        smooth = df['current_uA'].rolling(window=sw, center=True, min_periods=1).mean()

        # ── Window detection for long training window (~12 s in ~15 s recording) ─
        # The 40th-percentile approach fails here because training takes >80% of
        # the recording — the 40th pct lands inside the training zone, making the
        # threshold too high and causing the fallback to fire.
        # Fix: use the first 2 s (pre-training idle) as the idle reference.
        pre_samples = int(sample_rate * 2.0)
        idle_uA     = float(smooth.iloc[:pre_samples].median())
        threshold   = idle_uA * 1.08    # 8 % above pre-training idle

        above   = smooth > threshold
        changes = above.astype(int).diff().fillna(0)
        starts  = df['time_s'][changes ==  1].values
        ends    = df['time_s'][changes == -1].values
        if len(ends) < len(starts):
            ends = np.append(ends, df['time_s'].iloc[-1])

        # Pick the longest sustained window (= the training session)
        best_s = best_e = best_d = None
        for s, e in zip(starts, ends):
            d = e - s
            if best_d is None or d > best_d:
                best_s, best_e, best_d = float(s), float(e), d

        if best_s is None:
            best_s, best_e = df['time_s'].quantile(0.2), df['time_s'].quantile(0.8)
            best_d = best_e - best_s
            print('  WARNING: detection fallback used — check trace manually')

        t_start, t_end = best_s, best_e
        window_s          = t_end - t_start
        energy_uJ         = calc_energy_uJ(df, t_start, t_end)
        idle_energy_uJ    = IDLE_POWER_W * window_s * 1e6
        ml_energy_uJ      = energy_uJ - idle_energy_uJ
        energy_per_upd_nJ = (energy_uJ   / N_UPDATES_FULL) * 1000
        ml_energy_per_upd_nJ = (ml_energy_uJ / N_UPDATES_FULL) * 1000
        us_per_upd        = (window_s * 1e6) / N_UPDATES_FULL

        aifes_full_results.append({
            'run': idx+1, 'file': fpath.name, 'window_s': window_s,
            'total_energy_uJ': energy_uJ,
            'energy_per_upd_nJ':    energy_per_upd_nJ,
            'ml_energy_per_upd_nJ': ml_energy_per_upd_nJ,
            'us_per_upd': us_per_upd,
        })
        print(f'  Window            : {t_start:.2f} - {t_end:.2f} s  ({window_s:.2f} s)')
        print(f'  Idle ref (pre-2s) : {idle_uA/1000:.1f} mA, threshold: {threshold/1000:.1f} mA')
        print(f'  Energy (raw)      : {energy_per_upd_nJ:.1f} nJ/update')
        print(f'  Energy (ML-only)  : {ml_energy_per_upd_nJ:.1f} nJ/update')
        print(f'  Latency           : {us_per_upd:.0f} us/update')

        ax = axes[idx][0]
        step = max(1, len(df)//5000)
        ds   = df.iloc[::step]
        ax.plot(ds['time_s'], ds['current_uA']/1000, lw=0.5, color='seagreen', alpha=0.7, label='Current (mA)')
        ax.axvspan(t_start, t_end, alpha=0.20, color='gold',
                   label=f'Training window ({window_s:.2f} s)')
        ax.axvline(t_start, color='darkgoldenrod', lw=1.5, ls='--')
        ax.axvline(t_end,   color='darkgoldenrod', lw=1.5, ls='--')
        ax.axhline(idle_uA/1000, color='gray', lw=1, ls=':', alpha=0.7, label=f'Pre-training idle ({idle_uA/1000:.0f} mA)')
        ax.set_title(f'AIfES Full Training | {fpath.name} | {ml_energy_per_upd_nJ:.0f} nJ ML-only/upd | {window_s:.1f} s')
        ax.set_xlabel('Time (s)'); ax.set_ylabel('Current (mA)'); ax.legend(fontsize=9)
        y_lo = df['current_uA'].quantile(0.002)/1000; y_hi = df['current_uA'].quantile(0.998)/1000
        ax.set_ylim(y_lo - (y_hi-y_lo)*0.3, y_hi + (y_hi-y_lo)*0.3)

    plt.suptitle('AIfES Full On-Device Training (Method 3) -- PPK2 Traces\\n'
                 '20 epochs x 320 mini-batches = 6,400 gradient steps | Glorot init | 77.1% accuracy',
                 fontsize=11, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(RESULTS_DIR/'aifes_full_training_traces.png', bbox_inches='tight', dpi=130)
    plt.show()
    aifes_full_df = pd.DataFrame(aifes_full_results)
    print('\\n=== AIfES Full Training Results ===')
    print(aifes_full_df[['run','window_s','energy_per_upd_nJ','ml_energy_per_upd_nJ','us_per_upd']].to_string(index=False))
""")

# ─────────────────────────────────────────────────────────────────────────────
# Cell 17 — four-way energy bar chart: remove error bars, cleaner labels
# ─────────────────────────────────────────────────────────────────────────────
set_src(17, """\
# ── Four-way energy comparison: raw vs ML-only (no error bars) ──────────────
have_full = len(aifes_full_results) > 0

def _m(df, col): return df[col].mean()

labels = ['AIfES (float32)\\nMethod 1', 'TF Lite Micro (INT8)\\nMethod 1',
          'TinyOL (float32)\\nMethod 2', 'AIfES Full (float32)\\nMethod 3']

raw_nJ = [_m(aifes_df,'energy_per_inf_nJ'), _m(tflm_df,'energy_per_inf_nJ'),
          _m(tinyol_df,'energy_per_upd_nJ'),
          _m(aifes_full_df,'energy_per_upd_nJ') if have_full else float('nan')]
ml_nJ  = [_m(aifes_df,'ml_energy_per_inf_nJ'), _m(tflm_df,'ml_energy_per_inf_nJ'),
          _m(tinyol_df,'ml_energy_per_upd_nJ'),
          _m(aifes_full_df,'ml_energy_per_upd_nJ') if have_full else float('nan')]

import numpy as np
x = np.arange(4)
w = 0.38

fig, ax = plt.subplots(figsize=(11, 6))
ax.bar(x - w/2, raw_nJ, w, color=COLORS, alpha=0.30, edgecolor=COLORS, linewidth=1.5, label='Total measured')
ax.bar(x + w/2, ml_nJ,  w, color=COLORS, alpha=0.92, edgecolor='white', linewidth=0.5, label='ML-only (idle corrected)')

for i, (r, m) in enumerate(zip(raw_nJ, ml_nJ)):
    if not np.isnan(m):
        ax.text(x[i]+w/2, m * 1.25, f'{m:.0f} nJ', ha='center', va='bottom', fontsize=9, fontweight='bold')

ax.set_yscale('log')
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=10)
ax.set_ylabel('Energy per operation (nJ)  [log scale]', fontsize=11)
ax.set_title('Energy per ML Operation -- ESP32 @ 240 MHz\\n'
             'Darker = ML-only (idle corrected)  |  Light = total system energy',
             fontsize=11, fontweight='bold')
import matplotlib.ticker as mticker
ax.yaxis.set_major_formatter(mticker.FuncFormatter(
    lambda v, _: f'{v/1000:.1f} uJ' if v >= 1000 else f'{v:.0f} nJ'))
ax.legend(fontsize=10, loc='upper left')
fig.text(0.5, -0.02,
    f'Idle correction: SGP30 48mA + DHT22 0.1mA + devboard 10mA = 58.1mA at {V_SUPPLY}V',
    ha='center', fontsize=9, color='gray', style='italic')
plt.tight_layout()
plt.savefig(RESULTS_DIR/'four_way_comparison.png', bbox_inches='tight', dpi=150)
plt.show()
print('Saved: four_way_comparison.png')
""")

# ─────────────────────────────────────────────────────────────────────────────
# Cell 23 — Energy breakdown: simpler annotations, no error bars
# ─────────────────────────────────────────────────────────────────────────────
set_src(23, """\
# ── Plot A: Energy breakdown (ML vs idle) ────────────────────────────────────
import numpy as np
import matplotlib.ticker as mticker
have_full = len(aifes_full_results) > 0

def _m(df, col): return df[col].mean()

labels = ['AIfES\\nM1', 'TFLM\\nM1', 'TinyOL\\nM2', 'AIfES Full\\nM3']
raw_nJ = [_m(aifes_df,'energy_per_inf_nJ'), _m(tflm_df,'energy_per_inf_nJ'),
          _m(tinyol_df,'energy_per_upd_nJ'), _m(aifes_full_df,'energy_per_upd_nJ') if have_full else np.nan]
ml_nJ  = [_m(aifes_df,'ml_energy_per_inf_nJ'), _m(tflm_df,'ml_energy_per_inf_nJ'),
          _m(tinyol_df,'ml_energy_per_upd_nJ'), _m(aifes_full_df,'ml_energy_per_upd_nJ') if have_full else np.nan]
idle_nJ = [r - m for r, m in zip(raw_nJ, ml_nJ)]

x = np.arange(4)
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# Left — stacked bar (ML + idle)
ax = axes[0]
ax.bar(x, ml_nJ,   width=0.5, color=COLORS, alpha=0.90, label='ML computation')
ax.bar(x, idle_nJ, width=0.5, color='#cccccc', alpha=0.85, label='Sensor idle (58.1 mA)',
       edgecolor='#aaaaaa', linewidth=0.8, bottom=ml_nJ)
ax.set_yscale('log')
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=11)
ax.set_ylabel('Energy per operation (nJ)  [log scale]', fontsize=10)
ax.set_title('Energy Breakdown per Operation', fontsize=11, fontweight='bold')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(
    lambda v, _: f'{v/1000:.0f} uJ' if v >= 10000 else (f'{v/1000:.1f} uJ' if v >= 1000 else f'{v:.0f} nJ')))
# One clean label per bar at the top
for i, (ml, idle) in enumerate(zip(ml_nJ, idle_nJ)):
    total = ml + idle
    if not np.isnan(total):
        pct = int(round(100 * ml / total))
        ax.text(x[i], total * 1.6, f'{pct}% ML', ha='center', va='bottom', fontsize=9, fontweight='bold')
ax.legend(fontsize=9)

# Right — ML-only, µJ
ax2 = axes[1]
bars = ax2.bar(x, [v/1000 for v in ml_nJ], width=0.5, color=COLORS, alpha=0.88, edgecolor='white')
for bar, val in zip(bars, ml_nJ):
    if not np.isnan(val):
        ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()*1.04,
                 f'{val/1000:.1f} uJ', ha='center', va='bottom', fontsize=10, fontweight='bold')
ax2.set_xticks(x); ax2.set_xticklabels(labels, fontsize=11)
ax2.set_ylabel('ML-only energy per operation (uJ)', fontsize=10)
ax2.set_title('ML-Only Energy (idle corrected)', fontsize=11, fontweight='bold')

plt.suptitle('Energy Analysis -- ESP32 @ 240 MHz | Mould Prediction', fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig(RESULTS_DIR/'thesis_energy_breakdown.png', bbox_inches='tight', dpi=150)
plt.show()
print('Saved: thesis_energy_breakdown.png')
""")

# ─────────────────────────────────────────────────────────────────────────────
# Cell 24 — Latency + RAM: fix overlapping text
# ─────────────────────────────────────────────────────────────────────────────
set_src(24, """\
# ── Plot B: Latency + RAM ────────────────────────────────────────────────────
import numpy as np
labels4 = ['AIfES\\nM1', 'TFLM\\nM1', 'TinyOL\\nM2', 'AIfES Full\\nM3']
x = np.arange(4)
lat_us  = [45.7, 73.2, 13.1, 1914.0]
heap_kb = [30.1, 30.2, 30.0, 34.1]
bss_kb  = [0.0,  0.0,  1.2, 57.2]

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# Latency — log scale, label placement adjusted per bar height
ax = axes[0]
bars = ax.bar(x, lat_us, color=COLORS, alpha=0.88, width=0.5, edgecolor='white')
ax.set_yscale('log')
ax.set_xticks(x); ax.set_xticklabels(labels4, fontsize=11)
ax.set_ylabel('Latency per operation (us)', fontsize=10)
ax.set_title('Latency per Operation\\n(serial monitor, @ 240 MHz)', fontsize=11, fontweight='bold')
import matplotlib.ticker as mticker
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f} us'))
for bar, val in zip(bars, lat_us):
    # Place label above bar always (log scale — multiply by a fixed factor)
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()*1.6,
            f'{val:.1f} us', ha='center', va='bottom', fontsize=9, fontweight='bold')

# RAM — stacked bar
ax2 = axes[1]
ax2.bar(x, heap_kb, width=0.5, color=COLORS, alpha=0.88, label='Peak heap (dynamic)', edgecolor='white')
ax2.bar(x, bss_kb,  width=0.5, color=COLORS, alpha=0.40, label='BSS static arrays',
        edgecolor='#555555', linewidth=0.8, hatch='//', bottom=heap_kb)
for i, (h, b) in enumerate(zip(heap_kb, bss_kb)):
    total = h + b
    ax2.text(x[i], total + 1.5, f'{total:.0f} KB', ha='center', va='bottom',
             fontsize=10, fontweight='bold')
ax2.set_xticks(x); ax2.set_xticklabels(labels4, fontsize=11)
ax2.set_ylabel('RAM (KB)', fontsize=10)
ax2.set_ylim(0, 105)
ax2.set_title('On-Device RAM Usage\\nHeap + BSS static buffers', fontsize=11, fontweight='bold')
ax2.legend(fontsize=9, loc='upper left')

plt.suptitle('Latency and RAM -- ESP32 @ 240 MHz', fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig(RESULTS_DIR/'thesis_latency_ram.png', bbox_inches='tight', dpi=150)
plt.show()
print('Saved: thesis_latency_ram.png')
""")

# ─────────────────────────────────────────────────────────────────────────────
# Cell 25 — Remove radar entirely; clean accuracy vs energy scatter only
# ─────────────────────────────────────────────────────────────────────────────
set_src(25, """\
# ── Plot C: Accuracy vs ML-energy (scatter) ──────────────────────────────────
import numpy as np
import matplotlib.ticker as mticker
have_full = len(aifes_full_results) > 0

ml_nJ_vals = [
    aifes_df['ml_energy_per_inf_nJ'].mean(),
    tflm_df['ml_energy_per_inf_nJ'].mean(),
    tinyol_df['ml_energy_per_upd_nJ'].mean(),
    aifes_full_df['ml_energy_per_upd_nJ'].mean() if have_full else np.nan,
]
acc_vals    = [94.0, 93.7, 86.1, 77.1]
params_vals = [0, 0, 17, 193]
short_labels = ['AIfES\\n(Method 1)', 'TFLM\\n(Method 1)',
                'TinyOL\\n(Method 2)', 'AIfES Full\\n(Method 3)']

# Fixed label offsets to avoid overlap
offsets_x = [-0.65, +0.15, +0.15, -0.70]   # in log-scale fractions (multiplied below)
offsets_y = [-2.8,  -2.8,  +1.5,  +1.5]

fig, ax = plt.subplots(figsize=(9, 6))
for i, (e, a, p, lbl, ox, oy) in enumerate(
        zip(ml_nJ_vals, acc_vals, params_vals, short_labels, offsets_x, offsets_y)):
    if np.isnan(e): continue
    sz = 200 + p * 1.5
    ax.scatter(e/1000, a, s=sz, color=COLORS[i], zorder=5,
               edgecolors='white', linewidths=1.5, alpha=0.92)
    # Offset label: ox is fraction of the x value
    xe = e/1000
    ax.annotate(lbl, xy=(xe, a),
                xytext=(xe * (1 + ox), a + oy),
                fontsize=10, color=COLORS[i], fontweight='bold',
                arrowprops=dict(arrowstyle='-', color=COLORS[i], lw=0.8) if abs(ox) > 0.3 else None)

ax.set_xscale('log')
ax.set_xlabel('ML-only energy per operation (uJ)  [log scale]', fontsize=11)
ax.set_ylabel('Accuracy on held-out test set (%)', fontsize=11)
ax.set_ylim(70, 100)
ax.set_title('Accuracy vs Energy Trade-off -- ESP32 On-Device ML\\n'
             'Bubble size = number of trainable parameters on-device', fontsize=11, fontweight='bold')
ax.xaxis.set_major_formatter(mticker.FuncFormatter(
    lambda v, _: f'{v:.2f}' if v < 1 else f'{v:.0f}'))
# Annotate the infrastructure independence axis
ax.annotate('', xy=(ml_nJ_vals[3]/1000, 77.1), xytext=(ml_nJ_vals[0]/1000, 94.0),
            arrowprops=dict(arrowstyle='->', color='gray', lw=1.2, linestyle='dashed'))
ax.text(0.52, 0.52, 'Infrastructure\\nindependence\\nincreases →',
        transform=ax.transAxes, ha='center', fontsize=9, color='gray', style='italic')
plt.tight_layout()
plt.savefig(RESULTS_DIR/'thesis_tradeoff.png', bbox_inches='tight', dpi=150)
plt.show()
print('Saved: thesis_tradeoff.png')
""")

# ─────────────────────────────────────────────────────────────────────────────
# Cell 26 — Dashboard: fix overlapping text, no error bars
# ─────────────────────────────────────────────────────────────────────────────
set_src(26, """\
# ── Plot D: Summary dashboard (2 x 2) ───────────────────────────────────────
import numpy as np
import matplotlib.ticker as mticker
have_full = len(aifes_full_results) > 0

ml_nJ_vals = [
    aifes_df['ml_energy_per_inf_nJ'].mean(),
    tflm_df['ml_energy_per_inf_nJ'].mean(),
    tinyol_df['ml_energy_per_upd_nJ'].mean(),
    aifes_full_df['ml_energy_per_upd_nJ'].mean() if have_full else np.nan,
]
lat_us   = [45.7, 73.2, 13.1, 1914.0]
acc_vals = [94.0, 93.7, 86.1, 77.1]
total_ram= [30.1, 30.2, 31.2, 91.3]

labels4 = ['AIfES\\nM1', 'TFLM\\nM1', 'TinyOL\\nM2', 'AIfES Full\\nM3']
x = np.arange(4)

fig, axes = plt.subplots(2, 2, figsize=(12, 8))

def clean_bar(ax, vals, ylabel, title, unit='', logy=False, fmt='{:.1f}'):
    bars = ax.bar(x, vals, color=COLORS, alpha=0.88, width=0.52, edgecolor='white', linewidth=0.5)
    if logy: ax.set_yscale('log')
    ax.set_xticks(x); ax.set_xticklabels(labels4, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_title(title, fontsize=10, fontweight='bold')
    for bar, val in zip(bars, vals):
        if not np.isnan(val):
            y = bar.get_height()
            # For log scale multiply, for linear add a margin
            top = y * 1.5 if logy else y + max(v for v in vals if not np.isnan(v)) * 0.03
            ax.text(bar.get_x()+bar.get_width()/2, top,
                    fmt.format(val)+unit, ha='center', va='bottom', fontsize=9, fontweight='bold')

clean_bar(axes[0,0], [v/1000 for v in ml_nJ_vals], 'ML-only energy/op (uJ)',
          'Energy (ML-only, idle corrected)', unit=' uJ', logy=True, fmt='{:.1f}')
axes[0,0].yaxis.set_major_formatter(mticker.FuncFormatter(
    lambda v, _: f'{v:.2f}' if v < 1 else f'{v:.0f}'))

clean_bar(axes[0,1], lat_us, 'Latency/op (us)', 'Latency', unit=' us', logy=True, fmt='{:.1f}')
axes[0,1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}'))

clean_bar(axes[1,0], acc_vals, 'Accuracy (%)', 'Accuracy on Test Set', unit='%', fmt='{:.1f}')
axes[1,0].set_ylim(65, 100)

clean_bar(axes[1,1], total_ram, 'RAM (KB)', 'Total RAM (heap + BSS)', unit=' KB', fmt='{:.0f}')

plt.suptitle('ESP32 On-Device ML -- Four-Method Benchmark Summary\\n'
             'Input(10) -> Dense(16,ReLU) -> Dense(1,Sigmoid) | Mould Prediction',
             fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig(RESULTS_DIR/'thesis_dashboard.png', bbox_inches='tight', dpi=150)
plt.show()
print('Saved: thesis_dashboard.png')
""")

with open('energy_analysis.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
print("Done. Cells updated: 12, 14, 17, 23, 24, 25, 26")
