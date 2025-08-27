好的，我已经结合你提供的论文内容和所有核心代码文件，整理了一份可以直接放到 GitHub 的 **详细 README.md**，包含标题、简介、功能说明、系统结构、使用方法和引用等，排版采用标准 Markdown（`#`、`##` 等）。你复制后直接作为 `README.md` 文件即可。

---

# Transfer-Learning-based Cross-Stimulus Recognition Algorithm for SSVEP-BCI Systems

This repository provides the **implementation and system code** for my MSc dissertation:
**“Transfer Learning-based Cross-Stimulus Recognition Algorithm for SSVEP-BCI Systems” (The University of Manchester, 2023)**.

It includes:

* A **real-time BCI speller system** with GUI (Beta simulation, Online test, Demo).
* **TLCCA (Transfer Learning-based CCA)** training, testing, and recognition pipelines.
* **Offline comparison of eight SSVEP algorithms** on **Benchmark** and **BETA** datasets.

---

## ✨ Key Features

* **Three GUI Modes (pygame-based)**

  * **Beta simulation**: dataset-driven real-time recognition (with `simulation.py` / `gui.py`).
  * **Online real-time**: connects to EEG device and performs live recognition (`gui_bci.py` + `eeg_processor.py`).
  * **Demo mode**: simplified single-window demo.

* **TLCCA Real-Time Engine**

  * Filter-bank analysis (coefficients follow $n^{-1.25}+0.25$)
  * Standard SSVEP harmonics, adaptive time windows.
  * Cross-stimulus transfer across different frequencies.

* **Trainer & Extractor**

  * `extract block.py`: train TLCCA models for BETA subjects (per subject/block/time-window).
  * Generates `.mat` model files + corresponding test datasets.

* **CLI Real-Time Runner**

  * `try222.py`: lightweight command-line runner, supports subject/block/time-window selection.
  * No GUI required.

* **Offline Algorithm Comparison**

  * `modify_lele.docx` (dissertation) & included MATLAB/Python codes implement **8 methods**:

    * CCA, eCCA, ms-eCCA, eTRCA, ms-eTRCA, TDCA, tlCCA-1, tlCCA-2
  * Results validated on **Benchmark (35 subjects)** and **BETA (70 subjects)** datasets.

---

## 📂 Repository Structure

```
.
├── gui.py              # GUI speller (with experimenter/participant dual interface)
├── gui_bci.py          # GUI for BETA dataset & online test
├── simulation.py       # GUI in simulation mode
├── eeg processor.py    # Real-time TLCCA recognition engine (for GUI mode)
├── try222.py           # CLI real-time recognition (no GUI)
├── extract block.py    # TLCCA trainer + test data extractor
├── modify_lele.docx    # MSc dissertation (system description + experiments)
```

---

## 🚀 Usage

### 1. Environment

* Python 3.8+
* Required packages:

  ```bash
  pip install numpy scipy scikit-learn pygame pandas
  ```

### 2. Train Models & Extract Data

```bash
python extract\ block.py
```

This will generate:

* `tlcca_models/S{subject}_tlcca_model_exclude_{block}.mat`
* `test_data/S{subject}_blocks_{block}_test_data.mat`

### 3. Run CLI Real-Time Recognition

```bash
python try222.py
```

* Select subject, block, and time window length (0.3s–1.2s).
* Loads model & test data, performs recognition in terminal.

### 4. Run GUI System

```bash
python gui.py
```

Modes available:

* **Speller beta dataset simulation**
* **Speller online test**
* **Speller demo**

For online test, ensure EEG hardware connection and correct COM settings.

### 5. Real-Time Recognition with GUI

`eeg processor.py` is automatically loaded by `gui_bci.py` when EEG recognition starts.

---

## 📊 Experimental Results

* Large-scale validation on **Benchmark (35 subjects)** and **BETA (70 subjects)**.
* TLCCA achieved significant improvements in:

  * Recognition accuracy
  * Information transfer rate (ITR)

Detailed results and figures are in the dissertation (`modify_lele.docx`).

---

## 📖 Reference

This implementation is based on the work of:

```bibtex
@article{wong2021transferring,
  title={Transferring subject-specific knowledge across stimulus frequencies in SSVEP-based BCIs},
  author={Wong, Chi Man and Wang, Ze and Rosa, Agostinho C and Chen, CL Philip and Jung, Tzyy-Ping and Hu, Yong and Wan, Feng},
  journal={IEEE Transactions on Automation Science and Engineering},
  volume={18},
  number={2},
  pages={552--563},
  year={2021},
  publisher={IEEE}
}
```

Original reference code and materials:

* `E:\Dropbox\Disk\BCI competition 2019\ssvep-training-local-system-for-matlab\my\paper_ssvep_acc_dataset_transfer_als_20190930.m`
* `E:\Dropbox\Disk\BCI competition 2019\ssvep-training-local-system-for-matlab\my\paper_data_transfer_result_20190930.xlsx`

Prepared by **Chi Man Wong** ([chiman465@gmail.com](mailto:chiman465@gmail.com)), Date: 22 June 2022.

---

## 📌 Notes

* If you use this code for academic publication, **please cite Wong et al. (2021)**.
* This repository extends their work by:

  * Adding **GUI interfaces**
  * Implementing **real-time TLCCA recognition**
  * Providing a **full experimental BCI speller system**

---

要不要我帮你在 README 里加上 **运行示例截图（GUI界面和终端运行效果）** 的占位符？这样放到 GitHub 上会更直观。
