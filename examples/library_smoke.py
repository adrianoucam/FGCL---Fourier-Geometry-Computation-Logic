"""Run from project root: python -m examples.library_smoke --out results/library.json."""
import argparse
import numpy as np
from fgcl import FourierExtension, bochner_riesz_filter, boolean_spectrum, walsh_transform
from fgcl.reproducibility import experiment_record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default='results/library.json')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    rng = np.random.default_rng(args.seed)
    n = 32
    t = np.arange(n) / n
    clean = np.cos(2 * np.pi * 2 * t)
    noisy = clean + .25 * np.cos(2 * np.pi * 13 * t)
    truth = rng.choice([-1., 1.], size=32)
    nodes = np.arange(n)[:, None]
    weights = np.full(n, 1/n)
    values = rng.standard_normal(n) + 1j * rng.standard_normal(n)
    config = {'n': n, 'cutoff': .2, 'order': 1., 'block_size': 8,
              'limitation': 'finite periodic grids and exhaustive truth tables; no theorem validation'}
    with experiment_record(args.out, seed=args.seed, config=config,
                           inputs={'clean': clean, 'noisy': noisy, 'truth': truth,
                                   'nodes': nodes, 'targets': t[:, None],
                                   'weights': weights, 'values': values},
                           sources=['oai-br-2026', 'oai-extension-2026', 'oai-ug-conventions-2026']) as metrics:
        filtered = bochner_riesz_filter(noisy, cutoff=.2)
        metrics['identity_mse'] = float(np.mean((noisy - clean)**2))
        metrics['bochner_riesz_mse'] = float(np.mean((filtered - clean)**2))
        op = FourierExtension(nodes, t[:, None], weights, block_size=8)
        # Independent NumPy inverse DFT baseline: identical convention/normalization.
        metrics['extension_ifft_max_error'] = float(np.max(np.abs(op.apply(values) - np.fft.ifft(values))))
        spectrum = boolean_spectrum(truth)
        metrics['walsh_parseval_error'] = abs(spectrum['total_energy'] - float(np.mean(truth**2)))
        metrics['walsh_inverse_max_error'] = float(np.max(np.abs(walsh_transform(spectrum['coefficients'], inverse=True) - truth)))
        metrics['boolean_degree_energy'] = spectrum['degree_energy'].tolist()
    print(args.out)


if __name__ == '__main__':
    main()
