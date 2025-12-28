import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

sns.set_theme(style="whitegrid", palette="muted")
METRICS = ['clarity', 'correctness', 'distractor_quality', 'relevance']

def load_data(path):
    rows = []
    for f in Path(path).rglob("evaluated_mcqs.json"):
        for m in json.load(open(f)):
            evals = {k: v.get('score', 0) for k, v in m.get('evaluation', {}).items()}
            rows.append({'experiment': f.parent.name, **evals})
    df = pd.DataFrame(rows)
    if not df.empty:
        df['total_score'] = df[METRICS].mean(axis=1)
    return df

def save_plot(name, title, ylabel, output_dir):
    plt.title(title, fontsize=14, fontweight='bold', pad=15)
    plt.ylabel(ylabel)
    if plt.gca().get_legend():
        plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
    plt.savefig(output_dir / name, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    base, out = Path("data/output/mcqs"), Path("data/output/analysis")
    out.mkdir(parents=True, exist_ok=True)
    df = load_data(base)
    
    if df.empty: return print("No data found.")
    print(f"Analyzing {len(df)} MCQs from {df['experiment'].nunique()} experiments...")

    # Average scores comparison
    df.melt(id_vars='experiment', value_vars=METRICS).pipe(
        lambda d: sns.barplot(data=d, x='variable', y='value', hue='experiment')
    )
    save_plot('average_scores_comparison.png', 'Avg Scores', 'Score (0-2)', out)

    # Combined overall scores
    avg = df.groupby('experiment')['total_score'].mean().sort_values(ascending=False).reset_index()
    ax = sns.barplot(data=avg, x='experiment', y='total_score', hue='experiment', palette='rocket', legend=False)
    for p in ax.patches:
        ax.annotate(f'{p.get_height():.2f}', (p.get_x() + p.get_width()/2, p.get_height()), ha='center', va='bottom')
    save_plot('combined_overall_scores.png', 'Overall Progress', 'Score (0-2)', out)

    # Distributions
    for m in METRICS:
        dist = df.groupby(['experiment', m]).size().unstack(fill_value=0).pipe(lambda d: d.div(d.sum(1), axis=0) * 100)
        dist.plot(kind='bar', stacked=True, color=['#ff9999','#66b3ff','#99ff99'], figsize=(8,5))
        save_plot(f'distribution_{m}.png', f'{m.title()} Distribution', 'Percentage (%)', out)

    print(f"Done! Results: {out}")

if __name__ == "__main__":
    main()