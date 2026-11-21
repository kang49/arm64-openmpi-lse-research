# Characterizing and Optimizing ARM64 Large System Extensions (LSE) and Lock-Free Shared-Memory Queues in Open MPI

**Author:** Kankawee Aramrak (Undergraduate Computer Science Student)  
**Date:** November 2026  
**Paper:** [PDF](
https://raw.githubusercontent.com/kang49/arm64-openmpi-lse-research/c52403d8ee3c8881b20b3d44dfe061e93e7ae297/paper/ARM64_OpenMPI_LSE_Research_Paper.pdf) | [LaTeX Source](paper/ARM64_OpenMPI_LSE_Research_Paper.tex)

---

## Overview

Modern ARM64 processors (ARMv8.1-A and higher) implement hardware **Large System Extensions (LSE)**—single-instruction atomic read-modify-write (`ldaddal`, `swpal`) and 64/128-bit compare-and-swap (`casal`, `caspal`)—alongside `FEAT_LRCPC` (`ldapr`) for weak memory ordering. However, generic distribution builds and asymmetric contention paths in upstream **Open MPI v6.0** prevent optimal utilization of these hardware units.

This repository contains the IEEEtran research paper, micro-batched hardware benchmarks, figure-generation scripts, and upstream-ready patches from our bare-metal investigation on a quad-core ARMv8.2-A (Cortex-A76) node.

---

## Key Contributions & Verified Results

| Experiment / Optimization | Metric | Baseline | Optimized / Hardware LSE | Improvement |
| :--- | :--- | :--- | :--- | :--- |
| **Micro-Batched Atomics ($K=32$, $N=4$ cores)** | Variance ($\text{ns}^2$) | `4,480.95` (LL/SC) | **`1,153.86`** (`ldaddal`) | **3.88× lower variance** |
| **Micro-Batched Atomics ($K=32$, $N=4$ cores)** | p99 / p99.9 Tail | `317.13` / `421.88 ns` | **`155.09`** / **`172.45 ns`** | **2.04× / 2.45× lower tail** |
| **128-bit CAS `opal_lifo_pop_atomic` ($T=2$)** | Pop+Push Latency | `180.4 ± 4.8 ns` | **`32.6 ± 0.5 ns`** | **5.53× speedup** |
| **128-bit CAS `opal_lifo_pop_atomic` ($T=4, 8$)** | Pop+Push Latency | `168.8` / `165.8 ns` | **`34.0`** / **`38.2 ns`** | **4.96× / 4.34× speedup** |
| **`mca_part_persist_progress` (`FEAT_LRCPC ldapr`)** | `MPI_Test()` Poll (`MPI_THREAD_MULTIPLE`) | `57.05 ± 0.23 ns` | **`27.20 ± 0.75 ns`** | **2.10× faster (-52.3%)** |
| **Multi-Pair Saturation (`osu_mbw_mr`, 4 ranks)** | Regression Sanity Check | — | **`31.52 GB/s`** @ 256 KB | **10.20M msgs/sec** @ 4 B |

### Upstream Open MPI v6.0 Patches
The two clean, isolated patches are included in [`patches/`](patches/) and published on our Open MPI fork:
1. **`opal/lifo`:** Restore symmetric 5-attempt contention backoff to the 128-bit CAS `opal_lifo_pop_atomic` path ([`fix/opal-lifo-cas128-backoff`](https://github.com/kang49/ompi/compare/main...fix/opal-lifo-cas128-backoff))
2. **`part/persist`:** Avoid atomic RMW and `pthread_mutex` overhead in `mca_part_persist_progress` when uninitialized via a thread-safe `FEAT_LRCPC` (`ldapr`) acquire-load guard ([`fix/part-persist-progress-fastpath`](https://github.com/kang49/ompi/compare/main...fix/part-persist-progress-fastpath))

---

## Repository Structure

```text
.
├── paper/
│   ├── ARM64_OpenMPI_LSE_Research_Paper.pdf   # Compiled IEEEtran paper (5 pages)
│   ├── ARM64_OpenMPI_LSE_Research_Paper.tex   # LaTeX source
│   └── figures/                               # Publication plots & AArch64 disassembly capture
├── benchmarks/
│   ├── bench_tail_batch.c                     # K=32 micro-batched cntvct_el0 atomic benchmark
│   ├── bench_mpi_test.c                       # 10^6 MPI_Test() polling benchmark (MPI_THREAD_MULTIPLE)
│   └── generate_figures.py                    # Matplotlib script to regenerate paper figures
├── patches/
│   ├── 0001-opal-lifo-add-contention-backoff-to-128-bit-CAS-pop-.patch
│   └── 0001-part-persist-avoid-atomic-and-mutex-overhead-when-un.patch
├── LICENSE
└── README.md
```

---

## Reproducibility

### Testbed Hardware & Software
- **Node:** Bare-metal quad-core ARM Cortex-A76 (Broadcom BCM2712 SoC, ARMv8.2-A + LSE + `FEAT_LRCPC`)
- **Memory Hierarchy:** 64 KB L1I/L1D, 512 KB private L2/core, 2 MB shared L3 DSU, 8 GB LPDDR4X-4267
- **OS & Toolchain:** Debian 13 (Linux `6.18.60`), GCC `14.2.0` (`-O3 -mcpu=cortex-a76`)

### 1. Lock CPU Frequency (Eliminate DVFS Artifacts)
```bash
for cpu in /sys/devices/system/cpu/cpu[0-3]/cpufreq/scaling_governor; do
    echo performance | sudo tee "$cpu"
done
```

### 2. Run Micro-Batched Atomic Tail-Latency Benchmark
```bash
gcc -O3 -mcpu=cortex-a76 -pthread benchmarks/bench_tail_batch.c -o bench_tail_batch
./bench_tail_batch
```

### 3. Run `MPI_Test()` Polling Benchmark (`MPI_THREAD_MULTIPLE`)
```bash
mpicc -O3 -mcpu=cortex-a76 benchmarks/bench_mpi_test.c -o bench_mpi_test
for i in 1 2 3 4 5; do mpirun -np 2 --bind-to core ./bench_mpi_test; done
```

---

## Citation

If you use this work, benchmarks, or patches in your research, please cite:

```bibtex
@misc{aramrak2026arm64lse,
  author       = {Aramrak, Kankawee},
  title        = {Characterizing and Optimizing ARM64 Large System Extensions (LSE) and Lock-Free Shared-Memory Queues in Open MPI},
  year         = {2026},
  month        = nov,
  howpublished = {\url{https://github.com/kang49/arm64-openmpi-lse-research}}
}
```

## License

The research paper, benchmarks, and plotting scripts in this repository are licensed under the [MIT License](LICENSE). The Open MPI patches under [`patches/`](patches/) follow the upstream Open MPI BSD-3-Clause license.
