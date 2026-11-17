# FGCL v0.2 — Deepfake / FFT-DCT / Robustness / XAI

**Status:** executable research infrastructure, not a trained deepfake detector, not a proof or reproduction of Mizohata–Takeuchi. Existing v0.1 commands remain supported.

## Setup

Python 3.10–3.12 recommended. Windows PowerShell:

```powershell
cd fgcl
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[images]"
python -m unittest discover -s tests -v
```

For an existing PyTorch classifier install the appropriate CUDA/CPU PyTorch build first, then `pip install -e ".[torch]"`. Captum is optional: `pip install -e ".[xai]"`. **Do not install PyTorch CUDA wheels without checking your GPU and driver.**

## v0.2 features

- `fgcl.spectral`: normalized FFT and DCT energy features, nonnegative symmetric spectral masks, Gaussian low/high-pass and random positive baselines, distortion matching by image MSE.
- `fgcl.benchmark`: strict `test`-only manifest, probabilities in explicit training class order, image-level CSV and JSON summary, F1-macro, OVR ROC-AUC, flip rate, group-cluster bootstrap 95% CI for paired accuracy change.
- `fgcl.adapters`: optional torchvision ConvNeXt-Tiny model factory, strict checkpoint load, probability predictor. **The supplied checkpoint must have identical architecture and class order.**
- `fgcl.xai`: gradient saliency, optional Captum Integrated Gradients / Saliency / InputXGradient / GradientShap, cosine attribution stability. Attribution code is independent and not automatically included in the benchmark.
- Existing SAT and geometric demonstrations are preserved from v0.1.

## Manifest and evaluation

Create a CSV with **path,label,group,split**. All rows must have `split=test`. Paths can be absolute or relative to CSV. `group` must identify the original video or identity across frames and manipulations. Ensure train/validation/test are disjoint **outside FGCL**; the manifest loader cannot verify your training provenance.

```csv
path,label,group,split
D:/dataset/test/original/video001/001.png,original,video001,test
D:/dataset/test/FaceSwap/video002/001.png,FaceSwap,video002,test
```

Create a Python importable module `my_model.py` with `build_model(num_classes)` matching your checkpoint. See `examples/model_module_template.py`. Then:

```powershell
python -m fgcl benchmark --manifest test_manifest.csv --model-module my_model --checkpoint checkpoints/best.pt --classes original Face2Face FaceShifter FaceSwap NeuralTextures --device cuda --out results/ffpp_v02 --seed 42 --strength 0.2
```

For matched MSE instead of fixed strength:

```powershell
python -m fgcl benchmark --manifest test_manifest.csv --model-module my_model --checkpoint checkpoints/best.pt --classes original Face2Face FaceShifter FaceSwap NeuralTextures --target-mse 0.001 --out results/matched
```

**Class order must exactly match training.** Model module must be on `PYTHONPATH` (e.g. run in its folder). Checkpoint loading is strict, safe `weights_only=True`, no arbitrary pickle. Outputs: `predictions.csv` with full score vectors and FFT/DCT descriptors, `metrics.json` with per-method results. MSE targets that cannot be reached are explicitly counted.

## Standalone API

```python
from fgcl.spectral import spectral_features, apply_variant, match_mse
from fgcl.metrics import classification_metrics
from fgcl.benchmark import evaluate_manifest

# predictor(rgb_hwc_float_0_1) -> probabilities array of shape [num_classes]
report = evaluate_manifest('test_manifest.csv', predictor, 'results/experiment',
                           classes=['original','FaceSwap'], methods=['cairo_positive','random_positive','lowpass','highpass'],
                           strength=.2, seed=42)
```

## Scientific controls and limits

1. `cairo_positive` uses a Fourier power spectrum inspired by a *form* in Cairo's work; it does **not** implement her combinatorial counterexample.
2. FFT/DCT descriptors are exported, but **not yet fused into a trained ConvNeXt classifier**. Training requires a controlled experiment with disjoint groups, which this release deliberately does not silently perform.
3. No performance numbers are supplied until an actual model and dataset are evaluated. Dummy predictors are for smoke testing only.
4. MSE is not SSIM/LPIPS. MSE matching can be affected by clipping; verify perceptual equivalence before publication.
5. AUC for absent classes is undefined; the summary returns null. Bootstrap intervals reflect group resampling and may be unstable with few groups.
6. XAI heatmap stability must use the same target class and preprocessing; optional methods require Captum. No DeepLift/DeepLiftShap.
7. Frame-level metrics can be overconfident; report video-level aggregation separately in subsequent work.
8. `torchvision` compatibility varies by Python/CUDA build. Test on your environment.

## References
- Hannah Cairo, *A Counterexample to the Mizohata–Takeuchi Conjecture*, arXiv:2502.06137v2 (2025).
- Hannah Cairo & Ruixiang Zhang, *Power Loss for the Mizohata–Takeuchi Conjecture on C^k Convex Hypersurfaces*, arXiv:2512.08064v1 (2025).
