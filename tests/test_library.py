import builtins
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from fgcl import (FourierExtension, bochner_riesz_filter, bochner_riesz_mask,
                  boolean_spectrum, walsh_transform)
from fgcl.reproducibility import array_sha256, experiment_record
from fgcl.spectral import dct2
from fgcl.metrics import classification_metrics


class LibraryTests(unittest.TestCase):
    def test_extension_dense_adjoint_and_blocking(self):
        rng = np.random.default_rng(7)
        nodes, targets = rng.normal(size=(7, 3)), rng.normal(size=(11, 3))
        weights = rng.uniform(.1, 1, size=7)
        f = rng.normal(size=7) + 1j*rng.normal(size=7)
        g = rng.normal(size=11) + 1j*rng.normal(size=11)
        matrix = np.exp(2j*np.pi*(targets @ nodes.T))*weights
        for block in (1, 4, 99):
            op = FourierExtension(nodes, targets, weights, block)
            np.testing.assert_allclose(op.apply(f), matrix @ f, atol=1e-13)
            np.testing.assert_allclose(op.adjoint(g), matrix.conj().T @ g, atol=1e-13)
            np.testing.assert_allclose(np.vdot(op.apply(f), g), np.vdot(f, op.adjoint(g)), atol=1e-13)

    def test_extension_ifft_and_zero_target(self):
        rng = np.random.default_rng(4)
        n = 16
        f = rng.normal(size=n) + 1j*rng.normal(size=n)
        op = FourierExtension(np.arange(n)[:, None], (np.arange(n)/n)[:, None], np.ones(n)/n)
        np.testing.assert_allclose(op.apply(f), np.fft.ifft(f), atol=1e-13)
        self.assertAlmostEqual(abs(op.apply(f)[0]-f.mean()), 0)
        with self.assertRaises(ValueError):
            FourierExtension([[0]], [[0]], weights=[-1])
        with self.assertRaises(ValueError):
            FourierExtension([[0]], [[0, 1]])
        with self.assertRaises(ValueError):
            op.apply([np.nan]*n)

    def test_bochner_riesz_analytic_modes_and_energy(self):
        t = np.arange(32)/32
        mode = np.exp(2j*np.pi*4*t)
        np.testing.assert_allclose(bochner_riesz_filter(mode, .25, 2), (1-(.125/.25)**2)**2 * mode, atol=1e-13)
        np.testing.assert_allclose(bochner_riesz_filter(np.ones((9, 8, 5))), 1, atol=1e-13)
        rng = np.random.default_rng(3)
        x = rng.normal(size=(7, 8, 3))
        y = bochner_riesz_filter(x, axes=(0, 1))
        self.assertLessEqual(np.sum(y*y), np.sum(x*x)+1e-12)
        for channel in range(3):
            np.testing.assert_allclose(y[:,:,channel], bochner_riesz_filter(x[:,:,channel]))
        mask = bochner_riesz_mask((8,), .25, order=0)
        self.assertEqual(mask[2], 0)  # Explicit open-ball boundary convention.
        np.testing.assert_allclose(bochner_riesz_filter(x, axes=(1, 0), spacing=(2, 1)),
                                   bochner_riesz_filter(x, axes=(0, 1), spacing=(1, 2)))
        for kwargs in ({'cutoff': 0}, {'order': -1}, {'spacing': 0}, {'axes': (0, 0)}):
            with self.assertRaises(ValueError):
                bochner_riesz_filter(x, **kwargs)

    def test_walsh_direct_parseval_parity_influence(self):
        rng = np.random.default_rng(2)
        x = rng.normal(size=16) + 1j*rng.normal(size=16)
        matrix = np.array([[(-1)**((i&j).bit_count()) for j in range(16)] for i in range(16)])
        coefficients = walsh_transform(x)
        np.testing.assert_allclose(coefficients, matrix @ x / 16, atol=1e-13)
        np.testing.assert_allclose(walsh_transform(coefficients, inverse=True), x, atol=1e-13)
        self.assertAlmostEqual(np.sum(abs(coefficients)**2), np.mean(abs(x)**2))
        parity = np.array([(-1)**((i&5).bit_count()) for i in range(16)])
        report = boolean_spectrum(parity)
        np.testing.assert_allclose(report['degree_energy'], [0, 0, 1, 0, 0])
        np.testing.assert_allclose(report['influences'], [1, 0, 1, 0])
        for i, influence in enumerate(boolean_spectrum(x)['influences']):
            self.assertAlmostEqual(influence, np.mean(abs(x-x[np.arange(16) ^ (1<<i)])**2)/4)
        for bad in ([], [1, 2, 3], [1, np.nan]):
            with self.assertRaises(ValueError):
                walsh_transform(bad)
        with self.assertRaises(ValueError):
            walsh_transform(x, max_size=8)

    def test_numpy_dct_against_cosine_definition(self):
        original_import = builtins.__import__
        def without_scipy(name, *args, **kwargs):
            if name.startswith('scipy'):
                raise ImportError('exercise CPU NumPy fallback')
            return original_import(name, *args, **kwargs)
        x = np.random.default_rng(7).normal(size=(7, 8, 3))
        def basis(n):
            matrix = np.sqrt(2/n)*np.cos(np.pi*np.arange(n)[:,None]*(np.arange(n)[None,:]+.5)/n)
            matrix[0] /= np.sqrt(2)
            return matrix
        expected = np.einsum('ih,hwc,jw->ijc', basis(7), x, basis(8))
        with patch('builtins.__import__', side_effect=without_scipy):
            actual = dct2(x)
        np.testing.assert_allclose(actual, expected, atol=1e-13)
        self.assertAlmostEqual(np.sum(actual**2), np.sum(x**2))

    def test_auc_ties_against_pairwise_baseline(self):
        y = np.array([0, 0, 1, 1, 1])
        p = np.array([[.5, .5], [.9, .1], [.5, .5], [.2, .8], [.8, .2]])
        result = classification_metrics(y, p, ['a', 'b'])
        for i, name in enumerate(('a', 'b')):
            delta = p[y==i, i][:,None] - p[y!=i, i][None,:]
            expected = np.mean((delta>0) + .5*(delta==0))
            self.assertAlmostEqual(result['per_class'][name]['auc'], expected)

    def test_provenance_success_failure_and_hashes(self):
        x = np.arange(8).reshape(2, 4)
        self.assertEqual(array_sha256(x), array_sha256(np.asfortranarray(x)))
        self.assertNotEqual(array_sha256(x), array_sha256(x.astype(float)))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'record.json'
            with experiment_record(path, seed=9, config={'cutoff': .25}, inputs={'x': x}) as metrics:
                metrics['mse'] = 0.
            record = json.loads(path.read_text())
            self.assertEqual(record['status'], 'completed')
            self.assertEqual(record['input_sha256']['x'], array_sha256(x))
            self.assertIn('hardware', record)
            self.assertGreaterEqual(record['elapsed_seconds'], 0)
            with self.assertRaises(RuntimeError):
                with experiment_record(path, seed=9, config={}, inputs={}):
                    raise RuntimeError('test failure')
            self.assertEqual(json.loads(path.read_text())['status'], 'failed')


if __name__ == '__main__':
    unittest.main()
