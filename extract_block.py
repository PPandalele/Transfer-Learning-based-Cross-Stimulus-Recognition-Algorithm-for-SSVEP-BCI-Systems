# -*- coding: utf-8 -*-
"""
Fixed full tlCCA trainer - fully consistent with beta.py logic
Key Fix: weight matrix dimensions and indexing strategy fully consistent with beta.py
"""
import os, sys
import scipy.io as sio
import pandas as pd  
import warnings
warnings.filterwarnings('ignore')
import time
import numpy as np
from scipy import signal
from scipy.signal import butter, iirnotch, filtfilt
from sklearn.cross_decomposition import CCA
from scipy.linalg import inv

def matlab_canoncorr_exact(X, Y):
    """MATLAB canoncorr implementation - fully consistent with beta.py"""
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    if Y.ndim == 1:
        Y = Y.reshape(-1, 1)
    
    # Centering
    X = X - np.mean(X, axis=0)
    Y = Y - np.mean(Y, axis=0)
    
    n = X.shape[0]
    
    # Compute covariance matrices (MATLAB style)
    Cxx = (X.T @ X) / (n - 1)
    Cyy = (Y.T @ Y) / (n - 1) 
    Cxy = (X.T @ Y) / (n - 1)
    
    try:
        # Use Cholesky decomposition, closer to MATLAB
        Lx = np.linalg.cholesky(Cxx + 1e-12 * np.eye(Cxx.shape[0]))
        Ly = np.linalg.cholesky(Cyy + 1e-12 * np.eye(Cyy.shape[0]))
        
        M = np.linalg.solve(Lx, Cxy)
        M = np.linalg.solve(Ly.T, M.T).T
        
        U, s, Vt = np.linalg.svd(M, full_matrices=False)
        
        A = np.linalg.solve(Lx.T, U[:, 0])
        B = np.linalg.solve(Ly.T, Vt[0, :])
        
        return A, B
        
    except:
        # Backup solution
        cca = CCA(n_components=1)
        cca.fit(X, Y)
        return cca.x_weights_[:, 0], cca.y_weights_[:, 0]

def matlab_square(t, duty=20):
    """MATLAB square function - fully consistent with beta.py"""
    T = 2 * np.pi
    t_mod = np.mod(t, T)
    duty_radians = T * duty / 100
    s = np.where(t_mod < duty_radians, 1, -1)
    return s

def matlab_my_conv_H(fs, ph, Fs, tw, refresh_rate, erp_period):
    """MATLAB my_conv_H implementation - fully consistent with beta.py"""
    sig_len = int(np.floor(tw * Fs))
    t = np.arange(sig_len) / Fs
    h0 = np.cos(2 * np.pi * fs * t + ph) + 1
    
    sel_idx = np.round(Fs / refresh_rate * np.arange(refresh_rate * tw)) + 1
    sel_idx = sel_idx.astype(int)
    
    h_val = h0[0]
    cn = 1
    h = np.zeros(len(h0))
    
    for m in range(1, len(h0) + 1):
        if cn <= len(sel_idx) and m == sel_idx[cn-1]:
            h_val = h0[m-1]
            if cn >= len(sel_idx):
                pass
            else:
                cn = cn + 1
        h[m-1] = h_val
    
    hs = matlab_square(2 * np.pi * fs * t + ph, duty=20) + 1
    hs = hs.astype(float)
    
    count_thres = int(np.floor(0.9 * Fs / fs))
    count = count_thres + 1
    
    for m in range(len(hs)):
        if hs[m] == 0:
            count = count_thres + 1
        else:
            if count >= count_thres:
                hs[m] = h[m]
                count = 1
            else:
                count = count + 1
                hs[m] = 0
    
    erp_len = int(np.round(erp_period * Fs))
    H = np.zeros((erp_len, erp_len + sig_len - 1))
    
    for k in range(erp_len):
        start_idx = k
        end_idx = k + sig_len
        if end_idx <= H.shape[1]:
            H[k, start_idx:end_idx] = hs
    
    H = H[:, :sig_len]
    return H, hs

