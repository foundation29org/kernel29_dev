import math
import numpy as np
import matplotlib.pyplot as plt

# Define alpha such that f(5) = 0
alpha = math.log(1.93)  # ~ 0.657

def penalty_function(s):
    """
    Computes f(s) = 1 - [2 * (e^(alpha*(s-1)) - 1)] / [e^(5*alpha) - 1].
    """
    numerator = 2 * (math.exp(alpha * (s - 1)) - 1)
    denominator = math.exp(5 * alpha) - 1
    return 1 - (float(numerator) / float(denominator))

# Generate scores from 1.0 to 6.0 in increments of 0.1
scores = np.arange(1.0, 6.1, 0.1)
results = []

# Compute and store the function values
for s in scores:
    val = penalty_function(s)
    results.append((s, val))

# Print the results (score, penalty)
print("Score (s) | Penalty f(s)")
print("------------------------")
for s, val in results:
    print(f"{s:8.1f} | {val: .4f}")

# Plot the function
plt.plot(scores, [penalty_function(s) for s in scores], marker='o')
plt.title("Penalty Function f(s) from s=1 to s=6")
plt.xlabel("Score (s)")
plt.ylabel("Penalty f(s)")
plt.grid(True)
plt.show()
