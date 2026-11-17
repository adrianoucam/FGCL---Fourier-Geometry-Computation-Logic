"""Fourier, Geometry, Computation & Logic: finite experiments, not theorem certificates."""
__version__ = '0.3.0'

from .boolean import boolean_spectrum, walsh_transform
from .fourier import FourierExtension, bochner_riesz_filter, bochner_riesz_mask

__all__ = ['FourierExtension', 'bochner_riesz_filter', 'bochner_riesz_mask',
           'boolean_spectrum', 'walsh_transform', '__version__']
