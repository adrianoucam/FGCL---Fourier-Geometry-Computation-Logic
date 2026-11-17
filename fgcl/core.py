"""FGCL: reproducible numerical analogues, not proofs of Cairo's theorems."""
import numpy as np

def spectral_mask(shape, seed=0, peaks=12, sigma=0.055):
    """Positive Fourier-domain mask built from a real spatial kernel h: |FFT(h)|²."""
    rng=np.random.default_rng(seed)
    h=np.zeros(shape, dtype=float)
    for _ in range(peaks):
        h[tuple(rng.integers(0,s) for s in shape)]+=rng.uniform(.3,1)
    yy,xx=np.meshgrid(np.fft.fftfreq(shape[0]),np.fft.fftfreq(shape[1]),indexing='ij')
    gaussian=np.exp(-2*np.pi**2*(sigma*min(shape))**2*(xx**2+yy**2))
    H=np.fft.fft2(h)*gaussian
    m=np.abs(H)**2
    return m/(m.max()+1e-12)

def perturb_image(image, mask, strength=.25):
    """Blend identity and a nonnegative, conjugate-symmetric Fourier mask; output float [0,1]."""
    x=np.asarray(image,dtype=np.float64)
    if x.ndim not in (2,3) or x.shape[:2]!=mask.shape: raise ValueError('image/mask shape mismatch')
    if not 0<=strength<=1: raise ValueError('strength must be in [0,1]')
    gain=(1-strength)+strength*mask
    if x.ndim==3: gain=gain[...,None]
    y=np.fft.ifft2(np.fft.fft2(x,axes=(0,1))*gain,axes=(0,1)).real
    return np.clip(y,0,1)

def hypercube_projection(dim=12, seed=0, max_points=65536):
    """Finite projection of {0,1}^dim into R²; pedagogical analogue only."""
    if not 1<=dim<=20 or 2**dim>max_points: raise ValueError('dim too large')
    rng=np.random.default_rng(seed)
    basis=rng.normal(size=(dim,2));basis/=np.linalg.norm(basis,axis=0)
    codes=np.arange(2**dim,dtype=np.uint32)
    bits=((codes[:,None]>>np.arange(dim))&1).astype(float)
    return bits@basis

def projected_lattice(rank=4, radius=2, seed=0, max_points=100000):
    """Finite integer lattice [-radius,radius]^rank projected into R²."""
    if rank<1 or radius<1 or (2*radius+1)**rank>max_points: raise ValueError('grid too large')
    rng=np.random.default_rng(seed)
    basis=rng.normal(size=(rank,2));basis/=np.linalg.norm(basis,axis=0)
    grid=np.stack(np.meshgrid(*([np.arange(-radius,radius+1)]*rank),indexing='ij'),axis=-1).reshape(-1,rank)
    return grid@basis

def occupancy(points, bins=32):
    """2D histogram concentration statistic (not a Kakeya maximal operator)."""
    h,_,_=np.histogram2d(points[:,0],points[:,1],bins=bins)
    return {'n':len(points),'occupied_cells':int(np.count_nonzero(h)),'max_cell':int(h.max()),'collision_pairs':int(np.sum(h*(h-1)/2))}

def stress_curve(scales, seed=0):
    """Illustrative log/power scaling; not estimates or replications of MT constants."""
    scales=np.asarray(scales,dtype=float)
    if np.any(scales<=1):raise ValueError('R must be >1')
    return {'R':scales.tolist(),'log_R':np.log(scales).tolist(),'power_R_1_3':(scales**(1/3)).tolist()}
