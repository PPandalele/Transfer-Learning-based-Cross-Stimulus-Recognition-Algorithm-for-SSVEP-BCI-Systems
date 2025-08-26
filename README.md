# Transfer-Learning-based-Cross-Stimulus-Recognition-Algorithm-for-SSVEP-BCI-Systems
Real-time and offline pipelines for cross-stimulus SSVEP spelling with TLCCA, including a full GUI, a CLI real-time runner, per-subject/block model extraction, and offline baselines on BETA / Benchmark datasets.

✨ Key Features

Three GUI modes: Beta simulation (dataset-driven real-time), Online real-time (experimenter-configured), and Demo (participant-controlled). The GUI provides preparation, block-progress, and rest pages, plus keyboard layout/parameter editors. 

TLCCA real-time engine with filter-bank processing and standard SSVEP harmonics; FB coefficients follow 
(
𝑛
−
1.25
+
0.25
)
(n
−1.25
+0.25). 

Per-subject/block trainer to build TLCCA models and export test windows for BETA subjects/blocks and time windows. 

CLI real-time runner (no GUI) for quick testing on chosen subject/block/time-window. 

Offline baselines and comparisons against multiple CCA/TRCA variants on BETA and Benchmark (with proper citation to the original implementation by Chi Man Wong et al., 2021).

🗂️ Repository Structure
.
├─ gui_bci.py                # Full-screen speller GUI with three modes and setting pages
├─ eeg processor.py          # TLCCAOnlineRecognition (real-time engine used by GUI)
├─ extract block.py          # FixedTLCCATrainer for per-subject/block model & data export
├─ try222.py                 # CLI real-time TLCCA (no GUI) for subject/block/window testing
└─ offline/                  # (optional) offline baselines & comparisons (CCA/TRCA/TLCCA, MATLAB)


gui_bci.py defines the BCISpellerSystem application, pages for main mode select, preparation, block progress, rest, and parameter editors (keyboard layout, JFPM modulation, block count, block texts, cue/flash/pause/rest/time-window). Defaults include cue=0.5 s, flash=2.0 s, pause=0.5 s, rest=60 s, blocks=3, trials=5, time-window=0.8 s. 

eeg processor.py implements TLCCAOnlineRecognition with 
𝐹
𝑠
F
s
	​

=250, 5 sub-bands, 5 harmonics, and filter-bank coefficients 
(
𝑛
−
1.25
+
0.25
)
(n
−1.25
+0.25); it loads per-subject models and block test data, and scores all 40 targets. Edit base_dir to point to your local model/data paths. 

extract block.py provides FixedTLCCATrainer that mirrors the original beta.py logic (frequency/phase ordering, sub-band filters, notch, latency, target/source splits), producing TLCCA weights/templates and block-wise test data for chosen subject / block / time-window. 

try222.py is a no-GUI runner that prompts for subject (1–70), block (1–4), and window (0.3–1.2 s), then loads the matching model & test data from base_dir and performs real-time scoring. 

🔧 Installation
# Python ≥3.9 recommended
pip install numpy scipy pygame pandas scikit-learn


If you use Windows paths with spaces (e.g., eeg processor.py, extract block.py), call them with quotes:

python "eeg processor.py"
python "extract block.py"

📦 Data & Models

Datasets: BETA (70 subjects) and Tsinghua Benchmark (35 subjects), each with 40 targets (8.0–15.8, 0.2 steps) and JFPM encoding.

Per-subject model/test files: the trainer exports TLCCA models (weights/templates, target/source indices, frequency/phase ordering) and block-wise test data compatible with the real-time engine. 

In eeg processor.py and try222.py, update base_dir to your model/data root (default code uses a local Windows path). 
 

🚀 Quick Start
1) Train per-subject/block TLCCA (export models & test data)
python "extract block.py"


The trainer reproduces beta.py logic: frequency/phase ordering, sub-band filters (Chebyshev/Butter fallback), notch at 50 Hz, latency, FB coefficients, source/target splits. It saves model (TLCCA weights/templates) and block test data for chosen time-windows. 

2) Run the GUI
python gui_bci.py


Main page lets you choose mode: Speller beta dataset simulation, Speller online test, Speller demo. 

