# FGCL — Agent instructions for Codex

## Mission
Develop FGCL — Fourier, Geometry, Computation & Logic — with reproducible, mathematically honest numerical experiments and optional integrations with the user's deepfake/XAI, 3D and BDH-Graph-DDE SAT projects.

## Non-negotiable rules
- Never describe finite hypercube/lattice projections as a proof or replication of the Cairo or Cairo–Zhang theorems.
- Separate paper-derived results, numerical approximations, and speculative ML adaptations in code, plots, and papers.
- Preserve existing user models/checkpoints and their class ordering. No implicit retraining.
- No dataset leakage: splits must be grouped by source video/identity; document grouping.
- SAT outcomes: SAT only with validated witness; UNSAT only with proof/certified solver; timeout=UNKNOWN.
- CPU fallback is mandatory; GPU is optional and memory-aware.
- Always run `python -m unittest discover -s tests -v` after code changes.
- Reproducibility: log random seeds, configs, versions, hardware, elapsed time, and input hashes.

## Milestones
1. Paper-level discretizations and unit-verified Fourier/X-ray identities.
2. FFT/DCT baselines, matched distortions, score-vector ROC-AUC/F1/EER and group-disjoint deepfake benchmarks.
3. XAI stability with Captum/GradCAM, memory caps and visual reports.
4. Tomography phantom Radon/sparse-view experiments.
5. CDCL baselines and BDH-Graph-DDE integration; report decisions/conflicts/PAR-2.

## Definition of done
Every new method has tests, a baseline, config documentation, measurable outputs, a clear limitation statement, and a small reproducible example.

## v0.2 rules
- Treat `fgcl.benchmark.evaluate_manifest` as evaluation-only; never auto-download or train checkpoints.
- Keep `classes` in original checkpoint logit order; reject unnormalized score vectors.
- Require `path,label,group,split` in benchmark CSV and only test rows.
- Report comparisons at matched distortion and per-group bootstrap; do not infer statistical significance from frame counts alone.
- XAI Captum is optional, use small internal batch size; do not add DeepLift/DeepLiftShap.
- Future milestone: true trainable ConvNeXt + FFT/DCT fusion, identity-aware splits, video aggregation, SSIM/LPIPS and JPEG controls.
