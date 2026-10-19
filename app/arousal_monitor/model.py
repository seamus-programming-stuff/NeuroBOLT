"""The frozen EEG-to-BOLD model: ridge regression trained on all 29 VU scans (scripts/ext_transfer.py)."""
import numpy as np

from .features import bands60


class FrozenModel:
    """Predicts 64 DiFuMo regions + the global signal (in VU target units) from the EEG features.

    standardize='model' uses the VU training statistics (pure zero-shot); 'self' standardizes each
    feature with the recording's own mean and SD, which removed most of the site difference in the
    ds006040 validation and needs no fMRI.
    """

    def __init__(self, path):
        z = np.load(path, allow_pickle=False)
        self.weights, self.intercept = z["weights"], z["intercept"]
        self.mean, self.sd = z["mean"], z["sd"]
        self.labels = [str(s) for s in z["labels"]]
        self.feature_set = str(z["feature_set"])

    def inputs(self, features):
        return features if self.feature_set == "full" else bands60(features)

    def predict(self, features, standardize="self", stats=None):
        x = self.inputs(features)
        if standardize == "model":
            mean, sd = self.mean, self.sd
        elif standardize == "self":
            mean, sd = x.mean(axis=0), x.std(axis=0) + 1e-8
        elif standardize == "stats":
            mean, sd = stats
        else:
            raise ValueError(standardize)
        return ((x - mean) / sd) @ self.weights + self.intercept

    def column(self, name):
        return self.labels.index(name)
