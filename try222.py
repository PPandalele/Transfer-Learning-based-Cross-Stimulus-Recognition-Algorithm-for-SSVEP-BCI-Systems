#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced TLCCA real-time recognition system - supports model and data selection
"""

import numpy as np
import scipy.io as sio
import scipy.signal as signal
import time
import os

class TLCCAOnlineRecognition:
    def __init__(self, recognition_window):
        # Basic parameters
        self.Fs = 250
        self.num_of_subbands = 5

        self.latency_delay = 0.0
        self.recognition_window = recognition_window
        
        # Character set
        self.beta_standard_chars = [
            '.', ',', '<', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '_'
        ]
        

        self.num_of_harmonics = 5  # Add this attribute
        self.num_of_subbands = 5
        
        # 🔑 Filter bank coefficients (formula 11 in the paper)
        self.FB_coef = np.array([(n**(-1.25) + 0.25) for n in range(1, self.num_of_subbands + 1)])
        print(f"   FB系数: {self.FB_coef}")
        # Model parameters
        self.online_weights = {}
        self.online_templates = {}
        self.target_order = None
        self.sti_f = None
        self.pha_val = None
        self.source_freq_idx = None
        self.target_freq_idx = None
        
        # Real-time data
        self.source_data = None
        self.streaming_buffer = None
        self.received_samples = 0
        self.test_eeg_data = None

        self.subband_filters = {}
        for k in range(1, self.num_of_subbands + 1):
            Wp = np.array([(8*k)/(self.Fs/2), 90/(self.Fs/2)])
            Ws = np.array([(8*k-2)/(self.Fs/2), 100/(self.Fs/2)])
            
            try:
                N, Wn = signal.cheb1ord(Wp, Ws, 3, 40)
                b, a = signal.cheby1(N, 0.5, Wn, btype='band')
                self.subband_filters[k] = {'bpB': b, 'bpA': a}
            except:
                b, a = signal.butter(6, Wn, btype='band')
                self.subband_filters[k] = {'bpB': b, 'bpA': a}

        
        print("🧠 TLCCA real-time recognition system initialized")

    
    def select_model_and_data(self):
        """Select model and data files"""
        print("\n" + "="*50)
        print("🎯 TLCCA real-time recognition system - Model and data selection")
        print("="*50)
        
        # 1. 选择Subject
        print("\n1. Subject selection")
        print("-" * 30)
        while True:
            try:
                subject_num = int(input("Enter Subject number (1-70): ").strip())
                if 1 <= subject_num <= 70:
                    break
                else:
                    print("❌ Subject number must be between 1 and 70")
            except ValueError:
                print("❌ Please enter a valid number")
        
        # 2. 选择Test Block
        print(f"\n2. Test Block selection")
        print("-" * 30)
        while True:
            try:
                test_block = int(input("Enter test Block number (1-4): ").strip())
                if 1 <= test_block <= 4:
                    break
                else:
                    print("❌ Block number must be between 1 and 4")
            except ValueError:
                print("❌ Please enter a valid number")
        # 🔑 New: select window length
        print("\n⏱️ Recognition window length selection:")
        print("1=0.3s, 2=0.4s, 3=0.5s, 4=0.6s, 5=0.7s")
        print("6=0.8s, 7=0.9s, 8=1.0s, 9=1.1s, 10=1.2s")

        while True:
            try:
                window_choice = input("Select window length (1-10, default:6): ").strip()
           
                window_options = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]
                
                if window_choice == "":
                    window_duration = 0.8  
                    break
                else:
                    choice_idx = int(window_choice) - 1
                    if 0 <= choice_idx < len(window_options):
                        window_duration = window_options[choice_idx]
                        break
                    else:
                        print("❌ Please enter number between 1-10")
            except ValueError:
                print("❌ Please enter a valid number")

        print(f"✅ Selected window length: {window_duration}s")
        
    
        print(f"\n3. Construct file paths")
        print("-" * 30)
        base_dir = r"D:\HuaweiMoveData\Users\PPand\Desktop\BCI_GUI"
        
        model_path = os.path.join(base_dir, "tlcca_models", f"S{subject_num}_tlcca_model_exclude_{test_block}.mat")
        test_data_path = os.path.join(base_dir, "test_data", f"S{subject_num}_blocks_{test_block}_test_data.mat")
        
        print(f"📂 Model path: {model_path}")
        print(f"📂 Test data path: {test_data_path}")
        

        print(f"\n4. Check file existence")
        print("-" * 30)
        if not os.path.exists(model_path):
            print(f"❌ Model file does not exist: {model_path}")
            print("💡 Please run extract_block.py to generate model file first")
            return None, None, None, None
            
        if not os.path.exists(test_data_path):
            print(f"❌ Test data file does not exist: {test_data_path}")
            print("💡 Please run extract_block.py to generate test data file first")
            return None, None, None, None
        
        print("✅ All files exist")
        return model_path, test_data_path, subject_num, test_block

    def load_pretrained_model(self, model_path):
        """Load pretrained model - fixed version"""
        try:
            model_data = sio.loadmat(model_path)
            print(f"✅ Model loaded successfully: {model_path}")
            
           
            if 'target_order' in model_data:
                self.target_order = model_data['target_order'].flatten()
                print(f"   Loaded target_order from model: {self.target_order[:5]}...")
            if 'sti_f' in model_data:
                self.sti_f = model_data['sti_f'].flatten()
                print(f"   Loaded frequencies from model: {self.sti_f[:5]}...")
            if 'pha_val' in model_data:
                self.pha_val = model_data['pha_val'].flatten()
                print(f"   Loaded phase info from model")
            if 'source_freq_idx' in model_data:
                self.source_freq_idx = model_data['source_freq_idx'].flatten()
                print(f"   Source domain indices: {self.source_freq_idx[:5]}...")
            if 'target_freq_idx' in model_data:
                self.target_freq_idx = model_data['target_freq_idx'].flatten()
                print(f"   Target domain indices: {self.target_freq_idx[:5]}...")
            
            
            self.online_weights = {}
            self.online_templates = {}
            
            weights_loaded = 0
            for sub_band in range(1, self.num_of_subbands + 1):
               
                wx_source_key = f'Wx_source_band{sub_band}'
                wy_source_key = f'Wy_source_band{sub_band}'
                wx_transfer_key = f'Wx_transfer_band{sub_band}'
                template_transfer_key = f'templates_transfer_band{sub_band}'
                
              
                if wx_source_key in model_data:
                    self.online_weights[wx_source_key] = model_data[wx_source_key]
                    weights_loaded += 1
                if wy_source_key in model_data:
                    self.online_weights[wy_source_key] = model_data[wy_source_key]
                    weights_loaded += 1
                if wx_transfer_key in model_data:
                    self.online_weights[wx_transfer_key] = model_data[wx_transfer_key]
                    weights_loaded += 1
                if template_transfer_key in model_data:
                    self.online_templates[template_transfer_key] = model_data[template_transfer_key]
                    weights_loaded += 1
            
            print(f"✅ Weights loaded successfully: {weights_loaded}个")
            
            #  3：Verifying character-weight mapping relation
            print(f"\n🔍 Verifying character-weight mapping relation:")
            for i in range(5):
                char = self.beta_standard_chars[i]
                reordered_pos = None
                for pos, orig_idx in enumerate(self.target_order):
                    if orig_idx == i:
                        reordered_pos = pos
                        break
                
                if reordered_pos is not None:
                    freq = self.sti_f[reordered_pos]
                   
                    wx_source_key = f'Wx_source_band1'
                    wx_transfer_key = f'Wx_transfer_band1'
                    
                    source_weights = self.online_weights.get(wx_source_key, np.array([]))
                    transfer_weights = self.online_weights.get(wx_transfer_key, np.array([]))
                    
                    source_exists = (source_weights.size > 0 and i < source_weights.shape[1] and 
                                np.any(source_weights[:, i] != 0))
                    transfer_exists = (transfer_weights.size > 0 and i < transfer_weights.shape[1] and 
                                    np.any(transfer_weights[:, i] != 0))
                    
                    status = "✅" if (source_exists or transfer_exists) else "❌"
                    print(f"  Character'{char}'(Original index{i}) -> Reordered position{reordered_pos} -> Frequency{freq:.1f}Hz -> Weight exists{status}")
            
            return True
            
        except Exception as e:
            print(f"❌ Model loading failed: {e}")
            return False

    def _init_default_mapping(self):
        """Initialize default mapping"""
        sti_f = np.array([8.6, 8.8, 9, 9.2, 9.4, 9.6, 9.8, 10, 10.2, 10.4, 10.6, 10.8,
                         11, 11.2, 11.4, 11.6, 11.8, 12, 12.2, 12.4, 12.6, 12.8,
                         13, 13.2, 13.4, 13.6, 13.8, 14, 14.2, 14.4, 14.6, 14.8,
                         15, 15.2, 15.4, 15.6, 15.8, 8, 8.2, 8.4])
        
        pha_val = np.array([0.0, 0.5, 1.0, 1.5] * 10)  
        target_order = np.argsort(sti_f)  
        sti_f = sti_f[target_order]  
        
        self.target_order = target_order
        self.sti_f = sti_f
        self.pha_val = pha_val
        self.source_freq_idx = np.arange(1, len(sti_f), 2)
        self.target_freq_idx = np.arange(0, len(sti_f), 2)

    def load_source_data(self, test_data_path, test_block):
        """Load test data from MAT file - corrected time alignment"""
        try:
            print(f"📊 Loading test data: {test_data_path}")
            test_data = sio.loadmat(test_data_path)
            
            data_key = f'block_{test_block}_data'
            if data_key not in test_data:
                print(f"❌ Data key not found: {data_key}")
                return False
            
            self.test_eeg_data = test_data[data_key]
            print(f"✅ Test data loaded successfully: {test_data_path}")
            print(f"   Data key: {data_key}")
            print(f"   Data shape: {self.test_eeg_data.shape}")
            
            if self.test_eeg_data.ndim == 3:
                channels, samples_per_trial, trials = self.test_eeg_data.shape
                
              
                if hasattr(self, 'subject_num') and self.subject_num <= 15:
                    self.char_duration = 3.0  
                else:
                    self.char_duration = 4.0  
                
           
                actual_sampling_rate = 250  
                print(f"   Actual trial duration: {self.char_duration:.3f}s ")
                print(f"   Samples per trial: {samples_per_trial}")
                print(f"   Sampling rate: {actual_sampling_rate}Hz")
                
   
                total_samples = samples_per_trial * trials
                self.source_data = np.zeros((channels, total_samples))
                
                for trial_idx in range(trials):
                    start_col = trial_idx * samples_per_trial
                    end_col = start_col + samples_per_trial
                    self.source_data[:, start_col:end_col] = self.test_eeg_data[:, :, trial_idx]
                
         
                self.streaming_buffer = np.zeros((channels, 0))
                self.received_samples = 0
                
      
                self.total_samples = total_samples  # Total samples
                self.channels = channels  
                
                print(f"✅ Source data prepared successfully: {self.source_data.shape}")
                print(f"   Correction后总时长: {self.source_data.shape[1]/self.Fs:.2f}秒")
                print(f"   Correction后Character时长: {self.char_duration:.3f}s")
                print(f"   Character数量: {trials}")
                print(f"   Total samples: {self.total_samples}")  
            
                
             
                print(f"   CharacterTimeWindow:")
                for i in range(min(5, trials)):
                    start_time = i * self.char_duration
                    end_time = (i + 1) * self.char_duration
                    analysis_time = start_time + self.latency_delay
                    char = self.beta_standard_chars[i] if i < len(self.beta_standard_chars) else '?'
                    print(f"     Character{i}('{char}'): {start_time:.3f}-{end_time:.3f}s, Analysis starts at{analysis_time:.3f}s开始")
                    
                return True
            else:
                print(f"❌ Data dimension error: {self.test_eeg_data.shape}")
                return False
                
        except Exception as e:
            print(f"❌ Data loading failed: {e}")
            return False

    def simulate_data_streaming(self, current_time):
        """True 250Hz real-time data stream - one sample every 4ms"""
        
        expected_samples = int(current_time * self.Fs)
        
       
        while self.received_samples < expected_samples and self.received_samples < self.total_samples:
           
            new_sample = self.source_data[:, self.received_samples:self.received_samples+1]
            
            
            if self.streaming_buffer.shape[1] == 0:
                self.streaming_buffer = new_sample
            else:
              
                if self.streaming_buffer.shape[1] <= self.received_samples:
                    
                    extension = np.zeros((self.streaming_buffer.shape[0], 1000))
                    self.streaming_buffer = np.concatenate([self.streaming_buffer, extension], axis=1)
                
                self.streaming_buffer[:, self.received_samples] = new_sample.flatten()
            
            self.received_samples += 1
        
        return self.received_samples

    def get_data_window(self, window_start, window_end):
        """Get data window"""
        start_sample = int(window_start * self.Fs)
        end_sample = int(window_end * self.Fs)
        available_samples = self.streaming_buffer.shape[1]
        
        start_sample = max(0, start_sample)
        end_sample = min(end_sample, available_samples)
        
        if start_sample >= end_sample:
            return None
        
        return self.streaming_buffer[:, start_sample:end_sample]

    def apply_subband_filter(self, data, sub_band):
        """Sub-band filtering - using the same filters as in training"""
        try:
            if data.shape[1] < 10:
                return data
            
           
            if sub_band in self.subband_filters:
                b = self.subband_filters[sub_band]['bpB']
                a = self.subband_filters[sub_band]['bpA']
                filtered_data = signal.filtfilt(b, a, data, axis=1)
                return filtered_data
            else:
                return data
        except:
            return data

    def generate_reference_signals(self, freq, phase, length):
        """Generate reference signals - standard multi-harmonics in paper"""
        try:
            t = np.arange(length) / self.Fs
            ref_signals = []
          
            for harmonic in range(1, self.num_of_harmonics + 1):
                harmonic_freq = freq * harmonic
                cos_signal = np.cos(2 * np.pi * harmonic_freq * t + phase * harmonic)
                sin_signal = np.sin(2 * np.pi * harmonic_freq * t + phase * harmonic)
                ref_signals.extend([cos_signal, sin_signal])
            
            return np.array(ref_signals)  # (2*harmonics, length)
        except:
            return np.zeros((2*self.num_of_harmonics, length))

    def calculate_correlation(self, x, y):
        """Calculate correlation coefficient"""
        try:
            if len(x) != len(y) or len(x) < 2:
                return 0.0
            
            x = x - np.mean(x)
            y = y - np.mean(y)
            
            x_std = np.std(x)
            y_std = np.std(y)
            
            if x_std == 0 or y_std == 0:
                return 0.0
            
            correlation = np.corrcoef(x, y)[0, 1]
            if np.isnan(correlation):
                return 0.0
            
            return abs(correlation)
        except:
            return 0.0


    def matlab_canoncorr_exact(self, X, Y):
        """MATLAB canoncorr implementation - fully consistent with tlcca beta.py"""
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        if Y.ndim == 1:
            Y = Y.reshape(-1, 1)
        
       
        X = X - np.mean(X, axis=0)
        Y = Y - np.mean(Y, axis=0)
        
        n = X.shape[0]
        
      
        Cxx = (X.T @ X) / (n - 1)
        Cyy = (Y.T @ Y) / (n - 1) 
        Cxy = (X.T @ Y) / (n - 1)
        
        try:
      
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
            from sklearn.cross_decomposition import CCA
            cca = CCA(n_components=1)
            cca.fit(X, Y)
            return cca.x_weights_[:, 0], cca.y_weights_[:, 0]
    
    def run_real_time_recognition(self, duration=80.0):
        """Run real-time recognition - true simulation of real-time data stream"""
        print("\n" + "="*60)
        print("🚀 Start real-time recognition")
        print("="*60)
        print(f"🔧 Configuration parameters:")
        print(f"   Recognition window length: {self.recognition_window}s")
        
        recognition_count = 0
        correct_count = 0
        trial_results = {}
        
       
        start_real_time = time.time()
        update_interval = 0.02  
        window_duration = self.recognition_window  
        if hasattr(self, 'subject_num') and self.subject_num <= 15:
            char_duration = 3.0 
        else:
            char_duration = 4.0  
        
        while True:
            
            current_time = time.time() - start_real_time
            
            if current_time >= duration:
                break
            
            
            self.simulate_data_streaming(current_time)
            
         
            current_char_idx = int(current_time / char_duration)
            
            if current_char_idx >= len(self.beta_standard_chars):
                break
            
           
            char_start_time = current_char_idx * char_duration
            char_end_time = char_start_time + char_duration
            
   
            
            char_relative_time = current_time - char_start_time
            cue_duration = 0.5  
            physiological_delay = 0.13  
            recognition_start_offset = cue_duration + physiological_delay  

           
            if hasattr(self, 'subject_num') and self.subject_num <= 15:
                flicker_duration = 2.0  
            else:
                flicker_duration = 3.0 

            recognition_end_offset = cue_duration + flicker_duration  

            if (char_start_time <= current_time <= char_end_time and 
                recognition_start_offset <= char_relative_time <= recognition_end_offset):
                
          
               
                window_end_time = current_time
                window_start_time = window_end_time - window_duration

               
                recognition_absolute_start = char_start_time + recognition_start_offset
                if window_start_time < recognition_absolute_start:
                    window_start_time = recognition_absolute_start
                
                
                window_start_sample = int(window_start_time * self.Fs)
                window_end_sample = int(window_end_time * self.Fs)
                
              
                min_samples = int(max(0.2, window_duration * 0.8) * self.Fs)  
                expected_samples = window_end_sample - window_start_sample
                
                if (window_end_sample <= self.received_samples and 
                    expected_samples >= min_samples):
                    
                    data_window = self.streaming_buffer[:, window_start_sample:window_end_sample]
                    
                   
                    if data_window.shape[1] >= min_samples:
                        
                    
                        all_scores = self.calculate_tlcca_scores_for_all_chars(data_window)
                        
                       
                        best_idx = np.argmax(all_scores)
                        predicted_char = self.beta_standard_chars[best_idx]
                        target_char = self.beta_standard_chars[current_char_idx]
                       
                        char_relative_time = current_time - char_start_time
                        actual_window_duration = data_window.shape[1] / self.Fs
                        
                        is_correct = predicted_char.lower() == target_char.lower()
                        
                       
                        recognition_count += 1
                        if current_char_idx not in trial_results:
                            trial_results[current_char_idx] = {
                                'target': target_char, 
                                'predictions': [], 
                                'correct': 0, 
                                'total': 0
                            }
                        
                        trial_results[current_char_idx]['predictions'].append(predicted_char)
                        trial_results[current_char_idx]['total'] += 1
                        
                        if is_correct:
                            correct_count += 1
                            trial_results[current_char_idx]['correct'] += 1
                        
                      
                        status = "✅" if is_correct else "❌"
                        
                        print(f"🚀 Time{current_time:5.2f}s | Samples{self.received_samples} | "
                            f"Character{current_char_idx}('{target_char}') | Window[{window_start_time:.2f}-{window_end_time:.2f}] | "
                            f"Relative{char_relative_time:.3f}s | Window{actual_window_duration:.2f}s | Predicted:'{predicted_char}' | {status}")
            
           
            time.sleep(update_interval)

        
       
        print("\n" + "="*60)
        print("📊 Recognition result statistics")
        print("="*60)
        
        for trial_idx, stats in trial_results.items():
            final_pred = max(set(stats['predictions']), key=stats['predictions'].count)
            acc = stats['correct'] / stats['total'] * 100
            final_correct = "✅" if final_pred == stats['target'] else "❌"
            print(f"Trial {trial_idx:2d}: '{stats['target']}' -> '{final_pred}' ({acc:5.1f}%) {final_correct}")
        
        overall_acc = (correct_count / recognition_count * 100) if recognition_count > 0 else 0
        trial_acc = sum(1 for s in trial_results.values() 
                    if max(set(s['predictions']), key=s['predictions'].count) == s['target']) / len(trial_results) * 100
        
        print(f"\n🎯 Final result:")
        print(f"   Trial accuracy: {trial_acc:.1f}%")
        print(f"   Real-time accuracy: {overall_acc:.1f}%")
        print(f"   Recognition count: {recognition_count}")
        print(f"   Average Each Character Recognition count: {recognition_count/len(trial_results):.1f}")
        
        return trial_results



    def calculate_tlcca_scores_for_all_chars(self, eeg_window):
        """Calculate TLCCA scores for all characters - consistent with tlcca beta.py logic"""
        
       
        try:
            processed_window = np.zeros_like(eeg_window)
            
           
            Fo = 50
            Q = 35
            M = int(np.floor((self.Fs/2) / Fo))  # M=2
            notchB = np.array([1.0])
            notchA = np.array([1.0])
            
            for k in range(1, M+1):
                w0 = (k * Fo) / (self.Fs/2)
                b_k, a_k = signal.iirnotch(w0, Q)
                notchB = np.convolve(notchB, b_k)
                notchA = np.convolve(notchA, a_k)
            
            for ch in range(eeg_window.shape[0]):
                processed_window[ch, :] = signal.filtfilt(notchB, notchA, eeg_window[ch, :])
            eeg_window = processed_window
        except:
            pass
        
        
        all_scores = []
        
        for char_idx in range(len(self.beta_standard_chars)):
           
            reordered_pos = None
            for pos, orig_idx in enumerate(self.target_order):
                if orig_idx == char_idx:
                    reordered_pos = pos
                    break
            
            if reordered_pos is None:
                all_scores.append(0.0)
                continue
            
           
            freq = self.sti_f[reordered_pos]
            phase = self.pha_val[reordered_pos]
            Y1 = self.generate_reference_signals(freq, phase, eeg_window.shape[1])
            
            total_score = 0.0
            
           
            for sub_band in range(1, self.num_of_subbands + 1):
                X_filtered = self.apply_subband_filter(eeg_window, sub_band)
                
                
                rho_i = self.calculate_single_char_score(X_filtered, Y1, reordered_pos, sub_band)
                
                fb_weight = self.FB_coef[sub_band-1]
                total_score += fb_weight * rho_i
            
            all_scores.append(total_score)
        
        return all_scores

    def calculate_single_char_score(self, X_filtered, Y1, reordered_pos, sub_band):
        """Calculate score of a single character in one sub-band"""
        
        wx_source_key = f'Wx_source_band{sub_band}'
        wy_source_key = f'Wy_source_band{sub_band}'  
        wx_transfer_key = f'Wx_transfer_band{sub_band}'
        templates_transfer_key = f'templates_transfer_band{sub_band}'

        r1a = r1b = r3 = 0.0

        
        source_domain_idx = None
        for i, freq_idx in enumerate(self.source_freq_idx):
            if freq_idx == reordered_pos:
                source_domain_idx = i
                break

        target_domain_idx = None
        for i, freq_idx in enumerate(self.target_freq_idx):
            if freq_idx == reordered_pos:
                target_domain_idx = i
                break

        
        if reordered_pos in self.source_freq_idx and source_domain_idx is not None:
           
            if wx_source_key in self.online_weights and wy_source_key in self.online_weights:
                try:
                    W1_x = self.online_weights[wx_source_key][:, source_domain_idx]
                    W1_y = self.online_weights[wy_source_key][:, source_domain_idx] 
                    
                    if np.any(W1_x != 0) and np.any(W1_y != 0):
                        X_proj = W1_x.T @ X_filtered
                        Y_proj = W1_y.T @ Y1
                        r1a = self.calculate_correlation(X_proj.flatten(), Y_proj.flatten())
                except Exception as e:
                    r1a = 0.0
            
            r1b = 0.0  
            
        elif reordered_pos in self.target_freq_idx and target_domain_idx is not None:
            r1a = 0.0  
            
            corresponding_source_idx = target_domain_idx
            
            if (wx_transfer_key in self.online_weights and 
                templates_transfer_key in self.online_templates):
                try:
                    W2_x = self.online_weights[wx_transfer_key][:, corresponding_source_idx]
                    H1_r1 = self.online_templates[templates_transfer_key][:, corresponding_source_idx]
                    
                    if np.any(W2_x != 0) and np.any(H1_r1 != 0):
                        X_proj = W2_x.T @ X_filtered
                        template_len = min(len(H1_r1), len(X_proj))
                        if template_len > 10:
                            r1b = self.calculate_correlation(
                                X_proj[:template_len].flatten(), 
                                H1_r1[:template_len].flatten()
                            )
                except Exception as e:
                    r1b = 0.0

      
        if reordered_pos in self.source_freq_idx and source_domain_idx is not None:
            if wx_source_key in self.online_weights:
                try:
                    W1_x = self.online_weights[wx_source_key][:, source_domain_idx]
                    if np.any(W1_x != 0):
                        try:
                           
                            filtered_test_signal = W1_x.T @ X_filtered
                            filtered_test_reshaped = filtered_test_signal.reshape(-1, 1)
                            ref1_reshaped = Y1.T
                            
                            A1, B1 = self.matlab_canoncorr_exact(filtered_test_reshaped, ref1_reshaped)
                            proj1 = filtered_test_reshaped @ A1.reshape(-1, 1)
                            proj2 = ref1_reshaped @ B1.reshape(-1, 1)
                            r3 = self.calculate_correlation(proj1.flatten(), proj2.flatten())
                        except:
                            
                            min_len = min(len(filtered_test_signal), Y1.shape[1])
                            r3 = self.calculate_correlation(
                                filtered_test_signal[:min_len], 
                                Y1[0, :min_len]
                            )
                except Exception as e:
                    r3 = 0.0
                    
        elif reordered_pos in self.target_freq_idx and target_domain_idx is not None:
            corresponding_source_idx = target_domain_idx
            if wx_transfer_key in self.online_weights:
                try:
                    W1_x = self.online_weights[wx_transfer_key][:, corresponding_source_idx]
                    if np.any(W1_x != 0):
                        try:
                            
                            filtered_test_signal = W1_x.T @ X_filtered
                            filtered_test_reshaped = filtered_test_signal.reshape(-1, 1)
                            ref1_reshaped = Y1.T
                            
                            A1, B1 = self.matlab_canoncorr_exact(filtered_test_reshaped, ref1_reshaped)
                            proj1 = filtered_test_reshaped @ A1.reshape(-1, 1)
                            proj2 = ref1_reshaped @ B1.reshape(-1, 1)
                            r3 = self.calculate_correlation(proj1.flatten(), proj2.flatten())
                        except:
                            
                            min_len = min(len(filtered_test_signal), Y1.shape[1])
                            r3 = self.calculate_correlation(
                                filtered_test_signal[:min_len], 
                                Y1[0, :min_len]
                            )
                except Exception as e:
                    r3 = 0.0

        
        rho_i = (np.sign(r1a) * r1a**2 + np.sign(r1b) * r1b**2 + np.sign(r3) * r3**2)
        
        return rho_i
    def precise_sleep_until(self, target_time):
        """High-precision sleep until target time"""
        while True:
            current = time.time()
            remaining = target_time - current
            if remaining <= 0:
                break
            if remaining > 0.001:
                time.sleep(remaining - 0.001)
            else:
                time.sleep(0.0001)  

def main():
    """Main function - supports selecting different Subjects and Blocks"""
    print("🎯 TLCCA Real_time Recognition System")
    print("="*50)
    
    # 🔑 1. 首先选择Window长度
    print("\n⏱️ Recognition window length selection:")
    print("1=0.3s, 2=0.4s, 3=0.5s, 4=0.6s, 5=0.7s")
    print("6=0.8s, 7=0.9s, 8=1.0s, 9=1.1s, 10=1.2s")

    while True:
        try:
            window_choice = input("Select window length (1-10, default:6): ").strip()
            
           
            window_options = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]
            
            if window_choice == "":
                window_duration = 0.8 
                break
            else:
                choice_idx = int(window_choice) - 1
                if 0 <= choice_idx < len(window_options):
                    window_duration = window_options[choice_idx]
                    break
                else:
                    print("❌ Please enter a number between:1-10")
        except ValueError:
            print("❌ Please enter a valid number")

    print(f"✅ Selected window length: {window_duration}s")
    
  
    tlcca = TLCCAOnlineRecognition(recognition_window=window_duration)
    
    
    print("\n📋 Select test configuration:")
    
   
    while True:
        try:
            subject_num = int(input("Enter Subject number (1-70): ").strip())
           
            tlcca.subject_num = subject_num
            if 1 <= subject_num <= 70:
                break
            else:
                print("❌ Subject number must be between 1 and 70")
        except ValueError:
            print("❌ Please enter a valid number")
    
    
    while True:
        try:
            test_block = int(input("Enter test Block number (1-4): ").strip())
            if 1 <= test_block <= 4:
                break
            else:
                print("❌ Block number must be between 1 and 4")
        except ValueError:
            print("❌ Please enter a valid number")
    
    
    base_dir = r"D:\HuaweiMoveData\Users\PPand\Desktop\BCI_GUI"
    
    model_path = os.path.join(base_dir, "tlcca_models", f"S{subject_num}_tlcca_model_exclude_{test_block}.mat")
    test_data_path = os.path.join(base_dir, "test_data", f"S{subject_num}_blocks_{test_block}_test_data.mat")
    
    print(f"\n📂 Using configuration:")
    print(f"   Subject: S{subject_num}")
    print(f"   Test Block: {test_block}")
    print(f"   Window Duration: {window_duration}s")
    print(f"   Model path: {model_path}")
    print(f"   Test data path: {test_data_path}")
    

    if not os.path.exists(model_path):
        print(f"❌ Model file does not exist: {model_path}")
        print("💡 Please run extract_block.py to generate model file first")
        return
        
    if not os.path.exists(test_data_path):
        print(f"❌ Test data file does not exist: {test_data_path}")
        print("💡 Please run extract_block.py to generate test data file first")
        return
    
    print("✅ All files exist")
    

    if not tlcca.load_pretrained_model(model_path):
        return
    
    if not tlcca.load_source_data(test_data_path, test_block):
        return
    
  
    total_data_duration = 120.0  # 40Character × 3.0秒 = 120秒
    print(f"\n✨ Start real-time recognition (total_data_duration: {total_data_duration:.1f}s)...")
 
    tlcca.run_real_time_recognition(total_data_duration)
    print("\n🎉 Recognition completed!")


if __name__ == "__main__":
    main()