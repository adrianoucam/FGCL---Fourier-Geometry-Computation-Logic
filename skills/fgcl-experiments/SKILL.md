---
name: fgcl-experiments
description: Plan, implement, and validate FGCL Fourier-geometric experiments, deepfake robustness and SAT benchmarks.
---

# FGCL experiment skill

1. Read `AGENTS.md`, `README.md`, and the relevant cited paper before coding.
2. Classify the requested change as **mathematical reproduction**, **numerical analogy**, or **new research hypothesis**.
3. Define measurable hypotheses and strong matched baselines, including seeds and distortion controls.
4. Implement CPU-first with optional GPU; enforce limits for dimension, samples, memory and runtime.
5. Add tests for invariants, identity behavior, output validation, and failure modes.
6. Export reproducible CSV/JSON and preserve provenance, split integrity and metadata.
7. Run tests and report actual results, including negative results and unsupported claims.
8. Never invent theorem replications, solver performance, or model accuracy.

References: Cairo arXiv:2502.06137; Cairo & Zhang arXiv:2512.08064.

## FGCL 0.2 workflow
1. Validate the test manifest and provenance of groups.
2. Verify the existing model architecture and exact checkpoint class order.
3. Evaluate `clean`, `cairo_positive`, `random_positive`, `lowpass`, `highpass` at fixed strength and at matched MSE.
4. Export per-image probabilities and FFT/DCT descriptors; report macro-F1, OVR AUC, paired group bootstrap intervals, flip rates.
5. Optional XAI: compare same-target attribution maps with Captum/gradient saliency; report undefined cosine if zero norm.
6. State clearly that these are exploratory adaptations, not Cairo's proved counterexamples.
