# Transfer-Learning-based Cross-Stimulus Recognition Algorithm for SSVEP-BCI Systems

Real-time and offline pipelines for cross-stimulus SSVEP spelling with TLCCA, including a full GUI, a CLI real-time runner, per-subject/block model extraction, and offline baselines on BETA / Benchmark datasets.

---

## ✨ Key Features
- **Three GUI modes**  
  - **Beta simulation**: dataset-driven real-time recognition.  
  - **Online real-time**: connects to EEG devices, experimenter-configured.  
  - **Demo**: participant-controlled single-window demo.  
- **TLCCA real-time engine** with filter-bank processing and standard SSVEP harmonics (filter-bank coefficients follow `n^(-1.25) + 0.25`).  
- **Per-subject/block trainer** to build TLCCA models and export block-level test data and time windows.  
- **CLI real-time runner (no GUI)** for quick testing on chosen subject/block/time-window.  
- **Offline baselines and comparisons** against multiple CCA/TRCA variants on BETA and Benchmark datasets (with citation to Wong et al., 2021).  

---

## 🗂️ Repository Structure
```text
.
├─ gui_bci.py                # GUI with three modes and setting pages
├─ eeg processor.py          # TLCCAOnlineRecognition (real-time engine)
├─ extract block.py          # FixedTLCCATrainer (per-subject/block model export)
├─ try222.py                 # CLI real-time TLCCA (no GUI)
└─ offline/                  # Offline baselines & comparisons (CCA/TRCA/TLCCA, MATLAB)
