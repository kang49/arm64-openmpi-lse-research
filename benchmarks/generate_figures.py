import matplotlib.pyplot as plt
import numpy as np
import os
from PIL import Image, ImageDraw, ImageFont

os.makedirs('../paper/figures', exist_ok=True)
plt.rcParams['font.family'] = 'serif'
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 0.8

# ==============================================================================
# FIGURE 1: (a) Micro-batched (K=32, cntvct_el0) Mean & p99 Tail Latency
#           (b) 4-Way opal_lifo_t Isolation (T=2, 4, 8 threads, M=5 trials)
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.3), dpi=300)

cores = np.array([1, 2, 3, 4])
llsc_mean = np.array([7.95,  38.95, 64.77,  109.40])
llsc_p99  = np.array([8.10,  81.02, 169.56, 317.13])
lse_mean  = np.array([5.98,  58.78, 85.61,  93.09])
lse_p99   = np.array([9.26,  62.50, 109.95, 155.09])

ax1.plot(cores, llsc_p99, 'o--', color='#b71c1c', linewidth=1.8, markersize=5.5, label='LL/SC p99 Tail (ldaxr/stlxr)')
ax1.plot(cores, llsc_mean, 'o-', color='#ef5350', linewidth=2.2, markersize=6, label='LL/SC Mean [0.397 aborts/op @ N=4]')
ax1.plot(cores, lse_p99, 's--', color='#0d47a1', linewidth=1.8, markersize=5.5, label='LSE p99 Tail (ldaddal)')
ax1.plot(cores, lse_mean, 's-', color='#42a5f5', linewidth=2.2, markersize=6, label='LSE Mean [0.000 aborts/op @ N=4]')

ax1.annotate('2.04x Lower p99 Tail\n(155.1 ns vs 317.1 ns)',
             xy=(4.0, 155.1), xytext=(2.68, 255),
             arrowprops=dict(arrowstyle='->', color='#0d47a1', lw=1.5),
             fontsize=8.3, fontweight='bold', color='#0d47a1',
             bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='#bbdefb', alpha=0.95))

ax1.set_xticks(cores)
ax1.set_xticklabels(['N=1', 'N=2', 'N=3', 'N=4'], fontsize=9)
ax1.set_ylabel('Amortized Op Latency (ns, Log Scale)', fontsize=10, fontweight='bold')
ax1.set_xlabel('Competing Cortex-A76 Physical Cores (N)', fontsize=10, fontweight='bold')
ax1.set_title('(a) K=32 Batched Mean & p99 Tail (0.72 ns/op timer)', fontsize=10.2, fontweight='bold')
ax1.set_yscale('log')
ax1.set_ylim(4, 750)
ax1.grid(True, which='both', linestyle=':', alpha=0.55)
ax1.legend(loc='upper left', fontsize=7.6, frameon=True)

# Subplot (b): 4-Way Isolation across T=2, 4, 8 (M=5 trials)
threads = np.array([2, 4, 8])
x = np.arange(len(threads))
w = 0.20

unp_mean   = [180.4, 168.8, 165.8]
unp_std    = [4.8,   1.3,   1.3]
novol_mean = [179.6, 168.6, 165.0]
novol_std  = [2.8,   2.1,   2.4]
pat_mean   = [32.6,  34.0,  38.2]
pat_std    = [0.5,   0.0,   0.4]
ll_mean    = [33.6,  31.8,  35.6]
ll_std     = [3.1,   0.4,   0.5]

b1 = ax2.bar(x - 1.5*w, unp_mean,   yerr=unp_std,   capsize=2.5, width=w, color='#d32f2f', edgecolor='#222', label='Unpatched CAS128')
b2 = ax2.bar(x - 0.5*w, novol_mean, yerr=novol_std, capsize=2.5, width=w, color='#fb8c00', edgecolor='#222', label='No-Volatile Only (No Backoff)')
b3 = ax2.bar(x + 0.5*w, pat_mean,   yerr=pat_std,   capsize=2.5, width=w, color='#2e7d32', edgecolor='#222', label='No-Volatile + 5-Try Backoff')
b4 = ax2.bar(x + 1.5*w, ll_mean,    yerr=ll_std,    capsize=2.5, width=w, color='#1976d2', edgecolor='#222', label='64-bit LL/SC (ldaxr/stlxr)')

for bar, m in zip(b1, unp_mean):
    ax2.text(bar.get_x() + bar.get_width()/2, m + 5, f'{m:.0f}', ha='center', va='bottom', fontsize=7.2, fontweight='bold', color='#b71c1c')
for bar, m in zip(b2, novol_mean):
    ax2.text(bar.get_x() + bar.get_width()/2, m + 5, f'{m:.0f}', ha='center', va='bottom', fontsize=7.2, fontweight='bold', color='#e65100')
