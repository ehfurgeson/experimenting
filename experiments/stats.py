"""Small statistics helpers, written in plain Python.

The project deliberately avoids convenience wrappers, and the sample sizes here
are small, so the estimators are written out explicitly and deterministically.
Every random procedure takes a seed, so a rerun gives the same numbers.
"""

import math
import random


def clean(values):
    """Return the usable numeric values of a sequence."""
    return [
        float(value) for value in values
        if isinstance(value, (int, float)) and not isinstance(value, bool)
        and math.isfinite(float(value))
    ]


def quantile(values, probability):
    """Return the linear-interpolated quantile of a sorted-able sequence."""
    ordered = sorted(values)
    if not ordered:
        return None
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[int(position)]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def median(values):
    return quantile(values, 0.5)


def mean(values):
    return sum(values) / len(values) if values else None


def stdev(values):
    if len(values) < 2:
        return None
    average = mean(values)
    return math.sqrt(sum((value - average) ** 2 for value in values) / (len(values) - 1))


def summarize(values):
    """Return the usual descriptive statistics of a sample."""
    values = clean(values)
    if not values:
        return {
            "n": 0, "n_present": 0, "mean": None, "sd": None, "min": None,
            "q25": None, "median": None, "q75": None, "max": None,
        }
    return {
        "n": len(values),
        "n_present": len(values),
        "mean": mean(values),
        "sd": stdev(values),
        "min": min(values),
        "q25": quantile(values, 0.25),
        "median": median(values),
        "q75": quantile(values, 0.75),
        "max": max(values),
    }


def bootstrap_median_difference(first, second, iterations = 4000, seed = 20261021):
    """Return the median difference and a percentile interval."""
    first, second = clean(first), clean(second)
    if not first or not second:
        return None, None, None
    generator = random.Random(seed)
    differences = []
    for _ in range(iterations):
        left = [first[generator.randrange(len(first))] for _ in first]
        right = [second[generator.randrange(len(second))] for _ in second]
        differences.append(median(left) - median(right))
    differences.sort()
    return (
        median(first) - median(second),
        quantile(differences, 0.025),
        quantile(differences, 0.975),
    )


def permutation_p_value(first, second, iterations = 4000, seed = 20261021):
    """Return a two-sided permutation p-value for a difference in medians."""
    first, second = clean(first), clean(second)
    if not first or not second:
        return None
    observed = abs(median(first) - median(second))
    pooled = first + second
    generator = random.Random(seed)
    count = 0
    for _ in range(iterations):
        generator.shuffle(pooled)
        difference = abs(median(pooled[:len(first)]) - median(pooled[len(first):]))
        if difference >= observed - 1e-12:
            count += 1
    return (count + 1) / (iterations + 1)


def roc_auc(first, second):
    """Return the probability that a random first value exceeds a random second."""
    first, second = clean(first), clean(second)
    if not first or not second:
        return None
    wins = 0.0
    for value in first:
        for other in second:
            wins += 1.0 if value > other else 0.5 if value == other else 0.0
    return wins / (len(first) * len(second))


def impute(rows, columns, medians = None):
    """Fill missing values with the column median, given or computed."""
    if medians is None:
        medians = {}
        for column in columns:
            values = clean(row.get(column) for row in rows)
            medians[column] = median(values) if values else 0.0
    filled = []
    for row in rows:
        new = dict(row)
        for column in columns:
            value = row.get(column)
            if (not isinstance(value, (int, float)) or isinstance(value, bool)
                    or not math.isfinite(value)):
                new[column] = medians.get(column, 0.0)
        filled.append(new)
    return filled, medians


def standardize(rows, columns, parameters = None):
    """Scale using supplied training parameters, or fit them on these rows."""
    if parameters is None:
        parameters = {}
        for column in columns:
            values = clean(row.get(column) for row in rows)
            if values:
                parameters[column] = (mean(values), stdev(values) or 0.0)
    scaled = []
    for row in rows:
        new = dict(row)
        for column, (average, spread) in parameters.items():
            value = row.get(column)
            if isinstance(value, (int, float)) and not isinstance(value, bool) and spread:
                new[column] = (value - average) / spread
            else:
                new[column] = 0.0
        scaled.append(new)
    return scaled, parameters


def logistic_regression(rows, columns, target, *, learning_rate = 0.1, epochs = 2000,
                        penalty = 0.01):
    """Fit a small L2-regularised logistic regression and return the weights."""
    weights = {column: 0.0 for column in columns}
    bias = 0.0
    for _ in range(epochs):
        gradients = {column: 0.0 for column in columns}
        bias_gradient = 0.0
        for row in rows:
            score = bias + sum(weights[column] * row.get(column, 0.0) for column in columns)
            probability = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, score))))
            error = probability - row[target]
            for column in columns:
                gradients[column] += error * row.get(column, 0.0)
            bias_gradient += error
        count = len(rows) or 1
        for column in columns:
            weights[column] -= learning_rate * (
                gradients[column] / count + penalty * weights[column]
            )
        bias -= learning_rate * bias_gradient / count
    return weights, bias


def predict(weights, bias, row, columns):
    score = bias + sum(weights[column] * row.get(column, 0.0) for column in columns)
    return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, score))))


def cross_validated_accuracy(rows, columns, target, folds = 5, seed = 20261021):
    """Return the mean held-out accuracy of a stratified k-fold fit."""
    if not rows:
        return None
    positives = [row for row in rows if row[target] == 1]
    negatives = [row for row in rows if row[target] == 0]
    if min(len(positives), len(negatives)) < folds:
        return None
    generator = random.Random(seed)
    generator.shuffle(positives)
    generator.shuffle(negatives)
    buckets = [[] for _ in range(folds)]
    for index, row in enumerate(positives):
        buckets[index % folds].append(row)
    for index, row in enumerate(negatives):
        buckets[index % folds].append(row)
    correct = 0
    counted = 0
    for index in range(folds):
        held_out = buckets[index]
        training = [row for other, bucket in enumerate(buckets) if other != index
                    for row in bucket]
        if not held_out or not training:
            continue
        training, medians = impute(training, columns)
        held_out, _ = impute(held_out, columns, medians)
        scaled, parameters = standardize(training, columns)
        scaled_held_out, _ = standardize(held_out, columns, parameters = parameters)
        weights, bias = logistic_regression(scaled, columns, target)
        for row in scaled_held_out:
            probability = predict(weights, bias, row, columns)
            counted += 1
            if (probability >= 0.5) == (row[target] == 1):
                correct += 1
    return correct / counted if counted else None
