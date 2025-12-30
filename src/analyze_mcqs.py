import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

sns.set_theme(style="whitegrid", palette="muted")

METRICS = ['clarity', 'correctness', 'distractor_quality', 'relevance']
EXPERIMENTS_FOLDER = "data/output/mcqs"
EVALUATORS_FOLDER = "data/output/different_evaluators1"
OUTPUT_FOLDER = "data/output/analysis"


def load_data(path, group_name, recursive=False):
    """
    Load MCQ evaluation data from JSON files
    """
    pattern = "**/*.json" if recursive else "*.json"
    rows = []
    for f in Path(path).glob(pattern):
        if recursive and f.name != "evaluated_mcqs.json":
            continue
        name = f.parent.name if recursive else f.stem
        for mcq in json.load(open(f)):
            scores = {k: v.get('score', 0)
                      for k, v in mcq.get('evaluation', {}).items()}
            rows.append({group_name: name, **scores})
    df = pd.DataFrame(rows)
    if not df.empty:
        df['total_score'] = df[METRICS].mean(axis=1)
    return df


def plot_comparison(df, group_col, prefix, output_dir):
    """
    Create comparison plots for MCQ evaluations
    """
    if df.empty:
        print(f"No data for {prefix}.")
        return

    print(
        f"Analyzing {len(df)} MCQs from {df[group_col].nunique()} {prefix}...")

    # Average scores
    melted = df.melt(id_vars=group_col, value_vars=METRICS)
    sns.barplot(data=melted, x='variable', y='value', hue=group_col)
    plt.title(f'{prefix.title()} - Avg Scores')
    plt.ylabel('Score (0-2)')
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.savefig(
        output_dir / f'{prefix}_average_scores.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Overall scores
    avg = df.groupby(group_col)['total_score'].mean(
    ).sort_values(ascending=False)
    ax = sns.barplot(x=avg.index, y=avg.values, hue=avg.index,
                     palette='rocket', legend=False)
    for i, v in enumerate(avg.values):
        ax.text(i, v, f'{v:.2f}', ha='center', va='bottom')
    plt.title(f'{prefix.title()} - Overall Scores')
    plt.ylabel('Score (0-2)')
    plt.savefig(
        output_dir / f'{prefix}_overall_scores.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Distributions
    for metric in METRICS:
        dist = df.groupby([group_col, metric]).size().unstack(fill_value=0)
        (dist.div(dist.sum(axis=1), axis=0) * 100).plot(
            kind='bar', stacked=True, color=['#ff9999', '#66b3ff', '#99ff99'], figsize=(8, 5))
        plt.title(f'{prefix.title()} - {metric.title()} Distribution')
        plt.ylabel('Percentage (%)')
        plt.savefig(
            output_dir / f'{prefix}_distribution_{metric}.png', dpi=300, bbox_inches='tight')
        plt.close()


def main():
    out = Path(OUTPUT_FOLDER)
    out.mkdir(parents=True, exist_ok=True)

    df_experiments = load_data(
        EXPERIMENTS_FOLDER, 'experiment', recursive=True)
    plot_comparison(df_experiments, 'experiment', 'experiments', out)

    df_evaluators = load_data(EVALUATORS_FOLDER, 'evaluator', recursive=False)
    plot_comparison(df_evaluators, 'evaluator', 'evaluators', out)

    print(f"Results saved to: {out}")


if __name__ == "__main__":
    main()