class FixedTLCCATrainer:
    """tlCCA trainer fully consistent with beta.py logic"""
    
    def __init__(self, data_dir, tlcca_window_time=1.0):
        self.data_dir = data_dir
        self.tlcca_window_time = tlcca_window_time
        
        # ===== 与beta.py完全一致的参数设置 =====
        self.Fs = 250
        self.transfer_type = 2
        self.latencyDelay = round(0.13 * self.Fs)
        self.num_of_subbands = 5
        self.num_of_harmonics = 5
        self.is_center_std = 0
        self.num_of_signal_templates = 5
        
        # EEG channel configuration
        self.ch_used = [48, 54, 55, 56, 57, 58, 61, 62, 63]
        self.ch_used = [x-1 for x in self.ch_used]  # Convert to 0-based
        
        # ===== Key Fix: frequency-phase setup consistent with beta.py =====
        self._setup_frequency_phase_beta()
        
        # ===== Filter setup consistent with beta.py =====
        self._setup_filters_beta()
        
        # Filter bank coefficients
        self.FB_coef0 = np.array([i**(-1.25) + 0.25 for i in range(1, self.num_of_subbands + 1)])
        # Dynamic flicker duration (adjusted in load_subject_data)
        self.flicker_duration = 2.0  # default value
        self.subject_type = 'short'  # default value
        self.train_length = 500  # default value

        print(f"✅ Fixed TLCCATrainer initialization completed (fully based on beta.py logic)")
        print(f"   Data directory: {data_dir}")
        print(f"   tlCCA window: {tlcca_window_time}s")
        print(f"   Source domain frequencies: {len(self.source_freq_idx)}")
        print(f"   Target domain frequencies: {len(self.target_freq_idx)}")

    def _setup_frequency_phase_beta(self):

        pha_val = np.array([0, 0.5, 1, 1.5, 0, 0.5, 1, 1.5, 0, 0.5, 1, 1.5, 0, 0.5, 1, 1.5, 0, 0.5, 1, 1.5,
                           0, 0.5, 1, 1.5, 0, 0.5, 1, 1.5, 0, 0.5, 1, 1.5, 0, 0.5, 1, 1.5, 0, 0.5, 1, 1.5]) * np.pi
        sti_f = np.array([8.6, 8.8, 9, 9.2, 9.4, 9.6, 9.8, 10, 10.2, 10.4, 10.6, 10.8,
                         11, 11.2, 11.4, 11.6, 11.8, 12, 12.2, 12.4, 12.6, 12.8,
                         13, 13.2, 13.4, 13.6, 13.8, 14, 14.2, 14.4, 14.6, 14.8,
                         15, 15.2, 15.4, 15.6, 15.8, 8, 8.2, 8.4])
        
        target_order = np.argsort(sti_f)
        self.sti_f = sti_f[target_order]
        self.pha_val = pha_val[target_order]
        self.target_order = target_order
        
     
        self.source_freq_idx = np.arange(1, len(self.sti_f), 2)
        self.target_freq_idx = np.arange(0, len(self.sti_f), 2)
        
       
        self.sti_f_original = sti_f.copy()
        self.pha_val_original = pha_val.copy()
        
       
        self.beta_standard_chars = [
            '.', ',', '<'] + list('abcdefghijklmnopqrstuvwxyz0123456789_')

    def _setup_filters_beta(self):
        """Filter setup consistent with beta.py"""
        
        subband_signal = {}
        for k in range(1, self.num_of_subbands + 1):
            Wp = np.array([(8*k)/(self.Fs/2), 90/(self.Fs/2)])
            Ws = np.array([(8*k-2)/(self.Fs/2), 100/(self.Fs/2)])
            
            try:
                N, Wn = signal.cheb1ord(Wp, Ws, 3, 40)
                b, a = signal.cheby1(N, 0.5, Wn, btype='band')
                subband_signal[k] = {'bpB': b, 'bpA': a}
            except:
                b, a = signal.butter(6, Wn, btype='band')
                subband_signal[k] = {'bpB': b, 'bpA': a}
        
        self.subband_signal = subband_signal
        
        Fo = 50
        Q  = 35
        M  = int(np.floor((self.Fs/2) / Fo))
        notchB = np.array([1.0])
        notchA = np.array([1.0])
        for k in range(1, M+1):
            w0 = (k * Fo) / (self.Fs/2)
            b_k, a_k = signal.iirnotch(w0, Q)
            notchB = np.convolve(notchB, b_k)
            notchA = np.convolve(notchA, a_k)
        
        self.notchB = notchB
        self.notchA = notchA

    def load_subject_data(self, subject_num):
        
        filepath = os.path.join(self.data_dir, f'S{subject_num}.mat')
        try:
            mat_data = sio.loadmat(filepath)
            data_struct = mat_data['data']
            eegdata = data_struct[0,0]['EEG']
            
        
            data = np.transpose(eegdata, [0, 1, 3, 2])
            
        
            if subject_num <= 15:
                self.flicker_duration = 2.0  
                self.subject_type = 'short'
                self.train_length = 500  
            else:
                self.flicker_duration = 3.0  
                self.subject_type = 'long'
                self.train_length = 750 

            print(f'Subject {subject_num} Config: Flicker duration={self.flicker_duration}s, Type={self.subject_type}')

       
            start_idx = int(np.floor(0.5*self.Fs)) + 1 - 1  
            end_idx = start_idx + self.latencyDelay + int(self.flicker_duration*self.Fs)
            eeg = data[self.ch_used, start_idx:end_idx, :, :]
            
            print(f'✓ Subject {subject_num} loaded successfully')
            print(f'  EEG shape: {eeg.shape} [channels, time, frequencies, blocks]')
            
            return eeg
            
        except Exception as e:
            print(f'✗ Error loading subject {subject_num}: {e}')
            return None

    def train_model(self, eeg_data, training_blocks):
       
        print(f'Training tlCCA model with blocks: {training_blocks}')
       
        

        d1_, d2_, d3_, d4_ = eeg_data.shape
        d1 = d3_  # frequencies
        d2 = d4_  # blocks  
        d3 = d1_  # channels
        d4 = d2_  # time points
        
        print(f'    Data dimensions: freq={d1}, blocks={d2}, channels={d3}, time={d4}')
  
        print('    🔧 Preprocessing and filtering (与beta.py完全一致)...')
        self._preprocess_data_beta(eeg_data, training_blocks, d1, d2, d3, d4)
        
        self._reorganize_data_beta()
  
        self._train_model_beta(d3)
        
        print('  ✅ Model training completed')
        return self.subband_signal

    def _preprocess_data_beta(self, eeg_data, training_blocks, d1, d2, d3, d4):

        processed_count = 0
        total_to_process = d1 * len(training_blocks)
        
        for i in range(d1):
            for j_enum, j in enumerate(training_blocks):
                j_idx = j - 1
                
               
                y0 = eeg_data[:, :, i, j_idx]
                
         
                try:
                    y_temp = signal.filtfilt(self.notchB, self.notchA, y0.T)
                    y = y_temp.T
                except:
                    y = y0
                
                for sub_band in range(1, self.num_of_subbands + 1):
                    y_sb = np.zeros((d3, 2*self.Fs))
                    
                    for ch_no in range(d3):
                        try:
                            tmp2 = signal.filtfilt(self.subband_signal[sub_band]['bpB'], 
                                                 self.subband_signal[sub_band]['bpA'], 
                                                 y[ch_no, :])
                        except:
                            tmp2 = y[ch_no, :]
                        
                
                        start_cut = self.latencyDelay
                        end_cut = self.latencyDelay + 2*self.Fs
                        
                        if end_cut <= len(tmp2):
                            y_sb[ch_no, :] = tmp2[start_cut:end_cut]
                        elif start_cut < len(tmp2):
                            available_len = len(tmp2) - start_cut
                            y_sb[ch_no, :available_len] = tmp2[start_cut:]
                    
            
                    if 'SSVEPdata' not in self.subband_signal[sub_band]:
                        self.subband_signal[sub_band]['SSVEPdata'] = np.zeros((d3, 2*self.Fs, len(training_blocks), d1))
                    self.subband_signal[sub_band]['SSVEPdata'][:, :, j_enum, i] = y_sb
                
                processed_count += 1
                if processed_count % 20 == 0:
                    print(f'      process: {processed_count}/{total_to_process} ({processed_count/total_to_process*100:.1f}%)')
        
        print(f'    ✅ Preprocessing completed: {processed_count}/{total_to_process}')

    def _reorganize_data_beta(self):
      
        print('    🔧 Reordering data by frequency order...')
        for k in range(1, self.num_of_subbands + 1):
            self.subband_signal[k]['SSVEPdata'] = self.subband_signal[k]['SSVEPdata'][:, :, :, self.target_order]
        
        print('    🔧 Dividing source and target domain data...')
        for k in range(1, self.num_of_subbands + 1):
            self.subband_signal[k]['SSVEPdata_source'] = self.subband_signal[k]['SSVEPdata'][:, :, :, self.source_freq_idx]
            self.subband_signal[k]['SSVEPdata_target'] = self.subband_signal[k]['SSVEPdata'][:, :, :, self.target_freq_idx]

    def _train_model_beta(self, d3):
        
        no_of_class = len(self.source_freq_idx)  
        dataLength = int(2 * self.Fs)
        
    
        print('      🔧 Generating source frequency reference signals...')
        ref_source = {}
        for i in range(len(self.source_freq_idx)):
            freq_idx = self.source_freq_idx[i]
            testFres = self.sti_f[freq_idx] * np.arange(1, self.num_of_harmonics + 1)
            t = np.arange(dataLength) / self.Fs
            
            ref_signal = []
            for h in range(self.num_of_harmonics):
                cos_comp = np.cos(2 * np.pi * testFres[h] * t + self.pha_val[freq_idx] * (h + 1))
                sin_comp = np.sin(2 * np.pi * testFres[h] * t + self.pha_val[freq_idx] * (h + 1))
                ref_signal.append(cos_comp)
                ref_signal.append(sin_comp)
            
            ref_source[i] = np.array(ref_signal)
        
       
        for sub_band in range(1, self.num_of_subbands + 1):
            print(f'      🔧 Training subband {sub_band}/{self.num_of_subbands} (与beta.py完全一致)...')
            
           
            train_length = int(self.tlcca_window_time * self.Fs)
            self.subband_signal[sub_band]['templates_transfer'] = np.zeros((train_length, no_of_class))
            self.subband_signal[sub_band]['templates_source'] = np.mean(self.subband_signal[sub_band]['SSVEPdata_source'], axis=2)
            
         
            self.subband_signal[sub_band]['Wx_source'] = np.zeros((d3, no_of_class))
            self.subband_signal[sub_band]['Wy_source'] = np.zeros((2*self.num_of_harmonics, no_of_class))
            self.subband_signal[sub_band]['Wx_transfer'] = np.zeros((d3, no_of_class))
            
          
            for stim_no in range(no_of_class):
           
                d0 = self.num_of_signal_templates // 2
                d1_temp = no_of_class
                
                if (stim_no + 1) <= d0:
                    template_st = 1
                    template_ed = self.num_of_signal_templates
                elif ((stim_no + 1) > d0) and ((stim_no + 1) < (d1_temp - d0 + 1)):
                    template_st = (stim_no + 1) - d0
                    template_ed = (stim_no + 1) + (self.num_of_signal_templates - d0 - 1)
                else:
                    template_st = (d1_temp - self.num_of_signal_templates + 1)
                    template_ed = d1_temp
                
                template_idx = np.arange(template_st - 1, template_ed)
                
                # Multi-stimulus CCA 
                mscca_X = []
                mscca_Y = []
                
                for m in range(self.num_of_signal_templates):
                    mm = template_idx[m]
                    tmp = self.subband_signal[sub_band]['templates_source'][:, :, mm]
                    
                    if self.is_center_std == 1:
                        tmp = tmp - np.mean(tmp, axis=1, keepdims=True)
                        tmp = tmp / np.std(tmp, axis=1, keepdims=True)
                    
                    mscca_X.append(tmp.T)
                    mscca_Y.append(ref_source[mm].T)
                
                mscca_X = np.vstack(mscca_X)
                mscca_Y = np.vstack(mscca_Y)
                
                # CCA
                A, B = matlab_canoncorr_exact(mscca_X, mscca_Y)
                
                
                self.subband_signal[sub_band]['Wx_source'][:, stim_no] = A
                self.subband_signal[sub_band]['Wy_source'][:, stim_no] = B
            
            # ALS transfer learning 

            self._als_transfer_learning_beta(sub_band, no_of_class, d3, dataLength, train_length)
            
            print(f'        ✅ sub_band{sub_band} Training completed')
            
            
                   

    def _als_transfer_learning_beta(self, sub_band, no_of_class, d3, dataLength, train_length):
       
        for stim_no in range(no_of_class):
           
            fs_target = self.sti_f[self.target_freq_idx[stim_no]]
            ph_target = self.pha_val[self.target_freq_idx[stim_no]]
            
            frequency_period = 1.05 * (1 / self.sti_f[self.source_freq_idx[stim_no]])
            fs_0 = self.sti_f[self.source_freq_idx[stim_no]]
            ph_0 = self.pha_val[self.source_freq_idx[stim_no]]
            
            st = 0
            ssvep0 = self.subband_signal[sub_band]['templates_source'][:, st:st+dataLength, stim_no]
            
          
            H0, h0 = matlab_my_conv_H(fs_0, ph_0, self.Fs, dataLength/self.Fs, 60, frequency_period)
            h_len = H0.shape[0]
            
           
            np.random.seed(42 + stim_no)
            w0_old = np.random.randn(1, d3)
            
            try:
                H0_H0T_inv = np.linalg.inv(H0 @ H0.T)
            except:
                H0_H0T_inv = np.linalg.pinv(H0 @ H0.T)
            
            x_hat_old = w0_old @ ssvep0 @ H0.T @ H0_H0T_inv
            e_old = np.linalg.norm(w0_old @ ssvep0 - x_hat_old @ H0)
            
            iter_err = [100]
            iter_count = 1
            
           
            while iter_err[-1] > 0.0001 and iter_count < 200:
                try:
                    try:
                        ssvep0_ssvep0T_inv = np.linalg.inv(ssvep0 @ ssvep0.T)
                    except:
                        ssvep0_ssvep0T_inv = np.linalg.pinv(ssvep0 @ ssvep0.T)
                    
                    w0_new = x_hat_old @ H0 @ ssvep0.T @ ssvep0_ssvep0T_inv
                    x_hat_new = w0_new @ ssvep0 @ H0.T @ H0_H0T_inv
                    e_new = np.linalg.norm(w0_new @ ssvep0 - x_hat_new @ H0)
                    
                    iter_count += 1
                    iter_err.append(abs(e_old - e_new))
                    
                    w0_old = w0_new / np.std(w0_new)
                    x_hat_old = x_hat_new / np.std(x_hat_new)
                    e_old = e_new
                    
                except:
                    break
            
            
            x_hat_ = x_hat_old
            x_hat = x_hat_.flatten()[:h_len]
            
           
            y_re = x_hat @ H0
            y_ = w0_old @ ssvep0
            
           
            zero_indices = np.where(y_re == 0)[0]
            if len(zero_indices) > 0:
                try:
                    start_replace = self.Fs
                    end_replace = start_replace + len(zero_indices)
                    if end_replace <= len(y_re):
                        y_re[zero_indices] = 0.8 * y_re[start_replace:end_replace]
                except:
                    pass
            
            
            try:
                r = np.corrcoef(y_.flatten(), y_re.flatten())
                ycor = abs(r[0, 1])
                if np.isnan(ycor):
                    ycor = 0.0
            except:
                ycor = 0.0
            
          
            self.subband_signal[sub_band]['Wx_transfer'][:, stim_no] = w0_old.flatten()
            
          
            H_target, h_target = matlab_my_conv_H(fs_target, ph_target, self.Fs, dataLength/self.Fs, 60, frequency_period)
            y_hat = x_hat @ H_target
            
            
            zero_indices_target = np.where(y_hat == 0)[0]
            if len(zero_indices_target) > 0:
                try:
                    start_replace = self.Fs
                    end_replace = start_replace + len(zero_indices_target)
                    if end_replace <= len(y_hat):
                        y_hat[zero_indices_target] = 0.8 * y_hat[start_replace:end_replace]
                except:
                    pass
            
           
            target_signal_quality = 0.0
            if len(y_hat) > 0:
                try:
                    t = np.arange(len(y_hat)) / self.Fs
                    ideal_sin = np.sin(2 * np.pi * fs_target * t + ph_target)
                    ideal_cos = np.cos(2 * np.pi * fs_target * t + ph_target)
                    
                    sin_corr = abs(np.corrcoef(y_hat, ideal_sin)[0,1]) if len(y_hat) == len(ideal_sin) else 0
                    cos_corr = abs(np.corrcoef(y_hat, ideal_cos)[0,1]) if len(y_hat) == len(ideal_cos) else 0
                    target_signal_quality = max(sin_corr, cos_corr)
                    
                    if np.isnan(target_signal_quality):
                        target_signal_quality = 0.0
                        
                except:
                    target_signal_quality = 0.0
            
          
            template_len = min(len(y_hat), train_length)
            self.subband_signal[sub_band]['templates_transfer'][:template_len, stim_no] = y_hat[:template_len]
            
            print(f'          ALS {stim_no+1}/{no_of_class}completed：iter_count{iter_count}, ycor{ycor:.4f}, target_signal_quality:{target_signal_quality:.4f}')
            
            if target_signal_quality > 0.3:
                print(f'            ✅ High quality target domain signal')
            elif ycor > 0.7:
                print(f'            ✅ High quality transfer learning')

    def extract_test_data(self, eeg_data, test_blocks, subject_num, extract_mode='raw'):
        """Extracting test data"""
        print(f'  Extracting test data from blocks: {test_blocks}')
        
        extracted_data = {}
        
        for block_id in test_blocks:
            if block_id < 1 or block_id > eeg_data.shape[3]:
                continue
            
            block_idx = block_id - 1
            print(f'    Extracting Block {block_id}...')
            

            if extract_mode == 'processed':
         
                print(f'    Using processed mode: applying time alignment (cue removal + latency compensation)')
                
              
                processed_block_data = np.zeros((len(self.ch_used), self.train_length, 40))
                
                for freq_idx in range(40):
                  
                    y0 = eeg_data[:, :, freq_idx, block_idx]
                    
                    
                    try:
                        y_temp = signal.filtfilt(self.notchB, self.notchA, y0.T)
                        y = y_temp.T
                    except:
                        y = y0

                    
                    start_cut = self.latencyDelay
                    end_cut = self.latencyDelay + self.train_length
                    
                    if end_cut <= y.shape[1]:
                        processed_block_data[:, :, freq_idx] = y[:, start_cut:end_cut]
                    elif start_cut < y.shape[1]:
                        available_len = y.shape[1] - start_cut
                        processed_block_data[:, :available_len, freq_idx] = y[:, start_cut:]
                
                block_data = processed_block_data
                print(f'    Processed data shape: {block_data.shape} [channels, time_processed, frequencies]')
                
            elif extract_mode == 'raw':
               
                print(f'    Using TRUE raw mode: extracting complete original trial data')
                
                
                original_eeg_data = self._load_original_beta_data(subject_num, block_idx)
                if original_eeg_data is not None:
                    block_data = original_eeg_data
                    print(f'    TRUE Raw data shape: {block_data.shape} [channels, time_complete_trial, frequencies]')
                else:
                    print(f'    ⚠️ Failed to load original data, falling back to processed data')
                    block_data = eeg_data[:, :, :, block_idx]
                    print(f'    Fallback data shape: {block_data.shape} [channels, time_processed, frequencies]')
            else:
                raise ValueError(f"Unknown extract_mode: {extract_mode}. Use 'raw' or 'processed'")
            
           
            gui_char_to_condition_map = {}
            condition_to_char_map = {}

            for condition_idx, char in enumerate(self.beta_standard_chars):
                gui_char_to_condition_map[char] = condition_idx
                condition_to_char_map[condition_idx] = char

            print(f'      🔑 Block {block_id} 字符映射: {len(gui_char_to_condition_map)}个字符')
            
            block_info = {
                'block_id': block_id,
                'gui_char_to_condition_map': gui_char_to_condition_map,
                'condition_to_char_map': condition_to_char_map,
                'available_chars': self.beta_standard_chars.copy(),
                'eeg_data': block_data,
                'trial_frequencies': [self.sti_f_original[i] for i in range(40)],
                'trial_phases': [self.pha_val_original[i] for i in range(40)],
                'standard_frequencies': self.sti_f.copy(),
                'standard_phases': self.pha_val.copy(),
                'source_freq_idx': self.source_freq_idx.copy(),
                'target_freq_idx': self.target_freq_idx.copy(),
                'target_order': self.target_order.copy(),
                'extraction_method': 'beta_consistent_algorithm',
            }
            
            extracted_data[f'block_{block_id}'] = block_info
        
        print(f'  ✅ Test data extraction completed')
        return extracted_data

    def _load_original_beta_data(self, subject_num, block_idx):
        
        try:
            filepath = os.path.join(self.data_dir, f'S{subject_num}.mat')
            mat_data = sio.loadmat(filepath)
            data_struct = mat_data['data']
            eegdata = data_struct[0,0]['EEG']
            
            data = np.transpose(eegdata, [0, 1, 3, 2])
            original_block_data = data[self.ch_used, :, :, block_idx]
            
            return original_block_data
            
        except Exception as e:
            print(f'    ❌ Failed to load original data: {e}')
            return None

    def save_model_and_test_data(self, subject_num, training_blocks, test_blocks, trained_model, test_data):
        """Saving model and test data"""
        
        for dir_name in ["tlcca_models", "test_data"]:
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
        
        print(f'  Saving model and test data (BETA CONSISTENT)...')
       
        model_data = {}
        
     
        model_data['sti_f'] = self.sti_f.copy()
        model_data['pha_val'] = self.pha_val.copy()
        model_data['source_freq_idx'] = self.source_freq_idx.copy()
        model_data['target_freq_idx'] = self.target_freq_idx.copy()
        model_data['target_order'] = self.target_order.copy()
        model_data['Fs'] = self.Fs
        model_data['num_of_harmonics'] = self.num_of_harmonics
        model_data['num_of_subbands'] = self.num_of_subbands
        model_data['tlcca_window_time'] = self.tlcca_window_time
        
        
        weights_saved = 0
        for sub_band in range(1, self.num_of_subbands + 1):
            if sub_band in self.subband_signal:
                band_data = self.subband_signal[sub_band]

                weight_mappings = [
                    ('Wx_source', f'Wx_source_band{sub_band}'),
                    ('Wy_source', f'Wy_source_band{sub_band}'),
                    ('Wx_transfer', f'Wx_transfer_band{sub_band}'),
                    ('templates_transfer', f'templates_transfer_band{sub_band}'),
                    ('templates_source', f'templates_source_band{sub_band}')
                ]
                
                for weight_attr, model_key in weight_mappings:
                    weight_data = band_data.get(weight_attr)
                    
                    if weight_data is not None and hasattr(weight_data, 'shape') and weight_data.size > 0:
                        if np.any(weight_data != 0):
                            model_data[model_key] = weight_data.copy()
                            print(f"    ✅ Save {model_key}: {weight_data.shape}")
                            weights_saved += 1
        
       
        test_str = "_".join(map(str, test_blocks))
        model_filename = os.path.join("tlcca_models", f'S{subject_num}_tlcca_model_exclude_{test_str}.mat')
  
        try:
            sio.savemat(model_filename, model_data)
            print(f"✅ Saved successfully: {model_filename}")
            print(f"   source_freq: (9, {len(self.source_freq_idx)}) ")
            print(f"   weights_saved: {weights_saved}")
        except Exception as e:
            print(f"❌ Save failed: {e}")
            return None, None
        
       
        test_save_data = {}
        for block_key, block_info in test_data.items():
            test_save_data[f'{block_key}_data'] = block_info['eeg_data']
            test_save_data[block_key] = block_info
        
        test_filename = os.path.join("test_data", f'S{subject_num}_blocks_{test_str}_test_data.mat')
        
        try:
            sio.savemat(test_filename, test_save_data)
            print(f"✅ Saved successfully: {test_filename}")
        except Exception as e:
            print(f"❌ Save failed: {e}")
            return model_filename, None
        
        return model_filename, test_filename

    def process_subject(self, subject_num, test_blocks, extract_mode='raw'):
       
        print(f'\n=== Processing Subject S{subject_num} (BETA CONSISTENT) ===')

        print(f'🔧 self.source_freq: (9, {len(self.source_freq_idx)}) 而不是 (9, 40)')
        
       
        all_blocks = [1, 2, 3, 4]
        training_blocks = [b for b in all_blocks if b not in test_blocks]
        print(f'Training blocks: {training_blocks}, Test blocks: {test_blocks}')
        
   
        print(f'\n1. Loading data...')
        eeg_data = self.load_subject_data(subject_num)
        if eeg_data is None:
            return None, None
      
        print(f'\n2. Training model (BETA CONSISTENT)...')
        trained_model = self.train_model(eeg_data, training_blocks)
        
        # 3. Extracting test data
        print(f'\n3. Extracting test data...')
        test_data = self.extract_test_data(eeg_data, test_blocks, subject_num, extract_mode)
        
     
        print(f'\n4. Saving results...')
        model_path, test_path = self.save_model_and_test_data(
            subject_num, training_blocks, test_blocks, trained_model, test_data
        )
        
        print(f'\n' + '=' * 60)
        print(f'           BETA CONSISTENT Processing Complete!')
        print('=' * 60)
   
        print(f'✓ Subject: S{subject_num}')
        print(f'✓ Training blocks: {training_blocks}') 
        print(f'✓ Test blocks: {test_blocks}')
        print(f'✓ Self.source_freq: (9, {len(self.source_freq_idx)}) ')
        print(f'✓ Model file: {os.path.basename(model_path) if model_path else "FAILED"}')
        print(f'✓ Test data file: {os.path.basename(test_path) if test_path else "FAILED"}')
        

        
        return model_path, test_path

