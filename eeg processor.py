#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版TLCCA实时识别系统 - 支持模型和数据选择
"""

import numpy as np
import scipy.io as sio
import scipy.signal as signal
import time
import os

class TLCCAOnlineRecognition:
    # [EN] __init__: Auto-generated summary of this method's purpose.
    def __init__(self, subject_num=1, test_block=1, recognition_window=0.8, gui_mode=False):
        # 基础参数
        self.Fs = 250
        self.num_of_subbands = 5
        self.latency_delay = 0.0
        self.recognition_window = recognition_window
        self.subject_num = subject_num
        self.test_block = test_block
        
        self.gui_mode = False
        self.recognition_results = []  # 存储每个字符的识别结果
        self.result_timestamps = [] 
        self.recognition_started = False
        # 自动构建文件路径
        base_dir = r"D:\HuaweiMoveData\Users\PPand\Desktop\BCI_GUI"
        self.model_path = os.path.join(base_dir, "tlcca_models", f"S{subject_num}_tlcca_model_exclude_{test_block}.mat")
        self.test_data_path = os.path.join(base_dir, "test_data", f"S{subject_num}_blocks_{test_block}_test_data.mat")
        
    
        
        # 字符集
        self.beta_standard_chars = [
            '.', ',', '<', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '_'
        ]
        

        self.num_of_harmonics = 5  # 添加这个属性
        self.num_of_subbands = 5
        
        # 🔑 论文公式11的滤波器组系数
        self.FB_coef = np.array([(n**(-1.25) + 0.25) for n in range(1, self.num_of_subbands + 1)])
        print(f"   FB coefficients: {self.FB_coef}")
        # 模型参数
        self.online_weights = {}
        self.online_templates = {}
        self.target_order = None
        self.sti_f = None
        self.pha_val = None
        self.source_freq_idx = None
        self.target_freq_idx = None
        
        # 实时数据
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

    # [EN] set_gui_mode: Auto-generated summary of this method's purpose.

    def set_gui_mode(self, recognition_queue=None):
        """设置GUI模式"""
        self.gui_mode = True
        print("📱 Set to GUI mode")
    
    # [EN] run_gui_recognition: Auto-generated summary of this method's purpose.
    
    def run_gui_recognition(self):
        """GUI模式下运行识别 - 按照原本的方式"""
        try:
            print("============================================================")
            print("🚀 Start Beta simulation real-time recognition")
            print("============================================================")
            print(f"🔧 Configuration::")
            print(f"   Recognition window length: {self.recognition_window}s")
            
            self.recognition_started = True
            
            # 清空结果列表
            self.recognition_results = ['?'] * 40  # 初始化40个字符的结果
            
            # 按照原本的方式运行识别
            self.run_real_time_recognition_for_gui()
            
        except Exception as e:
            print(f"❌ GUI recognition run failed: {e}")
            
    # [EN] get_result_for_char: Auto-generated summary of this method's purpose.
            
    def get_result_for_char(self, char_index):
        """获取指定字符的识别结果"""
        if not self.recognition_started:
            return None  # 识别还未开始
            
        if 0 <= char_index < len(self.recognition_results):
            return self.recognition_results[char_index]
        return None
        
    # [EN] get_all_results: Auto-generated summary of this method's purpose.
        
    def get_all_results(self):
        """获取所有识别结果"""
        return self.recognition_results.copy()
    
    # [EN] get_result_for_char_with_delay: Auto-generated summary of this method's purpose.
    
    def get_result_for_char_with_delay(self, char_index, delay_seconds=2.0):
        """获取指定字符的识别结果 - 带延迟检查"""
        import time
        
        if not self.recognition_started:
            return None  # 识别还未开始
            
        if not (0 <= char_index < len(self.recognition_results)):
            return None
            
        # 检查结果是否已经产生
        if self.result_timestamps[char_index] == 0:
            return None  # 结果还未产生
            
        # 检查延迟时间是否已过
        current_time = time.time()
        result_time = self.result_timestamps[char_index]
        
        if current_time - result_time >= delay_seconds:
            # 延迟时间已过，可以返回结果
            return self.recognition_results[char_index]
        else:
            # 还没到显示时间
            return None
        
    # [EN] run_real_time_recognition_for_gui: Auto-generated summary of this method's purpose.
        
    def run_real_time_recognition_for_gui(self):
        """为GUI运行的实时识别 - 完全按照原本的方法"""
        import time
        
        # 计算参数
        if self.subject_num <= 15:
            char_duration = 3.0
            flicker_duration = 2.0
        else:
            char_duration = 4.0
            flicker_duration = 3.0
        
        # 清空结果列表
        self.recognition_results = ['?'] * 40  # 初始化40个字符的结果
        self.result_timestamps = [0] * 40     # 初始化时间戳
        
        # 记录识别开始的真实时间
        recognition_start_time = time.time()
            
        # 对每个字符进行识别 - 按照原本的逻辑
        for char_idx in range(40):
            target_char = self.beta_standard_chars[char_idx]
            char_start_time = char_idx * char_duration
            
            # 按照原本的时间窗口计算
            recognition_windows = []
            
            # 计算识别窗口（按照原本的逻辑）
            window1_start = char_start_time + 0.63  # cue + 生理延迟
            window1_end = window1_start + self.recognition_window
            
            # 确保不超出字符时间范围
            if window1_end > char_start_time + char_duration:
                window1_end = char_start_time + char_duration
                
            if window1_end - window1_start >= 0.2:  # 窗口足够长
                recognition_windows.append((window1_start, window1_end))
            
            best_result = '?'
            best_confidence = -1
            
            # 对每个时间窗口进行识别
            for window_start, window_end in recognition_windows:
                start_sample = int(window_start * self.Fs)
                end_sample = int(window_end * self.Fs)
                
                if end_sample > self.total_samples:
                    end_sample = self.total_samples
                    
                if start_sample >= end_sample:
                    continue
                
                # 提取数据窗口
                eeg_window = self.source_data[:, start_sample:end_sample]
                
                # 识别
                all_scores = self.calculate_tlcca_scores_for_all_chars(eeg_window)
                max_idx = np.argmax(all_scores)
                predicted_char = self.beta_standard_chars[max_idx]
                confidence = all_scores[max_idx]
                
                # 按照原本的格式输出
                is_correct = "✅" if predicted_char == target_char else "❌"
                print(f"🚀 Time {window_end:.2f}s | Samples{end_sample} | Char{char_idx}('{target_char}') | Window[{window_start:.2f}-{window_end:.2f}] | Relative{window_end - char_start_time:.3f}s | Window{window_end - window_start:.2f}s | Pred:'{predicted_char}' | {is_correct}")
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_result = predicted_char
            
            # 保存这个字符的最终结果和时间戳
            self.recognition_results[char_idx] = best_result
            self.result_timestamps[char_idx] = time.time()  # 记录结果产生的真实时间
        
        print("============================================================")
        print("✅ Beta simulation recognition finished")
        print("============================================================")

    # [EN] get_recognition_at_time: Auto-generated summary of this method's purpose.

    def get_recognition_at_time(self, char_index, current_time):
        """根据字符索引和当前时间获取识别结果"""
        try:
            # 计算字符时间窗口
            if self.subject_num <= 15:
                char_duration = 3.0
            else:
                char_duration = 4.0
                
            char_start_time = char_index * char_duration
            
            # 计算识别窗口（从cue结束+生理延迟开始）
            recognition_start = char_start_time + 0.63  # 0.5s cue + 0.13s 生理延迟
            
            # 检查是否到达识别时间
            if current_time < recognition_start:
                return None  # 还没到识别时间
                
            # 计算识别窗口结束时间
            window_end = min(recognition_start + self.recognition_window, char_start_time + char_duration)
            actual_time = min(current_time, window_end)
            
            # 计算实际使用的窗口长度
            window_length = actual_time - recognition_start
            if window_length < 0.2:  # 窗口太短
                return None
                
            # 提取EEG数据
            start_sample = int(recognition_start * self.Fs)
            end_sample = int(actual_time * self.Fs)
            
            if end_sample > self.total_samples:
                end_sample = self.total_samples
                
            if start_sample >= end_sample:
                return None
                
            eeg_window = self.source_data[:, start_sample:end_sample]
            
            # 执行tlCCA识别
            all_scores = self.calculate_tlcca_scores_for_all_chars(eeg_window)
            
            # 返回最佳结果
            max_idx = np.argmax(all_scores)
            predicted_char = self.beta_standard_chars[max_idx]
            confidence = all_scores[max_idx]
            
            result = {
                'char': predicted_char,
                'confidence': confidence,
                'window_length': window_length,
                'char_index': char_index
            }
            
            print(f"🧠 Time {actual_time:.2f}s | Char{char_index}('{self.beta_standard_chars[char_index]}') | Window{window_length:.2f}s | Pred:'{predicted_char}' | 置信度:{confidence:.3f}")
            
            return result
            
        except Exception as e:
            print(f"❌ Failed to get recognition result: {e}")
            return None

    # [EN] initialize_for_gui: Auto-generated summary of this method's purpose.

    def initialize_for_gui(self):
        """专为GUI模式初始化"""
        success1 = self.load_pretrained_model(self.model_path)
        if not success1:
            return False
        
        success2 = self.load_source_data(self.test_data_path, self.test_block)
        if not success2:
            return False
        
        print("✅ GUI mode initialization completed")
        return True

    # [EN] get_recognition_for_char: Auto-generated summary of this method's purpose.

    def get_recognition_for_char(self, char_idx, current_time):
        """为GUI提供特定字符的识别结果"""
        try:
            # 根据字符索引和当前时间，提取对应的EEG数据窗口
            char_duration = 3.0 if self.subject_num <= 15 else 4.0
            char_start_time = char_idx * char_duration
            
            # 计算识别窗口
            recognition_start = char_start_time + 0.63  # cue时间 + 生理延迟
            recognition_end = current_time
            window_duration = min(recognition_end - recognition_start, self.recognition_window)
            
            if window_duration < 0.2:  # 窗口太小
                return None
            
            # 提取EEG数据窗口
            start_sample = int(recognition_start * self.Fs)
            end_sample = int(recognition_end * self.Fs)
            
            if end_sample > self.total_samples:
                return None
            
            eeg_window = self.source_data[:, start_sample:end_sample]
            
            # 进行识别
            all_scores = self.calculate_tlcca_scores_for_all_chars(eeg_window)
            
            # 返回最高分的字符
            best_idx = np.argmax(all_scores)
            predicted_char = self.beta_standard_chars[best_idx]
            confidence = all_scores[best_idx]
            
            return {
                'char': predicted_char,
                'confidence': confidence,
                'scores': all_scores
            }
            
        except Exception as e:
            print(f"❌ 识别Char时出错: {e}")
            return None
    

    # [EN] initialize_and_run: Auto-generated summary of this method's purpose.
    

    def initialize_and_run(self):
        """一键初始化和运行"""
        if not self.load_pretrained_model(self.model_path):
            return False
        if not self.load_source_data(self.test_data_path, self.test_block):
            return False
        
        # 自动计算运行时长
        if self.subject_num <= 15:
            char_duration = 3.0  # 0.5s + 2s + 0.5s
        else:
            char_duration = 4.0  # 0.5s + 3s + 0.5s
        
        total_duration = len(self.beta_standard_chars) * char_duration
        return self.run_real_time_recognition(total_duration)

    # [EN] select_model_and_data: Auto-generated summary of this method's purpose.

    def select_model_and_data(self):
        """选择模型和数据文件"""
        print("\n" + "="*50)
        print("🎯 TLCCA real-time recognition - model & data selection")
        print("="*50)
        
        # 1. 选择Subject
        print("\n1. Subject selection")
        print("-" * 30)
        while True:
            try:
                subject_num = int(input("请输入Subject编号 (1-70): ").strip())
                if 1 <= subject_num <= 70:
                    break
                else:
                    print("❌ Subject number must be between 1 and 70")
            except ValueError:
                print("❌ Please enter a valid number")
        
        # 2. 选择测试Block
        print(f"\n2. Test block selection")
        print("-" * 30)
        while True:
            try:
                test_block = int(input("请输入测试Block编号 (1-4): ").strip())
                if 1 <= test_block <= 4:
                    break
                else:
                    print("❌ Block number must be between 1 and 4")
            except ValueError:
                print("❌ Please enter a valid number")
        # 🔑 新增：选择窗口长度
        print("\n⏱️ Recognition window length选择:")
        print("1=0.3s, 2=0.4s, 3=0.5s, 4=0.6s, 5=0.7s")
        print("6=0.8s, 7=0.9s, 8=1.0s, 9=1.1s, 10=1.2s")

        while True:
            try:
                window_choice = input("请选择窗口长度 (1-10, 默认6): ").strip()
                
                # 窗口时间映射：0.3s到1.2s，步长0.1s
                window_options = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]
                
                if window_choice == "":
                    window_duration = 0.8  # 默认值，对应选择6
                    break
                else:
                    choice_idx = int(window_choice) - 1
                    if 0 <= choice_idx < len(window_options):
                        window_duration = window_options[choice_idx]
                        break
                    else:
                        print("❌ Please enter a number between 1 and 10")
            except ValueError:
                print("❌ Please enter a valid number")

        print(f"✅ 选择的Window长度: {window_duration}s")
        
        # 3. 构建文件路径
        print(f"\n3. Build file paths")
        print("-" * 30)
        base_dir = r"D:\HuaweiMoveData\Users\PPand\Desktop\BCI_GUI"
        
        model_path = os.path.join(base_dir, "tlcca_models", f"S{subject_num}_tlcca_model_exclude_{test_block}.mat")
        test_data_path = os.path.join(base_dir, "test_data", f"S{subject_num}_blocks_{test_block}_test_data.mat")
        
        print(f"📂 Model path: {model_path}")
        print(f"📂 Test data path: {test_data_path}")
        
        # 4. 检查文件是否存在
        print(f"\n4. File existence check")
        print("-" * 30)
        if not os.path.exists(model_path):
            print(f"❌ Model file does not exist: {model_path}")
            print("💡 Please run extract_block.py to generate the model file")
            return None, None, None, None
            
        if not os.path.exists(test_data_path):
            print(f"❌ Test data file does not exist: {test_data_path}")
            print("💡 Please run extract_block.py to generate the test data file")
            return None, None, None, None
        
        print("✅ All files exist")
        return model_path, test_data_path, subject_num, test_block

    # [EN] load_pretrained_model: Auto-generated summary of this method's purpose.

    def load_pretrained_model(self, model_path):
        """加载预训练模型 - 修复版"""
        try:
            model_data = sio.loadmat(model_path)
            print(f"✅ Model loaded: {model_path}")
            
            # 🔑 修复1：按照extract_block.py的方式加载映射信息
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
            
            # 🔑 修复2：完全按照try.py的成功方式加载权重
            self.online_weights = {}
            self.online_templates = {}
            
            weights_loaded = 0
            for sub_band in range(1, self.num_of_subbands + 1):
                # 🔑 关键：使用与extract_block.py保存时完全相同的键名
                wx_source_key = f'Wx_source_band{sub_band}'
                wy_source_key = f'Wy_source_band{sub_band}'
                wx_transfer_key = f'Wx_transfer_band{sub_band}'
                template_transfer_key = f'templates_transfer_band{sub_band}'
                
                # 🔑 修复：按照try.py的方式直接保存到online_weights
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
            
            print(f"✅ Weights loaded: {weights_loaded}个")
            
            # 🔑 修复3：验证字符-权重映射关系
            print(f"\n🔍 验证Char-权重映射关系:")
            for i in range(5):
                char = self.beta_standard_chars[i]
                reordered_pos = None
                for pos, orig_idx in enumerate(self.target_order):
                    if orig_idx == i:
                        reordered_pos = pos
                        break
                
                if reordered_pos is not None:
                    freq = self.sti_f[reordered_pos]
                    # 检查第一个子频带的权重
                    wx_source_key = f'Wx_source_band1'
                    wx_transfer_key = f'Wx_transfer_band1'
                    
                    source_weights = self.online_weights.get(wx_source_key, np.array([]))
                    transfer_weights = self.online_weights.get(wx_transfer_key, np.array([]))
                    
                    source_exists = (source_weights.size > 0 and i < source_weights.shape[1] and 
                                np.any(source_weights[:, i] != 0))
                    transfer_exists = (transfer_weights.size > 0 and i < transfer_weights.shape[1] and 
                                    np.any(transfer_weights[:, i] != 0))
                    
                    status = "✅" if (source_exists or transfer_exists) else "❌"
                    print(f"  Char'{char}'(orig idx{i}) -> reordered pos{reordered_pos} -> freq{freq:.1f}Hz -> weights exist{status}")
            
            return True
            
        except Exception as e:
            print(f"❌ Model loading failed: {e}")
            return False

    # [EN] _init_default_mapping: Auto-generated summary of this method's purpose.

    def _init_default_mapping(self):
        """初始化默认映射"""
        sti_f = np.array([8.6, 8.8, 9, 9.2, 9.4, 9.6, 9.8, 10, 10.2, 10.4, 10.6, 10.8,
                         11, 11.2, 11.4, 11.6, 11.8, 12, 12.2, 12.4, 12.6, 12.8,
                         13, 13.2, 13.4, 13.6, 13.8, 14, 14.2, 14.4, 14.6, 14.8,
                         15, 15.2, 15.4, 15.6, 15.8, 8, 8.2, 8.4])
        
        pha_val = np.array([0.0, 0.5, 1.0, 1.5] * 10)  # 与try.py保持一致
        target_order = np.argsort(sti_f)  # 按频率排序
        sti_f = sti_f[target_order]  # 重新排序频率
        
        self.target_order = target_order
        self.sti_f = sti_f
        self.pha_val = pha_val
        self.source_freq_idx = np.arange(1, len(sti_f), 2)
        self.target_freq_idx = np.arange(0, len(sti_f), 2)

    # [EN] load_source_data: Auto-generated summary of this method's purpose.

    def load_source_data(self, test_data_path, test_block):
        """从MAT文件加载测试数据 - 修正时间对应"""
        try:
            print(f"📊 Load test data: {test_data_path}")
            test_data = sio.loadmat(test_data_path)
            
            data_key = f'block_{test_block}_data'
            if data_key not in test_data:
                print(f"❌ 找不到Data key: {data_key}")
                return False
            
            self.test_eeg_data = test_data[data_key]
            print(f"✅ Test data loaded: {test_data_path}")
            print(f"   Data key: {data_key}")
            print(f"   Data shape: {self.test_eeg_data.shape}")
            
            if self.test_eeg_data.ndim == 3:
                channels, samples_per_trial, trials = self.test_eeg_data.shape
                
                # 🔑 关键修正：使用真实的2.0秒作为字符时长
                # 🔑 根据被试编号动态设置字符时长
                if hasattr(self, 'subject_num') and self.subject_num <= 15:
                    self.char_duration = 3.0  # 1-15号被试
                else:
                    self.char_duration = 4.0  # 16-70号被试
                
                # 🔑 修正：使用真实的250Hz采样率
                actual_sampling_rate = 250  # 修正为250Hz
                print(f"   Actual duration per trial: {self.char_duration:.3f}s (基于MATLAB分析)")
                print(f"   每个trialSamples数: {samples_per_trial}")
                print(f"   Sampling rate: {actual_sampling_rate}Hz")
                
                # 重组为连续数据
                total_samples = samples_per_trial * trials
                self.source_data = np.zeros((channels, total_samples))
                
                for trial_idx in range(trials):
                    start_col = trial_idx * samples_per_trial
                    end_col = start_col + samples_per_trial
                    self.source_data[:, start_col:end_col] = self.test_eeg_data[:, :, trial_idx]
                
                # 初始化流式缓冲区
                self.streaming_buffer = np.zeros((channels, 0))
                self.received_samples = 0
                
                # 🔑 修复：添加缺失的属性
                self.total_samples = total_samples  # 总样本数
                self.channels = channels  # 通道数
                
                print(f"✅ Source data prepared: {self.source_data.shape}")
                print(f"   Corrected total duration: {self.source_data.shape[1]/self.Fs:.2f}秒")
                print(f"   修正后Char时长: {self.char_duration:.3f}s")
                print(f"   Char数量: {trials}")
                print(f"   总Samples数: {self.total_samples}")  # 🔑 添加调试信息
            
                
                # 🔑 显示正确的字符时间窗口
                print(f"   CharTimeWindow:")
                for i in range(min(5, trials)):
                    start_time = i * self.char_duration
                    end_time = (i + 1) * self.char_duration
                    analysis_time = start_time + self.latency_delay
                    char = self.beta_standard_chars[i] if i < len(self.beta_standard_chars) else '?'
                    print(f"     Char{i}('{char}'): {start_time:.3f}-{end_time:.3f}s, analysis from{analysis_time:.3f}s开始")
                    
                return True
            else:
                print(f"❌ Data dimension error: {self.test_eeg_data.shape}")
                return False
                
        except Exception as e:
            print(f"❌ Data loading failed: {e}")
            return False

    # [EN] simulate_data_streaming: Auto-generated summary of this method's purpose.

    def simulate_data_streaming(self, current_time):
        """真正的250Hz实时数据流 - 每4ms一个样本"""
        # 🔑 关键：按250Hz严格计算应该有多少样本
        expected_samples = int(current_time * self.Fs)
        
        # 🔑 逐个样本地添加，模拟真实的连续采集
        while self.received_samples < expected_samples and self.received_samples < self.total_samples:
            # 获取下一个样本
            new_sample = self.source_data[:, self.received_samples:self.received_samples+1]
            
            # 添加到流缓冲区（真正的连续追加）
            if self.streaming_buffer.shape[1] == 0:
                self.streaming_buffer = new_sample
            else:
                # 🔑 连续追加，不重新分配内存
                if self.streaming_buffer.shape[1] <= self.received_samples:
                    # 扩展缓冲区
                    extension = np.zeros((self.streaming_buffer.shape[0], 1000))
                    self.streaming_buffer = np.concatenate([self.streaming_buffer, extension], axis=1)
                
                self.streaming_buffer[:, self.received_samples] = new_sample.flatten()
            
            self.received_samples += 1
        
        return self.received_samples

    # [EN] get_data_window: Auto-generated summary of this method's purpose.

    def get_data_window(self, window_start, window_end):
        """获取数据窗口"""
        start_sample = int(window_start * self.Fs)
        end_sample = int(window_end * self.Fs)
        available_samples = self.streaming_buffer.shape[1]
        
        start_sample = max(0, start_sample)
        end_sample = min(end_sample, available_samples)
        
        if start_sample >= end_sample:
            return None
        
        return self.streaming_buffer[:, start_sample:end_sample]

    # [EN] apply_subband_filter: Auto-generated summary of this method's purpose.

    def apply_subband_filter(self, data, sub_band):
        """子频带滤波 - 使用与训练时相同的滤波器"""
        try:
            if data.shape[1] < 10:
                return data
            
            # 使用预先设计好的滤波器
            if sub_band in self.subband_filters:
                b = self.subband_filters[sub_band]['bpB']
                a = self.subband_filters[sub_band]['bpA']
                filtered_data = signal.filtfilt(b, a, data, axis=1)
                return filtered_data
            else:
                return data
        except:
            return data

    # [EN] generate_reference_signals: Auto-generated summary of this method's purpose.

    def generate_reference_signals(self, freq, phase, length):
        """生成参考信号 - 论文标准多谐波"""
        try:
            t = np.arange(length) / self.Fs
            ref_signals = []
            
            # 🔑 生成多个谐波的正弦和余弦信号
            for harmonic in range(1, self.num_of_harmonics + 1):
                harmonic_freq = freq * harmonic
                cos_signal = np.cos(2 * np.pi * harmonic_freq * t + phase * harmonic)
                sin_signal = np.sin(2 * np.pi * harmonic_freq * t + phase * harmonic)
                ref_signals.extend([cos_signal, sin_signal])
            
            return np.array(ref_signals)  # (2*harmonics, length)
        except:
            return np.zeros((2*self.num_of_harmonics, length))

    # [EN] calculate_correlation: Auto-generated summary of this method's purpose.

    def calculate_correlation(self, x, y):
        """计算相关系数"""
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


    # [EN] matlab_canoncorr_exact: Auto-generated summary of this method's purpose.


    def matlab_canoncorr_exact(self, X, Y):
        """MATLAB canoncorr实现 - 与tlcca beta.py完全一致"""
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        if Y.ndim == 1:
            Y = Y.reshape(-1, 1)
        
        # 中心化
        X = X - np.mean(X, axis=0)
        Y = Y - np.mean(Y, axis=0)
        
        n = X.shape[0]
        
        # 计算协方差矩阵（使用MATLAB的方式）
        Cxx = (X.T @ X) / (n - 1)
        Cyy = (Y.T @ Y) / (n - 1) 
        Cxy = (X.T @ Y) / (n - 1)
        
        try:
            # 使用Cholesky分解，更接近MATLAB
            Lx = np.linalg.cholesky(Cxx + 1e-12 * np.eye(Cxx.shape[0]))
            Ly = np.linalg.cholesky(Cyy + 1e-12 * np.eye(Cyy.shape[0]))
            
            # 求解广义特征值问题
            M = np.linalg.solve(Lx, Cxy)
            M = np.linalg.solve(Ly.T, M.T).T
            
            U, s, Vt = np.linalg.svd(M, full_matrices=False)
            
            A = np.linalg.solve(Lx.T, U[:, 0])
            B = np.linalg.solve(Ly.T, Vt[0, :])
            
            return A, B
            
        except:
            # 备用方案
            from sklearn.cross_decomposition import CCA
            cca = CCA(n_components=1)
            cca.fit(X, Y)
            return cca.x_weights_[:, 0], cca.y_weights_[:, 0]
    
    # [EN] run_real_time_recognition: Auto-generated summary of this method's purpose.
    
    def run_real_time_recognition(self, duration=80.0):
        """运行实时识别 - 真正模拟实时数据流"""
        print("\n" + "="*60)
        print("🚀 开始真实Time实时识别")
        print("="*60)
        print(f"🔧 Configuration::")
        print(f"   Recognition window length: {self.recognition_window}s")
        
        recognition_count = 0
        correct_count = 0
        trial_results = {}
        
        # 🔑 关键：使用真实时间，而不是程序循环时间
        start_real_time = time.time()
        update_interval = 0.02  # 20ms更新间隔
        window_duration = self.recognition_window  # 🔑 使用对象的窗口参数
        if hasattr(self, 'subject_num') and self.subject_num <= 15:
            char_duration = 3.0  # 1-15号被试: 0.5s+2s+0.5s = 3s
        else:
            char_duration = 4.0  # 16-70号被试: 0.5s+3s+0.5s = 4s
        
        while True:
            # 🔑 关键修复：获取真实流逝的时间
            current_time = time.time() - start_real_time
            
            if current_time >= duration:
                break
            
            # 🔑 关键：模拟真实数据流 - 数据连续不断地以250Hz采集
            self.simulate_data_streaming(current_time)
            
            # 🔑 确定当前属于哪个字符
            current_char_idx = int(current_time / char_duration)
            
            if current_char_idx >= len(self.beta_standard_chars):
                break
            
            # 🔑 计算当前字符的时间范围
            char_start_time = current_char_idx * char_duration
            char_end_time = char_start_time + char_duration
            
   
            # 计算字符内的相对时间
            char_relative_time = current_time - char_start_time
            cue_duration = 0.5  # 提示时间
            physiological_delay = 0.13  # 生理延迟
            recognition_start_offset = cue_duration + physiological_delay  # 0.63秒

            # 🔑 修改：根据Subject动态设置识别结束时间
            if hasattr(self, 'subject_num') and self.subject_num <= 15:
                flicker_duration = 2.0  # 1-15号被试：2秒闪烁
            else:
                flicker_duration = 3.0  # 16-70号被试：3秒闪烁

            recognition_end_offset = cue_duration + flicker_duration  # 动态计算结束时间

            # 只在有效识别窗口内进行识别
            if (char_start_time <= current_time <= char_end_time and 
                recognition_start_offset <= char_relative_time <= recognition_end_offset):
                
          
                # 窗口结束时间是当前时间
                window_end_time = current_time
                window_start_time = window_end_time - window_duration

                # 🔑 确保窗口不早于识别开始时间
                recognition_absolute_start = char_start_time + recognition_start_offset
                if window_start_time < recognition_absolute_start:
                    window_start_time = recognition_absolute_start
                
                # 🔑 转换为样本索引
                window_start_sample = int(window_start_time * self.Fs)
                window_end_sample = int(window_end_time * self.Fs)
                
                # 🔑 检查是否有足够的数据（至少0.5秒的数据）
                # 🔑 检查是否有足够的数据（根据窗口大小动态调整）
                min_samples = int(max(0.2, window_duration * 0.8) * self.Fs)  # 至少窗口的80%或0.2s  # 至少125个样本
                expected_samples = window_end_sample - window_start_sample
                
                if (window_end_sample <= self.received_samples and 
                    expected_samples >= min_samples):
                    
                    # 提取窗口数据
                    data_window = self.streaming_buffer[:, window_start_sample:window_end_sample]
                    
                   
                    if data_window.shape[1] >= min_samples:
                        
                    
                        all_scores = self.calculate_tlcca_scores_for_all_chars(data_window)
                        
                        # 选择最高分数的字符
                        best_idx = np.argmax(all_scores)
                        predicted_char = self.beta_standard_chars[best_idx]
                        target_char = self.beta_standard_chars[current_char_idx]
                        # 计算字符相对时间
                        char_relative_time = current_time - char_start_time
                        actual_window_duration = data_window.shape[1] / self.Fs
                        
                        is_correct = predicted_char.lower() == target_char.lower()
                        
                        # 记录结果
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
                        
                        # 显示识别状态
                        status = "✅" if is_correct else "❌"
                        
                        print(f"🚀 Time{current_time:5.2f}s | Samples{self.received_samples} | "
                            f"Char{current_char_idx}('{target_char}') | Window[{window_start_time:.2f}-{window_end_time:.2f}] | "
                            f"Relative{char_relative_time:.3f}s | Window{actual_window_duration:.2f}s | Pred:'{predicted_char}' | {status}")
            
            # 🔑 关键：严格按20ms间隔更新
            time.sleep(update_interval)

        
        # 最终统计
        print("\n" + "="*60)
        print("📊 Recognition statistics")
        print("="*60)
        
        for trial_idx, stats in trial_results.items():
            final_pred = max(set(stats['predictions']), key=stats['predictions'].count)
            acc = stats['correct'] / stats['total'] * 100
            final_correct = "✅" if final_pred == stats['target'] else "❌"
            print(f"Trial {trial_idx:2d}: '{stats['target']}' -> '{final_pred}' ({acc:5.1f}%) {final_correct}")
        
        overall_acc = (correct_count / recognition_count * 100) if recognition_count > 0 else 0
        trial_acc = sum(1 for s in trial_results.values() 
                    if max(set(s['predictions']), key=s['predictions'].count) == s['target']) / len(trial_results) * 100
        
        print(f"\n🎯 Final results:")
        print(f"   Per-trial accuracy: {trial_acc:.1f}%")
        print(f"   Real-time accuracy: {overall_acc:.1f}%")
        print(f"   Recognition count: {recognition_count}")
        print(f"   平均每CharRecognition count: {recognition_count/len(trial_results):.1f}")
        
        return trial_results



    # [EN] calculate_tlcca_scores_for_all_chars: Auto-generated summary of this method's purpose.



    def calculate_tlcca_scores_for_all_chars(self, eeg_window):
        """计算所有字符的TLCCA分数 - 与tlcca beta.py逻辑一致"""
        
        # 数据预处理 - 50Hz滤波
        try:
            processed_window = np.zeros_like(eeg_window)
            
            # 构建与训练时相同的多次谐波陷波滤波器
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
        
        # 对所有字符计算分数
        all_scores = []
        
        for char_idx in range(len(self.beta_standard_chars)):
            # 找到字符的重排序位置
            reordered_pos = None
            for pos, orig_idx in enumerate(self.target_order):
                if orig_idx == char_idx:
                    reordered_pos = pos
                    break
            
            if reordered_pos is None:
                all_scores.append(0.0)
                continue
            
            # 获取频率和相位
            freq = self.sti_f[reordered_pos]
            phase = self.pha_val[reordered_pos]
            Y1 = self.generate_reference_signals(freq, phase, eeg_window.shape[1])
            
            total_score = 0.0
            
            # 对每个子频带计算
            for sub_band in range(1, self.num_of_subbands + 1):
                X_filtered = self.apply_subband_filter(eeg_window, sub_band)
                
                # 计算单个字符在当前子频带的分数
                rho_i = self.calculate_single_char_score(X_filtered, Y1, reordered_pos, sub_band)
                
                # 论文公式11：加权求和
                fb_weight = self.FB_coef[sub_band-1]
                total_score += fb_weight * rho_i
            
            all_scores.append(total_score)
        
        return all_scores

    # [EN] calculate_single_char_score: Auto-generated summary of this method's purpose.

    def calculate_single_char_score(self, X_filtered, Y1, reordered_pos, sub_band):
        """计算单个字符在单个子频带的分数"""
        
        wx_source_key = f'Wx_source_band{sub_band}'
        wy_source_key = f'Wy_source_band{sub_band}'  
        wx_transfer_key = f'Wx_transfer_band{sub_band}'
        templates_transfer_key = f'templates_transfer_band{sub_band}'

        r1a = r1b = r3 = 0.0

        # 检查是否为源域字符
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

        # 论文公式10：三个分量
        if reordered_pos in self.source_freq_idx and source_domain_idx is not None:
            # 源域字符：使用源域权重
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
            
            r1b = 0.0  # 源域字符没有第二分量
            
        elif reordered_pos in self.target_freq_idx and target_domain_idx is not None:
            r1a = 0.0  # 目标域字符没有第一分量
            
            # 目标域字符：使用传递学习权重
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

        # 第三分量：CCA计算
        if reordered_pos in self.source_freq_idx and source_domain_idx is not None:
            if wx_source_key in self.online_weights:
                try:
                    W1_x = self.online_weights[wx_source_key][:, source_domain_idx]
                    if np.any(W1_x != 0):
                        try:
                            # 完整CCA计算
                            filtered_test_signal = W1_x.T @ X_filtered
                            filtered_test_reshaped = filtered_test_signal.reshape(-1, 1)
                            ref1_reshaped = Y1.T
                            
                            A1, B1 = self.matlab_canoncorr_exact(filtered_test_reshaped, ref1_reshaped)
                            proj1 = filtered_test_reshaped @ A1.reshape(-1, 1)
                            proj2 = ref1_reshaped @ B1.reshape(-1, 1)
                            r3 = self.calculate_correlation(proj1.flatten(), proj2.flatten())
                        except:
                            # 备用方案：简单相关性
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
                            # 完整CCA计算
                            filtered_test_signal = W1_x.T @ X_filtered
                            filtered_test_reshaped = filtered_test_signal.reshape(-1, 1)
                            ref1_reshaped = Y1.T
                            
                            A1, B1 = self.matlab_canoncorr_exact(filtered_test_reshaped, ref1_reshaped)
                            proj1 = filtered_test_reshaped @ A1.reshape(-1, 1)
                            proj2 = ref1_reshaped @ B1.reshape(-1, 1)
                            r3 = self.calculate_correlation(proj1.flatten(), proj2.flatten())
                        except:
                            # 备用方案：简单相关性
                            min_len = min(len(filtered_test_signal), Y1.shape[1])
                            r3 = self.calculate_correlation(
                                filtered_test_signal[:min_len], 
                                Y1[0, :min_len]
                            )
                except Exception as e:
                    r3 = 0.0

        # 论文公式10：ρi = Σ(sign(ri,m) * ri,m^2)
        rho_i = (np.sign(r1a) * r1a**2 + np.sign(r1b) * r1b**2 + np.sign(r3) * r3**2)
        
        return rho_i
    # [EN] precise_sleep_until: Auto-generated summary of this method's purpose.
    def precise_sleep_until(self, target_time):
        """高精度睡眠直到目标时间"""
        while True:
            current = time.time()
            remaining = target_time - current
            if remaining <= 0:
                break
            if remaining > 0.001:
                time.sleep(remaining - 0.001)
            else:
                time.sleep(0.0001)  # 100微秒精度

# [EN] main: Auto-generated summary of this method's purpose.

def main():
    """简化的主函数 - 支持GUI调用"""
    # 这个函数现在主要用于独立测试
    # GUI调用时会直接实例化类并调用相应方法
    pass

# 为GUI提供的便捷创建函数
# [EN] create_for_gui: Auto-generated summary of this method's purpose.
def create_for_gui(subject_num, test_block, recognition_window):
    """为GUI创建识别器实例"""
    recognizer = TLCCAOnlineRecognition(
        subject_num=subject_num,
        test_block=test_block,
        recognition_window=recognition_window,
        gui_mode=True
    )
    return recognizer


if __name__ == "__main__":
    main()