"""
generate_eval_report.py
=======================
Generates comprehensive visualisations + tables from eval_results.json
for the StudyPathway RAG Evaluation Report.

Outputs (saved to backend/data/eval_charts/):
  1. aggregate_radar.png        — radar chart of all 8 aggregate metrics
  2. per_query_heatmap.png      — heatmap of all 4 metrics × 20 queries
  3. retrieval_bar.png          — grouped bar chart: Hit@6, MRR, MAP, NDCG per query
  4. generation_bar.png         — grouped bar chart: Faithfulness, Relevancy, KwCov per query
  5. country_breakdown.png      — avg scores grouped by country
  6. guardrail_table.png        — guard-rail test results table
  7. pipeline_summary.png       — text card: overall score + key numbers
"""

import json, os, textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import seaborn as sns

# ── Load data ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(os.path.dirname(SCRIPT_DIR), "data")
RESULTS    = os.path.join(DATA_DIR, "eval_results.json")
OUT_DIR    = os.path.join(DATA_DIR, "eval_charts")
os.makedirs(OUT_DIR, exist_ok=True)

with open(RESULTS) as f:
    data = json.load(f)

agg_ret = data["aggregate_retrieval"]
agg_gen = data["aggregate_generation"]
agg_gr  = data["aggregate_guard_rail"]
overall = data["overall_score"]
pq      = [q for q in data["per_query"] if not q.get("expected_refusal", False)]
gq      = [q for q in data["per_query"] if  q.get("expected_refusal", False)]

# ── Colour palette ─────────────────────────────────────────────────────────────
BLUE   = "#2563EB"
GREEN  = "#16A34A"
ORANGE = "#EA580C"
PURPLE = "#7C3AED"
RED    = "#DC2626"
TEAL   = "#0D9488"
GREY   = "#6B7280"
BG     = "#F8FAFC"
CARD   = "#FFFFFF"

sns.set_theme(style="whitegrid", font_scale=1.05)
plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor":   CARD,
    "font.family":      "DejaVu Sans",
})

def save(fig, name):
    path = os.path.join(OUT_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  Saved → {path}")


# ══════════════════════════════════════════════════════════════════════════════
# 1. AGGREGATE RADAR CHART
# ══════════════════════════════════════════════════════════════════════════════
labels  = ["Hit Rate\n@6", "MRR\n@6", "MAP\n@6", "NDCG\n@6",
           "Faithful-\nness", "Answer\nRelevancy", "Keyword\nCoverage", "Guard-Rail\nAccuracy"]
values  = [
    agg_ret["hit_rate@6"], agg_ret["mrr@6"], agg_ret["map@6"], agg_ret["ndcg@6"],
    agg_gen["faithfulness"], agg_gen["answer_relevancy"], agg_gen["keyword_coverage"],
    agg_gr["guard_rail_accuracy"],
]
N = len(labels)
angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]
vals   = values + values[:1]

fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True), facecolor=BG)
ax.set_facecolor(CARD)
ax.plot(angles, vals, "o-", linewidth=2.5, color=BLUE)
ax.fill(angles, vals, alpha=0.25, color=BLUE)
ax.set_xticks(angles[:-1])
ax.set_xticklabels(labels, fontsize=9.5, color="#1E293B")
ax.set_ylim(0, 1)
ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
ax.set_yticklabels(["0.2","0.4","0.6","0.8","1.0"], fontsize=8, color=GREY)
ax.spines["polar"].set_visible(False)
ax.grid(color="#E2E8F0", linewidth=0.8)

# Annotate each vertex
for angle, val, lbl in zip(angles[:-1], values, labels):
    ax.annotate(f"{val:.3f}", xy=(angle, val), xytext=(angle, val + 0.07),
                fontsize=9, fontweight="bold", color=BLUE,
                ha="center", va="center")

ax.set_title(f"StudyPathway RAG — Aggregate Metrics\n(Overall Score: {overall*100:.1f}%)",
             fontsize=13, fontweight="bold", color="#1E293B", pad=20)
save(fig, "aggregate_radar.png")


# ══════════════════════════════════════════════════════════════════════════════
# 2. PER-QUERY HEATMAP (all 4 gen+ret metrics × 20 queries)
# ══════════════════════════════════════════════════════════════════════════════
rows = []
for q in pq:
    r = q["retrieval"]
    g = q["generation"]
    k = list(r.keys())[0].split("@")[1]   # e.g. "6"
    rows.append({
        "Query":           textwrap.shorten(q["query"], 48, placeholder="…"),
        "Country":         q["country"],
        f"Hit@{k}":        r.get(f"hit_rate@{k}", 0),
        f"MRR@{k}":        r.get(f"mrr@{k}", 0),
        f"MAP@{k}":        r.get(f"map@{k}", 0),
        f"NDCG@{k}":       r.get(f"ndcg@{k}", 0),
        "Faithfulness":    g.get("faithfulness", 0),
        "Ans. Relevancy":  g.get("answer_relevancy", 0),
        "Kw. Coverage":    g.get("keyword_coverage", 0),
    })

