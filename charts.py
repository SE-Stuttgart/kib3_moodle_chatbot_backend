import matplotlib.pyplot as plt
import numpy as np

models = ("German_Semantic_STS_V2", "all-MiniLM-L6-v2", "bi-encoder_msmarco_bert-base_german")
penguin_means = {
    'GPU': (0.0170, 0.0057, 0.0090),
    'PC CPU': (0.0740, 0.0060, 0.0230),
    'Laptop': (0.2793, 0.0282, 0.1506),
    'Laptop(Small)': (0.2933, 0.0150, 0.0763),
}

x = np.arange(len(models))  # the label locations
width = 0.2  # the width of the bars
multiplier = 0

fig, ax = plt.subplots(layout='constrained')

for attribute, measurement in penguin_means.items():
    offset = width * multiplier
    rects = ax.bar(x + offset, measurement, width, label=attribute)
    ax.bar_label(rects, padding=3)
    multiplier += 1

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel('Time (s)')
ax.set_title('Query Time by Model and Device')
ax.set_xticks(x + width, models)
ax.legend(loc='upper left', ncols=4)
ax.set_ylim(0, 0.3)

plt.savefig('querytime.png')
plt.show()