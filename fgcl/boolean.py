"""Normalized Fourier analysis on F_2^d; exhaustive small-domain tools.

Integer indices encode bits least-significant first. These standard identities
also appear in the conventions of the Unique Games preprint; no reduction or
claimed complexity theorem from that manuscript is implemented here.
"""
import operator
import numpy as np


def walsh_transform(values, inverse=False, max_size=1 << 20):
    """O(N log N) Walsh transform; forward Hf/N, inverse Hf.

    N must be a power of two (N=1 allowed). Memory O(N); max_size is a caller
    adjustable guard. Inputs may be real or complex and are never modified.
    """
    values = np.asarray(values)
    max_size = operator.index(max_size)
    if (values.ndim != 1 or values.size == 0 or values.size & (values.size - 1)
            or values.size > max_size or not np.isfinite(values).all()):
        raise ValueError('expected finite power-of-two vector within max_size')
    result = values.astype(complex if np.iscomplexobj(values) else float, copy=True)
    width = 1
    while width < len(result):
        blocks = result.reshape(-1, 2 * width)
        left, right = blocks[:, :width].copy(), blocks[:, width:].copy()
        blocks[:, :width], blocks[:, width:] = left + right, left - right
        width *= 2
    return result if inverse else result / len(result)


def boolean_spectrum(values, max_size=1 << 20):
    """Return coefficients, energy by degree, and coordinate flip energies.

    Influence_i = E|f(x)-f(x xor 2^i)|^2/4. It equals Boolean influence only
    for {-1,+1}-valued functions. Full truth tables cost 2^d: not a SAT solver.
    """
    coefficients = walsh_transform(values, max_size=max_size)
    dimension = len(coefficients).bit_length() - 1
    energy = np.abs(coefficients)**2
    degrees = np.fromiter((i.bit_count() for i in range(len(energy))), dtype=int)
    by_degree = np.bincount(degrees, weights=energy, minlength=dimension + 1)
    indices = np.arange(len(energy))
    influences = np.array([energy[(indices & (1 << i)) != 0].sum()
                           for i in range(dimension)])
    return {'coefficients': coefficients, 'degree_energy': by_degree,
            'influences': influences, 'mean': coefficients[0],
            'total_energy': float(energy.sum())}
