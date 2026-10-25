#!/usr/bin/env python3
"""Synthetic protocol/representation/selection checks; never score real outcomes."""
import copy
import json
import unittest
from pathlib import Path

import numpy as np
import torch

from architecture_pilot import (MODELS, TinyTransformer, apply_transform, make_model,
                                metrics, model_counts, neural_fit, profile_gate,
                                tokenize, untokenize, validate_groups)
from thesis_study import ridge_select, standardize, weighted_mse


class ArchitecturePilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(2)

    def test_semantic_token_order_and_roundtrip(self):
        array = np.array([[[100 * g + 10 * b + lag for lag in range(12)]
                           for b in range(5)] for g in range(5)])
        flat = torch.from_numpy(array.reshape(1, 300))
        tokens = tokenize(flat)
        for lag in range(12):
            for group in range(5):
                for band in range(5):
                    self.assertEqual(tokens[0, lag, 5 * group + band].item(),
                                     100 * group + 10 * band + lag)
        self.assertTrue(torch.equal(untokenize(tokens), flat))
        self.assertFalse(torch.equal(tokens, flat.reshape(1, 12, 25)))

    def test_input_transform_excludes_heldout_values(self):
        train = np.array([[1., 2], [3, 6], [np.nan, 4]])
        (a, _), fit = standardize(train, np.array([[1e9, -1e9]]))
        (b, _), fit2 = standardize(train, np.array([[-1e9, 1e9]]))
        np.testing.assert_array_equal(a, b)
        np.testing.assert_array_equal(fit["median"], fit2["median"])
        np.testing.assert_allclose(apply_transform(train, fit), a)

    def test_exact_person_splits_and_overlap_rejection(self):
        path = Path(__file__).resolve().parents[1] / "reports/thesis_exploration/data/protocol.json"
        p = json.loads(path.read_text())
        validate_groups(p["folds"])
        bad = copy.deepcopy(p["folds"])
        bad[0]["training_order"][0] = bad[0]["test_people"][0]
        with self.assertRaises(ValueError):
            validate_groups(bad)

    def test_same_encoder_initialization_uniform_pool_and_parameter_cap(self):
        mean, lag = make_model("transformer_mean"), make_model("transformer_lag")
        mean.eval(); lag.eval()
        for key, value in mean.state_dict().items():
            self.assertTrue(torch.equal(value, lag.state_dict()[key]), key)
        x = torch.randn(4, 300)
        with torch.no_grad():
            a, aw = mean(x, True); b, bw = lag(x, True)
        torch.testing.assert_close(a, b)
        torch.testing.assert_close(aw, bw)
        torch.testing.assert_close(bw.sum(1), torch.ones(4, 1))
        self.assertLess(model_counts()["transformer_lag"], 20000)
        self.assertEqual(model_counts()["transformer_lag"] - model_counts()["transformer_mean"], 33)

    def test_learned_pool_receives_gradients(self):
        net = make_model("transformer_lag").eval()
        x = torch.randn(5, 300)
        net(x).square().mean().backward()
        self.assertGreater(float(net.pool_score.weight.grad.abs().sum()), 0)

    def test_raw_r2_not_squared_correlation_and_constant_prediction(self):
        y = np.linspace(-1, 1, 121)[:, None]
        m = metrics(.2 * y + 1, y)
        self.assertAlmostEqual(m["Pearson_r"], 1.)
        self.assertLess(m["predictive_R2"], 0)
        self.assertAlmostEqual(m["SD_ratio"], .2)
        self.assertTrue(np.isnan(metrics(np.zeros_like(y), y)["Pearson_r"]))

    def test_validation_weights_balance_people_not_frames(self):
        p = np.array([[0.], [3.], [3.], [3.]])
        y = np.zeros_like(p)
        w = np.array([.5, 1/6, 1/6, 1/6])
        self.assertAlmostEqual(float(weighted_mse(p, y, w)[0]), 4.5)
        self.assertNotAlmostEqual(float(weighted_mse(p, y, w)[0]), float((p*p).mean()))

    def test_ridge_on_raw_scalar_matches_closed_form(self):
        rng = np.random.default_rng(2)
        x, v = rng.normal(size=(30, 5)), rng.normal(size=(10, 5))
        y = rng.normal(size=(30, 1)) + 4
        pred, _ = ridge_select(x, y, v, np.zeros((10, 1)), np.full(10, .1), [10.])
        xc = x - x.mean(0)
        weight = np.linalg.solve(xc.T @ xc + 10*np.eye(5), xc.T @ (y-y.mean(0)))
        np.testing.assert_allclose(pred(v), (v-x.mean(0)) @ weight+y.mean(0), atol=1e-9)

    def test_budget_gate_blocks_before_test_scoring(self):
        self.assertTrue(profile_gate(10, 400))
        self.assertFalse(profile_gate(1000, 2000))

    def test_small_fit_has_only_training_and_validation_inputs(self):
        # No outer target is accepted by the fit API; synthetic fit checks the
        # selected checkpoint reproduces its saved validation scalar MSE.
        import time
        rng = np.random.default_rng(3)
        x = rng.normal(size=(20, 300)).astype("float32")
        xv = rng.normal(size=(8, 300)).astype("float32")
        y, yv = x[:, [0]], xv[:, [0]]
        p = {"seed": 41, "learning_rate": .001, "weight_decay": .01,
             "max_epochs": 3, "batch_size": 128, "patience": 10, "gradient_clip": 5.}
        w = np.full(8, 1/8, dtype="float32")
        pred, record, _ = neural_fit("mlp32", x, y, xv, yv, w, p, "cpu", time.monotonic()+30)
        loss = float(((pred(xv)-yv).squeeze()**2 * w).sum())
        self.assertAlmostEqual(record["validation_mse"], loss, places=6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
