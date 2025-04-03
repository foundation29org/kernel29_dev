import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

# Load the CSV data
df = pd.read_csv('model_prompt_performance.csv')

# Get unique models and prompts
unique_models = df['model_name'].unique()
unique_prompts = df['prompt_name'].unique()

# Create a mapping of models to evenly spaced x-coordinates between -0.9 and 0.9
model_positions = {}
num_models = len(unique_models)
x_positions = np.linspace(-0.9, 0.9, num_models)

for i, model in enumerate(unique_models):
    model_positions[model] = x_positions[i]

# Create a color mapping for prompts
prompt_colors = {}
cmap = plt.cm.get_cmap('tab10', len(unique_prompts))
for i, prompt in enumerate(unique_prompts):
    prompt_colors[prompt] = cmap(i)

# Create the figure and axis
plt.figure(figsize=(12, 8))
ax = plt.gca()

# Plot each data point as an 'X' symbol
for _, row in df.iterrows():
    model = row['model_name']
    prompt = row['prompt_name']
    x = model_positions[model]
    y = row['penalized_weighted_mean']
    
    plt.scatter(x, y, marker='X', s=100, color=prompt_colors[prompt], alpha=0.8)

# Set plot limits and labels
plt.xlim(-1, 1)
plt.ylim(-1, 1)
plt.xlabel('Models')
plt.ylabel('Penalized Weighted Mean')
plt.title('Model-Prompt Performance Comparison')
plt.grid(True, linestyle='--', alpha=0.7)

# Create bottom legend for model mapping
model_handles = [Line2D([0], [0], marker='|', color='w', markerfacecolor='black', 
                        markersize=10, label=f"{model} ({pos:.2f})") 
                for model, pos in model_positions.items()]
ax.legend(handles=model_handles, loc='lower center', bbox_to_anchor=(0.5, -0.15), 
          ncol=3, title="Model Mapping", fontsize=8)

# Create right legend for prompts
prompt_handles = [Line2D([0], [0], marker='X', color='w', markerfacecolor=color, 
                         markersize=10, label=prompt) 
                 for prompt, color in prompt_colors.items()]
ax2 = plt.gca().twinx()
ax2.legend(handles=prompt_handles, loc='center right', bbox_to_anchor=(1.15, 0.5), 
           title="Prompts", fontsize=8)
ax2.set_yticks([])  # Hide the right y-axis

# Adjust layout to make room for legends
plt.tight_layout()
plt.subplots_adjust(bottom=0.2, right=0.85)

# Save the figure
plt.savefig('model_prompt_performance.png', dpi=300, bbox_inches='tight')

# Show the plot
plt.show()