for bar, m in zip(b3, pat_mean):
    ax2.text(bar.get_x() + bar.get_width()/2, m + 4, f'{m:.1f}', ha='center', va='bottom', fontsize=7.2, fontweight='bold', color='#1b5e20')
for bar, m in zip(b4, ll_mean):
    ax2.text(bar.get_x() + bar.get_width()/2, m + 4, f'{m:.1f}', ha='center', va='bottom', fontsize=7.2, fontweight='bold', color='#0d47a1')

ax2.annotate('No-Volatile = 0% Gain;\nBackoff = 5.53x Speedup!',
             xy=(0.10, 49), xytext=(1.25, 118),
             arrowprops=dict(arrowstyle='->', color='#2e7d32', lw=1.5),
             fontsize=8.0, fontweight='bold', color='#2e7d32', ha='center',
             bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='#c8e6c9', alpha=0.95))

ax2.set_xticks(x)
ax2.set_xticklabels(['2 Threads\n(T < 4 Cores)', '4 Threads\n(T = 4 Cores)', '8 Threads\n(2x Oversubscribed)'], fontsize=8.5)
ax2.set_ylabel('Pop+Push Latency (ns/op, Mean ± 1σ)', fontsize=10, fontweight='bold')
ax2.set_xlabel('Concurrent Thread Count (T)', fontsize=10, fontweight='bold')
ax2.set_title('(b) 4-Way Isolation of opal_lifo_t Patch (M=5 Trials)', fontsize=10.2, fontweight='bold')
ax2.set_ylim(0, 225)
ax2.grid(True, axis='y', linestyle=':', alpha=0.6)
ax2.legend(loc='upper right', fontsize=7.2, frameon=True)

plt.tight_layout()
plt.savefig('../paper/figures/fig_atomic_scaling.pdf', bbox_inches='tight')
plt.savefig('../paper/figures/fig_atomic_scaling.png', bbox_inches='tight')
plt.close()

# ==============================================================================
# FIGURE 2: (a) Controlled Ablation of osu_latency (Fixed 2.40 GHz vs DVFS)
#           (b) End-to-End MPI_Test() Non-Blocking Polling Latency (MPI_THREAD_MULTIPLE)
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.1), dpi=300)

x_labels = ['1B', '2B', '4B', '8B', '16B', '32B', '64B', '128B', '256B']
xi = np.arange(len(x_labels))

dvfs_ondemand = [0.455, 0.455, 0.440, 0.430, 0.470, 0.470, 0.490, 0.530, 0.550]
v6_unp = [0.324, 0.320, 0.324, 0.322, 0.334, 0.340, 0.350, 0.380, 0.394]
v6_pat = [0.330, 0.328, 0.330, 0.330, 0.358, 0.352, 0.372, 0.392, 0.400]
v5_gen = [0.280, 0.280, 0.280, 0.280, 0.300, 0.298, 0.314, 0.340, 0.358]

ax1.plot(xi, dvfs_ondemand, 'x:', color='#9e9e9e', linewidth=1.6, markersize=5, label='DVFS Artifact (ondemand 1.5->2.4 GHz)')
ax1.plot(xi, v6_unp, 'o--', color='#d32f2f', linewidth=1.8, markersize=5, label='v6.0 -mcpu=cortex-a76 Unpatched (2.40 GHz)')
ax1.plot(xi, v6_pat, 's-', color='#2e7d32', linewidth=2.0, markersize=5, label='v6.0 -mcpu=cortex-a76 + ldapr Fast-Path (2.40 GHz)')
ax1.plot(xi, v5_gen, '^-', color='#1565c0', linewidth=1.8, markersize=5, label='Debian 5.0.7 Generic Reference (2.40 GHz)')

ax1.set_xticks(xi)
ax1.set_xticklabels(x_labels, fontsize=8.5)
ax1.set_ylabel('One-Way Ping-Pong Latency (µs)', fontsize=10, fontweight='bold')
ax1.set_xlabel('Message Payload Size', fontsize=10, fontweight='bold')
ax1.set_title('(a) osu_latency Ablation: DVFS vs Fixed 2.40 GHz', fontsize=10.2, fontweight='bold')
ax1.set_ylim(0.22, 0.65)
ax1.grid(True, linestyle=':', alpha=0.6)
ax1.legend(loc='upper left', fontsize=7.3, frameon=True)

# Subplot (b): MPI_Test() Non-Blocking Progress Poll Latency (MPI_THREAD_MULTIPLE, M=5)
cats = ['Unpatched v6.0\n(2x ldaddal + pthread_mutex)', 'Patched v6.0\n(FEAT_LRCPC ldapr Guard)']
test_means = [57.05, 27.20]
test_stds  = [0.23,  0.75]
cols = ['#d32f2f', '#2e7d32']

