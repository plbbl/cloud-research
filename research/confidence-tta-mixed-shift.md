# Confidence-Based Test-Time Adaptation Failure Under Mixed Covariate-Label Shift

## 1. Exact Claim
Confidence-thresholded entropy minimization methods (e.g., Tent, EATA, SAR) suffer catastrophic feedback collapse (>20% accuracy degradation below non-adapted baseline) under mixed online shifts where covariate corruption co-occurs with transient Dirichlet label imbalance ($\alpha \le 0.1$), because overconfident misclassifications on majority-corrupted classes induce self-reinforcing gradient shifts that permanently distort affine Batch Normalization parameters.

## 2. Evidence with Bare Source Links
* **Tent (Wang et al., 2021)**: https://arxiv.org/abs/2006.10726
* **EATA (Niu et al., 2022)**: https://arxiv.org/abs/2204.02610
* **SoTTA / Noisy Stream TTA (NeurIPS 2023)**: https://proceedings.neurips.cc/paper_files/paper/2023/hash/3fecb89417f7c688849b2f6168e2ee9d-Abstract-Conference.html
* **ODS / Open-world Data Shift (ICML 2023)**: https://proceedings.mlr.press/v202/zhou23f.html

## 3. Killed Weak Proxy
* **Killed:** Static sample-filtering by prediction entropy threshold ($H(p(x)) < H_0$). Under severe corruptions paired with skewed arrivals, overconfident false predictions pass the threshold and rapidly destabilize BN statistics.
* **Killed:** EMA teacher stabilization alone without class-prior balance; slow monotonic collapse still occurs.

## 4. Unknowns & Failure Modes
1. **Representation vs Classifier Shift:** Does failure manifest as feature rank collapse in representations or pure linear-layer bias drift?
2. **Batch Size Interaction:** Does batch size $B \in \{1, 4, 16, 64\}$ delay or eliminate collapse under identical Dirichlet concentrations?
3. **Critical Skew Boundary:** The exact transition boundary $(\alpha^*, \text{severity})$ where EATA performance inverts relative to source baseline.

## 5. Next Decisive Task (< 24GB GPU Executable Protocol)
* **Goal:** Quantify the collapse transition boundary for Tent and EATA across 5 corruption types on CIFAR-100-C under dynamic Dirichlet label streams ($\alpha \in \{0.05, 0.1, 0.5, 1.0, \infty\}$).
* **Hardware:** Single 24GB GPU (RTX 3090/4090/A10), ~1.5 GPU hours.
* **Execution:**
  1. Stream test batches ($B=16$) on CIFAR-100-C (Gaussian noise, Defocus blur, Frost, Pixelate, Contrast; Severity 5) ordered by Dirichlet label sampler ($\alpha=0.1$).
  2. Evaluate (a) Source-only, (b) Tent ($lr=1e-4$), (c) EATA ($E_0=0.4 \ln C, \epsilon=0.05$) on ResNet-50.
  3. Track Top-1 Error trajectory and weight divergence $||\theta_t - \theta_0||_2$.
* **Falsification Criterion:** If Tent/EATA error exceeds source-only baseline by $>10\%$ on $\ge 3$ corruption types within 2,000 steps, claim is confirmed.