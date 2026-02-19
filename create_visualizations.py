#!/usr/bin/env python3
"""Generate visualizations for CodeCompass paper."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import seaborn as sns
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-paper')
sns.set_palette("colorblind")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['font.family'] = 'serif'

output_dir = Path('paper/figures')
output_dir.mkdir(exist_ok=True)

# Data from final analysis
conditions = ['A\n(Vanilla)', 'B\n(BM25)', 'C\n(Graph)']
g1_acs = [90.0, 100.0, 88.9]
g2_acs = [79.7, 85.1, 76.4]
g3_acs = [76.2, 78.2, 99.4]

# Figure 1: ACS by Condition and Group
fig, ax = plt.subplots(figsize=(8, 5))
x = np.arange(len(conditions))
width = 0.25

bars1 = ax.bar(x - width, g1_acs, width, label='G1 (Semantic)', color='#4C72B0')
bars2 = ax.bar(x, g2_acs, width, label='G2 (Structural)', color='#55A868')
bars3 = ax.bar(x + width, g3_acs, width, label='G3 (Hidden)', color='#C44E52')

ax.set_ylabel('Architectural Coverage Score (%)', fontsize=11)
ax.set_xlabel('Condition', fontsize=11)
ax.set_title('ACS by Condition and Task Group (n=258 trials)', fontsize=12, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(conditions)
ax.set_ylim([0, 105])
ax.legend(loc='upper left', frameon=True)
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.axhline(y=100, color='gray', linestyle=':', alpha=0.5)

# Add value labels on bars
for bars in [bars1, bars2, bars3]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height:.1f}%', ha='center', va='bottom', fontsize=8)

plt.tight_layout()
plt.savefig(output_dir / 'fig1_acs_by_condition.png', bbox_inches='tight')
plt.close()

# Figure 2: MCP Adoption by Task Group
fig, ax = plt.subplots(figsize=(7, 5))
groups = ['G1\n(Semantic)', 'G2\n(Structural)', 'G3\n(Hidden)']
adoption = [22.2, 0.0, 100.0]
not_adoption = [77.8, 100.0, 0.0]

x_pos = np.arange(len(groups))
bars1 = ax.bar(x_pos, adoption, label='MCP Used', color='#2ECC71')
bars2 = ax.bar(x_pos, not_adoption, bottom=adoption, label='MCP Ignored', color='#E74C3C')

ax.set_ylabel('Percentage of Trials (%)', fontsize=11)
ax.set_xlabel('Task Group (Condition C)', fontsize=11)
ax.set_title('MCP Tool Adoption by Task Group (n=88 trials)', fontsize=12, fontweight='bold')
ax.set_xticks(x_pos)
ax.set_xticklabels(groups)
ax.set_ylim([0, 105])
ax.legend(loc='upper right', frameon=True)
ax.grid(axis='y', alpha=0.3, linestyle='--')

# Add percentage labels
for i, (adopt, not_adopt) in enumerate(zip(adoption, not_adoption)):
    if adopt > 0:
        ax.text(i, adopt/2, f'{adopt:.1f}%', ha='center', va='center',
                fontweight='bold', color='white', fontsize=10)
    if not_adopt > 0:
        ax.text(i, adopt + not_adopt/2, f'{not_adopt:.1f}%', ha='center', va='center',
                fontweight='bold', color='white', fontsize=10)

plt.tight_layout()
plt.savefig(output_dir / 'fig2_mcp_adoption.png', bbox_inches='tight')
plt.close()

# Figure 3: Impact of MCP Usage on ACS
fig, ax = plt.subplots(figsize=(6, 5))
scenarios = ['MCP\nUsed\n(n=37)', 'MCP\nNot Used\n(n=51)']
acs_values = [99.5, 80.2]
colors = ['#2ECC71', '#E74C3C']

bars = ax.bar(scenarios, acs_values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
ax.set_ylabel('Mean ACS (%)', fontsize=11)
ax.set_title('Impact of MCP Tool Usage (Condition C)', fontsize=12, fontweight='bold')
ax.set_ylim([0, 105])
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.axhline(y=100, color='gray', linestyle=':', alpha=0.5)

# Add value labels and improvement annotation
for bar, val in zip(bars, acs_values):
    ax.text(bar.get_x() + bar.get_width()/2., val + 1,
            f'{val:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

# Add improvement arrow and text
ax.annotate('', xy=(1, 99.5), xytext=(0, 80.2),
            arrowprops=dict(arrowstyle='<->', color='black', lw=2))
ax.text(0.5, 90, '+19.2%\nimprovement', ha='center', va='center',
        fontsize=10, fontweight='bold', bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))

plt.tight_layout()
plt.savefig(output_dir / 'fig3_mcp_impact.png', bbox_inches='tight')
plt.close()

# Figure 4: FCTC Comparison
fig, ax = plt.subplots(figsize=(8, 5))
groups_fctc = ['G1', 'G2', 'G3']
a_fctc = [2.27, 1.43, 1.31]
b_fctc = [1.79, 1.17, 1.17]
c_fctc = [2.19, 1.50, 2.11]

x = np.arange(len(groups_fctc))
width = 0.25

bars1 = ax.bar(x - width, a_fctc, width, label='A (Vanilla)', color='#4C72B0')
bars2 = ax.bar(x, b_fctc, width, label='B (BM25)', color='#55A868')
bars3 = ax.bar(x + width, c_fctc, width, label='C (Graph)', color='#C44E52')

ax.set_ylabel('Steps to First Required File', fontsize=11)
ax.set_xlabel('Task Group', fontsize=11)
ax.set_title('First Correct Tool Call (FCTC) - Lower is Better', fontsize=12, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(groups_fctc)
ax.set_ylim([0, 2.5])
ax.legend(loc='upper right', frameon=True)
ax.grid(axis='y', alpha=0.3, linestyle='--')

# Add value labels
for bars in [bars1, bars2, bars3]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                f'{height:.2f}', ha='center', va='bottom', fontsize=8)

plt.tight_layout()
plt.savefig(output_dir / 'fig4_fctc_comparison.png', bbox_inches='tight')
plt.close()

# Figure 5: Overall Performance Summary
fig, ax = plt.subplots(figsize=(9, 5))
metrics = ['Overall\nACS', 'Completion\nRate', 'FCTC\n(avg)']
a_metrics = [82.0, 54, 1.67]
b_metrics = [87.1, 62, 1.36]
c_metrics = [88.3, 66, 1.93]

x = np.arange(len(metrics))
width = 0.25

# Normalize FCTC for display (invert since lower is better)
display_a = [a_metrics[0], a_metrics[1], (3 - a_metrics[2]) * 30]  # Scale FCTC for visibility
display_b = [b_metrics[0], b_metrics[1], (3 - b_metrics[2]) * 30]
display_c = [c_metrics[0], c_metrics[1], (3 - c_metrics[2]) * 30]

bars1 = ax.bar(x - width, display_a, width, label='A (Vanilla)', color='#4C72B0')
bars2 = ax.bar(x, display_b, width, label='B (BM25)', color='#55A868')
bars3 = ax.bar(x + width, display_c, width, label='C (Graph)', color='#C44E52')

ax.set_ylabel('Score/Percentage', fontsize=11)
ax.set_title('Overall Performance Summary by Condition', fontsize=12, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(metrics)
ax.set_ylim([0, 100])
ax.legend(loc='upper left', frameon=True)
ax.grid(axis='y', alpha=0.3, linestyle='--')

# Add value labels (show original values, not scaled)
for i, (bars, orig) in enumerate([(bars1, a_metrics), (bars2, b_metrics), (bars3, c_metrics)]):
    for j, bar in enumerate(bars):
        height = bar.get_height()
        if j == 2:  # FCTC
            label = f'{orig[j]:.2f}'
        elif j == 1:  # Completion rate
            label = f'{int(orig[j])}%'
        else:  # ACS
            label = f'{orig[j]:.1f}%'
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                label, ha='center', va='bottom', fontsize=8)

# Add note about FCTC
ax.text(2, 85, 'FCTC inverted\n(lower is better)', ha='center', fontsize=7,
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

plt.tight_layout()
plt.savefig(output_dir / 'fig5_overall_summary.png', bbox_inches='tight')
plt.close()

# Figure 6: G3 Results Comparison (The Star Finding)
fig, ax = plt.subplots(figsize=(7, 5))
conditions_g3 = ['A\n(Vanilla)', 'B\n(BM25)', 'C\n(Graph)']
g3_values = [76.2, 78.2, 99.4]
colors_g3 = ['#95A5A6', '#95A5A6', '#2ECC71']

bars = ax.bar(conditions_g3, g3_values, color=colors_g3, alpha=0.8, edgecolor='black', linewidth=2)
ax.set_ylabel('ACS on G3 (Hidden Dependencies) (%)', fontsize=11)
ax.set_title('Graph Navigation Breakthrough on Hidden Dependencies', fontsize=12, fontweight='bold')
ax.set_ylim([0, 105])
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.axhline(y=100, color='gray', linestyle=':', alpha=0.5)

# Add value labels
for bar, val in zip(bars, g3_values):
    ax.text(bar.get_x() + bar.get_width()/2., val + 1,
            f'{val:.1f}%', ha='center', va='bottom', fontsize=12, fontweight='bold')

# Highlight the improvement
ax.annotate('+23.2pp', xy=(2, 99.4), xytext=(1.5, 90),
            arrowprops=dict(arrowstyle='->', color='red', lw=2),
            fontsize=11, fontweight='bold', color='red',
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))

plt.tight_layout()
plt.savefig(output_dir / 'fig6_g3_breakthrough.png', bbox_inches='tight')
plt.close()

print("✓ Generated 6 figures in paper/figures/:")
print("  - fig1_acs_by_condition.png")
print("  - fig2_mcp_adoption.png")
print("  - fig3_mcp_impact.png")
print("  - fig4_fctc_comparison.png")
print("  - fig5_overall_summary.png")
print("  - fig6_g3_breakthrough.png")
