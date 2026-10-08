# Label Flipping

Training-data poisoning (OWASP LLM03). Attacker with write access to a portion of the
training labels flips some of them to the wrong class. Features stay untouched — only
`y` changes. Goal is usually generic degradation (lower accuracy/precision/recall,
unreliable model), not a specific targeted misclassification.

Typical access point: wherever labels sit before/during training — a CSV in object
storage, a labels column in a DB table, or a compromised data-processing/ETL step that
writes labels.

## Methodology

1. **Find the label sink.** Identify where the ground-truth labels for the training set
   live and confirm you can write to them (file, DB row, pipeline script output).
2. **Baseline first.** Train/record accuracy on the *clean* data before touching
   anything — you need this to prove impact afterward.
3. **Pick a poison budget.** Fraction of labels to flip (`poison_percentage`, 0–1).
   Start at 10%, step up (20/30/40/50%) if you need to show a bigger effect. Clean,
   well-separated data tolerates low percentages with little/no accuracy loss — push
   higher or target a specific class if you need to demonstrate real damage.
4. **Select victims.** Random sample across both classes for generic degradation. For a
   more deliberate attack, only flip one direction (e.g. all `spam → not spam`) to bias
   the model toward a specific blind spot.
5. **Flip and persist.** Invert the label (`1 - y` for binary) at the chosen indices,
   write the poisoned labels back to wherever they came from (overwrite the CSV,
   update the DB rows, etc.) so the next training run consumes them.
6. **Retrain and compare.** Train a new model on the poisoned labels, then evaluate it
   on the original *clean* test set (never on poisoned labels). Compare accuracy
   against the step-2 baseline, and look at the decision boundary — it will usually
   shift even when the accuracy metric barely moves.

## Minimal reusable snippet

```python
import numpy as np

def flip_labels(y, poison_percentage, seed=1337):
    """Randomly flip a fraction of binary labels (0<->1). Returns (y_poisoned, flipped_indices)."""
    if not 0 <= poison_percentage <= 1:
        raise ValueError("poison_percentage must be between 0 and 1.")

    n_samples = len(y)
    n_to_flip = int(n_samples * poison_percentage)
    if n_to_flip == 0:
        return y.copy(), np.array([], dtype=int)

    rng = np.random.default_rng(seed)
    flipped_indices = rng.choice(n_samples, size=n_to_flip, replace=False)

    y_poisoned = y.copy()
    y_poisoned[flipped_indices] = np.where(y_poisoned[flipped_indices] == 0, 1, 0)
    return y_poisoned, flipped_indices
```

Usage:

```python
y_train_poisoned, flipped_idx = flip_labels(y_train, poison_percentage=0.10)

model = LogisticRegression().fit(X_train, y_train_poisoned)   # original X, poisoned y
acc = accuracy_score(y_test, model.predict(X_test))           # always score against clean y_test
```

For a targeted (one-direction) flip instead of random-both-ways, restrict the index pool
to one class before sampling:

```python
def flip_one_direction(y, from_class, to_class, poison_percentage, seed=1337):
    candidates = np.where(y == from_class)[0]
    n_to_flip = int(len(candidates) * poison_percentage)
    rng = np.random.default_rng(seed)
    flipped_indices = rng.choice(candidates, size=n_to_flip, replace=False)
    y_poisoned = y.copy()
    y_poisoned[flipped_indices] = to_class
    return y_poisoned, flipped_indices
```

## Checklist

- [ ] Confirmed where labels live and that you can write to them
- [ ] Recorded baseline accuracy/metrics on clean data
- [ ] Chose poison % and random-vs-targeted strategy
- [ ] Flipped labels, wrote them back to the sink
- [ ] Retrained, evaluated on the untouched clean test set
- [ ] Compared metrics + decision boundary against baseline to prove impact

## Gotchas

- On clean/separable data, low poisoning % (≤10-20%) can show almost no accuracy drop
  even though the decision boundary has already shifted — don't conclude "no effect"
  from accuracy alone, check the boundary/confusion matrix too.
- Real-world (noisy) datasets degrade at much lower poisoning percentages than clean
  synthetic demos — if asked to prove severity, say so rather than relying on a toy
  dataset's numbers.
- Always evaluate the poisoned model against the **original, unflipped** test labels —
  scoring against poisoned labels hides the attack's real effect.