Beta simulation: uses pre-exported model + test data to simulate real-time recognition; experimenter and participant views update jointly. 
 

Online real-time: experimenter configures keyboard layout/character set, per-character frequency & phase (JFPM), block count & block texts, and cue/flash/pause/rest/time-window (two pages: layout/JFPM editor and process settings). 

Demo: single-window participant-controlled run with Start / Pause / Continue / End. 

GUI pages (examples):

Preparation page: “Please Ready”. 

Block progress: shows finished block number and progress boxes. 

Rest page: “Please rest” with countdown. 

JFPM modulation editor: per-key frequency & phase (π units) overlay on the keyboard. 

Block/process settings: block count & texts, cue/flash/pause/time-window, between-block rest. 

3) Run real-time (CLI, no GUI)
python try222.py


Choose subject, test block, and window (0.3–1.2 s) from prompts.

The script loads the matching model and test data from base_dir, then performs TLCCA scoring across all 40 targets. 

🧠 Real-Time Engine (TLCCAOnlineRecognition)

Signal chain: 5 sub-bands (Chebyshev/Butter fallback), 5 harmonics, FB coefficients 
(
𝑛
−
1.25
+
0.25
)
(n
−1.25
+0.25), latency handling, and all-target correlation scoring; recognition windows follow dataset timing (e.g., cue+physiological delay before window). 

Model I/O: loads per-sub-band spatial filters/templates and frequency/phase ordering (target_order, sti_f, pha_val, source_freq_idx, target_freq_idx). Ensure your saved keys match the trainer’s keys. 
 

GUI integration: the engine exposes per-character results with timestamps so the GUI can update experimenter/participant views in sync. 
 

🔬 Offline Baselines & Comparisons

To compare TLCCA with classic methods (eCCA, ms-eCCA, eTRCA, ms-eTRCA, TDCA, etc.) on BETA and Benchmark, we adapt and extend the well-known implementation by Chi Man Wong.
If you use these parts for a publication, please cite:

@article{wong2021transferring,
  title={Transferring subject-specific knowledge across stimulus frequencies in SSVEP-based BCIs},
  author={Wong, Chi Man and Wang, Ze and Rosa, Agostinho C and Chen, CL Philip and Jung, Tzyy-Ping and Hu, Yong and Wan, Feng},
  journal={IEEE Transactions on Automation Science and Engineering},
  volume={18}, number={2}, pages={552--563}, year={2021}, publisher={IEEE}
}


Original code references noted in the source (author comment headers and dataset scripts). Please preserve the above citation when using or modifying the offline comparison components.

⚠️ Notes & Tips

Paths: Update base_dir in eeg processor.py and try222.py to your local project path where tlcca_models/ and test_data/ are stored. 
 

Filenames with spaces: Run with quotes (e.g., python "extract block.py").

Dependencies: Confirm pygame, numpy, scipy, pandas, scikit-learn are installed.

📄 How to Cite This Repository

If this work contributes to your research, please cite your thesis/paper and additionally cite Wong et al., 2021 (above) for the adapted baseline components.

🙏 Acknowledgments

Baseline method references and parts of the comparison code follow the implementation by Chi Man Wong and collaborators (see citation above).

Thanks to the maintainers of the BETA and Tsinghua Benchmark datasets.

📜 License

Please add a LICENSE file (e.g., MIT/BSD/Apache-2.0) to clarify reuse terms. If you adapt third-party code, ensure the license is compatible and keep original notices.

Appendix: Where things are in the code (pointers)

Mode selection UI (Main page with dropdown): draw_main_page(); options include Speller beta dataset simulation, Speller online test, Speller demo. 

Preparation / Progress / Rest pages: draw_start_page(), draw_block_progress_page(), draw_rest_page(). 

Layout & JFPM editors: draw_layout_page(), draw_jpfm_page(), draw_keyboard_with_params() (per-key freq/phase). 

Block/process settings: draw_trials_page(), draw_block_text_page() (blocks, block texts, cue/flash/pause/rest/time-window). 

TLCCA engine: TLCCAOnlineRecognition (filters/FB, harmonics, model/test loading, scoring). 

CLI real-time: prompts for subject/block/window and runs end-to-end without GUI.
