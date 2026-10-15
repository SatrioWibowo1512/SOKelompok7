"""Membuat gambar Gantt chart (PNG) dari jadwal yang dihitung scheduler_sim.py.

Membutuhkan matplotlib (pip install matplotlib). Contoh:
    python3 plot_gantt.py --out gambar
"""

import argparse
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import scheduler_sim as sim  # noqa: E402

COLORS = {"P1": "#4C78A8", "P2": "#F58518", "P3": "#54A24B", "P4": "#B279A2",
          "P5": "#E45756", sim.IDLE: "#BBBBBB"}


def draw(result, path):
    fig, ax = plt.subplots(figsize=(9, 1.9))
    for pid, start, end in result.slices:
        ax.barh(0, end - start, left=start, height=0.6, color=COLORS.get(pid, "#888888"),
                edgecolor="black")
        ax.text((start + end) / 2, 0, pid, ha="center", va="center", color="white", fontweight="bold")
    ticks = sorted({s for _, s, _ in result.slices} | {result.slices[-1][2]})
    ax.set_xticks(ticks)
    ax.set_yticks([])
    ax.set_xlim(0, result.slices[-1][2])
    ax.set_xlabel("Waktu")
    ax.set_title(f"Gantt chart: {result.name}", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Gambar Gantt chart semua algoritma.")
    parser.add_argument("--dataset", help="CSV pid,arrival,burst,priority (bawaan: dataset kelas)")
    parser.add_argument("--out", default="gambar", help="folder keluaran PNG")
    args = parser.parse_args()
    try:
        processes = sim.load_csv(args.dataset) if args.dataset else list(sim.DATASET_KELAS)
        results = sim.run_all(processes, sensitivity=True)
    except ValueError as error:
        print(f"Kesalahan input: {error}", file=sys.stderr)
        return 1
    os.makedirs(args.out, exist_ok=True)
    for number, result in enumerate(results, start=1):
        path = os.path.join(args.out, f"gantt_{number}.png")
        draw(result, path)
        print(path, "<-", result.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