bx = np.arange(len(cats))
bars = ax2.bar(bx, test_means, yerr=test_stds, capsize=5, width=0.45, color=cols, edgecolor='#222')
for bar, m, s in zip(bars, test_means, test_stds):
    ax2.text(bar.get_x() + bar.get_width()/2, m + s + 1.5, f'{m:.2f} ± {s:.2f} ns', ha='center', va='bottom', fontsize=9.2, fontweight='bold')

ax2.annotate('-52.3% Poll Latency\n(2.10x Faster MPI_Test!)\n& -38.29% CPU Spin Waste',
             xy=(1.0, 34), xytext=(0.75, 50),
             arrowprops=dict(arrowstyle='->', color='#2e7d32', lw=1.6),
             fontsize=8.5, fontweight='bold', color='#2e7d32', ha='center',
             bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='#c8e6c9', alpha=0.95))

ax2.set_xticks(bx)
ax2.set_xticklabels(cats, fontsize=9.0)
ax2.set_ylabel('Latency per MPI_Test() Call (ns)', fontsize=10, fontweight='bold')
ax2.set_title('(b) MPI_Test() Poll Latency (MPI_THREAD_MULTIPLE, M=5)', fontsize=10.2, fontweight='bold')
ax2.set_ylim(0, 72)
ax2.grid(True, axis='y', linestyle=':', alpha=0.6)

plt.tight_layout()
plt.savefig('../paper/figures/fig_ablation.pdf', bbox_inches='tight')
plt.savefig('../paper/figures/fig_ablation.png', bbox_inches='tight')
plt.close()

# ==============================================================================
# FIGURE 3: 4-Rank Multi-Pair Bandwidth & Message Rate (osu_mbw_mr)
# ==============================================================================
bw_sizes = ['1B', '4B', '16B', '64B', '256B', '1K', '4K', '16K', '64K', '256K', '512K', '1M', '4M']
bw_mbps  = [10.15, 40.81, 148.62, 452.19, 1318.32, 4547.80, 5252.84, 19529.94, 28592.30, 31520.08, 29889.48, 5138.16, 3790.36]
msgrate  = [10.15, 10.20, 9.29,   7.07,   5.15,    4.44,    1.28,    1.19,     0.44,     0.12,     0.057,    0.0049,  0.0009]

fig, ax1 = plt.subplots(figsize=(8.0, 3.8), dpi=300)
x = np.arange(len(bw_sizes))
w = 0.42

l1 = ax1.bar(x - w/2, [b/1000.0 for b in bw_mbps], width=w, color='#1565c0', edgecolor='#0d47a1', label='Aggregate Bandwidth (GB/s)')
ax1.set_xlabel('Message Payload Size', fontsize=10, fontweight='bold')
ax1.set_ylabel('Aggregate Bandwidth (GB/s)', color='#1565c0', fontsize=10, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(bw_sizes, fontsize=8.5)
ax1.grid(True, linestyle=':', alpha=0.5)
ax1.set_ylim(0, 40)

ax2 = ax1.twinx()
l2 = ax2.plot(x + w/2, msgrate, 'o-', color='#e65100', linewidth=2.2, markersize=5.5, label='Message Rate (M msgs/sec)')
ax2.set_ylabel('Message Rate (Million msgs/sec)', color='#e65100', fontsize=10, fontweight='bold')
ax2.set_ylim(0, 12.5)

ax1.annotate('Peak L3 Cache Saturation:\n31.52 GB/s at 256 KB', xy=(8.85, 31.6), xytext=(4.0, 33.5),
             arrowprops=dict(arrowstyle='->', color='#1565c0', lw=1.4),
             fontsize=8.3, fontweight='bold', color='#1565c0',
             bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='#bbdefb', alpha=0.95))

lines_leg = [l1] + l2
labels_leg = [l.get_label() for l in lines_leg]
ax1.legend(lines_leg, labels_leg, loc='upper right', fontsize=8.0, frameon=True)

plt.title('4-Rank Multi-Pair Shared-Memory Bandwidth & Message Rate (osu_mbw_mr)', fontsize=10.5, fontweight='bold')
plt.tight_layout()
plt.savefig('../paper/figures/fig_bandwidth.pdf', bbox_inches='tight')
plt.savefig('../paper/figures/fig_bandwidth.png', bbox_inches='tight')
plt.close()

# Note: term_objdump.png is now an authentic user terminal screenshot; do not overwrite it here.
print('FINAL_FIGURES_GENERATED')
