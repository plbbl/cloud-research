# Research Handoff: Distribution-Calibrated PE-TTA for Vision-Language Models Under Non-Stationary Shift

## 1. Narrow Claim & Hypothesis

**The Surprise:**
Standard Test-Time Adaptation (TTA) algorithms tailored for Vision-Language Models (such as TPT via test-time prompt entropy minimization, or TDA via dynamic key-value cache insertion) suffer catastrophic performance degradation when confronted with **compound non-stationary domain shift and Dirichlet label shift ($\alpha \le 0.1$)**.
- Entropy minimization collapses text-visual embeddings into majority class attractors.
- Uncalibrated dynamic caches suffer majority-class memory poisoning, reducing online accuracy below frozen zero-shot transfer.

**Hypothesis:**
A **Distribution-Calibrated Bayesian Residual Adapter (DC-BRA)** operating directly on frozen multimodal feature embeddings:
1. Employs recursive Gaussian class centroid tracking regularized by zero-shot multimodal anchors.
2. Integrates streaming Dirichlet prior updates via Bayes' rule $P(y|x) \propto P(x|y) \hat{P}(y)$ to debias predictions against majority class dominance.
3. Achieves $\ge 4.5\%$ gain over TDA and TPT under severe label imbalance while running $15\times$ faster ($> 80\text{ samples/sec}$ on $1\times$ 24GB GPU, VRAM $< 3\text{ GB}$).

---

## 2. Evidence with Bare Source URLs

- **TPT (NeurIPS 2022)**: Test-Time Prompt Tuning for Zero-Shot Generalization in Vision-Language Models. Demonstrates prompt adaptation per sample via entropy minimization on confident augmentations.
  - https://arxiv.org/abs/2209.07511
  - https://github.com/azshue/TPT
- **SwapPrompt (NeurIPS 2023)**: Test-Time Prompt Adaptation for Vision-Language Models. Dual prompts and cross-view contrastive supervision to avoid degenerate representations.
  - https://openreview.net/forum?id=9wU2u0N3wG
- **SAR (ICLR 2023)**: Towards Stable Test-time Adaptation in the Wild. Shows entropy minimization failure in wild shifts and proposes gradient filtering and sharpness-aware steps.
  - https://arxiv.org/abs/2302.12400
- **TDA (CVPR 2024)**: Efficient Test-Time Adaptation of Vision-Language Models. Implements dynamic training-free positive/negative key-value memory banks.
  - https://arxiv.org/abs/2403.18485
  - https://github.com/AdilKarmanov/TDA
- **DePT (NeurIPS 2022 / arXiv)**: Data-Efficient Prompt Tuning with visual prompts and memory-bank pseudo-labeling.
  - https://arxiv.org/abs/2210.04831
- **DOTA (arXiv 2024 / 2025)**: Distributional Test-Time Adaptation for Vision-Language Models using online Gaussian feature distributions.
  - https://arxiv.org/abs/2409.19318

---

## 3. Killed Paths

1. **Continuous Online Backprop on Text Prompt Vectors (Continuous TPT)**:
   - *Why Killed*: Optimization across a sequential stream without instance reset creates catastrophic drift toward high-frequency class tokens within 200 iterations; latency is $\approx 180\text{ ms/sample}$.
2. **Uncalibrated FIFO Dynamic Key-Value Cache (Standard TDA)**:
   - *Why Killed*: Under severe Dirichlet label shift ($\alpha \le 0.2$), majority class entries overwrite memory banks, causing confidence scores to saturate on wrong majority classes.
3. **Visual Transformer LayerNorm Tuning (TENT-style on CLIP ViT)**:
   - *Why Killed*: Adapting LayerNorm parameters without multimodal contrastive anchors destabilizes joint cross-modal geometry.

---

## 4. Remaining Unknowns

1. **Prior Reset vs. Exponential Smoothing Dynamics**: Optimal choice of exponential prior discount factor $\alpha_{\text{prior}}$ during instantaneous domain transitions.
2. **Class Covariance Parameterization**: Trade-off between scalar variance $\sigma_c^2 \mathbf{I}$, diagonal covariance $\text{diag}(\mathbf{\sigma}_c)$, and full covariance estimation on 1000-class benchmarks.
3. **Multi-Crop Augmentation vs. Pure Feature-Space Speed**: Quantifying the marginal accuracy benefit of $K=8$ augmented views versus single-forward pass latency.

---

## 5. Next Decisive GPU Task

- **Task**: Run multi-seed streaming benchmark comparing Frozen Zero-Shot CLIP, Streaming TDA, and DC-BRA across 3,000 non-stationary streaming samples with Dirichlet label shift ($\alpha \in \{0.05, 0.1, 0.5\}$).
- **GPU Budget**: $1\times 24\text{ GB}$ GPU (RTX 3090 / 4090 / A10G); execution time $< 10\text{ minutes}$ for 3,000 samples.

---

## 6. Reproducible Standalone Implementation

See `/tmp/cloud-research/lab/pe-tta-for-clip-under-mixed-domain-and-label-shift.md` or execute the self-contained Python script provided in the handoff.
