"""Finite Fourier operators on CPU. Numerical models, not restriction theorems.

Idea provenance and conventions: docs/SOURCES.md and docs/LIBRARY.md.
"""
import operator
import numpy as np


def _points(value, name):
    value = np.array(value, dtype=float, copy=True)
    if value.ndim != 2 or 0 in value.shape or not np.isfinite(value).all():
        raise ValueError(f'{name} must be a nonempty finite [count, dimension] array')
    return value


class FourierExtension:
    """Quadrature E f(x)=sum_j q_j f_j exp(2 pi i x dot xi_j).

    Caller supplies nodes and positive quadrature weights. ``adjoint`` is
    Euclidean E*, including q; it is not an inverse. Blocks avoid storing the
    full target-by-node matrix. Memory remains O(block_size * node_count).
    """

    def __init__(self, nodes, targets, weights=None, block_size=256):
        self.nodes = _points(nodes, 'nodes')
        self.targets = _points(targets, 'targets')
        if self.nodes.shape[1] != self.targets.shape[1]:
            raise ValueError('nodes and targets must have equal dimension')
        self.block_size = operator.index(block_size)
        if self.block_size < 1:
            raise ValueError('block_size must be positive')
        self.weights = (np.ones(len(self.nodes)) if weights is None
                        else np.array(weights, dtype=float, copy=True))
        if (self.weights.shape != (len(self.nodes),)
                or not np.isfinite(self.weights).all() or np.any(self.weights <= 0)):
            raise ValueError('weights must be finite, positive, one per node')
        for array in (self.nodes, self.targets, self.weights):
            array.setflags(write=False)

    def _blocks(self):
        for start in range(0, len(self.targets), self.block_size):
            stop = min(start + self.block_size, len(self.targets))
            phase = self.targets[start:stop] @ self.nodes.T
            yield slice(start, stop), np.exp(2j * np.pi * phase)

    @staticmethod
    def _vector(value, size):
        value = np.asarray(value, dtype=complex)
        if value.shape != (size,) or not np.isfinite(value).all():
            raise ValueError(f'expected finite vector of length {size}')
        return value

    def apply(self, values):
        values = self._vector(values, len(self.nodes))
        output = np.empty(len(self.targets), dtype=complex)
        for section, matrix in self._blocks():
            output[section] = matrix @ (self.weights * values)
        return output

    def adjoint(self, values):
        values = self._vector(values, len(self.targets))
        output = np.zeros(len(self.nodes), dtype=complex)
        for section, matrix in self._blocks():
            output += matrix.conj().T @ values[section]
        return self.weights * output


def bochner_riesz_mask(shape, cutoff=.25, order=1., spacing=1.):
    """Periodic-grid multiplier (1-|xi|^2/cutoff^2)_+^order.

    Frequencies use cycles per spacing unit; cutoff must be positive.
    Order zero means the *open* frequency ball, excluding its boundary.
    Supports arbitrary dimension; allocates O(product(shape)) memory.
    """
    shape = tuple(operator.index(n) for n in shape)
    if not shape or any(n < 1 for n in shape):
        raise ValueError('shape must contain positive integers')
    if not np.isfinite(cutoff) or cutoff <= 0 or not np.isfinite(order) or order < 0:
        raise ValueError('cutoff must be positive and order nonnegative, both finite')
    spacing = np.broadcast_to(np.asarray(spacing, dtype=float), (len(shape),))
    if not np.isfinite(spacing).all() or np.any(spacing <= 0):
        raise ValueError('spacing must be finite and positive')
    radius2 = np.zeros(shape)
    for axis, (size, step) in enumerate(zip(shape, spacing)):
        view = [1] * len(shape)
        view[axis] = size
        radius2 += np.fft.fftfreq(size, d=step).reshape(view)**2
    base = np.maximum(1 - radius2 / cutoff**2, 0)
    return (base > 0).astype(float) if order == 0 else base**order


def bochner_riesz_filter(signal, cutoff=.25, order=1., spacing=1., axes=None):
    """FFT periodic filtering; no clipping, rescaling, or implicit channel axis.

    ``axes=None`` transforms every axis. For HWC images pass ``axes=(0,1)``.
    Real input returns real output. Complex signals retain complex values.
    """
    signal = np.asarray(signal)
    if signal.ndim == 0 or signal.size == 0 or not np.isfinite(signal).all():
        raise ValueError('signal must be a nonempty finite array')
    axes = tuple(range(signal.ndim)) if axes is None else tuple(operator.index(a) for a in axes)
    if not axes or any(a < -signal.ndim or a >= signal.ndim for a in axes):
        raise ValueError('axes must be nonempty and within signal dimensions')
    axes = tuple(a % signal.ndim for a in axes)
    if len(set(axes)) != len(axes):
        raise ValueError('axes must be distinct')
    mask = bochner_riesz_mask(tuple(signal.shape[a] for a in axes), cutoff, order, spacing)
    # Move transformed axes to the front, preserving their requested order.
    moved = np.moveaxis(signal, axes, tuple(range(len(axes))))
    gain = mask.reshape(mask.shape + (1,) * (signal.ndim - len(axes)))
    result = np.fft.ifftn(np.fft.fftn(moved, axes=tuple(range(len(axes)))) * gain,
                          axes=tuple(range(len(axes))))
    result = np.moveaxis(result, tuple(range(len(axes))), axes)
    return result.real if np.isrealobj(signal) else result
