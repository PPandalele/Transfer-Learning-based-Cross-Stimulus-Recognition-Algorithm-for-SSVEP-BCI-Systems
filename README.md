# Transfer-Learning-based Cross-Stimulus Recognition Algorithm for SSVEP-BCI Systems

This repository provides the **implementation and system code** for my MSc dissertation:
**“Transfer Learning-based Cross-Stimulus Recognition Algorithm for SSVEP-BCI Systems”**.

It includes:

* A **real-time BCI speller system** with GUI (Beta simulation, Online test, Demo).
* **TLCCA (Transfer Learning-based CCA)** training, testing, and recognition pipelines.
* **Offline comparison of eight SSVEP algorithms** on **Benchmark** and **BETA** datasets.

---

## ✨ Key Features

* **Three GUI Modes (pygame-based)**

  * **Beta simulation**: dataset-driven real-time recognition (`gui_bci.py` + `eeg_processor.py`).
  * **Online real-time**: connects to EEG device and performs live recognition (`gui_bci.py` + `eeg_processor.py`).
  * **Demo mode**: simplified single-window demo.

* **TLCCA Real-Time Engine**

  * Filter-bank analysis (coefficients follow \$n^{-1.25}+0.25\$)
  * Standard SSVEP harmonics, adaptive time windows
  * Cross-stimulus transfer across different frequencies

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
├── gui_bci.py          # GUI for three modes
├── eeg processor.py    # Real-time TLCCA recognition engine (for GUI mode)
├── try222.py           # CLI real-time recognition (no GUI)
├── extract block.py    # TLCCA trainer + test data extractor
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
python gui_bci.py
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

Large-scale validation was performed on **two public datasets**:

* **Benchmark Dataset**: 40-target SSVEP dataset with **35 subjects**, 64-channel EEG, 6 blocks, frequency range **8–15.8 Hz (0.2 Hz step)** (Wang et al., 2017).
* **BETA Dataset**: Large-scale 40-target SSVEP dataset with **70 subjects**, 64-channel EEG, 4 blocks, real-world setting (outside shielded room), frequency range **8–15.8 Hz** (Liu et al., 2020).

On both datasets, **TLCCA (Transfer Learning-based CCA)** significantly improved:

* **Recognition accuracy**
* **Information Transfer Rate (ITR)**

Detailed numerical results and figures are included in the dissertation (`modify_lele.docx`).

---

## 🎥 GUI Demonstration Videos

I provide demonstration videos for the three GUI modes implemented in this project.
Videos should be placed in the repository under `assets/videos/` (create the folder if it does not exist).

### 1. **Beta Simulation Mode**

* **Description**: Dataset-driven real-time recognition simulating the BETA dataset spelling task.
* **Video**: 

https://github.com/user-attachments/assets/8819a012-9e7a-444f-974d-d3c422661885



### 2. **Online Real-Time Mode**

* **Description**: Connects to EEG device and performs live SSVEP recognition in real-time. The first video: specifically demonstrates how to set the parameters.

The second video: demonstrates how to connect to the EEG device and acquire data. .
* **Video**: 
https://github.com/user-attachments/assets/5b5a30c6-165b-4197-8294-a5865514ac60

* **Video**: 
https://github.com/user-attachments/assets/754fa551-fd6b-477a-a09b-7de21b80345b

### 3. **Demo Mode**

* **Description**: Simplified single-window demonstration of the BCI speller system.
* **Video**: 
https://github.com/user-attachments/assets/2d4ccdb9-a322-4cb9-a8ff-1391ef235332

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

### Datasets

```bibtex
@article{wang2017benchmark,
  title={A benchmark dataset for SSVEP-based brain–computer interfaces},
  author={Wang, Yijun and Chen, Xiaogang and Gao, Xiaorong and Gao, Shangkai},
  journal={IEEE Transactions on Neural Systems and Rehabilitation Engineering},
  volume={25},
  number={10},
  pages={1746--1752},
  year={2017},
  publisher={IEEE}
}

@article{liu2020beta,
  title={BETA: A Large Benchmark Database Toward SSVEP-BCI Application},
  author={Liu, Bingchuan and Huang, Xiaoshan and Wang, Yijun and Chen, Xiaogang and Gao, Xiaorong},
  journal={Frontiers in Neuroscience},
  volume={14},
  pages={627},
  year={2020},
  publisher={Frontiers}
}
```

---

## 📌 Notes

* If you use this code for academic publication, **please cite Wong et al. (2021)** and the relevant datasets (Wang et al., 2017; Liu et al., 2020).
* This repository extends their work by:

  * Adding **GUI interfaces**
  * Implementing **real-time TLCCA recognition**
  * Providing a **full experimental BCI speller system**

---