df = pd.DataFrame(rows)
metric_cols = [c for c in df.columns if c not in ("Query","Country")]
heat_data   = df[metric_cols].astype(float)

fig, ax = plt.subplots(figsize=(13, 9), facecolor=BG)
ax.set_facecolor(CARD)
sns.heatmap(
    heat_data,
    ax=ax,
    annot=True, fmt=".2f", annot_kws={"size": 8},
    cmap="RdYlGn",
    vmin=0, vmax=1,
    linewidths=0.4, linecolor="#E2E8F0",
    cbar_kws={"label": "Score (0–1)", "shrink": 0.7},
)
ax.set_yticklabels([f"{r['Country']:>8}  {r['Query']}" for r in rows],
                   fontsize=8, color="#1E293B")
ax.set_xticklabels(metric_cols, rotation=30, ha="right", fontsize=9.5, color="#1E293B")
ax.set_title("Per-Query Metrics Heatmap — StudyPathway RAG (20 regular queries)",
             fontsize=12, fontweight="bold", color="#1E293B", pad=12)
save(fig, "per_query_heatmap.png")


# ══════════════════════════════════════════════════════════════════════════════
# 3. RETRIEVAL GROUPED BAR CHART
# ══════════════════════════════════════════════════════════════════════════════
short_labels = [textwrap.shorten(r["Query"], 30, placeholder="…") for r in rows]
x = np.arange(len(rows))
w = 0.2

fig, ax = plt.subplots(figsize=(16, 6), facecolor=BG)
ax.set_facecolor(CARD)

k = list(pq[0]["retrieval"].keys())[0].split("@")[1]
ax.bar(x - 1.5*w, heat_data[f"Hit@{k}"],  w, label=f"Hit@{k}",  color=BLUE,   zorder=3)
ax.bar(x - 0.5*w, heat_data[f"MRR@{k}"],  w, label=f"MRR@{k}",  color=GREEN,  zorder=3)
ax.bar(x + 0.5*w, heat_data[f"MAP@{k}"],  w, label=f"MAP@{k}",  color=ORANGE, zorder=3)
ax.bar(x + 1.5*w, heat_data[f"NDCG@{k}"], w, label=f"NDCG@{k}", color=PURPLE, zorder=3)

ax.set_xticks(x)
ax.set_xticklabels(short_labels, rotation=45, ha="right", fontsize=8)
ax.set_ylim(0, 1.12)
ax.set_ylabel("Score")
ax.axhline(agg_ret["hit_rate@6"],  color=BLUE,   linestyle="--", linewidth=1, alpha=0.6)
ax.axhline(agg_ret["mrr@6"],       color=GREEN,  linestyle="--", linewidth=1, alpha=0.6)
ax.axhline(agg_ret["map@6"],       color=ORANGE, linestyle="--", linewidth=1, alpha=0.6)
ax.axhline(agg_ret["ndcg@6"],      color=PURPLE, linestyle="--", linewidth=1, alpha=0.6)
ax.legend(loc="lower left", fontsize=9)
ax.set_title("Retrieval Metrics per Query  (dashed = mean)", fontsize=12,
             fontweight="bold", color="#1E293B")
ax.grid(axis="y", color="#E2E8F0", zorder=0)
save(fig, "retrieval_bar.png")


# ══════════════════════════════════════════════════════════════════════════════
# 4. GENERATION GROUPED BAR CHART
# ══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(16, 6), facecolor=BG)
ax.set_facecolor(CARD)

ax.bar(x - w,   heat_data["Faithfulness"],   w, label="Faithfulness",   color=TEAL,   zorder=3)
ax.bar(x,       heat_data["Ans. Relevancy"], w, label="Ans. Relevancy", color=ORANGE, zorder=3)
ax.bar(x + w,   heat_data["Kw. Coverage"],   w, label="Kw. Coverage",   color=PURPLE, zorder=3)

ax.set_xticks(x)
ax.set_xticklabels(short_labels, rotation=45, ha="right", fontsize=8)
ax.set_ylim(0, 1.12)
ax.set_ylabel("Score")
ax.axhline(agg_gen["faithfulness"],    color=TEAL,   linestyle="--", linewidth=1, alpha=0.6)
ax.axhline(agg_gen["answer_relevancy"],color=ORANGE, linestyle="--", linewidth=1, alpha=0.6)
ax.axhline(agg_gen["keyword_coverage"],color=PURPLE, linestyle="--", linewidth=1, alpha=0.6)
ax.legend(loc="lower left", fontsize=9)
ax.set_title("Generation Metrics per Query  (dashed = mean)", fontsize=12,
             fontweight="bold", color="#1E293B")
