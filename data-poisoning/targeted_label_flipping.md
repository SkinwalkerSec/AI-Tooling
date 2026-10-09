# Targeted Label Flipping

Training-data poisoning (OWASP LLM03). A more surgical variant of generic label
flipping: instead of randomly flipping labels across all classes, the attacker targets
a single class and relabels a fraction of its samples to another class. The goal is a
model that is selectively blind to one class while still looking accurate overall.

Typical scenario: an attacker wants a spam filter that lets spam through (flip
`spam -> not_spam`), or a malware classifier that passes a specific family (flip
`malicious -> benign`). Overall accuracy stays high enough that monitoring dashboards
never fire.

## Methodology

1. **Identify the label sink.** Same as generic flipping: find where ground-truth labels
   live (CSV, DB column, pipeline output) and confirm write access.
2. **Baseline the model.** Train on clean data. Record overall accuracy *and*
   per-class metrics (precision, recall, class-specific accuracy). You need per-class
   numbers to prove the targeted impact later.
3. **Choose the target class and direction.** Decide which class to degrade
   (`target_class`) and what label to flip its samples to (`new_label`). For binary
   tasks this is straightforward (0 -> 1 or 1 -> 0). For multi-class, pick the
   destination class that is most plausible or causes the most damage.
4. **Set a poison fraction.** This fraction applies only to samples of the target class,
   not the entire dataset. Start at 30-50%. The threshold depends on the evaluator's
   success criteria: if the target class accuracy needs to drop below 0.4, you may need
   50% or more of that class flipped.
5. **Select and flip.** Randomly sample `poison_fraction * len(target_class_samples)`
   indices from the target class, then overwrite their labels with `new_label`. Features
   stay untouched.
6. **Retrain and evaluate.** Train on the poisoned labels, then score against the
   original clean test set. Check two things:
   - Target class accuracy dropped below the required threshold.
   - Overall accuracy stayed above the minimum (the attack is stealthy only if the
     model still looks good in aggregate).
7. **Extract and submit.** Pull model parameters (weights, intercept) and submit to the
   evaluator endpoint.

## Minimal reusable snippet

```python
import numpy as np

def targeted_class_label_flip(y, target_class, new_label, poison_fraction, seed=1337):
    """Flip a fraction of one class's labels to a chosen new label.

    Returns (y_poisoned, target_indices, flipped_indices).
    """
    if not 0 < poison_fraction <= 1:
        raise ValueError("poison_fraction must be in (0, 1].")

    y_poisoned = y.copy()
    target_indices = np.where(y == target_class)[0]
    n_to_flip = int(len(target_indices) * poison_fraction)
    if n_to_flip == 0:
        return y_poisoned, target_indices, np.array([], dtype=int)

    rng = np.random.default_rng(seed)
    flipped_indices = rng.choice(target_indices, size=n_to_flip, replace=False)

    y_poisoned[flipped_indices] = new_label
    return y_poisoned, target_indices, flipped_indices
```

Usage:

```python
from sklearn.linear_model import LogisticRegression

TARGET_CLASS  = 0   # class to degrade
NEW_LABEL     = 1   # relabel to this
POISON_FRAC   = 0.50

y_poisoned, _, flipped_idx = targeted_class_label_flip(
    y_train, TARGET_CLASS, NEW_LABEL, POISON_FRAC, seed=1337
)

model = LogisticRegression(random_state=1337, solver="liblinear")
model.fit(X_train, y_poisoned)

# always score against the clean, unflipped test set
overall_acc = model.score(X_test, y_test)

# per-class accuracy (the metric that proves the attack worked)
class_mask = (y_test == TARGET_CLASS)
target_class_acc = model.score(X_test[class_mask], y_test[class_mask])
```

## Difference from generic label flipping

| | Generic | Targeted |
|---|---|---|
| **Index pool** | All samples | Only samples of the target class |
| **Goal** | Degrade overall accuracy | Degrade one class while keeping overall accuracy high |
| **Stealth** | Low (accuracy tanks visibly) | High (aggregate metrics look normal) |
| **Poison fraction denominator** | Total dataset size | Target class size only |

## Checklist

- [ ] Confirmed label sink and write access
- [ ] Recorded baseline overall *and* per-class metrics on clean data
- [ ] Chose target class, new label, and poison fraction
- [ ] Flipped labels only within the target class
- [ ] Retrained and evaluated on the untouched clean test set
- [ ] Verified target class accuracy dropped below the required threshold
- [ ] Verified overall accuracy stayed above the minimum (stealth check)
- [ ] Extracted model parameters and submitted to evaluator

## Gotchas

- The poison fraction applies to the target class population, not the full dataset.
  Flipping 50% of a minority class may be only a small percentage of total samples,
  which is why overall accuracy stays high.
- If the target class is very small, even a high poison fraction may not flip enough
  absolute samples to shift the decision boundary. Check class balance first.
- Well-separated classes with large margins resist targeted flipping at lower fractions.
  Push to 50%+ or combine with feature-space tricks if the boundary barely moves.
- As with generic flipping, always evaluate against the original, unflipped test labels.
