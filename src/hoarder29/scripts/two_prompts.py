import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

# Load the CSV data
df = pd.read_csv('model_prompt_performance.csv')

# Get unique models and prompts
unique_models = df['model_name'].unique()
unique_prompts = sorted(df['prompt_name'].unique())

# Find the best performing prompt for each model
model_best_performance = {}
for model in unique_models:
    model_data = df[df['model_name'] == model]
    best_performance = model_data['penalized_weighted_mean'].max()
    model_best_performance[model] = best_performance

# Sort models based on their best performing prompt (highest to lowest)
sorted_models = sorted(unique_models, key=lambda model: model_best_performance[model], reverse=True)

# Create a mapping of models to evenly spaced x-coordinates between -0.9 and 0.9
# with best performing model at 0.9
model_positions = {}
num_models = len(sorted_models)
x_positions = np.linspace(-0.9, 0.9, num_models)

for i, model in enumerate(sorted_models):
    model_positions[model] = x_positions[num_models - i - 1]  # Reverse order so best is at 0.9

# Create a color mapping for prompts
prompt_colors = {}
cmap = plt.cm.get_cmap('tab10', len(unique_prompts))
for i, prompt in enumerate(unique_prompts):
    prompt_colors[prompt] = cmap(i)

# Create the figure and axis with proper Cartesian coordinates
fig, ax = plt.subplots(figsize=(12, 8))

# Plot each data point as an 'X' symbol
for _, row in df.iterrows():
    model = row['model_name']
    prompt = row['prompt_name']
    x = model_positions[model]
    y = row['penalized_weighted_mean']
    
    ax.scatter(x, y, marker='X', s=100, color=prompt_colors[prompt], alpha=0.8)

# Set up proper Cartesian coordinate system
ax.spines['left'].set_position('zero')
ax.spines['bottom'].set_position('zero')
ax.spines['right'].set_color('none')
ax.spines['top'].set_color('none')

# Set plot limits and labels
ax.set_xlim(-1, 1)
ax.set_ylim(-1, 1)
ax.set_xlabel('Models', x=1.0)
ax.set_ylabel('Penalized Weighted Mean', y=1.0)
ax.set_title('Model-Prompt Performance Comparison')
ax.grid(True, linestyle='--', alpha=0.7)

# Add model tick marks and labels on x-axis
ax.set_xticks(list(model_positions.values()))
ax.set_xticklabels(list(model_positions.keys()), rotation=45, ha='right')

# Create dedicated legend area for models at the bottom
# (No need for separate model legend as we're using axis ticks)

# Create right legend for prompts
prompt_handles = [Line2D([0], [0], marker='X', color='w', markerfacecolor=color, 
                         markersize=10, label=prompt) 
                 for prompt, color in prompt_colors.items()]
ax2 = plt.gca().twinx()
ax2.legend(handles=prompt_handles, loc='center right', bbox_to_anchor=(1.15, 0.5), 
           title="Prompts", fontsize=8)
ax2.set_yticks([])  # Hide the right y-axis

# Add additional horizontal and vertical lines to enhance the Cartesian look
ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
ax.axvline(x=0, color='k', linestyle='-', alpha=0.3)

# Adjust layout to make room for legends
plt.tight_layout()
plt.subplots_adjust(right=0.85)

# Save the figure
plt.savefig('model_prompt_performance.png', dpi=300, bbox_inches='tight')

# Show the plot
plt.show()