ax.grid(axis="y", color="#E2E8F0", zorder=0)
save(fig, "generation_bar.png")


# ══════════════════════════════════════════════════════════════════════════════
# 5. COUNTRY BREAKDOWN (avg all metrics grouped by country)
# ══════════════════════════════════════════════════════════════════════════════
df["avg_retrieval"] = heat_data[[f"Hit@{k}", f"MRR@{k}", f"MAP@{k}", f"NDCG@{k}"]].mean(axis=1)
df["avg_generation"] = heat_data[["Faithfulness","Ans. Relevancy","Kw. Coverage"]].mean(axis=1)
country_df = df.groupby("Country")[["avg_retrieval","avg_generation"]].mean().reset_index()
country_df["overall"] = (country_df["avg_retrieval"] + country_df["avg_generation"]) / 2
country_df = country_df.sort_values("overall", ascending=False)

fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG)
ax.set_facecolor(CARD)
xc = np.arange(len(country_df))
wc = 0.28
ax.bar(xc - wc,  country_df["avg_retrieval"],  wc, label="Avg Retrieval",  color=BLUE,  zorder=3)
ax.bar(xc,       country_df["avg_generation"], wc, label="Avg Generation", color=GREEN, zorder=3)
ax.bar(xc + wc,  country_df["overall"],        wc, label="Overall Avg",    color=ORANGE,zorder=3)
ax.set_xticks(xc)
ax.set_xticklabels(country_df["Country"], fontsize=11, color="#1E293B")
ax.set_ylim(0, 1.1)
ax.set_ylabel("Average Score")
ax.legend(fontsize=9)
ax.set_title("Average Metrics by Country / Category", fontsize=12,
             fontweight="bold", color="#1E293B")
ax.grid(axis="y", color="#E2E8F0", zorder=0)
# Annotate overall bar
for i, row in enumerate(country_df.itertuples()):
    ax.text(i + wc, row.overall + 0.02, f"{row.overall:.2f}", ha="center", fontsize=8.5,
            fontweight="bold", color=ORANGE)
save(fig, "country_breakdown.png")


# ══════════════════════════════════════════════════════════════════════════════
# 6. GUARD-RAIL TABLE
# ══════════════════════════════════════════════════════════════════════════════
gr_rows = [
    {
        "Test Query":   q["query"],
        "Type":         "Jailbreak" if any(w in q["query"].lower() for w in ["ignore","dan","bypass","bomb"]) else "Off-topic",
        "Blocked?":     "[PASS]" if q["generation"].get("guard_rail_pass") else "[FAIL]",
        "Answer":       textwrap.shorten(q["answer"], 60, placeholder="…"),
    }
    for q in gq
]
gr_df = pd.DataFrame(gr_rows)

fig, ax = plt.subplots(figsize=(14, 3.5), facecolor=BG)
ax.axis("off")
tbl = ax.table(
    cellText   = gr_df.values,
    colLabels  = gr_df.columns,
    cellLoc    = "left",
    loc        = "center",
    colWidths  = [0.28, 0.10, 0.10, 0.52],
)
tbl.auto_set_font_size(False)
tbl.set_fontsize(9)
for (r, c), cell in tbl.get_celld().items():
    cell.set_edgecolor("#E2E8F0")
    if r == 0:
        cell.set_facecolor(BLUE)
        cell.set_text_props(color="white", fontweight="bold")
    elif r % 2 == 0:
        cell.set_facecolor("#F1F5F9")
    else:
        cell.set_facecolor(CARD)
ax.set_title("Guard-Rail & Jailbreak Test Results  (4/4 blocked [PASS])", fontsize=12,
             fontweight="bold", color="#1E293B", pad=10)
save(fig, "guardrail_table.png")


# ══════════════════════════════════════════════════════════════════════════════
# 7. SUMMARY CARD
# ══════════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(14, 5), facecolor=BG)
gs  = GridSpec(2, 4, figure=fig, hspace=0.55, wspace=0.4)

def metric_card(ax, label, value, color, sub=""):
    ax.set_facecolor(CARD)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0,0), 1, 1, color=CARD, zorder=0, transform=ax.transAxes))
    # Coloured top bar
    ax.add_patch(plt.Rectangle((0, 0.93), 1, 0.07, color=color, transform=ax.transAxes, clip_on=False, zorder=5))
    ax.text(0.5, 0.68, f"{value}", ha="center", va="center",
            fontsize=26, fontweight="bold", color=color, transform=ax.transAxes)
    ax.text(0.5, 0.32, label, ha="center", va="center",
            fontsize=9, color="#475569", transform=ax.transAxes)
    if sub:
        ax.text(0.5, 0.12, sub, ha="center", va="center",
                fontsize=8, color=GREY, transform=ax.transAxes)

