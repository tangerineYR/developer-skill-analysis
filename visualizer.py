"""Offline plots for the frozen 2025 Wanted query snapshot."""
import argparse
import json
from pathlib import Path

import matplotlib
import matplotlib.font_manager as fm
import pandas as pd
import seaborn as sns

from analysis import (
    build_summary, compute_sample_audit, load_and_clean_data, normalization_audit,
)


def configure_font():
    names = {font.name for font in fm.fontManager.ttflist}
    for name in ("Malgun Gothic", "AppleGothic", "NanumGothic", "Noto Sans CJK JP", "Noto Sans CJK KR"):
        if name in names:
            matplotlib.rcParams["font.family"] = name
            matplotlib.rcParams["axes.unicode_minus"] = False
            return
    raise RuntimeError("Korean font unavailable. Install fonts-noto-cjk or NanumGothic before plotting.")


def plot_results(summary, output_dir, show=False):
    import matplotlib.pyplot as plt

    def save(fig, name):
        fig.tight_layout()
        fig.savefig(output_dir / name, dpi=150)
        if show:
            plt.show()
        plt.close(fig)

    counts = summary["role_counts"]
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(list(counts), list(counts.values()), color="#438b88")
    ax.bar_label(bars, padding=4)
    ax.set(title="직무별 분석 대상 공고 Row 수", xlabel="수집 표본 Row 수 (N)", xlim=(0, max(counts.values()) * 1.15))
    save(fig, "graph_job_role_counts.png")

    top = summary["top_skills_by_role"]
    for role, records in top.items():
        fig, ax = plt.subplots(figsize=(12, 9))
        records = records[::-1]
        bars = ax.barh([r["skill"] for r in records], [r["percentage"] for r in records], color="#438b88")
        ax.bar_label(bars, fmt="%.1f%%", padding=3)
        ax.set(title=f"{role}: 분석 표본 주요 기술 (N={counts[role]} rows)",
               xlabel="분석 표본 내 공고 포함 비율 (%) — 분모: 해당 직무 Row 수", xlim=(0, 100))
        save(fig, f"graph_top_skills_{role.replace(' ', '_')}.png")

    skills = sorted({r["skill"] for records in top.values() for r in records[:15]})
    # All selected skills must be measured even if outside another role's top 20.
    frequencies = summary["all_skill_frequencies"]
    matrix = pd.DataFrame({role: {s: next((r["percentage"] for r in records if r["skill"] == s), 0)
                                  for s in skills} for role, records in frequencies.items()}).T
    fig, ax = plt.subplots(figsize=(20, 6))
    sns.heatmap(matrix, annot=True, fmt=".1f", cmap="rocket_r", ax=ax, cbar_kws={"label": "% of role rows"})
    ax.set(title="직무별 분석 표본 내 주요 기술 포함 비율 (%)", xlabel="기술 — 분모: 해당 직무 Row 수", ylabel="직무")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    save(fig, "graph_skill_heatmap.png")

    fig, ax = plt.subplots(figsize=(12, 6))
    pd.DataFrame(summary["category_occurrence_composition"]).T.plot.barh(stacked=True, ax=ax, colormap="Set2")
    ax.set(title="직무별 기술 언급의 카테고리 구성 비율", xlabel="각 직무에서 집계된 canonical skill occurrence 기준 (%)", xlim=(0, 100), ylabel="직무")
    for container in ax.containers:
        ax.bar_label(container, labels=[f"{b.get_width():.1f}%" if b.get_width() > 5 else "" for b in container], label_type="center")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.19), ncol=4)
    save(fig, "graph_skill_category_stacked.png")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("wanted_jobs.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("."))
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()
    if not args.show:
        matplotlib.use("Agg")
    configure_font()
    df = load_and_clean_data(args.input)
    summary = build_summary(df, args.input)
    results = args.output_dir / "results"
    results.mkdir(parents=True, exist_ok=True)
    for name, data in (("analysis_summary.json", summary), ("sample_audit.json", compute_sample_audit(df))):
        (results / name).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    normalization_audit(df).to_csv(
        results / "normalization_audit.csv",
        index=False,
        lineterminator="\n",
    )
    from analysis import compute_skill_frequency

    figures_dir = results / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    plot_results(
        {**summary, "all_skill_frequencies": compute_skill_frequency(df)},
        figures_dir,
        args.show,
    )

    print(f"Analyzed {len(df)} historical rows; wrote graphs and results to {args.output_dir}")


if __name__ == "__main__":
    main()
