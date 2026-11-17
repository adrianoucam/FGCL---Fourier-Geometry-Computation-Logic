"""FFT/DCT descriptors and controlled perturbation baselines (research hypotheses)."""
import numpy as np
from .core import spectral_mask, perturb_image

def dct2(x):
    """Orthonormal DCT-II along H,W; scipy optional, no GPU required."""
    x = np.asarray(x, dtype=float)
    if x.ndim < 2 or 0 in x.shape or not np.isfinite(x).all():
        raise ValueError('expected finite array with at least two nonempty axes')
    try:
        from scipy.fft import dctn
    except ImportError:
        # Even extension gives DCT-II via FFT in O(N log N), without dense bases.
        result = x.copy()
        for axis in (0, 1):
            moved = np.moveaxis(result, axis, 0)
            n = moved.shape[0]
            even = np.concatenate((moved, moved[::-1]), axis=0)
            phase = np.exp(-1j * np.pi * np.arange(n) / (2*n))
            phase = phase.reshape((n,) + (1,) * (x.ndim-1))
            transformed = (np.fft.fft(even, axis=0)[:n] * phase).real / np.sqrt(2*n)
            transformed[0] /= np.sqrt(2)
            result = np.moveaxis(transformed, 0, axis)
        return result
    return dctn(x, type=2, norm="ortho", axes=(0,1))

def spectral_features(image, bands=(0.,.12,.3,.6,1.)):
    """Per-channel log FFT/DCT energies in radial bands, fixed-size descriptor."""
    x=np.asarray(image,dtype=float)
    if x.ndim==2:x=x[...,None]
    if x.ndim!=3 or x.shape[2] not in (1,3):raise ValueError('HWC grayscale/RGB required')
    h,w=x.shape[:2]
    fy,fx=np.meshgrid(np.fft.fftfreq(h),np.fft.fftfreq(w),indexing='ij')
    r=np.hypot(fx,fy)/np.sqrt(.5)
    yy,xx=np.meshgrid(np.arange(h)/max(1,h-1),np.arange(w)/max(1,w-1),indexing='ij')
    rd=np.hypot(xx,yy)/np.sqrt(2)
    fft=np.abs(np.fft.fft2(x,axes=(0,1)))**2
    dct=np.abs(dct2(x))**2
    feats=[]
    for spec,rad in ((fft,r),(dct,rd)):
        total=np.sum(spec,axis=(0,1))+1e-12
        for a,b in zip(bands[:-1],bands[1:]):
            sel=(rad>=a)&(rad<(b if b<1 else b+1e-9))
            feats.extend(np.log1p(np.sum(spec[sel],axis=0)/total).tolist())
    return np.asarray(feats,dtype=np.float32)

def apply_variant(image, method='cairo_positive', strength=.2, seed=0):
    """Methods: cairo_positive (inspired only), random_positive, lowpass, highpass, identity."""
    x=np.asarray(image,dtype=float)
    if x.ndim not in (2,3):raise ValueError('image must be HW or HWC')
    if not 0<=strength<=1:raise ValueError('strength outside [0,1]')
    if method=='identity':return x.copy()
    shape=x.shape[:2]
    if method=='cairo_positive':mask=spectral_mask(shape,seed=seed)
    else:
        fy,fx=np.meshgrid(np.fft.fftfreq(shape[0]),np.fft.fftfreq(shape[1]),indexing='ij')
        rad=np.hypot(fx,fy)
        if method=='lowpass':mask=np.exp(-rad**2/(2*.12**2))
        elif method=='highpass':mask=1-np.exp(-rad**2/(2*.12**2))
        elif method=='random_positive':
            rng=np.random.default_rng(seed)
            a=rng.standard_normal(shape)
            mask=np.abs(np.fft.fft2(a))**2
            mask/=mask.max()+1e-12
        else:raise ValueError('Unknown method: '+method)
    return perturb_image(x,mask,strength)

def match_mse(image,method,target_mse,seed=0,tol=1e-6):
    """Binary search strength; returns image, strength, achieved MSE, reachable flag."""
    if target_mse<0:raise ValueError('target_mse must be >=0')
    x=np.asarray(image,dtype=float)
    hi_image=apply_variant(x,method,1,seed)
    max_mse=float(np.mean((hi_image-x)**2))
    if target_mse>=max_mse:return hi_image,1.,max_mse,target_mse<=max_mse+tol
    lo,hi=0.,1.
    for _ in range(32):
        mid=(lo+hi)/2
        y=apply_variant(x,method,mid,seed)
        if np.mean((y-x)**2)<target_mse:lo=mid
        else:hi=mid
    s=(lo+hi)/2;y=apply_variant(x,method,s,seed)
    mse=float(np.mean((y-x)**2))
    return y,s,mse,abs(mse-target_mse)<=tol