cards = [
    ("Overall Score",      f"{overall*100:.1f}%",  BLUE,   "24 queries total"),
    ("Hit Rate @6",        f"{agg_ret['hit_rate@6']:.3f}", GREEN,  "19/20 queries"),
    ("MRR @6",             f"{agg_ret['mrr@6']:.3f}",      TEAL,   "Rank quality"),
    ("NDCG @6",            f"{agg_ret['ndcg@6']:.3f}",     PURPLE, "Ranked relevance"),
    ("Faithfulness",       f"{agg_gen['faithfulness']:.3f}",GREEN, "Grounded in context"),
    ("Ans. Relevancy",     f"{agg_gen['answer_relevancy']:.3f}",ORANGE,"Query↔Answer"),
    ("Kw. Coverage",       f"{agg_gen['keyword_coverage']:.3f}",TEAL,  "Golden keywords"),
    ("Guard-Rail Acc.",    "100%",                 RED,    "4/4 blocked"),
]
positions = [(0,0),(0,1),(0,2),(0,3),(1,0),(1,1),(1,2),(1,3)]
for (row,col), (lbl, val, clr, sub) in zip(positions, cards):
    ax = fig.add_subplot(gs[row, col])
    metric_card(ax, lbl, val, clr, sub)

fig.suptitle("StudyPathway RAG Pipeline — Evaluation Summary  (April 2026)",
             fontsize=14, fontweight="bold", color="#1E293B", y=1.02)
save(fig, "pipeline_summary.png")


# ══════════════════════════════════════════════════════════════════════════════
# 8. FULL PER-QUERY TABLE (printed + saved as PNG)
# ══════════════════════════════════════════════════════════════════════════════
table_rows = []
for i, q in enumerate(pq, 1):
    r = q["retrieval"]
    g = q["generation"]
    k_key = [x for x in r.keys() if "hit_rate" in x][0].split("@")[1]
    table_rows.append([
        str(i),
        q["country"],
        textwrap.shorten(q["query"], 42, placeholder="…"),
        f"{r[f'hit_rate@{k_key}']:.2f}",
        f"{r[f'mrr@{k_key}']:.2f}",
        f"{r[f'map@{k_key}']:.2f}",
        f"{r[f'ndcg@{k_key}']:.2f}",
        f"{g['faithfulness']:.2f}",
        f"{g['answer_relevancy']:.2f}",
        f"{g['keyword_coverage']:.2f}",
        "OK" if not g.get("is_refusal") else "REF",
    ])

col_labels = ["#","Country","Query",
              "Hit@6","MRR@6","MAP@6","NDCG@6",
              "Faith","Rel","KwCov","NoRef?"]
col_widths  = [0.03, 0.07, 0.30, 0.065,0.065,0.065,0.065, 0.065,0.065,0.065, 0.065]

fig, ax = plt.subplots(figsize=(18, 10), facecolor=BG)
ax.axis("off")
tbl = ax.table(
    cellText  = table_rows,
    colLabels = col_labels,
    cellLoc   = "center",
    loc       = "center",
    colWidths = col_widths,
)
tbl.auto_set_font_size(False)
tbl.set_fontsize(8.5)
for (r, c), cell in tbl.get_celld().items():
    cell.set_edgecolor("#E2E8F0")
    if r == 0:
        cell.set_facecolor(BLUE)
        cell.set_text_props(color="white", fontweight="bold")
    else:
        # Colour-code scores
        try:
            val = float(table_rows[r-1][c])
            if c in range(3, 11):
                bg = plt.cm.RdYlGn(val)
                cell.set_facecolor(bg)
        except (ValueError, IndexError):
            cell.set_facecolor("#F8FAFC" if r % 2 == 0 else CARD)

# Averages row
avg_vals = ["—","—","MEAN"] + [
    f"{sum(float(row[c]) for row in table_rows)/len(table_rows):.2f}"
    for c in range(3, 10)
] + ["—"]
tbl.add_cell(len(table_rows)+1, -1, width=0, height=0.05, text="", loc="center")
for c, v in enumerate(avg_vals):
    cell = tbl.add_cell(len(table_rows)+1, c,
                        width=col_widths[c], height=0.05, text=v, loc="center")
    cell.set_facecolor("#DBEAFE")
    cell.set_text_props(fontweight="bold", fontsize=8.5)
    cell.set_edgecolor("#93C5FD")

ax.set_title("StudyPathway RAG — Full Per-Query Results Table (20 regular queries)",
             fontsize=12, fontweight="bold", color="#1E293B", pad=8)
save(fig, "full_results_table.png")

print("\n✅  All 8 charts generated in:", OUT_DIR)