def main():
    """主函数"""
    print("=" * 70)

    print()
    
    try:
        # Data path setting
        data_path = input("Enter Beta dataset path (press Enter to use default): ").strip()
        if not data_path:
            data_path = r'D:\下载\transfer-learning-canonical-correlation-analysis-tlCCA--python-main\transfer-learning-canonical-correlation-analysis-tlCCA--python-main\Beta'
        
        if not os.path.exists(data_path):
            print(f"⚠️  Path does not exist: {data_path}")
            return
        
        # Subject selection
        subject_num = int(input("Enter subject number (1-70): ").strip())
        if not (1 <= subject_num <= 70):
            print("Subject number must be between 1 and 70")
            return
        
        # Test blocks selection
        test_input = input("Enter test blocks (e.g., 1 or 1,2): ").strip()
        test_blocks = [int(x.strip()) for x in test_input.split(",") if x.strip()]
        
        # tlCCA window
        print("\ntlCCA window options:")
        print("1=0.3s, 2=0.4s, 3=0.5s, 4=0.6s, 5=0.7s")
        print("6=0.8s, 7=0.9s, 8=1.0s, 9=1.1s, 10=1.2s")
        window_choice = input("Select window (1-10, default=8): ").strip()

        # Window mapping: 0.3s to 1.2s, step 0.1s
        window_options = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]

        try:
            choice_idx = int(window_choice) - 1
            if 0 <= choice_idx < len(window_options):
                tlcca_window_time = window_options[choice_idx]
            else:
                tlcca_window_time = 1.0  # default value corresponds to option 8
        except ValueError:
            tlcca_window_time = 1.0  # default value corresponds to option 8
        
        print(f"\nConfiguration confirmation:")
        print(f"  Subject: S{subject_num}")
        print(f"  Test blocks: {test_blocks}")
        print(f"  tlCCA window: {tlcca_window_time}s")
        
        # Data extraction mode selection
        print(f"\nData extraction mode selection:")
        print("1. raw - Save TRUE original full trial data (contains full cue+flicker+pause time, no processing)")
        print("2. processed - Apply time alignment (cue removal + 130ms latency compensation + clean SSVEP segment)")
        mode_choice = input("Select mode (1/2, default=1): ").strip()

        extract_mode = 'raw' if mode_choice != '2' else 'processed'
        print(f"Selected mode: {extract_mode}")
        print(f"  Data extraction mode: {extract_mode}")
        if input("\nConfirm start? (y/N): ").lower().strip() not in ['y', 'yes']:
            return
        
        # Start processing
        processor = FixedTLCCATrainer(data_dir=data_path, tlcca_window_time=tlcca_window_time)
        model_path, test_path = processor.process_subject(subject_num, test_blocks, extract_mode)
        if model_path and test_path:
            print(f"\n🎉 BETA-consistent Processing completed successfully!")
            print(f"   - Correct weight matrix dimensions: (9, 20)")
            
        else:
            print("❌ Processing failed")

    except Exception as e:
        print(f"\nError occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    np.random.seed(42)
    main()
