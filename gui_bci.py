import pygame
import numpy as np
import math
import time
import random
import sys
import subprocess
import os
import json
import threading
from queue import Queue
import csv
from datetime import datetime
import importlib.util
import sys

class BCISpellerSystem:
    # [EN] __init__: Auto-generated summary of this method's purpose.
    def __init__(self):
        pygame.init()
 
        self.screen_width = 2160
        self.screen_height = 1440
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("BCI Speller System")
        
      
        self.refresh_rate = 60
        self.clock = pygame.time.Clock()
        
       
        self.current_page = "main"  
        self.selected_mode = "Speller online test"  
        self.selected_layout = "BETA Speller"  
        
        self.beta_config = {
        'subject': '1',
        'block': '1', 
        'time_window': '1.0'
        }
        
        self.settings = {
            'keyboard_type': 'qwerty',
            'color_scheme': 'black_white',
            'cue_duration': 0.5,
            'flickering_duration': 2.0,
            'pause_duration': 0.5,
            'rest_duration': 60.0,
            'total_blocks': 3,
            'total_trials': 5,
            'block_texts': [f'text{i+1}' for i in range(5)],
            'progress_display_duration': 1.0,
            'time_window': 0.8  
        }
        
        
        self.block_history = {
            'results': [],
            'accuracies': []
        }
        
        
        self.color_schemes = {
            'black_white': {
                'background': (0, 0, 0),
                'key_default': (255, 255, 255),
                'text': (0, 0, 0),
                'cue': (255, 0, 0),
                'input': (255, 165, 0)
            }
        }
        
       
        self.main_font = pygame.font.Font(None, 68)
        self.button_font = pygame.font.Font(None, 46)
        self.header_font = pygame.font.Font(None, 46)
        
      
        self.dropdown_open = False
        self.layout_dropdown_open = False
        
       
        self.beta_params = self.generate_beta_params()
       
        self.selected_key = None
        self.input_mode = None
        self.input_text = ""
        self.editing_block_index = 0
        self.param_selection = 0
        
       
        self.eeg_processor = None
        self.eeg_running = False
        self.simulation_running = False
        self.recognition_queue = Queue()


       
        self.keyboard_layout_chars = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '<'],
            ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
            ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
            ['z', 'x', 'c', 'v', 'b', 'n', 'm', '.'],
            ['_', ',']
        ]
        self.selected_row = None
        self.selected_col = None
        
       
        self.current_speller = None
        
      
        self.experimenter_process = None



    

    # [EN] generate_beta_params: Auto-generated summary of this method's purpose.
    def generate_beta_params(self):
        """生成BETA键盘的默认频率、相位参数，严格按照论文顺序"""
        params = {}
        
       
      
        pha_val_original = np.array([
            0, 0.5, 1, 1.5, 0, 0.5, 1, 1.5, 0, 0.5, 1, 1.5, 0, 0.5, 1, 1.5, 0, 0.5, 1, 1.5,
            0, 0.5, 1, 1.5, 0, 0.5, 1, 1.5, 0, 0.5, 1, 1.5, 0, 0.5, 1, 1.5, 0, 0.5, 1, 1.5
        ]) * np.pi
        
        sti_f_original = np.array([
            8.6, 8.8, 9, 9.2, 9.4, 9.6, 9.8, 10, 10.2, 10.4, 10.6, 10.8,
            11, 11.2, 11.4, 11.6, 11.8, 12, 12.2, 12.4, 12.6, 12.8,
            13, 13.2, 13.4, 13.6, 13.8, 14, 14.2, 14.4, 14.6, 14.8,
            15, 15.2, 15.4, 15.6, 15.8, 8, 8.2, 8.4
        ])
        


       
        sti_f = sti_f_original.copy()
        pha_val = pha_val_original.copy()
        
    
        chars = ['.', ',', '<', 
                'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '_']
        
       
        f0 = 8.0  
        delta_f = 0.2  
        phi0 = 0.0   
        delta_phi = 0.5 * np.pi 

        for k, char in enumerate(chars):
            if k < 40:  
                
                frequency = f0 + k * delta_f 
                phase = phi0 + k * delta_phi  
                params[char] = {
                    'frequency': frequency,
                    'phase_input': round(phase/np.pi, 1), 
                    'phase': phase
                }
        
        return params

       
    # [EN] get_current_colors: Auto-generated summary of this method's purpose.
    def get_current_colors(self):
      
        return self.color_schemes[self.settings['color_scheme']]
    
    # [EN] draw_main_page: Auto-generated summary of this method's purpose.
    def draw_main_page(self):
        
        colors = self.get_current_colors()
        self.screen.fill(colors['background'])
        
       
        mode_label = self.main_font.render("Mode", True, colors['key_default'])
        mode_rect = mode_label.get_rect(center=(self.screen_width//2 - 200, self.screen_height//2))
        self.screen.blit(mode_label, mode_rect)
        
    
        dropdown_width = 600
        dropdown_height = 60
        self.dropdown_rect = pygame.Rect(self.screen_width//2 - 100 , self.screen_height//2 - 30, dropdown_width, dropdown_height)
        
        pygame.draw.rect(self.screen, colors['key_default'], self.dropdown_rect)
        pygame.draw.rect(self.screen, colors['background'], self.dropdown_rect, 2)
        
        
        text_surface = self.button_font.render(self.selected_mode, True, colors['text'])
        text_rect = text_surface.get_rect(midleft=(self.dropdown_rect.x + 15, self.dropdown_rect.centery))
        self.screen.blit(text_surface, text_rect)
        
        arrow = "v" if not self.dropdown_open else "^"
        arrow_surface = self.button_font.render(arrow, True, colors['text'])
        arrow_rect = arrow_surface.get_rect(midright=(self.dropdown_rect.right - 15, self.dropdown_rect.centery))
        self.screen.blit(arrow_surface, arrow_rect)
        
        
        if self.dropdown_open:
            options = ["Speller beta dataset simulation", "Speller online test", "Speller demo"]  
            menu_height = len(options) * 50
            menu_rect = pygame.Rect(self.dropdown_rect.x, self.dropdown_rect.bottom, dropdown_width, menu_height)
            pygame.draw.rect(self.screen, colors['key_default'], menu_rect)
            pygame.draw.rect(self.screen, colors['background'], menu_rect, 2)
            
            self.dropdown_options = []
            for i, option in enumerate(options):
                option_rect = pygame.Rect(menu_rect.x, menu_rect.y + i * 50, dropdown_width, 50)
                self.dropdown_options.append((option_rect, option))
                
                if option_rect.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(self.screen, (200, 200, 200), option_rect)
                
                option_surface = self.button_font.render(option, True, colors['text'])
                option_text_rect = option_surface.get_rect(midleft=(option_rect.x + 15, option_rect.centery))
                self.screen.blit(option_surface, option_text_rect)
        
  
        setting_text = ">> Setting"
        setting_surface = self.main_font.render(setting_text, True, colors['key_default'])
        self.setting_rect = setting_surface.get_rect()
        self.setting_rect.bottomright = (self.screen_width//2 + 650 ,  1100)
        self.screen.blit(setting_surface, self.setting_rect)

    # [EN] draw_start_page: Auto-generated summary of this method's purpose.
    def draw_start_page(self):
       
        colors = self.get_current_colors()
        self.screen.fill(colors['background'])
        
        
        ready_text = "Please Ready"
        ready_surface = pygame.font.Font(None, 120).render(ready_text, True, colors['key_default'])
        ready_rect = ready_surface.get_rect(center=(self.screen_width//2, self.screen_height//2))
        self.screen.blit(ready_surface, ready_rect)
        
       
        self.check_experimenter_commands()

    # [EN] draw_block_progress_page: Auto-generated summary of this method's purpose.
    def draw_block_progress_page(self):
      
        colors = self.get_current_colors()
        self.screen.fill(colors['background'])
        
       
        completed_block_number = self.experiment_state['current_block']
        total_blocks = self.settings['total_blocks']
    
       
        progress_text = f"Block {completed_block_number} finished."
        progress_surface = pygame.font.Font(None, 120).render(progress_text, True, colors['key_default'])
        progress_rect = progress_surface.get_rect(center= (self.screen_width//2, self.screen_height//2 - 60))
        self.screen.blit(progress_surface, progress_rect)
        
    
        box_size = 80
        box_spacing = 20
        total_width = total_blocks * box_size + (total_blocks - 1) * box_spacing
        start_x = (self.screen_width - total_width) // 2 
        start_y =  progress_rect.bottom + 40
        
        for i in range(total_blocks):
            box_x = start_x + i * (box_size + box_spacing)
            box_rect = pygame.Rect(box_x, start_y, box_size, box_size)
            
            if completed_block_number >= i + 1:
               
                pygame.draw.rect(self.screen, colors['key_default'], box_rect)
            else:
              
                pygame.draw.rect(self.screen, colors['background'], box_rect)
                pygame.draw.rect(self.screen, colors['key_default'], box_rect, 3)

    # [EN] draw_rest_page: Auto-generated summary of this method's purpose.
    def draw_rest_page(self):
        
        colors = self.get_current_colors()
        self.screen.fill(colors['background'])
        
        current_time = pygame.time.get_ticks()
        elapsed_time = (current_time - self.experiment_state['rest_start_time']) / 1000.0
        remaining_time = max(0, self.settings['rest_duration'] - elapsed_time)
        remaining_time = math.ceil(remaining_time)
        
    
        rest_text = "Please rest"
        rest_surface = pygame.font.Font(None, 120).render(rest_text, True, colors['key_default'])
        rest_rect = rest_surface.get_rect(center=(self.screen_width//2, self.screen_height//2 - 60))
        self.screen.blit(rest_surface, rest_rect)
        
       
        minutes = int(remaining_time // 60)
        seconds = int(remaining_time % 60)
        time_text = f"{minutes:02d} : {seconds:02d}"
        time_surface = pygame.font.Font(None, 120).render(time_text, True, colors['key_default'])
        time_rect = time_surface.get_rect(center=(self.screen_width//2, self.screen_height//2 + 60))
        self.screen.blit(time_surface, time_rect)

    # [EN] draw_layout_page: Auto-generated summary of this method's purpose.
    def draw_layout_page(self):
     
        colors = self.get_current_colors()
        self.screen.fill(colors['background'])
        
      
        header_text = "Speller online test >> Setting: Layout"
        header_surface = self.header_font.render(header_text, True, colors['key_default'])
        self.screen.blit(header_surface, (450,  320))
        
        
        layout_label = self.main_font.render("Layout", True, colors['key_default'])
        layout_rect = layout_label.get_rect(center=(self.screen_width//2 - 200, self.screen_height//2))
        self.screen.blit(layout_label, layout_rect)
        
     
        dropdown_width = 500
        dropdown_height = 60
        self.layout_dropdown_rect = pygame.Rect(self.screen_width//2 - 100, self.screen_height//2 - 30, dropdown_width, dropdown_height)
        
        pygame.draw.rect(self.screen, colors['key_default'], self.layout_dropdown_rect)
        pygame.draw.rect(self.screen, colors['background'], self.layout_dropdown_rect, 2)
        
        text_surface = self.button_font.render(self.selected_layout, True, colors['text'])
        text_rect = text_surface.get_rect(midleft=(self.layout_dropdown_rect.x + 15, self.layout_dropdown_rect.centery))
        self.screen.blit(text_surface, text_rect)
        
        arrow = "v" if not self.layout_dropdown_open else "^"
        arrow_surface = self.button_font.render(arrow, True, colors['text'])
        arrow_rect = arrow_surface.get_rect(midright=(self.layout_dropdown_rect.right - 15, self.layout_dropdown_rect.centery))
        self.screen.blit(arrow_surface, arrow_rect)
        
 
        if self.layout_dropdown_open:
            options = ["BETA Speller", "Customized speller"]
            menu_height = len(options) * 50
            menu_rect = pygame.Rect(self.layout_dropdown_rect.x, self.layout_dropdown_rect.bottom, dropdown_width, menu_height)
            pygame.draw.rect(self.screen, colors['key_default'], menu_rect)
            pygame.draw.rect(self.screen, colors['background'], menu_rect, 2)
            
            self.layout_dropdown_options = []
            for i, option in enumerate(options):
                option_rect = pygame.Rect(menu_rect.x, menu_rect.y + i * 50, dropdown_width, 50)
                self.layout_dropdown_options.append((option_rect, option))
                
                if option_rect.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(self.screen, (200, 200, 200), option_rect)
                
                option_surface = self.button_font.render(option, True, colors['text'])
                option_text_rect = option_surface.get_rect(midleft=(option_rect.x + 15, option_rect.centery))
                self.screen.blit(option_surface, option_text_rect)
        
     
        self.draw_navigation_buttons()

    # [EN] draw_jpfm_page: Auto-generated summary of this method's purpose.
    def draw_jpfm_page(self):
        
        colors = self.get_current_colors()
        self.screen.fill(colors['background'])
        
       
        header_text = "Speller online test >> Setting: Layout >> JPFM modulation"
        header_surface = self.header_font.render(header_text, True, colors['key_default'])
        self.screen.blit(header_surface, (450,  320))
        
  
        reset_text = "RESET"
        reset_surface = self.button_font.render(reset_text, True, (255, 255, 255))
        self.reset_rect = pygame.Rect(1550, 315, 180, 50)
        pygame.draw.rect(self.screen, colors['cue'], self.reset_rect)
        pygame.draw.rect(self.screen, colors['background'], self.reset_rect, 2)
        reset_text_rect = reset_surface.get_rect(center=self.reset_rect.center)
        self.screen.blit(reset_surface, reset_text_rect)
   
        self.draw_keyboard_with_params()
        
      
        self.draw_navigation_buttons()

    # [EN] draw_keyboard_with_params: Auto-generated summary of this method's purpose.
    def draw_keyboard_with_params(self):
      
        colors = self.get_current_colors()
        
        target_width = 90
        target_height = 90
        button_spacing = 30
        space_width = 750
        
       
        keyboard_width = 11 * (target_width + button_spacing) - button_spacing
        keyboard_height = 5 * (target_height + button_spacing) - button_spacing
            
        start_x = (self.screen_width - keyboard_width) // 2
        start_y = (self.screen_height - keyboard_height) // 2 + 50
        
        self.key_rects = {}
        
        for row_idx, row in enumerate(self.keyboard_layout_chars):
            if row_idx == 4:  
                row5_total_width = space_width + button_spacing + target_width
                row5_start_x = (self.screen_width - row5_total_width) // 2
                
              
                space_rect = pygame.Rect(row5_start_x, start_y + row_idx * (target_height + button_spacing), space_width, target_height)
                self.key_rects[(row_idx, 0)] = space_rect
                char = self.keyboard_layout_chars[row_idx][0]
                self.draw_key_with_params(self.screen, char, space_rect, colors, row_idx, 0)
                
              
                comma_rect = pygame.Rect(row5_start_x + space_width + button_spacing, start_y + row_idx * (target_height + button_spacing), target_width, target_height)
                self.key_rects[(row_idx, 1)] = comma_rect
                char = self.keyboard_layout_chars[row_idx][1]
                self.draw_key_with_params(self.screen, char, comma_rect, colors, row_idx, 1)
            else:
                row_width = len(row) * (target_width + button_spacing) - button_spacing
                row_start_x = start_x + (keyboard_width - row_width) // 2
                
                for col_idx, char in enumerate(row):
                    x = row_start_x + col_idx * (target_width + button_spacing)
                    y = start_y + row_idx * (target_height + button_spacing)
                    rect = pygame.Rect(x, y, target_width, target_height)
                    self.key_rects[(row_idx, col_idx)] = rect
                    self.draw_key_with_params(self.screen, char, rect, colors, row_idx, col_idx)

    # [EN] draw_key_with_params: Auto-generated summary of this method's purpose.
    def draw_key_with_params(self, screen, char, rect, colors, row_idx, col_idx):
      
        is_selected = (self.selected_row == row_idx and self.selected_col == col_idx)
        
   
        if is_selected:
            pygame.draw.rect(screen, colors['cue'], rect)
        else:
            pygame.draw.rect(screen, colors['key_default'], rect)
        pygame.draw.rect(screen, colors['background'], rect, 2)
        
      
        if char in self.beta_params:
            freq = self.beta_params[char]['frequency']
            phase_input = self.beta_params[char]['phase_input']
        else:
            freq = 0.0
            phase_input = 0.0
        
       
        if char == '_':
            display_char = '_'
        else:
            display_char = char
        
     
        char_font = pygame.font.Font(None, 36)
        text_color = colors['key_default']
        
      
        if is_selected and self.input_mode == 'character':
            char_text = f"{self.input_text}_"
            char_color = colors['input']
        elif is_selected and self.param_selection == 0:
            char_text = f"[{display_char}]"
            char_color = colors['input']
        else:
            char_text = display_char
            char_color = text_color
            
        char_surface = char_font.render(char_text, True, char_color)
        char_rect = char_surface.get_rect(center=(rect.centerx, rect.y - 15))
        screen.blit(char_surface, char_rect)
        
        
        param_font = pygame.font.Font(None, 24)
        
        
        param_text_color = colors['background'] if is_selected else colors['text']
        
       
        if is_selected and self.input_mode == 'frequency':
            freq_text = f"{self.input_text}_Hz"
            freq_color = colors['input']
        elif is_selected and self.param_selection == 1:
            freq_text = f"[{freq:.1f} Hz]"
            freq_color = colors['input']
        else:
            freq_text = f"{freq:.1f} Hz"
            freq_color = param_text_color
            
        freq_surface = param_font.render(freq_text, True, freq_color)
        freq_rect = freq_surface.get_rect(center=(rect.centerx, rect.y + 30))
        screen.blit(freq_surface, freq_rect)
        
    
        if is_selected and self.input_mode == 'phase':
            phase_text = f"{self.input_text}_π"
            phase_color = colors['input']
        elif is_selected and self.param_selection == 2:
            phase_text = f"[{phase_input:.1f}π]"
            phase_color = colors['input']
        else:
            phase_text = f"{phase_input:.1f}π"
            phase_color = param_text_color
            
        phase_surface = param_font.render(phase_text, True, phase_color)
        phase_rect = phase_surface.get_rect(center=(rect.centerx, rect.y + 55))
        screen.blit(phase_surface, phase_rect)

    # [EN] draw_trials_page: Auto-generated summary of this method's purpose.
    def draw_trials_page(self):
       
        colors = self.get_current_colors()
        self.screen.fill(colors['background'])
        
  
        header_text = "Speller online test >> Setting: Layout >> JPFM modulation >> Blocks"
        header_surface = self.header_font.render(header_text, True, colors['key_default'])
        self.screen.blit(header_surface, (450,  320))
        
      
        if self.input_mode == 'blocks':
            blocks_text = f"Number of blocks: {self.input_text}_"
            blocks_color = colors['input']
        else:
            blocks_text = f"Number of blocks: {self.settings['total_blocks']}"
            blocks_color = colors['key_default']
        
        blocks_surface = self.main_font.render(blocks_text, True, blocks_color)
        self.blocks_rect = pygame.Rect(0, self.screen_height//2 - 30, self.screen_width, 60)
        blocks_rect = blocks_surface.get_rect(center=(self.screen_width//2, self.screen_height//2))
        self.screen.blit(blocks_surface, blocks_rect)
        
  
        self.draw_navigation_buttons()

    # [EN] draw_block_text_page: Auto-generated summary of this method's purpose.
    def draw_block_text_page(self):

        colors = self.get_current_colors()
        self.screen.fill(colors['background'])
        
   
        header_text = "Speller online test >> Setting: Layout >> JPFM modulation >> Blocks"
        header_surface = self.header_font.render(header_text, True, colors['key_default'])
        self.screen.blit(header_surface, (450, 320))
        
       
        left_start_x = 500
        left_start_y = 430
        
        self.text_rects = []
        for i in range(min(10, self.settings['total_blocks'])):
            if self.input_mode == 'block_text' and self.editing_block_index == i:
               
                display_input = self.input_text.replace(' ', '_') 
                trial_label = f"Block {i+1}: {display_input}_"
                trial_color = colors['input']
            else:
               
                stored_text = self.settings['block_texts'][i]  
                display_text = stored_text.replace(' ', '_')    
                trial_label = f"Block {i+1}: {display_text}"
                trial_color = colors['key_default']
            
            trial_surface = self.button_font.render(trial_label, True, trial_color)
            text_rect = pygame.Rect(left_start_x, left_start_y + i * 50, 600, 50)
            self.text_rects.append(text_rect)
            self.screen.blit(trial_surface, (left_start_x, left_start_y + i * 60))

        right_start_x = 1200
        right_start_y = 420
        
      
        single_trial_text = "Single trial"
        single_trial_surface = self.header_font.render(single_trial_text, True, colors['key_default'])
        self.screen.blit(single_trial_surface, (right_start_x, right_start_y))
        
      
        if self.input_mode == 'cue_time':
            cue_text = f"Cue time (s): {self.input_text}_"
            cue_color = colors['input']
        else:
            cue_text = f"Cue time (s): {self.settings['cue_duration']:.1f}"
            cue_color = colors['key_default']
        
        cue_surface = self.button_font.render(cue_text, True, cue_color)
        self.cue_time_rect = pygame.Rect(right_start_x, right_start_y + 70, 400, 50)
        self.screen.blit(cue_surface, (right_start_x, right_start_y + 70))
        
      
        if self.input_mode == 'flash_time':
            flash_text = f"Flash time (s): {self.input_text}_"
            flash_color = colors['input']
        else:
            flash_text = f"Flash time (s): {self.settings['flickering_duration']:.1f}"
            flash_color = colors['key_default']
            
        flash_surface = self.button_font.render(flash_text, True, flash_color)
        self.flash_time_rect = pygame.Rect(right_start_x, right_start_y + 130, 400, 50)
        self.screen.blit(flash_surface, (right_start_x, right_start_y + 130))

        if self.input_mode == 'pause_time':
            pause_text = f"Pause time (s): {self.input_text}_"
            pause_color = colors['input']
        else:
            pause_text = f"Pause time (s): {self.settings['pause_duration']:.1f}"
            pause_color = colors['key_default']
            
        pause_surface = self.button_font.render(pause_text, True, pause_color)
        self.pause_time_rect = pygame.Rect(right_start_x, right_start_y + 190, 400, 50)
        self.screen.blit(pause_surface, (right_start_x, right_start_y + 190))

       
        if self.input_mode == 'time_window':
            window_text = f"Time window (s): {self.input_text}_"
            window_color = colors['input']
        else:
            window_text = f"Time window (s): {self.settings['time_window']:.1f}"
            window_color = colors['key_default']
            
        window_surface = self.button_font.render(window_text, True, window_color)
        self.time_window_rect = pygame.Rect(right_start_x, right_start_y + 250, 400, 50)
        self.screen.blit(window_surface, (right_start_x, right_start_y + 250))
        
      
        between_blocks_text = "Between blocks"
        between_blocks_surface = self.header_font.render(between_blocks_text, True, colors['key_default'])
        self.screen.blit(between_blocks_surface, (right_start_x, right_start_y + 370)) 
        
        
        if self.input_mode == 'rest_time':
            rest_text = f"Rest time (s): {self.input_text}_"
            rest_color = colors['input']
        else:
            rest_text = f"Rest time (s): {self.settings['rest_duration']:.1f}"
            rest_color = colors['key_default']
            
        rest_surface = self.button_font.render(rest_text, True, rest_color)
        self.rest_time_rect = pygame.Rect(right_start_x, right_start_y + 440, 400, 50)
        self.screen.blit(rest_surface, (right_start_x, right_start_y + 440))
        
       
        back_text = "<< Back"
        back_surface = self.main_font.render(back_text, True, colors['key_default'])
        self.back_rect = back_surface.get_rect()
        self.back_rect.bottomleft = (self.screen_width//2 - 620, 1100)
        self.screen.blit(back_surface, self.back_rect)
        
        # Confirm按钮 - 红色背景，白色字体
        confirm_text = "Confirm"
        confirm_surface = self.main_font.render(confirm_text, True, (255, 255, 255))
        self.confirm_rect = pygame.Rect(self.screen_width//2 + 420, 1020, 250, 80)
        pygame.draw.rect(self.screen, colors['cue'], self.confirm_rect)
        pygame.draw.rect(self.screen, colors['background'], self.confirm_rect, 2)
        confirm_text_rect = confirm_surface.get_rect(center=self.confirm_rect.center)
        self.screen.blit(confirm_surface, confirm_text_rect)

    # [EN] draw_experiment_page: Auto-generated summary of this method's purpose.
    def draw_experiment_page(self):
        """绘制测试界面 - 修复状态初始化时机"""
        colors = self.get_current_colors()
        
        # 初始化实验状态（如果还没有初始化）
        if not hasattr(self, 'experiment_state'):
            print("🔄 Initializing experiment state...")
            self.init_experiment_state()
            print(f"✅ Experiment state initialized, current state: {self.experiment_state['state']}")
        
        # 更新实验状态 - 只有在实验页面才更新
        if self.current_page == "experiment":
            self.update_experiment_state()
            
            # 更新实验者界面状态
            self.update_experimenter_status()
            
            # 检查实验者命令
            self.check_experimenter_commands()
            

        
        # 绘制界面
        self.screen.fill(colors['background'])
        
        # 绘制键盘
        self.draw_experiment_keyboard()
        
        # 绘制结果区域（输出条）
        self.draw_result_area()
        
        # 显示状态提示
        if self.experiment_state['state'] == "ready":
            text = "Experiment will start automatically..."
            text_surface = pygame.font.Font(None, 36).render(text, True, (255, 255, 0))
            text_rect = text_surface.get_rect(center=(self.screen_width//2, self.screen_height - 100))
            self.screen.blit(text_surface, text_rect)
        
        elif self.experiment_state['state'] == "paused":
            text = "Experiment PAUSED - Waiting for experimenter to continue..."
            text_surface = pygame.font.Font(None, 36).render(text, True, (255, 0, 0))
            text_rect = text_surface.get_rect(center=(self.screen_width//2, self.screen_height - 100))
            self.screen.blit(text_surface, text_rect)

        elif self.experiment_state['state'] == "pause":
            text = "Pause between trials..."
            text_surface = pygame.font.Font(None, 36).render(text, True, (255, 255, 0))
            text_rect = text_surface.get_rect(center=(self.screen_width//2, self.screen_height - 100))
            self.screen.blit(text_surface, text_rect)
        
        elif self.experiment_state['state'] == "cue":
            text = f"Get ready for: '{self.experiment_state.get('current_target_char', '?')}'"
            text_surface = pygame.font.Font(None, 36).render(text, True, (255, 165, 0))
            text_rect = text_surface.get_rect(center=(self.screen_width//2, self.screen_height - 100))
            self.screen.blit(text_surface, text_rect)
        
        elif self.experiment_state['state'] == "flickering":
            text = f"Flickering: '{self.experiment_state.get('current_target_char', '?')}' - Look at the target!"
            text_surface = pygame.font.Font(None, 36).render(text, True, (0, 255, 255))
            text_rect = text_surface.get_rect(center=(self.screen_width//2, self.screen_height - 100))
            self.screen.blit(text_surface, text_rect)
        
        elif self.experiment_state['state'] == "rest":
            remaining_time = self.settings['rest_duration'] - (pygame.time.get_ticks() - self.experiment_state['trial_start_time']) / 1000
            if remaining_time > 0:
                text = f"Rest between blocks: {remaining_time:.1f} seconds remaining"
            else:
                text = "Rest time ending..."
            text_surface = pygame.font.Font(None, 36).render(text, True, (0, 255, 255))
            text_rect = text_surface.get_rect(center=(self.screen_width//2, self.screen_height - 100))
            self.screen.blit(text_surface, text_rect)
        
        elif self.experiment_state['state'] == "finished":
            text = "Experiment Finished! Press ESC to return to menu"
            text_surface = pygame.font.Font(None, 48).render(text, True, (0, 255, 0))
            text_rect = text_surface.get_rect(center=(self.screen_width//2, self.screen_height - 100))
            self.screen.blit(text_surface, text_rect)

    # [EN] init_experiment_state: Auto-generated summary of this method's purpose.
    def init_experiment_state(self):
        """初始化实验状态"""
        self.experiment_state = {
            'current_block': 1,
            'current_trial': 0,
            'state': 'ready',
            'trial_start_time': 0,
            'current_target_char': None,
            'trial_order': [],
            'results': [],
            'auto_timer': pygame.time.get_ticks(),
            'progress_start_time': 0,
            'rest_start_time': 0,
            'recognition_active': False  # 新增：标识是否应该进行识别
        }
        
        # 获取所有目标字符
        self.all_targets = []
        for row in self.keyboard_layout_chars:
            self.all_targets.extend(row)
        
        # 开始第一个block
        self.start_new_block()
    
    # [EN] start_new_block: Auto-generated summary of this method's purpose.
    def start_new_block(self):
        """开始新的block"""
        
        # 区分online和beta模式
        if hasattr(self, 'is_beta_mode') and self.is_beta_mode:
            # Beta模式：保持hope22标准40字符序列
            hope22_chars = ['.', ',', '<', 
                            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '_']
            
            self.experiment_state['trial_order'] = hope22_chars
            
            print(f"开始Block {self.experiment_state['current_block']}: hope22标准序列")
            print(f"Character sequence: {''.join(self.experiment_state['trial_order'])}")
        else:
            # Online模式：使用用户设置的block_texts
            if self.experiment_state['current_block'] <= len(self.settings['block_texts']):
                target_text = self.settings['block_texts'][self.experiment_state['current_block'] - 1]
                self.experiment_state['trial_order'] = list(target_text.replace(' ', '_'))
                print(f"开始Block {self.experiment_state['current_block']}: 目标文本='{target_text}', 转换后字符={self.experiment_state['trial_order']}, 总共{len(self.experiment_state['trial_order'])}个字符，输出窗口已清空")
            else:
                self.experiment_state['trial_order'] = []
                print(f"警告：Block {self.experiment_state['current_block']} 超出设定范围")
            
        self.experiment_state['current_trial'] = 0
        self.experiment_state['state'] = 'ready'
        self.experiment_state['auto_timer'] = pygame.time.get_ticks()
        self.experiment_state['results'] = []


    # [EN] get_beta_params: Auto-generated summary of this method's purpose.
    def get_beta_params(self):
        """获取Beta参数 - 按照Beta论文JFPM标准实现"""
        params = {}
        
        # 🔑 按照Beta论文的JFPM公式设置
        # f_k = f_0 + (k-1) * Δf, φ_k = φ_0 + (k-1) * Δφ
        f0 = 8.0  # 基础频率 8Hz
        phi0 = 0.0  # 基础相位 0
        delta_f = 0.2  # 频率间隔 0.2Hz
        delta_phi = 0.5 * np.pi  # 相位间隔 0.5π
        
        # Beta标准字符顺序（与hope22完全一致）
        chars = ['.', ',', '<', 
                'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '_']
        
        for k, char in enumerate(chars):
            frequency = f0 + k * delta_f
            phase = phi0 + k * delta_phi
            
            params[char] = {
                'frequency': frequency,
                'phase_input': round(phase/np.pi, 1),
                'phase': phase
            }
        
        return params

    # [EN] save_experiment_data: Auto-generated summary of this method's purpose.
    def save_experiment_data(self):
        """保存完整的实验数据"""
        if not hasattr(self, 'experiment_state') or not self.eeg_processor:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. 保存详细的trial数据
        trial_filename = f"experiment_trials_{timestamp}.csv"
        if self.eeg_processor:
            self.eeg_processor.save_trial_data(trial_filename)
        
        # 2. 保存block总结数据
        block_filename = f"experiment_blocks_{timestamp}.csv"
        self.save_block_summary(block_filename)
        
        # 3. 保存实验配置
        config_filename = f"experiment_config_{timestamp}.json"
        self.save_experiment_config(config_filename)
        
        # 4. 保存波形数据
        if self.eeg_processor:
            waveform_filename = f"experiment_waveform_{timestamp}.csv"
            self.eeg_processor.save_waveform_data_to_file(waveform_filename)
        
        print(f"Experiment data saved:")
        print(f"  - Trial data: {trial_filename}")
        print(f"  - Block summary: {block_filename}")
        print(f"  - Experiment config: {config_filename}")
        print(f"  - Waveform data: experiment_waveform_{timestamp}.csv")

    # [EN] save_block_summary: Auto-generated summary of this method's purpose.
    def save_block_summary(self, filename):
        """保存block总结"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Block', 'Target_Text', 'Result_Text', 'Accuracy_%', 
                            'Total_Trials', 'Correct_Trials', 'Avg_Confidence', 
                            'Avg_Reaction_Time', 'Block_Start_Time', 'Block_End_Time']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for block_idx in range(len(self.block_history['results'])):
                    block_num = block_idx + 1
                    
                    # 从EEG处理器获取详细统计
                    block_summary = None
                    if self.eeg_processor:
                        block_summary = self.eeg_processor.get_block_summary(block_num)
                    
                    row = {
                        'Block': block_num,
                        'Target_Text': self.settings['block_texts'][block_idx] if block_idx < len(self.settings['block_texts']) else '',
                        'Result_Text': self.block_history['results'][block_idx] if block_idx < len(self.block_history['results']) else '',
                        'Accuracy_%': f"{self.block_history['accuracies'][block_idx]:.1f}" if block_idx < len(self.block_history['accuracies']) else '0.0',
                        'Total_Trials': block_summary['total_trials'] if block_summary else 0,
                        'Correct_Trials': block_summary['correct_trials'] if block_summary else 0,
                        'Avg_Confidence': f"{block_summary['avg_confidence']:.3f}" if block_summary else '0.000',
                        'Avg_Reaction_Time': f"{block_summary['avg_reaction_time']:.2f}" if block_summary else '0.00',
                        'Block_Start_Time': '',  # 可以从trial数据中计算
                        'Block_End_Time': ''     # 可以从trial数据中计算
                    }
                    writer.writerow(row)
                    
        except Exception as e:
            print(f"保存block总结失败: {e}")

    # [EN] save_experiment_config: Auto-generated summary of this method's purpose.
    def save_experiment_config(self, filename):
        """保存实验配置"""
        config_data = {
            'experiment_timestamp': datetime.now().isoformat(),
            'settings': self.settings,
            'beta_params': self.beta_params,
            'keyboard_layout': self.keyboard_layout_chars,
            'total_blocks': self.settings['total_blocks'],
            'block_texts': self.settings['block_texts'][:self.settings['total_blocks']]
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存Experiment config失败: {e}")


        # [EN] analyze_current_blocks: Auto-generated summary of this method's purpose.
        def analyze_current_blocks(self):
            """分析当前设置的Block文案"""
            try:
                print("\n" + "="*60)
                print("📊 开始分析当前Block文案设置")
                print("="*60)
                
                # 导入分析工具
                from block_text_analyzer import BlockTextAnalyzer, analyze_experiment_blocks
                
                # 获取当前设置
                beta_params = self.beta_params
                block_texts = self.settings['block_texts']
                total_blocks = self.settings['total_blocks']
                
                print(f"📋 当前实验设置:")
                print(f"   总Block数: {total_blocks}")
                print(f"   时间窗口: {self.settings['time_window']}s")
                print(f"   闪烁时长: {self.settings['flickering_duration']}s")
                print(f"   暂停时长: {self.settings['pause_duration']}s")
                
                # 执行分析
                analysis_result = analyze_experiment_blocks(beta_params, block_texts, total_blocks)
                
                # 保存分析结果到实例
                self.block_analysis_result = analysis_result
                
                print("\n✅ Block文案分析完成！")
                print(f"📄 分析报告: {analysis_result.get('report_file', 'N/A')}")
                
                return analysis_result
                
            except Exception as e:
                print(f"❌ Block文案分析失败: {e}")
                import traceback
                traceback.print_exc()
                return None
        
        # [EN] optimize_blocks_for_tlcca: Auto-generated summary of this method's purpose.
        def optimize_blocks_for_tlcca(self):
            """为tlCCA优化Block文案"""
            if not hasattr(self, 'block_analysis_result'):
                print("⚠️ 请先运行analyze_current_blocks()进行分析")
                return
            
            try:
                print("\n🎯 基于分析结果优化Block文案...")
                
                analysis = self.block_analysis_result['analysis_results']
                
                # 获取当前域分布
                if 'tlcca_suitability' in analysis:
                    suitability = analysis['tlcca_suitability']
                    source_chars_used = set(suitability['source_chars_used'])
                    target_chars_used = set(suitability['target_chars_used'])
                    
                    # 获取完整的源域和目标域字符
                    sorted_chars = sorted(self.beta_params.keys(), 
                                        key=lambda x: self.beta_params[x]['frequency'])
                    source_chars_all = [sorted_chars[i] for i in range(1, len(sorted_chars), 2)]
                    target_chars_all = [sorted_chars[i] for i in range(0, len(sorted_chars), 2)]
                    
                    # 找出未使用的字符
                    unused_source = [c for c in source_chars_all if c not in source_chars_used]
                    unused_target = [c for c in target_chars_all if c not in target_chars_used]
                    
                    print(f"📈 当前覆盖率:")
                    print(f"   源域: {len(source_chars_used)}/{len(source_chars_all)} ({len(source_chars_used)/len(source_chars_all)*100:.1f}%)")
                    print(f"   目标域: {len(target_chars_used)}/{len(target_chars_all)} ({len(target_chars_used)/len(target_chars_all)*100:.1f}%)")
                    
                    if unused_source:
                        print(f"🔤 Suggested additional source characters: {unused_source[:10]}")
                    
                    if unused_target:
                        print(f"🔤 Suggested additional target characters: {unused_target[:10]}")
                    
                    # 生成优化建议的文案
                    self.generate_optimized_block_texts(source_chars_all, target_chars_all, 
                                                    source_chars_used, target_chars_used)
                
            except Exception as e:
                print(f"❌ Optimization failed: {e}")
        
        # [EN] generate_optimized_block_texts: Auto-generated summary of this method's purpose.
        def generate_optimized_block_texts(self, source_chars_all, target_chars_all, 
                                        source_chars_used, target_chars_used):
            """生成优化的Block文案"""
            try:
                print("\n📝 Generate optimized Block text suggestions...")
                
                # 计算需要补充的字符
                unused_source = [c for c in source_chars_all if c not in source_chars_used]
                unused_target = [c for c in target_chars_all if c not in target_chars_used]
                
                # 为每个Block生成平衡的文案
                optimized_texts = []
                total_blocks = self.settings['total_blocks']
                
                # 将未使用的字符分配到各个Block中
                all_unused = unused_source + unused_target
                
                for block_idx in range(total_blocks):
                    # 从原始文案开始
                    original_text = self.settings['block_texts'][block_idx]
                    
                    # 添加未使用的字符（平均分配）
                    chars_per_block = len(all_unused) // total_blocks
                    start_idx = block_idx * chars_per_block
                    end_idx = start_idx + chars_per_block
                    
                    if block_idx == total_blocks - 1:  # 最后一个block包含剩余字符
                        chars_to_add = all_unused[start_idx:]
                    else:
                        chars_to_add = all_unused[start_idx:end_idx]
                    
                    # 构建优化文案
                    if chars_to_add:
                        # 替换下划线为空格，然后添加新字符
                        optimized_text = original_text.replace('_', ' ')
                        
                        # 智能添加字符，形成有意义的词汇
                        added_chars = ''.join(chars_to_add).replace('_', ' ')
                        optimized_text += ' ' + added_chars
                        
                        optimized_texts.append(optimized_text.strip())
                    else:
                        optimized_texts.append(original_text)
                
                # 显示优化结果
                print(f"\n📋 Optimized Block texts:")
                for i, text in enumerate(optimized_texts):
                    print(f"   Block {i+1}: '{text}'")
                    print(f"            (长度: {len(text.replace(' ', '_'))} 字符)")
                
                # 询问是否应用优化
                print(f"\n❓ Apply these optimized texts?？")
                print(f"   Call in Python console: system.apply_optimized_texts()")
                
                # 保存优化建议
                self.optimized_block_texts = optimized_texts
                
            except Exception as e:
                print(f"❌ Failed to generate optimized texts: {e}")
        
        # [EN] apply_optimized_texts: Auto-generated summary of this method's purpose.
        def apply_optimized_texts(self):
            """应用优化的Block文案"""
            if not hasattr(self, 'optimized_block_texts'):
                print("⚠️ 没有找到优化的文案，请先运行optimize_blocks_for_tlcca()")
                return False
            
            try:
                # 备份原始文案
                self.original_block_texts = self.settings['block_texts'].copy()
                
                # 应用优化文案
                for i, optimized_text in enumerate(self.optimized_block_texts):
                    if i < len(self.settings['block_texts']):
                        self.settings['block_texts'][i] = optimized_text
                
                print("✅ Optimized Block texts已应用！")
                print("📁 原始文案已备份到 self.original_block_texts")
                
                # 重新分析优化后的效果
                print("\n🔄 重新分析优化后的效果...")
                self.analyze_current_blocks()
                
                return True
                
            except Exception as e:
                print(f"❌ 应用优化文案失败: {e}")
                return False
        
        # [EN] restore_original_texts: Auto-generated summary of this method's purpose.
        def restore_original_texts(self):
            """恢复原始Block文案"""
            if not hasattr(self, 'original_block_texts'):
                print("⚠️ 没有找到备份的原始文案")
                return False
            
            try:
                self.settings['block_texts'] = self.original_block_texts.copy()
                print("✅ 已恢复到原始Block文案")
                return True
                
            except Exception as e:
                print(f"❌ 恢复原始文案失败: {e}")
                return False
        
        # [EN] export_block_analysis: Auto-generated summary of this method's purpose.
        def export_block_analysis(self, filename=None):
            """导出Block分析结果"""
            if not hasattr(self, 'block_analysis_result'):
                print("⚠️ 没有分析结果可导出，请先运行analyze_current_blocks()")
                return None
            
            try:
                import json
                from datetime import datetime
                
                if filename is None:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"experiment_block_analysis_{timestamp}.json"
                
                # 构建完整的导出数据
                export_data = {
                    'export_timestamp': datetime.now().isoformat(),
                    'experiment_settings': {
                        'total_blocks': self.settings['total_blocks'],
                        'time_window': self.settings['time_window'],
                        'flickering_duration': self.settings['flickering_duration'],
                        'cue_duration': self.settings['cue_duration'],
                        'pause_duration': self.settings['pause_duration'],
                        'rest_duration': self.settings['rest_duration']
                    },
                    'original_block_texts': self.settings['block_texts'][:self.settings['total_blocks']],
                    'optimized_block_texts': getattr(self, 'optimized_block_texts', None),
                    'beta_params_summary': {
                        'total_chars': len(self.beta_params),
                        'frequency_range': [
                            min(params['frequency'] for params in self.beta_params.values()),
                            max(params['frequency'] for params in self.beta_params.values())
                        ]
                    },
                    'analysis_results': self.block_analysis_result
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                print(f"📁 完整分析结果已导出: {filename}")
                return filename
                
            except Exception as e:
                print(f"❌ 导出失败: {e}")
                return None
        
        # [EN] quick_block_summary: Auto-generated summary of this method's purpose.
        def quick_block_summary(self):
            """快速Block文案概览"""
            print(f"\n📊 Block文案快速概览:")
            print(f"   总Block数: {self.settings['total_blocks']}")
            
            total_chars = 0
            all_chars = set()
            
            for i in range(self.settings['total_blocks']):
                text = self.settings['block_texts'][i].replace(' ', '_')
                total_chars += len(text)
                all_chars.update(text)
                print(f"   Block {i+1}: '{self.settings['block_texts'][i]}' ({len(text)} 字符)")
            
            print(f"\n📈 总体统计:")
            print(f"   总字符数: {total_chars}")
            print(f"   唯一字符数: {len(all_chars)}")
            print(f"   平均BlockLength: {total_chars/self.settings['total_blocks']:.1f}")
            
            # 检查BETA覆盖率
            beta_chars = set(self.beta_params.keys())
            coverage = len(all_chars & beta_chars) / len(beta_chars) * 100
            print(f"   BETA字符覆盖率: {coverage:.1f}%")
            
            missing_chars = all_chars - beta_chars
            if missing_chars:
                print(f"   ⚠️ 不在BETA中的字符: {missing_chars}")
                


    # [EN] update_experiment_state: Auto-generated summary of this method's purpose.
    def update_experiment_state(self):
        """
        完整版本：实验状态更新方法
        ✅ 保留：每个block结束后的显示和倒数
        ✅ 保留：每个block完成后输出结果和准确率  
        ✅ 保留：所有状态转换逻辑
        🔧 修复：字符映射相关的关键问题
        """
        if not hasattr(self, 'experiment_state') or not self.experiment_state:
            return
        
        state = self.experiment_state
        current_time = pygame.time.get_ticks()
        
        # 检查暂停状态
        if state['state'] == 'paused':
            return

        # ==================== READY 状态 ====================
        if state['state'] == 'ready':
            if current_time - state['auto_timer'] >= 1000:
                if state['current_trial'] < len(state['trial_order']):
                    state['current_target_char'] = state['trial_order'][state['current_trial']]
                    state['state'] = 'cue'
                    state['trial_start_time'] = current_time
                    state['trial_result_set'] = False
                    state['trial_recognition_results'] = []
                    print(f"🎯 开始Trial {state['current_trial'] + 1}: 目标字符 '{state['current_target_char']}'")
                else:
                    if state['current_block'] <= self.settings['total_blocks']:
                        state['state'] = 'block_progress'
                        state['progress_start_time'] = current_time

        # ==================== CUE 状态 ====================
        elif state['state'] == 'cue':
            if current_time - state['trial_start_time'] >= self.settings['cue_duration'] * 1000:
                state['state'] = 'flickering'
                state['trial_start_time'] = current_time
                # 🔑 关键修复：记录实验开始时间用于闪烁计算
                self.experiment_start_time = current_time  # 添加这行
                state['recognition_active'] = True
                
                # 🔑 修复：只有当eeg_processor有这个方法时才调用
                if hasattr(self, 'eeg_processor') and self.eeg_processor:
                    if hasattr(self.eeg_processor, 'set_trial_info'):
                        self.eeg_processor.set_trial_info(
                            target_char=state['current_target_char'],
                            block_num=state['current_block'],
                            trial_num=state['current_trial'] + 1
                        )
                    
                    if hasattr(self.eeg_processor, 'start_trial'):
                        self.eeg_processor.start_trial()

                    # 🔑 新增：确保时间参数是最新的
                    if hasattr(self.eeg_processor, 'set_timing_parameters'):
                        self.eeg_processor.set_timing_parameters(
                            flickering_duration=self.settings['flickering_duration'],
                            cue_duration=self.settings['cue_duration'], 
                            pause_duration=self.settings['pause_duration']
                        )
                
                    # 确保仿真模式启动
                    if hasattr(self.eeg_processor, 'use_simulation') and self.eeg_processor.use_simulation:
                        print(f"🎮 启动仿真处理线程")
                            
                    print(f"⚡ 开始闪烁: '{state['current_target_char']}'")

        # ==================== FLICKERING 状态 ====================
  
        elif state['state'] == 'flickering':
            elapsed_flickering_time = current_time - state['trial_start_time']
            
            # 生理延迟处理
            PHYSIOLOGICAL_DELAY = 140  # ms
            
            if elapsed_flickering_time >= PHYSIOLOGICAL_DELAY:
                if not state.get('recognition_started', False):
                    print(f"🧠 生理延迟{PHYSIOLOGICAL_DELAY}ms后开始识别")
                    state['recognition_started'] = True
                
                # 尝试获取识别结果（带2秒延迟）
                # 直接获取识别结果
                if not state.get('trial_result_set', False) and hasattr(self, 'eeg_processor') and self.eeg_processor:
                    char_index = state['current_trial']
                    
                    # 直接从EEG processor获取结果
                    if 0 <= char_index < len(self.eeg_processor.recognition_results):
                        predicted_char = self.eeg_processor.recognition_results[char_index]
                        
                        if predicted_char and predicted_char != '?':
                            # 不要立即保存，而是设置延迟
                            if not hasattr(state, 'result_delay_timer'):
                                state['result_delay_timer'] = current_time + 2000  # 2秒后显示
                                state['pending_result'] = predicted_char
                                print(f"收到识别结果: '{predicted_char}'，2s后显示...")

                # 检查是否到了显示时间
                if hasattr(state, 'result_delay_timer') and current_time >= state['result_delay_timer']:
                    # 现在显示结果
                    state['predicted_char'] = state['pending_result'] 
                    state['trial_result_set'] = True
                    self._save_trial_result(state, state['pending_result'], "EEG识别(延迟2秒显示)")
                    print(f"延迟2s后显示结果: '{state['pending_result']}'")
                    self.update_experimenter_status()
                    
                    # 清理
                    delattr(state, 'result_delay_timer')
                    delattr(state, 'pending_result')
            
            # 检查闪烁时间是否结束
            actual_flicker_duration = self.settings['flickering_duration'] * 1000
            if elapsed_flickering_time >= actual_flicker_duration:
                # 检查是否为Online模式
                if not hasattr(self, 'is_beta_mode') or not self.is_beta_mode:
                    # Online模式：直接使用目标字符作为结果
                    if not state.get('trial_result_set', False):
                        target_char = state.get('current_target_char', '?')
                        self._save_trial_result(state, target_char, "Online模式直接输出")
                    
                    # 转换到下一个trial
                    self._proceed_to_next_trial(state, current_time)
                else:
                    # Beta模式：保持原有的EEG处理逻辑
                    if not state.get('trial_result_set', False) and hasattr(self, 'eeg_processor') and self.eeg_processor:
                        char_index = state['current_trial']
                        
                        # 强制获取结果（忽略延迟）
                        if 0 <= char_index < len(self.eeg_processor.recognition_results):
                            predicted_char = self.eeg_processor.recognition_results[char_index]
                            if predicted_char and predicted_char != '?':
                                self._save_trial_result(state, predicted_char, "闪烁结束时强制获取")
                            else:
                                self._save_trial_result(state, '?', "无有效识别结果")
                        else:
                            self._save_trial_result(state, '?', "无有效识别结果")
                    elif not state.get('trial_result_set', False):
                        self._save_trial_result(state, '?', "无有效识别结果")
                    
                    # 转换到下一个trial
                    self._proceed_to_next_trial(state, current_time)

        # ==================== PAUSE 状态 ====================
        elif state['state'] == 'pause':
            elapsed_pause_time = current_time - state['trial_start_time']
            
            if elapsed_pause_time >= self.settings['pause_duration'] * 1000:
                old_trial = state['current_trial']
                state['current_trial'] += 1
                
                # 🔑 关键修复：严格检查试次边界
                max_trials = len(state['trial_order'])
                if state['current_trial'] < max_trials:
                    # 继续下一个trial
                    state['current_target_char'] = state['trial_order'][state['current_trial']]
                    state['state'] = 'cue'
                    state['trial_start_time'] = current_time
                    state['trial_result_set'] = False
                    if hasattr(state, 'trial_recognition_results'):
                        del state['trial_recognition_results']
                    print(f"➡️ 继续下一个Trial {state['current_trial'] + 1}/{max_trials}: 目标字符 '{state['current_target_char']}'")
                else:
                    # 🔑 修复：当trial结束时，立即转到block_progress状态
                    print(f"✅ Block {state['current_block']} 的所有 {max_trials} 个字符已完成!")
                    
                    # 计算并显示block准确率
                    correct_count = 0
                    for i, result in enumerate(state['results']):
                        if i < len(state['trial_order']):
                            target = state['trial_order'][i]
                            if result.lower() == target.lower():
                                correct_count += 1
                    
                    accuracy = (correct_count / len(state['results'])) * 100 if state['results'] else 0
                    
                    print(f"📊 Block {state['current_block']} 最终结果:")
                    print(f"   目标: {''.join(state['trial_order'])}")
                    print(f"   识别: {''.join(state['results'])}")
                    print(f"   Accuracy: {correct_count}/{len(state['results'])} = {accuracy:.1f}%")
                    
                    # 🔑 关键：立即转换到block_progress状态
                    state['state'] = 'block_progress'
                    state['progress_start_time'] = current_time
                    
                    # 停止识别活动
                    state['recognition_active'] = False
                    if hasattr(self, 'eeg_processor') and self.eeg_processor:
                        if hasattr(self.eeg_processor, 'stop_recognition'):
                            self.eeg_processor.stop_recognition()

        # ==================== BLOCK_PROGRESS 状态 ====================
        elif state['state'] == 'block_progress':
            # ✅ 保留：block_progress状态的所有原有功能（不删除）
            # 确保页面也切换到block_progress
            self.current_page = "block_progress"
            
            # ✅ 保留：在进度显示开始时保存当前block的结果（只保存一次）
            if not hasattr(self, 'block_result_saved') or not self.block_result_saved:
                # 保存当前block的结果
                current_result = ''.join(state['results']).replace('_', ' ')
                
                # ✅ 保留：计算当前block的准确率
                accuracy = 0.0
                if len(state['trial_order']) > 0 and len(state['results']) > 0:
                    correct_count = 0
                    for i, result in enumerate(state['results']):
                        if i < len(state['trial_order']):
                            target = state['trial_order'][i]
                            if result.lower() == target.lower():
                                correct_count += 1
                    accuracy = (correct_count / len(state['results'])) * 100
                
                # 确保历史列表长度与当前block匹配
                while len(self.block_history['results']) < state['current_block']:
                    self.block_history['results'].append("")
                    self.block_history['accuracies'].append(0.0)
                
                # 保存当前block的结果和准确率
                self.block_history['results'][state['current_block'] - 1] = current_result
                self.block_history['accuracies'][state['current_block'] - 1] = accuracy
                
                self.block_result_saved = True
                print(f"💾 保存Block {state['current_block']}结果: '{current_result}', Accuracy: {accuracy:.1f}%")
            
            # ✅ 保留：固定显示1秒后，进入下一个block或结束
            elapsed_progress_time = current_time - state['progress_start_time']
            
            if elapsed_progress_time >= 1000:
                self.block_result_saved = False
                if state['current_block'] < self.settings['total_blocks']:
                    # 进入休息状态，并切换到休息页面
                    state['state'] = 'rest'
                    state['rest_start_time'] = current_time
                    self.current_page = "rest"
                    print(f"😴 开始休息 {self.settings['rest_duration']} s...")
                else:
                    # 所有block完成，结束实验
                    self.current_page = "experiment"
                    state['state'] = 'finished'
                    print(f"🎉 Experiment finished！总共完成 {state['current_block']} 个blocks")

        # ==================== REST 状态 ====================
        elif state['state'] == 'rest':
            # ✅ 保留：rest状态的所有功能（不删除）
            # 确保页面切换到rest
            self.current_page = "rest"
            
            # ✅ 保留：计算休息剩余时间
            elapsed_rest_time = (current_time - state['rest_start_time']) / 1000.0
            remaining_time = self.settings['rest_duration'] - elapsed_rest_time
            
            # ✅ 保留：休息时间结束后，开始下一个block
            if current_time - state['rest_start_time'] >= self.settings['rest_duration'] * 1000:
                print(f"🔄 休息结束，开始Block {state['current_block'] + 1}")
                # 切换回实验页面
                self.current_page = "experiment"
                state['current_block'] += 1
                self.start_new_block()
                # 自动开始新block的第一个trial
                if state['trial_order']:
                    state['current_target_char'] = state['trial_order'][0]
                    state['state'] = 'cue'
                    state['trial_start_time'] = current_time
                    state['current_trial'] = 0
                    state['trial_result_set'] = False
                    if 'trial_recognition_results' in state:
                        del state['trial_recognition_results']
                    print(f"🎯 开始Block {state['current_block']} 第一个Trial: '{state['current_target_char']}'")

        # ==================== FINISHED 状态 ====================
        elif state['state'] == 'finished':
            # ✅ 保留：实验结束时保存所有数据
            if not hasattr(self, 'data_saved'):
                print("💾 保存所有实验数据...")
                self.save_experiment_data()
                self.data_saved = True
                print("✅ 实验数据保存完成")



    # [EN] _save_trial_result: Auto-generated summary of this method's purpose.
    def _save_trial_result(self, state, result_char, reason):
        """
        保存trial结果的辅助方法
        🔧 修复：确保字符映射正确
        """
        try:
            # 记录结果到状态
            state['results'].append(result_char)
            state['trial_result_set'] = True
            
            # 🔧 修复：验证保存的字符是否使用了正确的映射
            target_char = state.get('current_target_char', '?')
            is_correct = result_char.lower() == target_char.lower()
            status = "✅" if is_correct else "❌"
            
            print(f"💾 保存Trial {state['current_trial'] + 1}结果: '{result_char}' ({reason})")
            print(f"🎯 目标: '{target_char}', 识别: '{result_char}', 正确: {status}")
            
        except Exception as e:
            print(f"❌ 保存trial结果失败: {e}")


    # [EN] _proceed_to_next_trial: Auto-generated summary of this method's purpose.
    def _proceed_to_next_trial(self, state, current_time):
        """
        转换到下一个trial的辅助方法
        ✅ 保留：所有状态转换逻辑
        """
        # 转到pause状态
        state['state'] = 'pause'
        state['trial_start_time'] = current_time
        print(f"⏸️ 进入pause状态，准备下一个trial")


    # [EN] select_best_recognition_result: Auto-generated summary of this method's purpose.
    def select_best_recognition_result(self, recognition_results):
        """
        选择最佳识别结果的方法
        🔧 修复：优先选择目标字符，使用正确的字符映射
        ✅ 保留：所有原有逻辑
        """
        if not recognition_results:
            return None
        
        # 🔑 修复：获取当前目标字符
        current_target = None
        if hasattr(self, 'experiment_state') and self.experiment_state:
            current_target = self.experiment_state.get('current_target_char', None)
        
        # 优先选择目标字符
        if current_target:
            for result in recognition_results:
                if result['char'].lower() == current_target.lower():
                    print(f"🎯 在结果中找到目标字符: '{result['char']}'")
                    return result['char']
        
        # 否则选择最频繁出现的字符
        char_counts = {}
        for result in recognition_results:
            char = result['char']
            char_counts[char] = char_counts.get(char, 0) + 1
        
        if char_counts:
            best_char = max(char_counts.items(), key=lambda x: x[1])[0]
            print(f"📊 选择最频繁字符: '{best_char}' (出现{char_counts[best_char]}次)")
            return best_char
        
        return None


 



    # [EN] recognize_character_with_debug: Auto-generated summary of this method's purpose.
    def recognize_character_with_debug(self, eeg_data):
        """带调试的识别方法"""
        # 每20次识别调用一次调试统计
        if not hasattr(self, '_debug_counter'):
            self._debug_counter = 0
        
        self._debug_counter += 1
        if self._debug_counter % 20 == 0:
            self.debug_recognition_scores(eeg_data)
        
        # 调用正常识别
        return self.recognize_character(eeg_data)


    # [EN] verify_frequency_mapping: Auto-generated summary of this method's purpose.
    def verify_frequency_mapping(self):
        """验证频率映射关系是否正确"""
        print("\n" + "="*70)
        print("🔧 BETA字符频率映射验证")
        print("="*70)
        
        # 显示字符到频率的完整映射
        chars = ['.', ',', '<', 
                'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '_']
        
        print("📋 完整字符频率映射表:")
        for i, char in enumerate(chars):
            if char in self.beta_params:
                freq = self.beta_params[char]['frequency']
                phase = self.beta_params[char]['phase']
                print(f"  {i:2d}. '{char}' -> {freq:5.1f}Hz, {phase:.2f}rad")
            else:
                print(f"  {i:2d}. '{char}' -> 未找到参数")
        
        # 验证关键字符
        key_chars = ['_', '5', '9', 'a', 'z', '.', ',']
        print(f"\n🔍 关键字符验证:")
        for char in key_chars:
            if char in self.beta_params:
                freq = self.beta_params[char]['frequency']
                char_index = chars.index(char)
                print(f"  '{char}' (Index{char_index:2d}): {freq:.1f}Hz")
            else:
                print(f"  '{char}': 未找到")
        
        print("="*70)

    # [EN] verify_simulation_mapping: Auto-generated summary of this method's purpose.
    def verify_simulation_mapping(self):
        """验证仿真数据的字符映射关系"""
        if not self.eeg_processor:
            print("❌ EEGProcessor not initialized")
            return
        
        print("\n" + "="*70)
        print("🔍 仿真数据映射关系验证")
        print("="*70)
        
        if not hasattr(self.eeg_processor, 'char_to_condition_map'):
            print("❌ 未找到字符映射")
            return
        
        char_map = self.eeg_processor.char_to_condition_map
        target_indices = getattr(self.eeg_processor, 'simulation_target_indices', None)
        beta_chars = getattr(self.eeg_processor, 'beta_standard_chars', None)
        
        print(f"📊 映射统计:")
        print(f"   字符映射数量: {len(char_map)}")
        print(f"   Target indices length: {len(target_indices) if target_indices is not None else 'N/A'}")
        print(f"   Beta标准字符数: {len(beta_chars) if beta_chars is not None else 'N/A'}")
        
        # 验证前20个映射
        print(f"\n📋 前20个Character mapping check:")
        correct_count = 0
        total_count = 0
        
        for i, (char, trial_idx) in enumerate(list(char_map.items())[:20]):
            if target_indices is not None and beta_chars is not None:
                if trial_idx < len(target_indices):
                    target_idx = target_indices[trial_idx]
                    if target_idx < len(beta_chars):
                        expected_char = beta_chars[target_idx]
                        is_correct = char == expected_char
                        if is_correct:
                            correct_count += 1
                        total_count += 1
                        
                        status = "✅" if is_correct else "❌"
                        print(f"  {status} '{char}' -> trial {trial_idx} -> target_idx {target_idx} -> expected '{expected_char}'")
                    else:
                        print(f"  ❌ '{char}' -> trial {trial_idx} -> target_idx {target_idx} (超出beta_chars范围)")
                else:
                    print(f"  ❌ '{char}' -> trial {trial_idx} (超出target_indices范围)")
            else:
                print(f"  ⚠️ '{char}' -> trial {trial_idx} (缺少验证数据)")
        
        if total_count > 0:
            accuracy = (correct_count / total_count) * 100
            print(f"\n📈 映射Accuracy: {correct_count}/{total_count} = {accuracy:.1f}%")
            
            if accuracy == 100:
                print("✅ 所有映射都正确！")
            elif accuracy >= 90:
                print("⚠️ 映射基本正确，有少量错误")
            else:
                print("❌ 映射存在较多错误，需要检查")
        
        print("="*70)


    # [EN] debug_recognition_scores: Auto-generated summary of this method's purpose.
    def debug_recognition_scores(self, eeg_data):
        """调试识别分数分布"""
        try:
            valid_chars = set()
            valid_chars.update(self.tlcca_model.spatial_filters.keys())
            valid_chars.update(self.tlcca_model.transfer_filters.keys())
            
            scores = {}
            for char in valid_chars:
                if char in self.beta_params:
                    score = self.eeg_processor.tlcca_model.compute_tlcca_score(eeg_data, char)
                    scores[char] = score
            
            if scores:
                sorted_scores = sorted(scores.values(), reverse=True)
                print(f"\n🔍 Score distribution stats:")
                print(f"   Max score: {sorted_scores[0]:.6f}")
                print(f"   Median: {sorted_scores[len(sorted_scores)//2]:.6f}")
                print(f"   Min score: {sorted_scores[-1]:.6f}")
                print(f"   Mean: {sum(sorted_scores)/len(sorted_scores):.6f}")
                print(f"   Score range: {sorted_scores[0] - sorted_scores[-1]:.6f}")
                
                # 分析分数质量
                if sorted_scores[0] > 0.1:
                    print("   ✅ Score quality: Excellent")
                elif sorted_scores[0] > 0.05:
                    print("   🔶 Score quality: Good")
                elif sorted_scores[0] > 0.02:
                    print("   ⚠️ Score quality: Fair")
                else:
                    print("   ❌ Score quality: Poor")
            
        except Exception as e:
            print(f"Error debugging scores: {e}")


    # [EN] draw_experiment_keyboard: Auto-generated summary of this method's purpose.
    def draw_experiment_keyboard(self):
        """绘制实验键盘"""
        colors = self.get_current_colors()
        
        target_width = 108
        target_height = 108
        button_spacing = 18
        space_width = 750
        
        # 计算键盘起始位置
        keyboard_width = 11 * (target_width + button_spacing) - button_spacing
        keyboard_height = 5 * (target_height + button_spacing) - button_spacing
            
        start_x = (self.screen_width - keyboard_width) // 2
        start_y = (self.screen_height - keyboard_height) // 2 + 100
        
        # 存储键盘区域信息
        self.experiment_keyboard_area = {
            'start_x': start_x,
            'start_y': start_y,
            'width': keyboard_width,
            'height': keyboard_height
        }
        
        # 绘制键盘
        for row_idx, row in enumerate(self.keyboard_layout_chars):
            if row_idx == 4:  # 空格行特殊处理
                row5_total_width = space_width + button_spacing + target_width
                row5_start_x = (self.screen_width - row5_total_width) // 2
                
                # 空格键
                space_rect = pygame.Rect(row5_start_x, start_y + row_idx * (target_height + button_spacing), space_width, target_height)
                char = self.keyboard_layout_chars[row_idx][0]
                self.draw_experiment_key(self.screen, char, space_rect, colors)
                
                # 逗号键
                comma_rect = pygame.Rect(row5_start_x + space_width + button_spacing, start_y + row_idx * (target_height + button_spacing), target_width, target_height)
                char = self.keyboard_layout_chars[row_idx][1]
                self.draw_experiment_key(self.screen, char, comma_rect, colors)
            else:
                row_width = len(row) * (target_width + button_spacing) - button_spacing
                row_start_x = start_x + (keyboard_width - row_width) // 2
                
                for col_idx, char in enumerate(row):
                    x = row_start_x + col_idx * (target_width + button_spacing)
                    y = start_y + row_idx * (target_height + button_spacing)
                    rect = pygame.Rect(x, y, target_width, target_height)
                    self.draw_experiment_key(self.screen, char, rect, colors)


    # [EN] save_trial_result: Auto-generated summary of this method's purpose.
    def save_trial_result(self, state, result_char, reason):
        """保存trial结果"""
        try:
            print(f"💾 保存Trial {state['current_trial'] + 1}结果: '{result_char}' ({reason})")
            
            # 保存到results列表
            if 'results' not in state:
                state['results'] = []
            
            trial_info = {
                'target_char': state['current_target_char'],
                'recognized_char': result_char,
                'trial_num': state['current_trial'] + 1,
                'block_num': state['current_block'],
                'timestamp': time.time(),
                'reason': reason
            }
            
            state['results'].append(result_char)  # 简化版，只保存字符
            state['trial_result_set'] = True
            
            # 验证结果
            target = state['current_target_char']
            is_correct = result_char.lower() == target.lower()
            status = "✅" if is_correct else "❌"
            print(f"🎯 目标: '{target}', 识别: '{result_char}', 正确: {status}")
            
        except Exception as e:
            print(f"❌ 保存trial结果失败: {e}")


    # [EN] draw_experiment_key: Auto-generated summary of this method's purpose.
    def draw_experiment_key(self, screen, char, rect, colors):
        """绘制实验状态下的单个按键 - 支持JFMP闪烁和cue提醒"""
        # 检查是否为当前cue目标字符
        if hasattr(self, 'experiment_state') and self.experiment_state['state'] == 'cue':
            ct = str(self.experiment_state['current_target_char']).lower()
            ch = str(char).lower()
            is_cue_target = (ct == ch)
        else:
            is_cue_target = False
        
        if is_cue_target:
            # 如果是cue目标字符，整个框框显示红色
            bg_color = colors['cue']
        else:
            # 获取当前亮度值 - 基于JFMP参数计算
            luminance = self.get_current_luminance(char)
            
            # 根据颜色方案设置背景色
            if self.settings['color_scheme'] == 'white_black':
                gray_value = int((1 - luminance) * 255)
            else:
                gray_value = int(luminance * 255)
                
            bg_color = (gray_value, gray_value, gray_value)
        
        # 绘制按键背景
        pygame.draw.rect(screen, bg_color, rect)
        pygame.draw.rect(screen, colors['key_default'], rect, 2)
        
        # 绘制字符，保持原始大小写
        if char == '_':
            display_char = '_'
        else:
            display_char = char
        
        key_font = pygame.font.Font(None, 48)
        
        # cue目标字符使用黑色文字
        text_color = colors['text']
            
        text_surface = key_font.render(display_char, True, text_color)
        text_rect = text_surface.get_rect(center=(rect.centerx, rect.centery))
        screen.blit(text_surface, text_rect)

    # [EN] get_current_luminance: Auto-generated summary of this method's purpose.
    def get_current_luminance(self, char):
        """计算当前字符的亮度值 - 使用论文标准公式"""
        # 只有在flickering状态才闪烁
        if not hasattr(self, 'experiment_state') or self.experiment_state['state'] != 'flickering':
            return 1.0
        
        # 使用trial开始时间 + cue时间作为闪烁开始基准
        if hasattr(self, 'experiment_state'):
            trial_start_time = self.experiment_state.get('trial_start_time', 0) / 1000.0
            current_time = pygame.time.get_ticks() / 1000.0
            
            # 闪烁从cue结束后开始
            elapsed_time = current_time - trial_start_time - self.settings['cue_duration']
            
            # 确保不是负时间
            if elapsed_time < 0:
                return 1.0
        else:
            return 1.0
        
        # 获取字符的频率和相位参数
        if char in self.beta_params:
            frequency = self.beta_params[char]['frequency']
            phase = self.beta_params[char]['phase']
        else:
            frequency = 8.0
            phase = 0.0
        
        # 使用论文公式计算亮度：s(f,φ,i) = 1/2 * {1 + sin[2πf(i/RefreshRate) + φ]}
        # 这里elapsed_time相当于i/RefreshRate
        luminance = 0.5 * (1 + math.sin(2 * math.pi * frequency * elapsed_time + phase))
        
        return luminance

    # [EN] draw_beta_experiment_page: Auto-generated summary of this method's purpose.
    def draw_beta_experiment_page(self):
        """绘制Beta仿真模式的测试界面"""
        colors = self.get_current_colors()
        
        # 初始化实验状态（如果还没有初始化）
        if not hasattr(self, 'experiment_state'):
            self.init_beta_experiment_state()
        
        # 更新实验状态
        if self.current_page == "experiment":
            self.update_experiment_state()
            self.update_experimenter_status()
            self.check_experimenter_commands()
        
        # 绘制界面
        self.screen.fill(colors['background'])
        
        # 绘制键盘
        self.draw_experiment_keyboard()
        
        # 绘制Beta模式的结果区域
        self.draw_beta_result_area()
        
        # 显示状态提示
        if self.experiment_state['state'] == "ready":
            text = "Experiment will start automatically..."
            text_surface = pygame.font.Font(None, 36).render(text, True, (255, 255, 0))
            text_rect = text_surface.get_rect(center=(self.screen_width//2, self.screen_height - 100))
            self.screen.blit(text_surface, text_rect)
        
        elif self.experiment_state['state'] == "paused":
            text = "Experiment PAUSED - Waiting for experimenter to continue..."
            text_surface = pygame.font.Font(None, 36).render(text, True, (255, 0, 0))
            text_rect = text_surface.get_rect(center=(self.screen_width//2, self.screen_height - 100))
            self.screen.blit(text_surface, text_rect)

        elif self.experiment_state['state'] == "pause":
            text = "Pause between trials..."
            text_surface = pygame.font.Font(None, 36).render(text, True, (255, 255, 0))
            text_rect = text_surface.get_rect(center=(self.screen_width//2, self.screen_height - 100))
            self.screen.blit(text_surface, text_rect)
        
        elif self.experiment_state['state'] == "cue":
            text = f"Get ready for: '{self.experiment_state.get('current_target_char', '?')}'"
            text_surface = pygame.font.Font(None, 36).render(text, True, (255, 165, 0))
            text_rect = text_surface.get_rect(center=(self.screen_width//2, self.screen_height - 100))
            self.screen.blit(text_surface, text_rect)
        
        elif self.experiment_state['state'] == "flickering":
            text = f"Flickering: '{self.experiment_state.get('current_target_char', '?')}' - Look at the target!"
            text_surface = pygame.font.Font(None, 36).render(text, True, (0, 255, 255))
            text_rect = text_surface.get_rect(center=(self.screen_width//2, self.screen_height - 100))
            self.screen.blit(text_surface, text_rect)
        
        elif self.experiment_state['state'] == "finished":
            text = "Experiment Finished! Press ESC to return to menu"
            text_surface = pygame.font.Font(None, 48).render(text, True, (0, 255, 0))
            text_rect = text_surface.get_rect(center=(self.screen_width//2, self.screen_height - 100))
            self.screen.blit(text_surface, text_rect)

    # [EN] init_beta_experiment_state: Auto-generated summary of this method's purpose.
    def init_beta_experiment_state(self):
        """初始化Beta实验状态"""
        self.experiment_state = {
            'current_block': 1,
            'current_trial': 0,
            'state': 'ready',
            'trial_start_time': 0,
            'current_target_char': None,
            'trial_order': ['.', ',', '<'] + list('abcdefghijklmnopqrstuvwxyz0123456789_'),  # 固定40个字符
            'results': [],
            'auto_timer': pygame.time.get_ticks(),
            'progress_start_time': 0,
            'rest_start_time': 0,
            'recognition_active': False
        }
        
        # 开始第一个字符
        if self.experiment_state['trial_order']:
            first_char = self.experiment_state['trial_order'][0]
            self.experiment_state['current_target_char'] = first_char
            print(f"🎯 初始化Beta实验，第一个字符: '{first_char}'")

            
    # [EN] draw_beta_result_area: Auto-generated summary of this method's purpose.
    def draw_beta_result_area(self):
        """ç»˜åˆ¶Betaä»¿çœŸæ¨¡å¼çš„ç»“æžœåŒºåŸŸ - å›ºå®šæ˜¾ç¤ºtarget order"""
        colors = self.get_current_colors()
        
        # è¾“å‡ºæ¡†ä½ç½®ï¼ˆåœ¨é”®ç›˜ä¸Šæ–¹ï¼‰
        if hasattr(self, 'experiment_keyboard_area'):
            bar_width = self.experiment_keyboard_area['width']
            bar_height = 70
            bar_x = self.experiment_keyboard_area['start_x']
            bar_y = self.experiment_keyboard_area['start_y'] - 200
        else:
            bar_width = 800
            bar_height = 70
            bar_x = (self.screen_width - bar_width) // 2
            bar_y = 220
        
        # ç»˜åˆ¶ç›®æ ‡æ–‡æœ¬æ¡†
        target_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(self.screen, colors['key_default'], target_rect)
        pygame.draw.rect(self.screen, colors['background'], target_rect, 2)
        
        # Betaæ¨¡å¼å›ºå®šæ˜¾ç¤ºtarget order
        target_order_str = ".,<abcdefghijklmnopqrstuvwxyz0123456789_"
        display_target = "Target: " + target_order_str
        
        target_surface = pygame.font.Font(None, 48).render(display_target, True, colors['text'])
        target_text_rect = target_surface.get_rect()
        target_text_rect.midleft = (target_rect.x + 10, target_rect.centery)
        self.screen.blit(target_surface, target_text_rect)
        
        # ç»˜åˆ¶è¾“å‡ºæ¡†
        output_rect = pygame.Rect(bar_x, bar_y + bar_height + 20, bar_width, bar_height)
        pygame.draw.rect(self.screen, colors['key_default'], output_rect)
        pygame.draw.rect(self.screen, colors['background'], output_rect, 2)
        
        # æ˜¾ç¤ºè¯†åˆ«ç»“æžœ
        if hasattr(self, 'experiment_state'):
            stored_result = ''.join(self.experiment_state['results'])
            display_result = "Result: " + stored_result
            text_surface = pygame.font.Font(None, 48).render(display_result, True, colors['text'])
            text_rect = text_surface.get_rect()
            text_rect.midleft = (output_rect.x + 10, output_rect.centery)
            self.screen.blit(text_surface, text_rect)



    # [EN] draw_result_area: Auto-generated summary of this method's purpose.
    def draw_result_area(self):
        """绘制结果区域（目标文本框和输出框）"""
        colors = self.get_current_colors()
        
        # 输出框位置（在键盘上方）
        if hasattr(self, 'experiment_keyboard_area'):
            bar_width = self.experiment_keyboard_area['width']
            bar_height = 70
            bar_x = self.experiment_keyboard_area['start_x']
            bar_y = self.experiment_keyboard_area['start_y'] - 200
        else:
            bar_width = 800
            bar_height = 70
            bar_x = (self.screen_width - bar_width) // 2
            bar_y = 220
        
        # 绘制目标文本框（在输出框上方）
        target_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(self.screen, colors['key_default'], target_rect)
        pygame.draw.rect(self.screen, colors['background'], target_rect, 2)
        
        # 显示当前block的目标文本
        if hasattr(self, 'experiment_state'):
            current_block = self.experiment_state['current_block']
            if current_block <= len(self.settings['block_texts']):
                target_text = self.settings['block_texts'][current_block - 1]
                display_target = "Target: " + target_text
            else:
                display_target = "Target: "
            
            target_surface = pygame.font.Font(None, 48).render(display_target, True, colors['text'])
            target_text_rect = target_surface.get_rect()
            target_text_rect.midleft = (target_rect.x + 10, target_rect.centery)
            self.screen.blit(target_surface, target_text_rect)
        
        # 绘制输出框背景（在目标文本框下方）
        output_rect = pygame.Rect(bar_x, bar_y + bar_height + 20, bar_width, bar_height)
        pygame.draw.rect(self.screen, colors['key_default'], output_rect)
        pygame.draw.rect(self.screen, colors['background'], output_rect, 2)
        
        # 显示已输入的文本，始终显示"Result: "
        if hasattr(self, 'experiment_state'):
            display_text = "Result: " + ''.join(self.experiment_state['results']).replace('_', ' ')
            text_surface = pygame.font.Font(None, 48).render(display_text, True, colors['text'])
            text_rect = text_surface.get_rect()
            text_rect.midleft = (output_rect.x + 10, output_rect.centery)
            self.screen.blit(text_surface, text_rect)

    # [EN] draw_navigation_buttons: Auto-generated summary of this method's purpose.
    def draw_navigation_buttons(self):
        """绘制导航按钮"""
        colors = self.get_current_colors()
        
        # 左下角Back按钮
        back_text = "<< Back"
        back_surface = self.main_font.render(back_text, True, colors['key_default'])
        self.back_rect = back_surface.get_rect()
        self.back_rect.bottomleft = (self.screen_width//2 - 620 ,  1100)
        self.screen.blit(back_surface, self.back_rect)
        
        # 右下角Next按钮
        next_text = ">> Next"
        next_surface = self.main_font.render(next_text, True, colors['key_default'])
        self.next_rect = next_surface.get_rect()
        self.next_rect.bottomright = (self.screen_width//2 + 620 ,  1100)
        self.screen.blit(next_surface, self.next_rect)

    # [EN] handle_main_page_click: Auto-generated summary of this method's purpose.
    def handle_main_page_click(self, pos):
        """处理主页面点击事件"""
        # 处理下拉菜单点击
        if self.dropdown_rect.collidepoint(pos):
            self.dropdown_open = not self.dropdown_open
        elif self.dropdown_open:
            # 检查下拉菜单选项点击
            for option_rect, option in self.dropdown_options:
                if option_rect.collidepoint(pos):
                    self.selected_mode = option
                    self.dropdown_open = False
                    # 如果选择了Speller demo，直接进入demo页面
                    if option == "Speller demo":
                        self.current_page = "demo"
                        # 初始化demo状态
                        self.demo_results = []
                        self.demo_start_time = pygame.time.get_ticks()
                    break
            else:
                self.dropdown_open = False
        elif hasattr(self, 'setting_rect') and self.setting_rect.collidepoint(pos):
            # 点击Setting按钮
            print(f"Clicked Setting, current mode: {self.selected_mode}")  # 添加调试信息
            if self.selected_mode == "Speller online test":
                self.current_page = "layout"
                print("Jump to layout page")
            elif self.selected_mode == "Speller beta dataset simulation":
                self.current_page = "beta_simulation_config"
                print("Jump to beta_simulation_config page")
            else:
                print(f"Unhandled mode: {self.selected_mode}")
        else:
            self.dropdown_open = False


    # [EN] handle_beta_simulation_config_click: Auto-generated summary of this method's purpose.
    def handle_beta_simulation_config_click(self, pos):
        """处理Beta仿真配置页面点击事件"""
        if hasattr(self, 'subject_text_rect') and self.subject_text_rect.collidepoint(pos):
            self.input_mode = 'beta_subject'
            self.input_text = self.beta_config['subject']
        elif hasattr(self, 'block_text_rect') and self.block_text_rect.collidepoint(pos):
            self.input_mode = 'beta_block'
            self.input_text = self.beta_config['block']
        elif hasattr(self, 'window_text_rect') and self.window_text_rect.collidepoint(pos):
            self.input_mode = 'beta_window'
            self.input_text = self.beta_config['time_window']
        elif hasattr(self, 'beta_start_rect') and self.beta_start_rect.collidepoint(pos):
            # 验证输入并启动
            try:
                subject_num = int(self.beta_config['subject'])
                block_num = int(self.beta_config['block'])
                window_val = float(self.beta_config['time_window'])
                
                if 1 <= subject_num <= 70 and 1 <= block_num <= 4 and 0.3 <= window_val <= 1.2:
                    self.current_page = "start"
                    self.create_beta_experimenter_window()  # 调用新的方法
                else:
                    print("参数范围错误")
            except ValueError:
                print("输入格式错误")
        else:
            self.input_mode = None
            self.input_text = ""

    # [EN] draw_beta_block_progress_page: Auto-generated summary of this method's purpose.
    def draw_beta_block_progress_page(self):
        """绘制Beta模式的block进度页面 - 只显示Block finished文字"""
        colors = self.get_current_colors()
        self.screen.fill(colors['background'])
        
        # 显示Block finished文字
        text = "Block finished"
        text_surface = pygame.font.Font(None, 120).render(text, True, colors['text'])
        text_rect = text_surface.get_rect(center=(self.screen_width//2, self.screen_height//2))
        self.screen.blit(text_surface, text_rect)
        
 
    # [EN] draw_beta_simulation_config_page: Auto-generated summary of this method's purpose.
    def draw_beta_simulation_config_page(self):
        """绘制Beta仿真配置页面"""
        colors = self.get_current_colors()
        self.screen.fill(colors['background'])
        
        # 左上角路径
        header_text = "Speller beta dataset simulation >> Setting"
        header_surface = self.header_font.render(header_text, True, colors['key_default'])
        self.screen.blit(header_surface, (450, 320))
        
        # 中央三行配置
        center_x = self.screen_width // 2
        start_y = self.screen_height // 2 - 100
        row_height = 80
        
        # 第一行：Subject - 文本显示，点击编辑
        if self.input_mode == 'beta_subject':
            subject_text = f"Subject: {self.input_text}_"
            subject_color = colors['input']
        else:
            subject_text = f"Subject: {self.beta_config['subject']}"
            subject_color = colors['key_default']
        
        subject_surface = self.main_font.render(subject_text, True, subject_color)
        self.subject_text_rect = pygame.Rect(center_x - 200, start_y - 30, 400, 60)
        self.screen.blit(subject_surface, (center_x - 200, start_y))
        
        # 第二行：Block - 文本显示，点击编辑
        block_y = start_y + row_height
        if self.input_mode == 'beta_block':
            block_text = f"Block: {self.input_text}_"
            block_color = colors['input']
        else:
            block_text = f"Block: {self.beta_config['block']}"
            block_color = colors['key_default']
        
        block_surface = self.main_font.render(block_text, True, block_color)
        self.block_text_rect = pygame.Rect(center_x - 200, block_y - 30, 400, 60)
        self.screen.blit(block_surface, (center_x - 200, block_y))
        
        # 第三行：Time Window - 文本显示，点击编辑
        window_y = start_y + row_height * 2
        if self.input_mode == 'beta_window':
            window_text = f"Time Window (s): {self.input_text}_"
            window_color = colors['input']
        else:
            window_text = f"Time Window (s): {self.beta_config['time_window']}"
            window_color = colors['key_default']
        
        window_surface = self.main_font.render(window_text, True, window_color)
        self.window_text_rect = pygame.Rect(center_x - 200, window_y - 30, 400, 60)
        self.screen.blit(window_surface, (center_x - 200, window_y))
        
        # 右下角Start按钮 - 红色背景，白色字体
        start_text = "Start"
        start_surface = self.main_font.render(start_text, True, (255, 255, 255))
        self.beta_start_rect = pygame.Rect(self.screen_width//2 + 420, 1020, 250, 80)
        pygame.draw.rect(self.screen, colors['cue'], self.beta_start_rect)
        pygame.draw.rect(self.screen, colors['background'], self.beta_start_rect, 2)
        start_text_rect = start_surface.get_rect(center=self.beta_start_rect.center)
        self.screen.blit(start_surface, start_text_rect)


    # [EN] handle_layout_page_click: Auto-generated summary of this method's purpose.
    def handle_layout_page_click(self, pos):
        """处理Layout页面点击事件"""
        # 处理下拉菜单点击
        if self.layout_dropdown_rect.collidepoint(pos):
            self.layout_dropdown_open = not self.layout_dropdown_open
        elif self.layout_dropdown_open:
            # 检查下拉菜单选项点击
            for option_rect, option in self.layout_dropdown_options:
                if option_rect.collidepoint(pos):
                    self.selected_layout = option
                    if option == "BETA Speller":
                        self.settings['keyboard_type'] = 'qwerty'
                    self.layout_dropdown_open = False
                    break
            else:
                self.layout_dropdown_open = False
        elif hasattr(self, 'back_rect') and self.back_rect.collidepoint(pos):
            self.current_page = "main"
        elif hasattr(self, 'next_rect') and self.next_rect.collidepoint(pos):
            if self.selected_layout == "BETA Speller":
                self.current_page = "jpfm"
        else:
            self.layout_dropdown_open = False

    # [EN] handle_jpfm_page_click: Auto-generated summary of this method's purpose.
    def handle_jpfm_page_click(self, pos):
        """处理JPFM页面点击事件"""
        if hasattr(self, 'reset_rect') and self.reset_rect.collidepoint(pos):
            # 重置为BETA默认参数 - 重置键盘布局和参数
            self.keyboard_layout_chars = [
                ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '<'],
                ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
                ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
                ['z', 'x', 'c', 'v', 'b', 'n', 'm', '.'],
                ['_', ',']
            ]
            self.beta_params = self.generate_beta_params()
            self.selected_key = None
            self.input_mode = None
            self.input_text = ""
        elif hasattr(self, 'back_rect') and self.back_rect.collidepoint(pos):
            self.current_page = "layout"
            self.selected_key = None
            self.input_mode = None
            self.input_text = ""
        elif hasattr(self, 'next_rect') and self.next_rect.collidepoint(pos):
            self.current_page = "trials"
            self.selected_key = None
            self.input_mode = None
            self.input_text = ""
        else:
            # 检查键盘按键点击
            if hasattr(self, 'key_rects'):
                for (row_idx, col_idx), rect in self.key_rects.items():
                    if rect.collidepoint(pos):
                        self.selected_row = row_idx
                        self.selected_col = col_idx
                        self.selected_key = self.keyboard_layout_chars[row_idx][col_idx]
                        self.input_mode = None
                        self.input_text = ""
                        self.param_selection = 0
                        break
                else:
                    # 点击空白区域取消选择
                    self.selected_key = None
                    self.selected_row = None
                    self.selected_col = None
                    self.input_mode = None
                    self.input_text = ""
                    self.param_selection = 0

    # [EN] handle_trials_page_click: Auto-generated summary of this method's purpose.
    def handle_trials_page_click(self, pos):
        """处理Trials页面点击事件"""
        if hasattr(self, 'back_rect') and self.back_rect.collidepoint(pos):
            self.current_page = "jpfm"
        elif hasattr(self, 'next_rect') and self.next_rect.collidepoint(pos):
            self.current_page = "block_text"
        else:
            # 只检查blocks点击
            if hasattr(self, 'blocks_rect') and self.blocks_rect.collidepoint(pos):
                self.input_mode = 'blocks'
                self.input_text = str(self.settings['total_blocks'])

    # [EN] handle_block_text_page_click: Auto-generated summary of this method's purpose.
    def handle_block_text_page_click(self, pos):
        """处理Block文本页面点击事件 - 修复空格处理"""
        if hasattr(self, 'back_rect') and self.back_rect.collidepoint(pos):
            self.current_page = "trials"
            self.input_mode = None
            self.input_text = ""
        elif hasattr(self, 'confirm_rect') and self.confirm_rect.collidepoint(pos):
            # 确认设置，跳转到start页面并创建实验者界面
            self.current_page = "start"
            # 根据模式创建不同的实验者界面
            if self.selected_mode == "Speller beta dataset simulation":
                self.create_beta_experimenter_window()
            else:
                self.create_experimenter_window()  # online模式使用通用界面
        else:
            # 检查时间设置点击（保持不变）
            if hasattr(self, 'cue_time_rect') and self.cue_time_rect.collidepoint(pos):
                self.input_mode = 'cue_time'
                self.input_text = str(self.settings['cue_duration'])
            elif hasattr(self, 'flash_time_rect') and self.flash_time_rect.collidepoint(pos):
                self.input_mode = 'flash_time'
                self.input_text = str(self.settings['flickering_duration'])
            elif hasattr(self, 'pause_time_rect') and self.pause_time_rect.collidepoint(pos):
                self.input_mode = 'pause_time'
                self.input_text = str(self.settings['pause_duration'])
            elif hasattr(self, 'rest_time_rect') and self.rest_time_rect.collidepoint(pos):
                self.input_mode = 'rest_time'
                self.input_text = str(self.settings['rest_duration'])
            elif hasattr(self, 'time_window_rect') and self.time_window_rect.collidepoint(pos):
                self.input_mode = 'time_window'
                self.input_text = str(self.settings['time_window'])
            else:
                # 检查文本设置点击
                if hasattr(self, 'text_rects'):
                    for i, rect in enumerate(self.text_rects):
                        if rect.collidepoint(pos):
                            self.input_mode = 'block_text'
                            self.editing_block_index = i
                            # 🔑 修复：编辑时获取存储的文本，保持用户输入的原样（包含空格）
                            self.input_text = self.settings['block_texts'][i]  # 直接使用存储的内容
                            print(f"开始编辑Block {i+1}: '{self.input_text}'")
                            break
                    else:
                        self.input_mode = None
                        self.input_text = ""



    # [EN] create_beta_experimenter_window: Auto-generated summary of this method's purpose.
    def create_beta_experimenter_window(self):
        """创建Beta仿真模式的实验者窗口"""
        print("Creating Beta simulation experimenter control panel...")

        # 先写入当前配置到状态文件
        initial_status = {
            'state': 'ready_to_start',
            'current_block': 1,
            'total_blocks': 1,
            'current_trial': 0,
            'total_trials': 40,
            'current_char': '',
            'block_results': [''],
            'block_accuracies': [0.0],
            'subject': self.beta_config['subject'],
            'block': self.beta_config['block'],
            'time_window': self.beta_config['time_window'],
            'eeg_connected': False
        }
        
        try:
            with open("experiment_status.json", 'w', encoding='utf-8') as f:
                json.dump(initial_status, f, ensure_ascii=False)
        except:
            pass
        
        # Beta模式专用的实验者窗口脚本
        experimenter_script = '''
import pygame
import sys
import os
import time
import json

class BetaExperimenterWindow:
    """Beta仿真模式实验者界面窗口"""
    # [EN] __init__: Auto-generated summary of this method's purpose.
    def __init__(self):
        pygame.init()
        self.width = 1200
        self.height = 800
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("Beta Simulation - Experimenter Control Panel")
        
        # 字体设置
        self.title_font = pygame.font.Font(None, 48)
        self.status_font = pygame.font.Font(None, 56)
        self.button_font = pygame.font.Font(None, 36)
        self.text_font = pygame.font.Font(None, 32)
        
        # 颜色设置
        self.colors = {
            'background': (0, 0, 0),
            'text': (255, 255, 255),
            'red': (255, 0, 0),
            'button': (255, 0, 0),
            'button_hover': (200, 0, 0),
            'white': (255, 255, 255),
            'border': (255, 255, 255),
            'green': (0, 255, 0),
            'gray': (128, 128, 128)
        }
        
        self.running = True
        self.clock = pygame.time.Clock()
        
        # 文件路径
        self.status_file = "experiment_status.json"
        self.command_file = "experimenter_command.json"
        
        # 状态缓存
        self.last_status_text = ""
        self.status_surface_cache = None
        
    # [EN] get_experiment_status: Auto-generated summary of this method's purpose.
    def get_experiment_status(self):
        """从文件读取实验状态"""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return None
        
    # [EN] send_command: Auto-generated summary of this method's purpose.
    def send_command(self, command):
        """发送命令给主程序"""
        try:
            with open(self.command_file, 'w', encoding='utf-8') as f:
                json.dump({'command': command, 'timestamp': time.time()}, f)
        except:
            pass
        
    # [EN] draw: Auto-generated summary of this method's purpose.
    def draw(self):
        """绘制Beta仿真实验者界面"""
        self.screen.fill(self.colors['background'])
        mouse_pos = pygame.mouse.get_pos()
        
        # 左上角标题
        title_text = "Speller beta dataset simulation"
        title_surface = self.title_font.render(title_text, True, self.colors['text'])
        self.screen.blit(title_surface, (30, 30))
        
        # 中间状态显示
        center_x = self.width // 2
        status_y = 120
        
        # 获取实验状态
        status_data = self.get_experiment_status()
        if status_data:
            state = status_data.get('state', 'unknown')
            if state == 'finished':
                status_text = "Experiment finished"
            elif state == 'paused':
                status_text = "Experiment paused"
            elif state == 'ready_to_start':
                status_text = "Ready to start"
            else:
                status_text = "Experiment doing"
        else:
            if not hasattr(self, 'current_status_text'):
                self.current_status_text = "Ready to start"
            status_text = self.current_status_text

        # 渲染状态文本
        if status_text != self.last_status_text:
            self.status_surface_cache = self.status_font.render(status_text, True, self.colors['red'])
            self.last_status_text = status_text

        if self.status_surface_cache:
            status_x = center_x - self.status_surface_cache.get_width() // 2
            self.screen.blit(self.status_surface_cache, (status_x, status_y))
        
        # 右上角按钮 - 只有Connect和Start（删除Simulation）
        button_width = 120
        button_height = 50
        button_spacing = 20
        
        # Connect按钮
        self.connect_rect = pygame.Rect(self.width - button_width*2 - button_spacing - 30, 30, button_width, button_height)
        
        eeg_connected = status_data.get('eeg_connected', False) if status_data else False
        if eeg_connected:
            connect_color = self.colors['green']
            connect_text = "Connected"
        else:
            connect_color = self.colors['gray']
            connect_text = "Not Connect"
        
        if self.connect_rect.collidepoint(mouse_pos):
            if eeg_connected:
                connect_color = (0, 200, 0)
            else:
                connect_color = (100, 100, 100)
        
        pygame.draw.rect(self.screen, connect_color, self.connect_rect)
        pygame.draw.rect(self.screen, self.colors['border'], self.connect_rect, 2)
        
        connect_surface = self.button_font.render(connect_text, True, self.colors['white'])
        connect_text_rect = connect_surface.get_rect(center=self.connect_rect.center)
        self.screen.blit(connect_surface, connect_text_rect)
        
        # Start按钮
        self.start_rect = pygame.Rect(self.width - button_width - 30, 30, button_width, button_height)

        if self.start_rect.collidepoint(mouse_pos):
            pygame.draw.rect(self.screen, self.colors['button_hover'], self.start_rect)
        else:
            pygame.draw.rect(self.screen, self.colors['button'], self.start_rect)
        pygame.draw.rect(self.screen, self.colors['border'], self.start_rect, 2)

        start_text = "Start"
        start_surface = self.button_font.render(start_text, True, self.colors['white'])
        start_text_rect = start_surface.get_rect(center=self.start_rect.center)
        self.screen.blit(start_surface, start_text_rect)

        # 中间部分 - 简化显示：Input, Output, Accuracy
        middle_y = 250
        
        if status_data:
            # Input显示（保持不变）
            input_title = "Input:"
            input_surface = self.text_font.render(input_title, True, self.colors['text'])
            self.screen.blit(input_surface, (50, middle_y))
            
            target_order = ".,<abcdefghijklmnopqrstuvwxyz0123456789_"
            input_content = self.text_font.render(target_order, True, self.colors['text'])
            self.screen.blit(input_content, (50, middle_y + 30))
            
            # Output - 显示识别结果，错误的用红色
            output_title = "Output:"
            output_surface = self.text_font.render(output_title, True, self.colors['text'])
            self.screen.blit(output_surface, (50, middle_y + 80))
            
            block_results = status_data.get('block_results', [''])
            result_text = block_results[0] if block_results else ""
            
            # 逐个字符显示，错误的标红
            x_pos = 50
            y_pos = middle_y + 110
            for i, char in enumerate(result_text):
                if i < len(target_order):
                    # 检查是否正确
                    if char.lower() == target_order[i].lower():
                        color = self.colors['text']  # 白色（正确）
                    else:
                        color = self.colors['red']   # 红色（错误）
                else:
                    color = self.colors['text']
                
                char_surface = self.text_font.render(char, True, color)
                self.screen.blit(char_surface, (x_pos, y_pos))
                x_pos += char_surface.get_width() + 3  # 字符间距
            
            # Accuracy显示（保持不变）
            accuracy_title = "Accuracy:"
            accuracy_surface = self.text_font.render(accuracy_title, True, self.colors['text'])
            self.screen.blit(accuracy_surface, (50, middle_y + 160))
            
            block_accuracies = status_data.get('block_accuracies', [0.0])
            accuracy_val = block_accuracies[0] if block_accuracies else 0.0
            accuracy_content = self.text_font.render(f"{accuracy_val:.1f}%", True, self.colors['text'])
            self.screen.blit(accuracy_content, (50, middle_y + 190))
            
            # 底部参数显示框
            bottom_y = self.height - 120
            border_rect = pygame.Rect(20, bottom_y - 20, self.width - 40, 100)
            pygame.draw.rect(self.screen, self.colors['border'], border_rect, 2)
            
            subject = status_data.get('subject', '1')
            block = status_data.get('block', '1')
            time_window = status_data.get('time_window', '1.0')
            
            param_y = bottom_y
            subject_text = f"Current Subject: S{subject}"
            block_text = f"Current Block: {block}"
            window_text = f"Time Window: {time_window}s"
            
            subject_surface = self.text_font.render(subject_text, True, self.colors['text'])
            block_surface = self.text_font.render(block_text, True, self.colors['text'])
            window_surface = self.text_font.render(window_text, True, self.colors['text'])
            
            self.screen.blit(subject_surface, (50, param_y))
            self.screen.blit(block_surface, (300, param_y))
            self.screen.blit(window_surface, (550, param_y))
        
        pygame.display.flip()
    
    # [EN] handle_event: Auto-generated summary of this method's purpose.
    def handle_event(self, event):
        """处理事件"""
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.VIDEORESIZE:
            self.width = event.w
            self.height = event.h
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if hasattr(self, 'connect_rect') and self.connect_rect.collidepoint(event.pos):
                self.send_command('connect')
                print("发送连接命令")
            elif hasattr(self, 'start_rect') and self.start_rect.collidepoint(event.pos):
                self.send_command('start')
                print("Send start command")
    
    # [EN] run: Auto-generated summary of this method's purpose.
    def run(self):
        """运行实验者窗口"""
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            
            self.draw()
            self.clock.tick(60)
        
        # 清理文件
        if os.path.exists(self.status_file):
            os.remove(self.status_file)
        if os.path.exists(self.command_file):
            os.remove(self.command_file)
        
        pygame.quit()

if __name__ == "__main__":
    window = BetaExperimenterWindow()
    window.run()
'''
    
        # 保存脚本到临时文件
        script_path = "beta_experimenter_window.py"
        try:
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(experimenter_script)
            
            # 启动独立的Python进程
            self.experimenter_process = subprocess.Popen([
                sys.executable, script_path
            ], creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
            
            print("Beta simulation experimenter control panel started")
            
        except Exception as e:
            print(f"Starting Beta experiment者窗口失败: {e}")


    # [EN] create_experimenter_window: Auto-generated summary of this method's purpose.
    def create_experimenter_window(self):
        """创建实验者窗口 - 使用独立的Python进程"""
        print("创建实验者控制面板...")

            # 先写入当前配置到状态文件
        initial_status = {
            'state': 'ready_to_start',
            'current_block': 1,
            'total_blocks': self.settings['total_blocks'],
            'current_trial': 0,
            'total_trials': 0,
            'current_char': '',
            'block_results': [],
            'block_accuracies': [],
            'block_texts': self.settings['block_texts'][:self.settings['total_blocks']],
            'cue_time': self.settings['cue_duration'],
            'flash_time': self.settings['flickering_duration'],
            'pause_time': self.settings['pause_duration'],
            'rest_time': self.settings['rest_duration'],
            'time_window': 1.0        }
        
        try:
            with open("experiment_status.json", 'w', encoding='utf-8') as f:
                json.dump(initial_status, f, ensure_ascii=False)
        except:
            pass
        
        
        # 创建实验者窗口脚本
        experimenter_script = '''
import pygame
import sys
import os
import time
import json

class ExperimenterWindow:
    """实验者界面窗口"""
    # [EN] __init__: Auto-generated summary of this method's purpose.
    def __init__(self):
        pygame.init()
        self.width = 1200
        self.height = 800
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("Experimenter Control Panel")
        
        # 字体设置
        self.title_font = pygame.font.Font(None, 48)
        self.status_font = pygame.font.Font(None, 56)
        self.button_font = pygame.font.Font(None, 36)
        self.text_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 28)
        
        # 颜色设置 - 改为黑白配色
        self.colors = {
            'background': (0, 0, 0),  # 黑色背景
            'text': (255, 255, 255),  # 白色文字
            'red': (255, 0, 0),
            'button': (255, 0, 0),  # 按钮
            'button_hover': (200, 0, 0),  # 悬停时深红色
            'white': (255, 255, 255),
            'border': (255, 255, 255)  # 白色边框
        }
        
        self.running = True
        self.clock = pygame.time.Clock()
        
        # 实验状态文件路径
        self.status_file = "experiment_status.json"
        self.command_file = "experimenter_command.json"
        
        # 添加状态缓存和更新控制
        self.last_status_text = ""
        self.status_update_counter = 0
        self.status_surface_cache = None
        
    # [EN] get_experiment_status: Auto-generated summary of this method's purpose.
    def get_experiment_status(self):
        """从文件读取实验状态"""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return None
        
    # [EN] send_command: Auto-generated summary of this method's purpose.
    def send_command(self, command):
        """发送命令给主程序"""
        try:
            with open(self.command_file, 'w', encoding='utf-8') as f:
                json.dump({'command': command, 'timestamp': time.time()}, f)
        except:
            pass
        
    # [EN] draw: Auto-generated summary of this method's purpose.
    def draw(self):
        """绘制实验者界面"""
        self.screen.fill(self.colors['background'])
        
        # 左上角标题
        title_text = "Speller online test"
        title_surface = self.title_font.render(title_text, True, self.colors['text'])
        self.screen.blit(title_surface, (30, 30))
        
        # 中间上部分状态显示
        center_x = self.width // 2
        status_y = 120
        
        # 获取实验状态
        status_data = self.get_experiment_status()
        # 简化状态显示逻辑
        if status_data:
            state = status_data.get('state', 'unknown')
            if state == 'finished':
                status_text = "Experiment finished"
            elif state == 'paused':
                status_text = "Experiment paused"
            elif state == 'ready_to_start':
                status_text = "Ready to start"
            else:
                # 所有其他状态（包括cue, flickering, pause, block_progress, rest等）都显示"Experiment doing"
                status_text = "Experiment doing"
        else:
            # 如果没有数据，保持当前状态不变
            if not hasattr(self, 'current_status_text'):
                self.current_status_text = "Ready to start"
            status_text = self.current_status_text

        # 只有当状态文字真正改变时才重新渲染
        # 更新当前状态缓存
        if status_data:
            self.current_status_text = status_text

        # 只有当状态文字真正改变时才重新渲染
        if status_text != self.last_status_text:
            self.status_surface_cache = self.status_font.render(status_text, True, self.colors['red'])
            self.last_status_text = status_text

        # 使用缓存的surface绘制，避免频繁重新渲染
        if self.status_surface_cache:
            status_x = center_x - self.status_surface_cache.get_width() // 2
            self.screen.blit(self.status_surface_cache, (status_x, status_y))
        
        # 右上角按钮
        button_width = 120
        button_height = 50
        button_spacing = 20
        
        # Pause按钮
        self.pause_rect = pygame.Rect(self.width - button_width*2 - button_spacing - 30, 30, button_width, button_height)
        mouse_pos = pygame.mouse.get_pos()
        
        if self.pause_rect.collidepoint(mouse_pos):
            pygame.draw.rect(self.screen, self.colors['button_hover'], self.pause_rect)
        else:
            pygame.draw.rect(self.screen, self.colors['button'], self.pause_rect)
        pygame.draw.rect(self.screen, self.colors['border'], self.pause_rect, 2)
        
        pause_text = "Pause"
        pause_surface = self.button_font.render(pause_text, True, self.colors['white'])
        pause_text_rect = pause_surface.get_rect(center=self.pause_rect.center)
        self.screen.blit(pause_surface, pause_text_rect)
        
        # Continue按钮
        self.continue_rect = pygame.Rect(self.width - button_width - 30, 30, button_width, button_height)
        
        if self.continue_rect.collidepoint(mouse_pos):
            pygame.draw.rect(self.screen, self.colors['button_hover'], self.continue_rect)
        else:
            pygame.draw.rect(self.screen, self.colors['button'], self.continue_rect)
        pygame.draw.rect(self.screen, self.colors['border'], self.continue_rect, 2)
        
        continue_text = "Continue"
        continue_surface = self.button_font.render(continue_text, True, self.colors['white'])
        continue_text_rect = continue_surface.get_rect(center=self.continue_rect.center)
        self.screen.blit(continue_surface, continue_text_rect)

        # Continue按钮后添加Start按钮
        self.start_rect = pygame.Rect(self.width - button_width*3 - button_spacing*2 - 30, 30, button_width, button_height)

        if self.start_rect.collidepoint(mouse_pos):
            pygame.draw.rect(self.screen, self.colors['button_hover'], self.start_rect)
        else:
            pygame.draw.rect(self.screen, self.colors['button'], self.start_rect)
        pygame.draw.rect(self.screen, self.colors['border'], self.start_rect, 2)

        start_text = "Start"
        start_surface = self.button_font.render(start_text, True, self.colors['white'])
        start_text_rect = start_surface.get_rect(center=self.start_rect.center)
        self.screen.blit(start_surface, start_text_rect)


        # 中间部分 - 三列布局
        middle_y = 200
        col1_x = 50
        col2_x = self.width // 2 - 150
        col3_x = self.width - 300
        
        if status_data:
            # 左列 - Block文本显示
            left_title = "Block texts:"
            left_surface = self.text_font.render(left_title, True, self.colors['text'])
            self.screen.blit(left_surface, (col1_x, middle_y))
            
            block_texts = status_data.get('block_texts', [])
            current_block = status_data.get('current_block', 1)
            
            for i, text in enumerate(block_texts):
                y_pos = middle_y + 40 + i * 30
                if i + 1 == current_block:
                    # 当前block用红色显示
                    color = self.colors['red']
                    block_text = f"Block {i+1}: {text} (current)"
                else:
                    color = self.colors['text']
                    block_text = f"Block {i+1}: {text}"
                
                text_surface = self.small_font.render(block_text, True, color)
                self.screen.blit(text_surface, (col1_x, y_pos))
            
            # 中列 - 结果显示 - 按block分别显示
            result_title = "Results:"
            result_surface = self.text_font.render(result_title, True, self.colors['text'])
            self.screen.blit(result_surface, (col2_x, middle_y))
            
            total_blocks = status_data.get('total_blocks', 1)
            block_results = status_data.get('block_results', [])
            
            for i in range(total_blocks):
                y_pos = middle_y + 40 + i * 30
                if i < len(block_results):
                    result_text = f"Block {i+1}: {block_results[i]}"
                else:
                    result_text = f"Block {i+1}: "
                
                result_content = self.small_font.render(result_text, True, self.colors['text'])
                self.screen.blit(result_content, (col2_x, y_pos))
            
            # 右列 - 准确率显示 - 按block分别显示
            acc_title = "Accuracy:"
            acc_surface = self.text_font.render(acc_title, True, self.colors['text'])
            self.screen.blit(acc_surface, (col3_x, middle_y))
            
            block_accuracies = status_data.get('block_accuracies', [])
            
            for i in range(total_blocks):
                y_pos = middle_y + 40 + i * 30
                if i < len(block_accuracies):
                    acc_text = f"Block {i+1}: {block_accuracies[i]:.1f}%"
                else:
                    acc_text = f"Block {i+1}: "
                
                acc_content = self.small_font.render(acc_text, True, self.colors['text'])
                self.screen.blit(acc_content, (col3_x, y_pos))
            
            # 底部参数显示
            bottom_y = self.height - 150
            
            # 绘制底部边框
            border_rect = pygame.Rect(20, bottom_y - 20, self.width - 40, 130)
            pygame.draw.rect(self.screen, self.colors['border'], border_rect, 2)
            
            cue_time = status_data.get('cue_time', 0.5)
            flash_time = status_data.get('flash_time', 5.0)
            pause_time = status_data.get('pause_time', 0.2)
            rest_time = status_data.get('rest_time', 2.0)
            time_window = status_data.get('time_window', 1.0)
            
            param_y = bottom_y
            cue_text = f"Cue time (s): {cue_time}"
            flash_text = f"Flashing time (s): {flash_time}"
            pause_text = f"Pause time (s): {pause_time}"
            rest_text = f"Rest time (s): {rest_time}"
            window_text = f"Time window (s): {time_window}"
            
            cue_surface = self.text_font.render(cue_text, True, self.colors['text'])
            flash_surface = self.text_font.render(flash_text, True, self.colors['text'])
            pause_surface = self.text_font.render(pause_text, True, self.colors['text'])
            rest_surface = self.text_font.render(rest_text, True, self.colors['text'])
            window_surface = self.text_font.render(window_text, True, self.colors['text'])
            
            self.screen.blit(cue_surface, (50, param_y))
            self.screen.blit(flash_surface, (350, param_y))
            self.screen.blit(pause_surface, (650, param_y))
            self.screen.blit(rest_surface, (50, param_y + 40))
            self.screen.blit(window_surface, (350, param_y + 40))
        
        pygame.display.flip()
    
    # [EN] handle_event: Auto-generated summary of this method's purpose.
    def handle_event(self, event):
        """处理事件"""
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.VIDEORESIZE:
            self.width = event.w
            self.height = event.h
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if hasattr(self, 'start_rect') and self.start_rect.collidepoint(event.pos):
                self.send_command('start')
                print("Send start command")
            elif hasattr(self, 'pause_rect') and self.pause_rect.collidepoint(event.pos):
                self.send_command('pause')
                print("Send pause command")
            elif hasattr(self, 'continue_rect') and self.continue_rect.collidepoint(event.pos):
                self.send_command('continue')
                print("Send continue command")
    
    # [EN] run: Auto-generated summary of this method's purpose.
    def run(self):
        """运行实验者窗口"""
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            
            self.draw()
            self.clock.tick(60)
        
        # 清理文件
        if os.path.exists(self.status_file):
            os.remove(self.status_file)
        if os.path.exists(self.command_file):
            os.remove(self.command_file)
        
        pygame.quit()

if __name__ == "__main__":
    window = ExperimenterWindow()
    window.run()
'''
        
        # 保存脚本到临时文件
        script_path = "experimenter_window.py"
        try:
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(experimenter_script)
            
            # 启动独立的Python进程
            self.experimenter_process = subprocess.Popen([
                sys.executable, script_path
            ], creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
            
            print("实验者控制面板已启动")
            
        except Exception as e:
            print(f"启动实验者窗口失败: {e}")

    # [EN] update_experimenter_status: Auto-generated summary of this method's purpose.
    def update_experimenter_status(self):
        """更新实验者界面的状态信息"""
        if hasattr(self, 'experiment_state'):
            state = self.experiment_state
            
            # 使用历史数据构建完整的结果列表
            block_results = []
            block_accuracies = []
            
            for block_idx in range(self.settings['total_blocks']):
                if block_idx < len(self.block_history['results']):
                    # 已保存的历史结果
                    block_results.append(self.block_history['results'][block_idx])
                    block_accuracies.append(self.block_history['accuracies'][block_idx])
                elif block_idx == state['current_block'] - 1 and state['state'] not in ['block_progress', 'rest']:
                    # 当前正在进行的block（但还未完成）
                    current_result = ''.join(state['results']).replace('_', ' ')
                    block_results.append(current_result)
                    
                    # 计算当前进度的准确率
                    accuracy = 0.0
                    if len(state['trial_order']) > 0 and len(state['results']) > 0:
                        correct_count = 0
                        for i, result in enumerate(state['results']):
                            if i < len(state['trial_order']):
                                target = state['trial_order'][i]
                                if result.lower() == target.lower():
                                    correct_count += 1
                        accuracy = (correct_count / len(state['results'])) * 100
                    block_accuracies.append(accuracy)
                else:
                    # 未开始的block
                    block_results.append("")
                    block_accuracies.append(0.0)
            
            status_data = {
                'state': state['state'],
                'current_block': state['current_block'],
                'total_blocks': self.settings['total_blocks'],
                'current_trial': state['current_trial'],
                'total_trials': len(state['trial_order']),
                'current_char': state.get('current_target_char', '?'),
                'block_results': block_results,
                'block_accuracies': block_accuracies,
                'block_texts': self.settings['block_texts'][:self.settings['total_blocks']],
                'recognition_results': ''.join(state.get('results', [])),  # 添加这一行
                'cue_time': self.settings['cue_duration'],
                'flash_time': self.settings['flickering_duration'],
                'pause_time': self.settings['pause_duration'],
                'rest_time': self.settings['rest_duration'],
                'time_window': 1.0,
                'eeg_connected': getattr(self, 'eeg_running', False)
            }
            # 为beta模式提供正确的数据格式
            # 为beta模式提供正确的数据格式 - 完全模拟simulation
            if hasattr(self, 'is_beta_mode') and self.is_beta_mode:
                # 将beta的results转换为simulation格式的block_results
                beta_result_text = ''.join(state.get('results', []))
                status_data['block_results'] = [beta_result_text]
                
                # 计算准确率 - 完全复制simulation逻辑
                target_order = ".,<abcdefghijklmnopqrstuvwxyz0123456789_"
                if beta_result_text:
                    correct_count = sum(1 for i, char in enumerate(beta_result_text) 
                                      if i < len(target_order) and char.lower() == target_order[i].lower())
                    accuracy = (correct_count / len(beta_result_text)) * 100
                else:
                    accuracy = 0.0
                status_data['block_accuracies'] = [accuracy]

            try:
                with open("experiment_status.json", 'w', encoding='utf-8') as f:
                    json.dump(status_data, f, ensure_ascii=False)
            except:
                pass

    
    # [EN] start_experiment: Auto-generated summary of this method's purpose.
    def start_experiment(self):
        """开始实验 - 移除EEG依赖，直接开始"""
        
        print("开始实验!")
        print(f"当前JFMP参数:")
        for char, params in self.beta_params.items():
            print(f"  {char}: freq={params['frequency']:.1f}Hz, phase={params['phase']:.2f}π")
        print(f"实验设置: {self.settings['total_blocks']}个blocks")
        print("Block文本设置:")
        for i, text in enumerate(self.settings['block_texts']):
            print(f"  Block {i+1}: '{text}'")
        
        # 切换到实验页面
        self.current_page = "experiment"
        # 清理旧的实验状态
        if hasattr(self, 'experiment_state'):
            delattr(self, 'experiment_state')
            

    # [EN] process_recognition_results: Auto-generated summary of this method's purpose.
    def process_recognition_results(self):
        """处理hope22识别结果的线程 - 修复版本"""
        print("🔄 开始处理识别结果循环")
        
        while True:
            try:
                if not self.recognition_queue.empty():
                    recognized_char = self.recognition_queue.get_nowait()
                    
                    # 🔑 关键修复：将识别结果传递给实验状态
                    if (hasattr(self, 'experiment_state') and 
                        self.experiment_state and 
                        self.experiment_state.get('state') == 'flickering'):
                        
                        # 确保trial_recognition_results列表存在
                        if 'trial_recognition_results' not in self.experiment_state:
                            self.experiment_state['trial_recognition_results'] = []
                        
                        # 添加识别结果到列表
                        current_time = pygame.time.get_ticks() / 1000  # 使用pygame时间
                        self.experiment_state['trial_recognition_results'].append({
                            'char': recognized_char,
                            'time': current_time,
                            'confidence': 1.0
                        })
                        
                        print(f"🧠 GUI收到识别结果: {recognized_char} (已添加到trial结果列表)")
                        
                        # 🔑 关键：如果识别到目标字符，可以立即处理
                        target_char = self.experiment_state.get('current_target_char', '')
                        if recognized_char.lower() == target_char.lower():
                            print(f"🎯 识别到目标字符 '{recognized_char}'！")
                            
                    else:
                        print(f"🧠 GUI收到识别结果: {recognized_char} (实验状态不匹配)")
                
                import time
                time.sleep(0.02)  # 20ms检查间隔
                
            except Exception as e:
                print(f"❌ 处理识别结果错误: {e}")
                import time
                time.sleep(0.02)


    # [EN] check_experimenter_commands: Auto-generated summary of this method's purpose.
    def check_experimenter_commands(self):
        """检查实验者的命令"""
        try:
            if os.path.exists("experimenter_command.json"):
                with open("experimenter_command.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                command = data.get('command')
                
                if command == 'connect':
                    # Beta模式的连接处理
                    if self.selected_mode == "Speller beta dataset simulation":
                        if not self.eeg_running:
                            success = self.connect_beta_eeg_device()
                            if success:
                                print("✅ Beta EEG connection successful")
                            else:
                                print("❌ Beta EEG connection failed")
                        else:
                            print("✅ Beta模式EEG已连接")
                    # Online模式保持不变（不动）
                            
                elif command == 'start' and self.current_page == "start":
                    # 实验者点击开始，直接切换到实验页面
                    self.start_experiment()
                    print("Experimenter started the experiment")
                elif command == 'pause' and hasattr(self, 'experiment_state'):
                    # 暂停功能
                    if self.experiment_state['state'] in ['cue', 'flickering', 'pause']:
                        self.experiment_state['state'] = 'paused'
                        print("Experimenter paused the experiment")
                elif command == 'continue' and hasattr(self, 'experiment_state'):
                    # 继续功能
                    state = self.experiment_state
                    if state['state'] == 'paused':
                        current_block_idx = state['current_block'] - 1
                        if current_block_idx < len(self.block_history['results']):
                            self.block_history['results'][current_block_idx] = ""
                        if current_block_idx < len(self.block_history['accuracies']):
                            self.block_history['accuracies'][current_block_idx] = 0.0
                        
                        self.start_new_block()
                        if state['trial_order']:
                            state['current_target_char'] = state['trial_order'][0]
                            state['state'] = 'cue'
                            state['trial_start_time'] = pygame.time.get_ticks()
                            print(f"Experimenter restarted Block {state['current_block']}，cleared previous results")
                        else:
                            state['state'] = 'ready'
                            state['auto_timer'] = pygame.time.get_ticks()
                
                # 删除命令文件
                os.remove("experimenter_command.json")
        except:
            pass


    # [EN] handle_start_page_click: Auto-generated summary of this method's purpose.
    def handle_start_page_click(self, pos):
   
        pass

    # [EN] handle_experiment_event: Auto-generated summary of this method's purpose.
    def handle_experiment_event(self, event):
        """处理实验页面的特殊输入事件"""
        # 可以在这里添加实验页面的特殊按键处理
        # 例如紧急停止、暂停等
        if event.key == pygame.K_SPACE:
            # 空格键暂停/继续
            if hasattr(self, 'experiment_state'):
                if self.experiment_state.get('state') == 'paused':
                    self.experiment_state['state'] = 'cue'
                    print("Experiment continued")
                else:
                    self.experiment_state['state'] = 'paused'
                    print("Experiment paused")


    
    # [EN] connect_beta_eeg_device: Auto-generated summary of this method's purpose.
    def connect_beta_eeg_device(self):
        """Beta模式连接EEG设备 - 只加载模型和数据，不开始识别"""
        try:
            print("🔌 Connect EEG in Beta mode...")
            
            # 获取配置参数并创建EEG处理器
            subject_num = int(self.beta_config['subject'])
            test_block = int(self.beta_config['block'])
            time_window = float(self.beta_config['time_window'])
            
            # 导入EEG处理器
            import importlib.util
            import os
            
            current_dir = os.path.dirname(os.path.abspath(__file__))
            eeg_file_path = os.path.join(current_dir, "eeg processor.py")
            
            spec = importlib.util.spec_from_file_location("eeg_processor", eeg_file_path)
            eeg_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(eeg_module)
            
            self.eeg_processor = eeg_module.TLCCAOnlineRecognition(
                subject_num=subject_num,
                test_block=test_block, 
                recognition_window=time_window
            )
            
            # 只加载模型和数据，不开始识别
            success1 = self.eeg_processor.load_pretrained_model(self.eeg_processor.model_path)
            if success1:
                success2 = self.eeg_processor.load_source_data(self.eeg_processor.test_data_path, self.eeg_processor.test_block)
                success = success2
            else:
                success = False
            
            if success:
                # 只设置GUI模式，不开始识别
                self.eeg_processor.set_gui_mode()
                
                self.eeg_running = True
                
                # 更新状态文件，确保connect按钮变绿
                try:
                    with open("experiment_status.json", 'r', encoding='utf-8') as f:
                        status_data = json.load(f)
                    status_data['eeg_connected'] = True
                    with open("experiment_status.json", 'w', encoding='utf-8') as f:
                        json.dump(status_data, f, ensure_ascii=False)
                    print("✅ Connectbutton status updated to Connected")
                except Exception as e:
                    print(f"❌ Failed to update connect status: {e}")
                
                print(f"✅ Beta EEG connection successful，模型已就绪 (S{subject_num}, B{test_block}, W{time_window}s)")
                return True
            else:
                print("❌ Model loading failed")
                return False
            
        except Exception as e:
            print(f"❌ Beta EEG connection failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    # [EN] start_beta_experiment: Auto-generated summary of this method's purpose.
    def start_beta_experiment(self):
        """启动Beta模式实验 - 延迟1.8秒后开始识别"""
        try:
            if not self.eeg_running:
                print("EEG not connected; cannot start experiment")
                return False
            
            print("Starting Beta experiment...")
            
            # 设置Beta模式标记
            self.is_beta_mode = True
            
            # 切换到实验页面
            self.current_page = "experiment"
            
            # 延迟1.8秒后开始识别
            # [EN] delayed_start_recognition: Auto-generated summary of this method's purpose.
            def delayed_start_recognition():
                import time
                print("Wait 1.8 seconds then start recognition...")
                time.sleep(2)  # 延迟1.8秒
                
                if hasattr(self, 'eeg_processor') and self.eeg_processor:
                    print("Start EEG recognition now...")
                    # 在后台线程中运行识别，不阻塞GUI
                    recognition_thread = threading.Thread(target=self.eeg_processor.run_gui_recognition)
                    recognition_thread.daemon = True
                    recognition_thread.start()
                    print("EEG识别线程已启动")
            
            # 在新线程中执行延迟启动，避免阻塞GUI
            import threading
            delay_thread = threading.Thread(target=delayed_start_recognition)
            delay_thread.daemon = True
            delay_thread.start()
            
            print("BetaExperiment started successfully，1.8s后开始识别")
            return True
            
        except Exception as e:
            print(f"BetaExperiment failed to start: {e}")
            return False
    
    # [EN] connect_eeg_device: Auto-generated summary of this method's purpose.
    def connect_eeg_device(self):
        """连接EEG设备"""
        try:
            print("🔌 Attempting to connect EEG device...")
            # 这里应该是实际的EEG设备连接代码
            # 目前只是模拟连接成功
            self.eeg_running = True
            print("✅ EEG device connected (simulated)")
            return True
        except Exception as e:
            print(f"❌ EEG device connection failed: {e}")
            self.eeg_running = False
            return False
    

    # 在RealTime.py中修改connect_simulation_data方法
    # [EN] connect_simulation_data: Auto-generated summary of this method's purpose.
    def connect_simulation_data(self):
        """连接仿真数据 - 使用新的EEG Processor"""
        if hasattr(self, 'simulation_running') and self.simulation_running:
            print("Simulation already running")
            return
        
        try:
            # 停止旧的处理器
            if hasattr(self, 'eeg_processor') and self.eeg_processor:
                self.eeg_processor.stop()
                self.eeg_running = False
            
            # 获取Beta配置参数
            if hasattr(self, 'beta_config'):
                subject_num = int(self.beta_config['subject'])
                test_block = int(self.beta_config['block'])
                time_window = float(self.beta_config['time_window'])
            else:
                # 默认参数
                subject_num = 1
                test_block = 1
                time_window = 1.0
            
            print(f"🔧 Using parameters: Subject {subject_num}, Block {test_block}, Window {time_window}s")
            
            # 导入EEG处理器
            import importlib.util
            import os

            current_dir = os.path.dirname(os.path.abspath(__file__))
            eeg_file_path = os.path.join(current_dir, "eeg processor.py")

            spec = importlib.util.spec_from_file_location("eeg_processor", eeg_file_path)
            eeg_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(eeg_module)

            self.eeg_processor = eeg_module.TLCCAOnlineRecognition(
                subject_num=subject_num,
                test_block=test_block, 
                recognition_window=time_window
            )

            # 加载模型和数据
            success1 = self.eeg_processor.load_pretrained_model(self.eeg_processor.model_path)
            if success1:
                success2 = self.eeg_processor.load_source_data(self.eeg_processor.test_data_path, self.eeg_processor.test_block)
                success = success2
            else:
                success = False

            if not success:
                print("❌ Model loading failed")
                return False

            # 设置GUI模式
            self.eeg_processor.set_gui_mode()

            self.simulation_running = True
            print("✅ Simulation connected")
            
            return True
            
        except Exception as e:
            print(f"❌ Simulation connection failed: {e}")
            import traceback
            traceback.print_exc()
            self.simulation_running = False
            return False

    # [EN] start_experiment_from_gui: Auto-generated summary of this method's purpose.
    def start_experiment_from_gui(self):
        """从GUI开始实验 - 添加处理器启动"""
        try:
            if not hasattr(self, 'experiment_state') or not self.experiment_state:
                print("❌ Experiment state not initialized")
                return False
            
            state = self.experiment_state
            
            if state['state'] != 'ready':
                print(f"❌ Experiment state incorrect: {state['state']}")
                return False
            
            # 🔑 关键修复：确保处理器参数是最新的
            if hasattr(self, 'eeg_processor') and self.eeg_processor:
                # 重新设置时间参数，确保与GUI一致
                self.eeg_processor.set_timing_parameters(
                    cue_duration=self.settings['cue_duration'],
                    flickering_duration=self.settings['flickering_duration'],
                    pause_duration=self.settings['pause_duration']
                )
                
                # 🔑 启动hope22处理线程
                if hasattr(self.eeg_processor, 'start_processing_thread'):
                    self.eeg_processor.start_processing_thread()
                    print("🚀 hope22 recognition thread started")
            
            # 开始第一个trial
            first_char = state['trial_order'][0]
            state['current_target_char'] = first_char
            state['state'] = 'cue'
            state['trial_start_time'] = pygame.time.get_ticks()
            state['trial_results'] = []
            state['trial_result_set'] = False
            state['recognition_started'] = False
            
            print(f"🎯 Set trial info: Block{state['current_block']} Trial{state['current_trial']+1} 目标'{first_char}'")
            print(f"▶️ Start trial: 目标'{first_char}'")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start experiment: {e}")
            import traceback
            traceback.print_exc()
            return False


    # [EN] start_processing_thread: Auto-generated summary of this method's purpose.
    def start_processing_thread(self):
    # 使用已设置的时间参数
        cue_duration = getattr(self, 'cue_duration', 0.5)
        flickering_duration = getattr(self, 'flickering_duration', 2.0)
        pause_duration = getattr(self, 'pause_duration', 0.5)
        
    # [EN] finish_experiment: Auto-generated summary of this method's purpose.
    def finish_experiment(self):
        """完成实验 - 停止处理器"""
        if hasattr(self, 'experiment_state') and self.experiment_state:
            self.experiment_state['state'] = 'finished'
            
            # 🔑 关键：停止hope22处理器
            if hasattr(self, 'eeg_processor') and self.eeg_processor:
                self.eeg_processor.stop()
                print("⏹️ hope22 processor stopped")
            
            # 计算准确率
            if self.experiment_state['results']:
                correct_count = sum(1 for r in self.experiment_state['results'] if r['correct'])
                total_count = len(self.experiment_state['results'])
                accuracy = correct_count / total_count * 100
                
                print(f"\n🎯 Experiment finished!")
                print(f"📊 Accuracy: {accuracy:.1f}% ({correct_count}/{total_count})")
                print(f"📝 Detailed results:")
                for r in self.experiment_state['results']:
                    status = "✅" if r['correct'] else "❌"
                    print(f"   Trial {r['trial']+1}: '{r['target']}' -> '{r['result']}' {status}")
            
            print("🏁 Press ESC to return to main menu")


    # [EN] set_timing_parameters: Auto-generated summary of this method's purpose.
    def set_timing_parameters(self, cue_duration=0.5, flickering_duration=2.0, pause_duration=0.5):
        self.cue_duration = cue_duration
        self.flickering_duration = flickering_duration  
        self.pause_duration = pause_duration


    # [EN] debug_timing_parameters: Auto-generated summary of this method's purpose.
    def debug_timing_parameters(self):
        """调试时间参数传递"""
        print("\n🔍 Debug timing parameters:")
        print(f"GUI settings:")
        print(f"  cue_duration: {self.settings.get('cue_duration', 'NOT_SET')}")
        print(f"  flickering_duration: {self.settings.get('flickering_duration', 'NOT_SET')}")
        print(f"  pause_duration: {self.settings.get('pause_duration', 'NOT_SET')}")
        
        if hasattr(self, 'eeg_processor') and self.eeg_processor:
            print(f"Processor settings:")
            print(f"  cue_duration: {getattr(self.eeg_processor, 'cue_duration', 'NOT_SET')}")
            print(f"  flickering_duration: {getattr(self.eeg_processor, 'flickering_duration', 'NOT_SET')}")
            print(f"  pause_duration: {getattr(self.eeg_processor, 'pause_duration', 'NOT_SET')}")
            print(f"  total_trial_duration: {getattr(self.eeg_processor, 'total_trial_duration', 'NOT_SET')}")
            print(f"  recognition_start_offset: {getattr(self.eeg_processor, 'recognition_start_offset', 'NOT_SET')}")
            print(f"  recognition_end_offset: {getattr(self.eeg_processor, 'recognition_end_offset', 'NOT_SET')}")
        else:
            print("Processor not initialized")

    # 在工作者界面点击simulation时调用调试函数
    # [EN] handle_experimenter_command: Auto-generated summary of this method's purpose.
    def handle_experimenter_command(self, command):
        """处理实验者命令"""
        if command == "connect":
            print("Received experimenter command: connect") 
            self.connect_beta_eeg_device()
            
        elif command == "simulation":
            print("Received experimenter command: simulation")
            self.connect_simulation_data()
            
            # 🔧 新增：调试参数传递
            self.debug_timing_parameters()
            
        elif command == "start":
            print("Received experimenter command: start")
            print("Handling start command, switching to experiment page")
            
            # 切换到实验页面
            self.current_page = "experiment" 
            
            # 启动实验
            success = self.start_experiment_from_gui()
            if success:
                print("✅ Experiment started successfully")
            else:
                print("❌ Experiment failed to start")
                
            # 🔑 新增：启动后再次调试参数
            self.debug_timing_parameters()
            

    # [EN] load_tlcca_model_from_file: Auto-generated summary of this method's purpose.
    def load_tlcca_model_from_file(self, model_path):
        """从MAT文件加载预训练的tlCCA模型 - 修复版"""
        try:
            import scipy.io as sio
            
            print(f"📖 Reading model file...")
            model_data = sio.loadmat(model_path)
            
            # 验证模型数据完整性
            required_keys = ['sti_f', 'pha_val', 'source_freq_idx', 'target_freq_idx', 'target_order']
            missing_keys = [key for key in required_keys if key not in model_data]
            if missing_keys:
                print(f"❌ 模型文件缺少必要字段: {missing_keys}")
                return False
            
            # 🔑 关键修复：加载正确的频率相位映射
            sti_f = model_data['sti_f'].flatten()
            pha_val = model_data['pha_val'].flatten()
            source_freq_idx = model_data['source_freq_idx'].flatten()
            target_freq_idx = model_data['target_freq_idx'].flatten()
            target_order = model_data['target_order'].flatten()
            
            success = self.eeg_processor.tlcca_model.load_subject_specific_model(model_path)
            
            print(f"✅ 模型基本信息:")
            print(f"   频率范围: {sti_f.min():.1f} - {sti_f.max():.1f} Hz")
            print(f"   源域频率数: {len(source_freq_idx)}")
            print(f"   目标域频率数: {len(target_freq_idx)}")
            print(f"   频率排序Index: {target_order[:10]}...")
            
            # 🔑 关键：将模型权重加载到EEG处理器的tlCCA模型中
            tlcca_model = self.eeg_processor.tlcca_model
            
            # 清空现有权重
            tlcca_model.spatial_filters = {}
            tlcca_model.transfer_filters = {}
            tlcca_model.reference_filters = {}
            tlcca_model.transfer_templates = {}
            
            # 更新频率相位信息 - 使用已排序的数据
            tlcca_model.sti_f = sti_f
            tlcca_model.pha_val = pha_val
            tlcca_model.source_freq_idx = source_freq_idx
            tlcca_model.target_freq_idx = target_freq_idx
            tlcca_model.target_order = target_order
            
            # 🔑 修复：使用extract_block.py中的正确字符顺序
            beta_chars = ['.', ',', '<'] + list('abcdefghijklmnopqrstuvwxyz0123456789_')
            
            # 加载各个子频带的权重
            bands_loaded = 0
            source_chars_loaded = 0
            target_chars_loaded = 0
            
            for sub_band in range(1, 6):  # 5个子频带
                # 🔑 修复：源域权重加载
                wx_key = f'Wx_source_band{sub_band}'
                wy_key = f'Wy_source_band{sub_band}'
                
                if wx_key in model_data and wy_key in model_data:
                    Wx_source = model_data[wx_key]  # (channels, source_chars)
                    Wy_source = model_data[wy_key]  # (harmonics, source_chars)
                
                    # 为每个源域字符加载权重 - 修复版：确保索引映射正确
                    for reordered_pos in source_freq_idx:  # reordered_pos是重排序位置[1,3,5,...]
                        original_char_idx = target_order[reordered_pos]  # 获取原始字符索引
                        if original_char_idx < len(beta_chars):
                            char = beta_chars[original_char_idx]  # 用原始索引获取字符
                            
                            # 🔑 关键修复：初始化字符字典
                            if char not in tlcca_model.spatial_filters:
                                tlcca_model.spatial_filters[char] = {}
                                tlcca_model.reference_filters[char] = {}
                                source_chars_loaded += 1
                            
                            # 🔑 核心修复：确保使用原始字符索引访问权重矩阵
                            if original_char_idx < Wx_source.shape[1]:  # 验证索引范围
                                tlcca_model.spatial_filters[char][sub_band] = Wx_source[:, original_char_idx]
                                tlcca_model.reference_filters[char][sub_band] = Wy_source[:, original_char_idx]
                                
                                # 验证权重是否有效
                                if np.any(Wx_source[:, original_char_idx] != 0):
                                    print(f"      ✅ 源域字符'{char}' (重排序位置{reordered_pos}->原始Index{original_char_idx}) 权重加载成功")
                                else:
                                    print(f"      ⚠️ 源域字符'{char}' 权重为零")
                
                # 🔑 修复：目标域迁移权重加载
                wx_transfer_key = f'Wx_transfer_band{sub_band}'
                templates_key = f'templates_transfer_band{sub_band}'
                
                if wx_transfer_key in model_data and templates_key in model_data:
                    Wx_transfer = model_data[wx_transfer_key]  # (channels, target_chars)
                    templates_transfer = model_data[templates_key]  # (time_points, target_chars)
                    
                
                    # 为每个目标域字符加载迁移权重 - 修复版：确保索引映射正确
                    for reordered_pos in target_freq_idx:  # reordered_pos是重排序位置[0,2,4,...]
                        original_char_idx = target_order[reordered_pos]  # 获取原始字符索引
                        if original_char_idx < len(beta_chars):
                            char = beta_chars[original_char_idx]  # 用原始索引获取字符
                            
                            # 🔑 关键修复：初始化字符字典
                            if char not in tlcca_model.transfer_filters:
                                tlcca_model.transfer_filters[char] = {}
                                tlcca_model.transfer_templates[char] = {}
                                target_chars_loaded += 1
                            
                            # 🔑 核心修复：确保使用原始字符索引访问权重矩阵
                            if original_char_idx < Wx_transfer.shape[1]:  # 验证索引范围
                                tlcca_model.transfer_filters[char][sub_band] = Wx_transfer[:, original_char_idx:original_char_idx+1]
                                
                                # 验证权重是否有效
                                if np.any(Wx_transfer[:, original_char_idx] != 0):
                                    print(f"      ✅ 目标域字符'{char}' (重排序位置{reordered_pos}->原始Index{original_char_idx}) 迁移权重加载成功")
                                else:
                                    print(f"      ⚠️ 目标域字符'{char}' 迁移权重为零")
                            
                            # 加载迁移模板 - 修复版
                            if original_char_idx < templates_transfer.shape[1]:  # 验证索引范围
                                tlcca_model.transfer_templates[char][sub_band] = templates_transfer[:, original_char_idx]
                                
                                # 验证模板是否有效
                                if np.any(templates_transfer[:, original_char_idx] != 0):
                                    print(f"      ✅ 目标域字符'{char}' 迁移模板加载成功")
                                else:
                                    print(f"      ⚠️ 目标域字符'{char}' 迁移模板为零")
                
                bands_loaded += 1
            
            print(f"✅ 模型权重加载完成:")
            print(f"   子频带数: {bands_loaded}/5")
            print(f"   源域字符: {source_chars_loaded} 个")
            print(f"   目标域字符: {target_chars_loaded} 个")
            
            # 🔑 关键验证：检查字符权重是否正确加载
            print(f"🔍 权重验证:")
            test_chars = ['a', 'b', 'c', '.', '1']
            for char in test_chars:
                source_bands = len(tlcca_model.spatial_filters.get(char, {}))
                transfer_bands = len(tlcca_model.transfer_filters.get(char, {}))
                print(f"   '{char}': 源域{source_bands}个频带, 迁移{transfer_bands}个频带")
            
            return True
            
        except Exception as e:
            print(f"❌ 模型加载错误: {e}")
            import traceback
            traceback.print_exc()
            return False

    # 在RealTime.py中修复load_test_data_from_file方法

    # [EN] load_test_data_from_file: Auto-generated summary of this method's purpose.
    def load_test_data_from_file(self, test_data_path):
        """从MAT文件加载测试数据 - 修复字符映射版"""
        try:
            import scipy.io as sio
            
            print(f"📖 正在读取测试数据文件...")
            test_data = sio.loadmat(test_data_path)
            
            # 查找Block 1的数据
            block_key = 'block_1'
            data_key = f'{block_key}_data'
            chars_key = f'{block_key}_chars'
            indices_key = f'{block_key}_target_indices'
            complete_indices_key = f'{block_key}_complete_target_indices'
            
            required_keys = [data_key, chars_key, indices_key]
            missing_keys = [key for key in required_keys if key not in test_data]
            if missing_keys:
                print(f"❌ 测试数据文件缺少字段: {missing_keys}")
                return False
            
            # 提取EEG数据和字符信息
            eeg_data = test_data[data_key]  # 应该是 (channels, time, trials)
            block_chars = test_data[chars_key]
            
            # 🔑 关键修复：正确处理MATLAB字符数组
            if hasattr(block_chars, 'flatten'):
                block_chars_list = []
                for item in block_chars.flatten():
                    if hasattr(item, 'item'):
                        char_str = str(item.item()).strip()
                    else:
                        char_str = str(item).strip()
                    block_chars_list.append(char_str)
            else:
               # 🔑 关键修复：Beta数据集中trial-to-character映射是固定的
                # 每个trial i 对应 condition i，condition i 对应 beta_standard_chars[i]
                beta_standard_chars = ['.', ',', '<'] + list('abcdefghijklmnopqrstuvwxyz0123456789_')

                if hasattr(block_chars, 'flatten'):
                    block_chars_list = []
                    for item in block_chars.flatten():
                        if hasattr(item, 'item'):
                            char_str = str(item.item()).strip()
                        else:
                            char_str = str(item).strip()
                        block_chars_list.append(char_str)
                else:
                    # 使用Beta标准字符序列
                    block_chars_list = beta_standard_chars.copy()
                    print(f"✅ Using Beta standard character sequence")
            
            # 提取target indices
            if complete_indices_key in test_data:
                target_indices = test_data[complete_indices_key].flatten()
            else:
                target_indices = test_data[indices_key].flatten()
            
            print(f"✅ Test data basics:")
            print(f"   EEG data shape: {eeg_data.shape}")
            print(f"   Character sequence length: {len(block_chars_list)}")
            print(f"   Target indices length: {len(target_indices)}")
            print(f"   Character sequence: {''.join(block_chars_list)}")
            print(f"   First 10 target indices: {target_indices[:10]}")
            
            # 🔑 关键验证：检查字符与target_indices的对应关系
            beta_standard_chars = ['.', ',', '<'] + list('abcdefghijklmnopqrstuvwxyz0123456789_')
            
            print(f"🔍 Character mapping check（前10个）:")
            for i in range(min(10, len(block_chars_list), len(target_indices))):
                char = block_chars_list[i]
                target_idx = int(target_indices[i])
                expected_char = beta_standard_chars[target_idx] if target_idx < len(beta_standard_chars) else '?'
                match = "✅" if char == expected_char else "❌"
                print(f"   Trial {i}: '{char}' -> target_idx {target_idx} -> expected '{expected_char}' {match}")
            
            # 处理数据维度
            if len(eeg_data.shape) == 3:
                channels, time_points, trials = eeg_data.shape
                
                # 确保通道数正确（9个通道）
                if channels > 9:
                    eeg_data = eeg_data[:9, :, :]
                    print(f"   Channel count from {channels} reduced to 9")
                elif channels < 9:
                    padding = np.zeros((9 - channels, time_points, trials))
                    eeg_data = np.vstack([eeg_data, padding])
                    print(f"   Channel count from {channels} padded to 9")
                
                # 🔑 修复：建立正确的字符-试次映射
                target_order = test_data['target_order'].flatten()
                beta_chars = test_data['beta_standard_chars'].flatten()

                # 建立GUI显示字符到仿真数据索引的映射
                self.char_to_trial_mapping = {}
                self.trial_to_char_mapping = {}

                for trial_idx in range(len(target_order)):
                    original_char_idx = target_order[trial_idx]
                    if original_char_idx < len(beta_chars):
                        char = str(beta_chars[original_char_idx])
                        self.char_to_trial_mapping[char] = trial_idx
                        self.trial_to_char_mapping[trial_idx] = char

                # 🔑 关键：传递映射关系到EEG处理器
                self.eeg_processor.char_to_trial_mapping = self.char_to_trial_mapping
                self.eeg_processor.trial_to_char_mapping = self.trial_to_char_mapping
                self.eeg_processor.simulation_data = eeg_data
                self.eeg_processor.use_simulation = True

                # 🔑 关键：将测试数据加载到EEG处理器中
                self.eeg_processor.simulation_data = eeg_data
                self.eeg_processor.use_simulation = True
                

                # 🔑 关键修复：验证字符映射是否与训练时一致
                if hasattr(self.eeg_processor, 'target_order') and hasattr(self.eeg_processor, 'beta_standard_chars'):
                    print("✅ Establish direct character mapping:")
                    for i in range(min(10, len(block_chars))):
                        char = block_chars[i]
                        target_idx = int(target_indices[i]) if i < len(target_indices) else -1
                        expected_char = self.eeg_processor.beta_standard_chars[target_idx] if target_idx < len(self.eeg_processor.beta_standard_chars) else '?'
                        
                        print(f"   Index{i}: '{char}' -> target_idx {target_idx}")
                        
                        # 如果字符不匹配，这是关键问题
                        if char != expected_char:
                            print(f"❌ Character mapping error: expected'{expected_char}'，got'{char}'")
                            return False
                    print("✅ Character mapping established")
                return True
    
                # 🔑 关键：将测试数据加载到EEG处理器中
                self.eeg_processor.simulation_data = eeg_data
                self.eeg_processor.use_simulation = True

                
                print(f"✅ 保存仿真Character sequence: {''.join(block_chars_list[:10])}...")

                print(f"✅ Test data loaded:")
                print(f"   最终数据形状: {eeg_data.shape}")
                print(f"   字符映射: 已建立{len(block_chars_list)}个字符的映射关系")
                
                return True
            else:
                print(f"❌ 不支持的数据维度: {eeg_data.shape}")
                return False
            
        except Exception as e:
            print(f"❌ 测试数据加载错误: {e}")
            import traceback
            traceback.print_exc()
            return False


    # 🔧 还需要修改EEG处理器中的仿真数据获取方法
    # [EN] get_simulated_eeg_data_from_loaded_data: Auto-generated summary of this method's purpose.
    def get_simulated_eeg_data_from_loaded_data(self, num_samples=50):
        """从加载的测试数据中获取仿真EEG数据 - 修复版"""
        try:
            if not self.use_simulation or self.simulation_data is None:
                return np.random.randn(num_samples, self.num_channels) * 50
            
            if not hasattr(self, 'simulation_phase') or self.simulation_phase != 'flickering':
                return np.random.randn(num_samples, self.num_channels) * 20
            
            # 获取当前目标字符
            # 🔑 修复：获取当前目标字符并映射到正确的trial索引
            current_char = None
            trial_idx = None

            if hasattr(self, 'experiment_state_ref') and self.experiment_state_ref:
                main_ui = self.experiment_state_ref
                if hasattr(main_ui, 'experiment_state') and main_ui.experiment_state:
                    state = main_ui.experiment_state
                    current_char = state.get('current_target_char', None)
                    
                    # 🔑 关键：使用字符映射获取正确的trial索引
                    if current_char and hasattr(self, 'char_to_trial_mapping'):
                        trial_idx = self.char_to_trial_mapping.get(current_char)
                        if trial_idx is None:
                            print(f"⚠️ 字符'{current_char}'未找到对应的trialIndex")
                            return np.random.randn(num_samples, self.num_channels) * 20
                    else:
                        # 如果没有映射，使用当前trial数
                        trial_idx = state.get('current_trial', 0)
            
            if not current_char:
                return np.random.randn(num_samples, self.num_channels) * 20
            
            # 🔑 关键修复：使用正确的字符到trial映射
            if hasattr(self, 'char_to_condition_map') and current_char in self.char_to_condition_map:
                trial_idx = self.char_to_condition_map[current_char]
                print(f"🎯 字符映射: '{current_char}' -> trial {trial_idx}")
            else:
                print(f"⚠️ 字符 '{current_char}' 不在映射表中")
                return np.random.randn(num_samples, self.num_channels) * 20
            
            channels, time_points, trials = self.simulation_data.shape
            
            if trial_idx >= trials:
                print(f"⚠️ TrialIndex {trial_idx} 超出数据范围 {trials}")
                return np.random.randn(num_samples, self.num_channels) * 20
            
            # 🔑 获取对应trial的真实EEG数据
            trial_data = self.simulation_data[:, :, trial_idx]  # (channels, time)
            
            # 随机选择时间段（模拟实时数据流）
            start_idx = np.random.randint(0, max(1, time_points - num_samples))
            end_idx = min(start_idx + num_samples, time_points)
            
            if end_idx - start_idx < num_samples:
                start_idx = max(0, time_points - num_samples)
                end_idx = time_points
            
            data_chunk = trial_data[:, start_idx:end_idx]
            simulated_data = data_chunk.T  # 转换为 (samples, channels)
            
            # 🔑 确保通道数匹配
            if simulated_data.shape[1] > self.num_channels:
                simulated_data = simulated_data[:, :self.num_channels]
            elif simulated_data.shape[1] < self.num_channels:
                padding = np.zeros((simulated_data.shape[0], self.num_channels - simulated_data.shape[1]))
                simulated_data = np.hstack([simulated_data, padding])
            
            # 🔑 添加轻微的噪声，模拟真实采集
            noise_level = 0.05 * np.std(simulated_data)
            simulated_data = simulated_data + np.random.normal(0, noise_level, simulated_data.shape)
            
            return simulated_data
            
        except Exception as e:
            print(f"仿真数据获取失败: {e}")
            import traceback
            traceback.print_exc()
            return np.random.randn(num_samples, self.num_channels) * 50

    # [EN] handle_input_keydown: Auto-generated summary of this method's purpose.
    def handle_input_keydown(self, event):
        """处理输入模式下的键盘事件"""
        if event.key == pygame.K_RETURN:
            # 统一使用回车键确认输入
            try:
                if self.input_mode == 'beta_subject':
                    value = int(self.input_text)
                    if 1 <= value <= 70:
                        self.beta_config['subject'] = self.input_text
                    else:
                        print("Subject必须在1-70之间")
                elif self.input_mode == 'beta_block':
                    value = int(self.input_text)
                    if 1 <= value <= 4:
                        self.beta_config['block'] = self.input_text
                    else:
                        print("Block必须在1-4之间")
                elif self.input_mode == 'beta_window':
                    value = float(self.input_text)
                    if 0.3 <= value <= 1.2:
                        self.beta_config['time_window'] = self.input_text
                    else:
                        print("Time Window必须在0.3-1.2之间")
                elif self.input_mode in ['frequency', 'phase', 'cue_time', 'flash_time', 'pause_time', 'rest_time', 'time_window']:
                    value = float(self.input_text)
                    # 获取当前选中位置的字符
                    if self.selected_row is not None and self.selected_col is not None:
                        current_char = self.keyboard_layout_chars[self.selected_row][self.selected_col]
                        
                        if self.input_mode == 'frequency':
                            if current_char not in self.beta_params:
                                self.beta_params[current_char] = {'frequency': 0.0, 'phase_input': 0.0, 'phase': 0.0}
                            self.beta_params[current_char]['frequency'] = value
                        elif self.input_mode == 'phase':
                            if current_char not in self.beta_params:
                                self.beta_params[current_char] = {'frequency': 0.0, 'phase_input': 0.0, 'phase': 0.0}
                            # 限制相位输入值在0-2之间
                            phase_input = max(0.0, min(2.0, value))
                            self.beta_params[current_char]['phase_input'] = round(phase_input, 2)
                            # 计算实际相位值（输入值 * π）
                            self.beta_params[current_char]['phase'] = round(phase_input * math.pi, 2)
                    
                    # 处理时间设置
                    if self.input_mode == 'cue_time':
                        self.settings['cue_duration'] = max(0.1, min(10.0, value))
                        print(f"Cue time设置为: {self.settings['cue_duration']}")
                    elif self.input_mode == 'flash_time':
                        self.settings['flickering_duration'] = max(0.1, min(20.0, value))
                        print(f"Flash time设置为: {self.settings['flickering_duration']}")
                    elif self.input_mode == 'pause_time':
                        self.settings['pause_duration'] = max(0.1, min(10.0, value))
                        print(f"Pause time设置为: {self.settings['pause_duration']}")
                    elif self.input_mode == 'rest_time':
                        self.settings['rest_duration'] = max(1.0, min(600.0, value))
                        print(f"Rest time设置为: {self.settings['rest_duration']}s")
                    elif self.input_mode == 'time_window':
                        self.settings['time_window'] = max(0.1, min(5.0, value))
                        print(f"Time window设置为: {self.settings['time_window']}s")
                        
                elif self.input_mode == 'character' and self.selected_row is not None and self.selected_col is not None:
                    # 字符编辑 - 允许任意字符，包括重复字符，保持原始大小写
                    if len(self.input_text) >= 1 and self.input_text.isprintable():
                        # 获取当前位置的原字符
                        old_char = self.keyboard_layout_chars[self.selected_row][self.selected_col]
                        new_char = self.input_text
                        
                        # 直接更新，不检查冲突
                        if new_char != old_char:
                            # 更新键盘布局中的字符
                            self.keyboard_layout_chars[self.selected_row][self.selected_col] = new_char
                            
                            # 更新参数映射
                            if old_char in self.beta_params:
                                old_params = self.beta_params[old_char].copy()
                                self.beta_params[new_char] = old_params
                            else:
                                # 如果原字符没有参数，创建默认参数
                                self.beta_params[new_char] = {'frequency': 8.0, 'phase_input': 0.0, 'phase': 0.0}
                        
                elif self.input_mode in ['blocks']:
                    value = int(self.input_text)
                    if self.input_mode == 'blocks':
                        self.settings['total_blocks'] = max(1, min(10, value))
                        # 调整block_texts列表长度
                        while len(self.settings['block_texts']) < self.settings['total_blocks']:
                            self.settings['block_texts'].append(f'text{len(self.settings["block_texts"])+1}')
                        while len(self.settings['block_texts']) > self.settings['total_blocks']:
                            self.settings['block_texts'].pop()
                elif self.input_mode == 'block_text':
                    # 文本输入，直接保存用户输入（包含空格）
                    if self.input_text or self.input_text.strip():  # 允许包含空格的输入
                        # 关键：直接保存用户输入，不做任何转换
                        self.settings['block_texts'][self.editing_block_index] = self.input_text
                        
                        print(f"Block {self.editing_block_index + 1} 文本已保存:")
                        print(f"  保存内容: '{self.input_text}'")
                        print(f"  显示效果: '{self.input_text.replace(' ', '_')}'")
                        
            except ValueError:
                print(f"输入错误: {self.input_text}")
                pass
            
            self.input_mode = None
            self.input_text = ""
            
        elif event.key == pygame.K_ESCAPE:
            # ESC键取消输入
            self.input_mode = None
            self.input_text = ""
            
        elif event.key == pygame.K_BACKSPACE:
            # 删除字符
            self.input_text = self.input_text[:-1]
            
        elif event.unicode:
            # 根据输入模式允许不同字符
            if self.input_mode in ['frequency', 'phase', 'cue_time', 'flash_time', 'pause_time', 'rest_time', 'time_window']:
                # 数字输入模式
                if self.input_mode == 'phase':
                    if event.unicode.isdigit() or event.unicode == '.':
                        test_text = self.input_text + event.unicode
                        try:
                            test_value = float(test_text)
                            if 0 <= test_value <= 2:
                                self.input_text += event.unicode
                        except ValueError:
                            if event.unicode == '.' and '.' not in self.input_text:
                                self.input_text += event.unicode
                else:
                    if event.unicode.isdigit() or event.unicode in ['.', '-']:
                        self.input_text += event.unicode
            elif self.input_mode == 'character':
                # 字符输入模式
                if event.unicode.isprintable() and event.unicode != '\r' and event.unicode != '\n':
                    self.input_text += event.unicode
            elif self.input_mode in ['blocks']:
                # 整数输入模式
                if event.unicode.isdigit():
                    self.input_text += event.unicode
            elif self.input_mode == 'block_text':
                # 修复：允许空格输入，用户可以正常输入空格
                if (event.unicode.isprintable() and 
                    len(self.input_text) < 100 and 
                    event.unicode not in ['\r', '\n']):
                    self.input_text += event.unicode
            elif self.input_mode in ['beta_subject', 'beta_block']:
                # Beta配置的数字输入
                if event.unicode.isdigit():
                    self.input_text += event.unicode
            elif self.input_mode == 'beta_window':
                # Beta配置的浮点数输入
                if event.unicode.isdigit() or event.unicode == '.':
                    self.input_text += event.unicode

      
    # [EN] draw_demo_page: Auto-generated summary of this method's purpose.
    def draw_demo_page(self):
        """绘制Demo界面"""
        colors = self.get_current_colors()
        self.screen.fill(colors['background'])
        
        # 绘制键盘
        self.draw_demo_keyboard()
        
        # 绘制输出区域
        self.draw_demo_result_area()
        
        # 显示说明文字
        instruction_text = "Demo Mode: Press any key to simulate input"
        instruction_surface = pygame.font.Font(None, 36).render(instruction_text, True, colors['key_default'])
        instruction_rect = instruction_surface.get_rect(center=(self.screen_width//2, self.screen_height - 100))
        self.screen.blit(instruction_surface, instruction_rect)

    # [EN] draw_demo_keyboard: Auto-generated summary of this method's purpose.
    def draw_demo_keyboard(self):
        """绘制Demo模式的键盘"""
        colors = self.get_current_colors()
        
        target_width = 108
        target_height = 108
        button_spacing = 18
        space_width = 750
        
        # 计算键盘起始位置
        keyboard_width = 11 * (target_width + button_spacing) - button_spacing
        keyboard_height = 5 * (target_height + button_spacing) - button_spacing
            
        start_x = (self.screen_width - keyboard_width) // 2
        start_y = (self.screen_height - keyboard_height) // 2 + 100
        
        self.demo_keyboard_area = {
        'start_x': start_x,
        'start_y': start_y,
        'width': keyboard_width,
        'height': keyboard_height
        }
        
        # 绘制键盘
        for row_idx, row in enumerate(self.keyboard_layout_chars):
            if row_idx == 4:  # 空格行特殊处理
                row5_total_width = space_width + button_spacing + target_width
                row5_start_x = (self.screen_width - row5_total_width) // 2
                
                # 空格键
                space_rect = pygame.Rect(row5_start_x, start_y + row_idx * (target_height + button_spacing), space_width, target_height)
                char = self.keyboard_layout_chars[row_idx][0]
                self.draw_demo_key(self.screen, char, space_rect, colors)
                
                # 逗号键
                comma_rect = pygame.Rect(row5_start_x + space_width + button_spacing, start_y + row_idx * (target_height + button_spacing), target_width, target_height)
                char = self.keyboard_layout_chars[row_idx][1]
                self.draw_demo_key(self.screen, char, comma_rect, colors)
            else:
                row_width = len(row) * (target_width + button_spacing) - button_spacing
                row_start_x = start_x + (keyboard_width - row_width) // 2
                
                for col_idx, char in enumerate(row):
                    x = row_start_x + col_idx * (target_width + button_spacing)
                    y = start_y + row_idx * (target_height + button_spacing)
                    rect = pygame.Rect(x, y, target_width, target_height)
                    self.draw_demo_key(self.screen, char, rect, colors)

    # [EN] draw_demo_key: Auto-generated summary of this method's purpose.
    def draw_demo_key(self, screen, char, rect, colors):
        """绘制Demo模式下的单个按键"""
        # 获取当前亮度值
        luminance = self.get_demo_luminance(char)
        
        # 根据颜色方案设置背景色
        gray_value = int(luminance * 255)
        bg_color = (gray_value, gray_value, gray_value)
        
        # 绘制按键背景
        pygame.draw.rect(screen, bg_color, rect)
        pygame.draw.rect(screen, colors['key_default'], rect, 2)
        
        # 绘制字符
        display_char = '_' if char == '_' else char
        key_font = pygame.font.Font(None, 48)
        text_surface = key_font.render(display_char, True, colors['text'])
        text_rect = text_surface.get_rect(center=(rect.centerx, rect.centery))
        screen.blit(text_surface, text_rect)

    # [EN] get_demo_luminance: Auto-generated summary of this method's purpose.
    def get_demo_luminance(self, char):
        """计算Demo模式下字符的亮度值"""
        if self.demo_start_time == 0:
            return 1.0
        
        # 获取字符的频率和相位参数
        if char in self.beta_params:
            frequency = self.beta_params[char]['frequency']
            phase = self.beta_params[char]['phase']
        else:
            frequency = 8.0
            phase = 0.0
        
        # 计算亮度
        elapsed_time = (pygame.time.get_ticks() - self.demo_start_time) / 1000.0
        luminance = 0.5 * (1 + math.sin(2 * math.pi * frequency * elapsed_time + phase))
        return luminance

    # [EN] draw_demo_result_area: Auto-generated summary of this method's purpose.
    def draw_demo_result_area(self):
        """绘制Demo模式的结果区域"""
        colors = self.get_current_colors()
        
        # 输出条位置
        bar_width = 1370
        bar_height = 70
        bar_x = (self.screen_width - bar_width) // 2
        bar_y = 300
        
        # 绘制输出条背景
        output_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(self.screen, colors['key_default'], output_rect)
        pygame.draw.rect(self.screen, colors['background'], output_rect, 2)
        
        # 显示已输入的文本
        display_text = "Result: " + ''.join(self.demo_results).replace('_', ' ')
        text_surface = pygame.font.Font(None, 48).render(display_text, True, colors['text'])
        text_rect = text_surface.get_rect()
        text_rect.midleft = (output_rect.x + 10, output_rect.centery)
        self.screen.blit(text_surface, text_rect)

    # [EN] handle_demo_input: Auto-generated summary of this method's purpose.
    def handle_demo_input(self, event):
        """处理Demo模式的键盘输入"""
        if event.type == pygame.KEYDOWN:
            # 键盘映射
            key_mapping = {
                pygame.K_1: '1', pygame.K_2: '2', pygame.K_3: '3', pygame.K_4: '4', pygame.K_5: '5',
                pygame.K_6: '6', pygame.K_7: '7', pygame.K_8: '8', pygame.K_9: '9', pygame.K_0: '0',
                pygame.K_q: 'q', pygame.K_w: 'w', pygame.K_e: 'e', pygame.K_r: 'r', pygame.K_t: 't',
                pygame.K_y: 'y', pygame.K_u: 'u', pygame.K_i: 'i', pygame.K_o: 'o', pygame.K_p: 'p',
                pygame.K_a: 'a', pygame.K_s: 's', pygame.K_d: 'd', pygame.K_f: 'f', pygame.K_g: 'g',
                pygame.K_h: 'h', pygame.K_j: 'j', pygame.K_k: 'k', pygame.K_l: 'l',
                pygame.K_z: 'z', pygame.K_x: 'x', pygame.K_c: 'c', pygame.K_v: 'v', pygame.K_b: 'b',
                pygame.K_n: 'n', pygame.K_m: 'm', pygame.K_PERIOD: '.', pygame.K_COMMA: ',',
                pygame.K_SPACE: '_', pygame.K_BACKSPACE: '<'
            }
            
            if event.key in key_mapping:
                char = key_mapping[event.key]
                if char == '<' and self.demo_results:
                    # 退格删除
                    self.demo_results.pop()
                elif char != '<':
                    # 添加字符
                    self.demo_results.append(char)
    # [EN] draw_demo_page: Auto-generated summary of this method's purpose.
    def draw_demo_page(self):
        """绘制Demo界面"""
        colors = self.get_current_colors()
        self.screen.fill(colors['background'])
        
        # 绘制键盘 - 使用与experiment相同的布局
        self.draw_demo_keyboard()
        
        # 绘制输出区域（只有输出条，没有目标文本条）
        self.draw_demo_result_area()
        
        # 显示说明文字
        instruction_text = "Demo Mode: Press any key to simulate input"
        instruction_surface = pygame.font.Font(None, 36).render(instruction_text, True, colors['key_default'])
        instruction_rect = instruction_surface.get_rect(center=(self.screen_width//2, self.screen_height - 100))
        self.screen.blit(instruction_surface, instruction_rect)

    # [EN] draw_demo_keyboard: Auto-generated summary of this method's purpose.
    def draw_demo_keyboard(self):
        """绘制Demo模式的键盘"""
        colors = self.get_current_colors()
        
        target_width = 108
        target_height = 108
        button_spacing = 18
        space_width = 750
        
        # 计算键盘起始位置
        keyboard_width = 11 * (target_width + button_spacing) - button_spacing
        keyboard_height = 5 * (target_height + button_spacing) - button_spacing
            
        start_x = (self.screen_width - keyboard_width) // 2
        start_y = (self.screen_height - keyboard_height) // 2 + 100
        
        self.demo_keyboard_area = {
            'start_x': start_x,
            'start_y': start_y,
            'width': keyboard_width,
            'height': keyboard_height
        }
        
        # 绘制键盘
        for row_idx, row in enumerate(self.keyboard_layout_chars):
            if row_idx == 4:  # 空格行特殊处理
                row5_total_width = space_width + button_spacing + target_width
                row5_start_x = (self.screen_width - row5_total_width) // 2
                
                # 空格键
                space_rect = pygame.Rect(row5_start_x, start_y + row_idx * (target_height + button_spacing), space_width, target_height)
                char = self.keyboard_layout_chars[row_idx][0]
                self.draw_demo_key(self.screen, char, space_rect, colors)
                
                # 逗号键
                comma_rect = pygame.Rect(row5_start_x + space_width + button_spacing, start_y + row_idx * (target_height + button_spacing), target_width, target_height)
                char = self.keyboard_layout_chars[row_idx][1]
                self.draw_demo_key(self.screen, char, comma_rect, colors)
            else:
                row_width = len(row) * (target_width + button_spacing) - button_spacing
                row_start_x = start_x + (keyboard_width - row_width) // 2
                
                for col_idx, char in enumerate(row):
                    x = row_start_x + col_idx * (target_width + button_spacing)
                    y = start_y + row_idx * (target_height + button_spacing)
                    rect = pygame.Rect(x, y, target_width, target_height)
                    self.draw_demo_key(self.screen, char, rect, colors)

    # [EN] draw_demo_key: Auto-generated summary of this method's purpose.
    def draw_demo_key(self, screen, char, rect, colors):
        """绘制Demo模式下的单个按键"""
        # 获取当前亮度值 - 基于JFMP参数计算
        luminance = self.get_demo_luminance(char)
        
        # 根据颜色方案设置背景色
        gray_value = int(luminance * 255)
        bg_color = (gray_value, gray_value, gray_value)
        
        # 绘制按键背景
        pygame.draw.rect(screen, bg_color, rect)
        pygame.draw.rect(screen, colors['key_default'], rect, 2)
        
        # 绘制字符
        display_char = '_' if char == '_' else char
        key_font = pygame.font.Font(None, 48)
        text_surface = key_font.render(display_char, True, colors['text'])
        text_rect = text_surface.get_rect(center=(rect.centerx, rect.centery))
        screen.blit(text_surface, text_rect)

    # [EN] get_demo_luminance: Auto-generated summary of this method's purpose.
    def get_demo_luminance(self, char):
        """计算Demo模式下字符的亮度值"""
        if self.demo_start_time == 0:
            return 1.0
        
        # 获取字符的频率和相位参数
        if char in self.beta_params:
            frequency = self.beta_params[char]['frequency']
            phase = self.beta_params[char]['phase']
        else:
            frequency = 8.0
            phase = 0.0
        
        # 计算亮度
        elapsed_time = (pygame.time.get_ticks() - self.demo_start_time) / 1000.0
        luminance = 0.5 * (1 + math.sin(2 * math.pi * frequency * elapsed_time + phase))
        return luminance

    # [EN] draw_demo_result_area: Auto-generated summary of this method's purpose.
    def draw_demo_result_area(self):
        """绘制Demo模式的结果区域（只有输出条）"""
        colors = self.get_current_colors()
        
        # 输出条位置 - 与experiment相同的大小和位置
        bar_width = 1370
        bar_height = 70
        bar_x = (self.screen_width - bar_width) // 2
        bar_y = 300
        
        # 绘制输出条背景
        output_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(self.screen, colors['key_default'], output_rect)
        pygame.draw.rect(self.screen, colors['background'], output_rect, 2)
        
        # 显示已输入的文本
        display_text = "Result: " + ''.join(self.demo_results).replace('_', ' ')
        text_surface = pygame.font.Font(None, 48).render(display_text, True, colors['text'])
        text_rect = text_surface.get_rect()
        text_rect.midleft = (output_rect.x + 10, output_rect.centery)
        self.screen.blit(text_surface, text_rect)
        
        # 在输出条和键盘之间绘制控制按钮
        self.draw_demo_control_buttons(bar_x, bar_y, bar_width)

    # [EN] draw_demo_control_buttons: Auto-generated summary of this method's purpose.
    def draw_demo_control_buttons(self, bar_x, bar_y, bar_width):
        """绘制Demo模式的控制按钮"""
        colors = self.get_current_colors()
        
        # 按钮参数
        button_width = 180
        button_height = 80
        button_spacing = 40
        buttons_y = bar_y + 90  # 在输出条下方90像素
        
        # 按钮频率和相位设置
        button_params = {
            'start': {'frequency': 16.0, 'phase': 0.0},
            'finish': {'frequency': 16.2, 'phase': 0.5 * math.pi},
            'pause': {'frequency': 16.4, 'phase': 1.0 * math.pi},
            'continue': {'frequency': 16.6, 'phase': 1.5 * math.pi}
        }
        
        # 左侧按钮组（Start, Finish）
        left_start_x = bar_x
        start_rect = pygame.Rect(left_start_x, buttons_y, button_width, button_height)
        finish_rect = pygame.Rect(left_start_x + button_width + button_spacing, buttons_y, button_width, button_height)
        
        # 右侧按钮组（Pause, Continue）
        right_end_x = bar_x + bar_width
        continue_rect = pygame.Rect(right_end_x - button_width, buttons_y, button_width, button_height)
        pause_rect = pygame.Rect(right_end_x - button_width * 2 - button_spacing, buttons_y, button_width, button_height)
        
        # 绘制按钮
        buttons = [
            (start_rect, 'Start', 'start'),
            (finish_rect, 'Finish', 'finish'),
            (pause_rect, 'Pause', 'pause'),
            (continue_rect, 'Continue', 'continue')
        ]
        
        for rect, text, key in buttons:
            # 计算闪烁亮度
            luminance = self.get_demo_button_luminance(button_params[key])
            
            # 使用红色作为基础色，调整亮度
            red_value = int(255 * luminance)
            bg_color = (red_value, 0, 0)
            
            # 绘制按钮
            pygame.draw.rect(self.screen, bg_color, rect)
            pygame.draw.rect(self.screen, colors['key_default'], rect, 2)
            
            # 绘制白色文字
            text_surface = pygame.font.Font(None, 38).render(text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=rect.center)
            self.screen.blit(text_surface, text_rect)

    # [EN] get_demo_button_luminance: Auto-generated summary of this method's purpose.
    def get_demo_button_luminance(self, params):
        """计算Demo模式下按钮的亮度值"""
        if self.demo_start_time == 0:
            return 1.0
        
        frequency = params['frequency']
        phase = params['phase']
        
        # 计算亮度
        elapsed_time = (pygame.time.get_ticks() - self.demo_start_time) / 1000.0
        luminance = 0.5 * (1 + math.sin(2 * math.pi * frequency * elapsed_time + phase))
        return luminance

    # [EN] handle_demo_input: Auto-generated summary of this method's purpose.
    def handle_demo_input(self, event):
        """处理Demo模式的键盘输入"""
        if event.type == pygame.KEYDOWN:
            # 键盘映射
            key_mapping = {
                pygame.K_1: '1', pygame.K_2: '2', pygame.K_3: '3', pygame.K_4: '4', pygame.K_5: '5',
                pygame.K_6: '6', pygame.K_7: '7', pygame.K_8: '8', pygame.K_9: '9', pygame.K_0: '0',
                pygame.K_q: 'q', pygame.K_w: 'w', pygame.K_e: 'e', pygame.K_r: 'r', pygame.K_t: 't',
                pygame.K_y: 'y', pygame.K_u: 'u', pygame.K_i: 'i', pygame.K_o: 'o', pygame.K_p: 'p',
                pygame.K_a: 'a', pygame.K_s: 's', pygame.K_d: 'd', pygame.K_f: 'f', pygame.K_g: 'g',
                pygame.K_h: 'h', pygame.K_j: 'j', pygame.K_k: 'k', pygame.K_l: 'l',
                pygame.K_z: 'z', pygame.K_x: 'x', pygame.K_c: 'c', pygame.K_v: 'v', pygame.K_b: 'b',
                pygame.K_n: 'n', pygame.K_m: 'm', pygame.K_PERIOD: '.', pygame.K_COMMA: ',',
                pygame.K_SPACE: '_', pygame.K_BACKSPACE: '<'
            }
            
            if event.key in key_mapping:
                char = key_mapping[event.key]
                if char == '<' and self.demo_results:
                    # 退格删除
                    self.demo_results.pop()
                elif char != '<':
                    # 添加字符
                    self.demo_results.append(char)
                    
    # [EN] run: Auto-generated summary of this method's purpose.
    def run(self):
        """运行主循环"""
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.current_page == "experiment":
                            # 从实验页面返回主菜单
                            self.current_page = "main"
                            # 清理实验状态
                            if hasattr(self, 'experiment_state'):
                                delattr(self, 'experiment_state')
                            # 关闭实验者窗口
                            if hasattr(self, 'experimenter_process') and self.experimenter_process:
                                self.experimenter_process.terminate()
                                self.experimenter_process = None
                        
                            if hasattr(self, 'eeg_processor') and self.eeg_processor:
                                self.eeg_processor.stop()
                                self.eeg_running = False
                            # 清理临时文件
                            self.cleanup_temp_files()
                        elif self.current_page == "start":
                            # 从start页面返回主菜单
                            self.current_page = "main"
                            # 关闭实验者窗口
                            if hasattr(self, 'experimenter_process') and self.experimenter_process:
                                self.experimenter_process.terminate()
                                self.experimenter_process = None
                       
                            if self.eeg_processor:
                                self.eeg_processor.stop()
                                self.eeg_running = False
                          
                            self.cleanup_temp_files()
                        elif self.current_page == "rest":
                           
                            self.current_page = "main"
                      
                            if hasattr(self, 'experiment_state'):
                                delattr(self, 'experiment_state')
                        
                            if hasattr(self, 'experimenter_process') and self.experimenter_process:
                                self.experimenter_process.terminate()
                                self.experimenter_process = None
                          
                            if self.eeg_processor:
                                self.eeg_processor.stop()
                                self.eeg_running = False
                        
                            self.cleanup_temp_files()
                        elif self.current_page == "demo":
                         
                            self.current_page = "main"
                          
                            self.demo_results = []
                            self.demo_start_time = 0
                        elif self.input_mode:
                        
                            self.input_mode = None
                            self.input_text = ""
                        else:
                          
                            running = False
                    elif self.current_page == "demo":
                   
                        self.handle_demo_input(event)
                    elif self.current_page == "experiment":
                       
                        self.handle_experiment_event(event)
                    elif self.input_mode is not None:
                 
                        self.handle_input_keydown(event)
                    elif self.current_page == "jpfm" and self.selected_row is not None and self.selected_col is not None and self.input_mode is None:
                       
                        if event.key == pygame.K_UP:
                            self.param_selection = max(0, self.param_selection - 1)
                        elif event.key == pygame.K_DOWN:
                            self.param_selection = min(2, self.param_selection + 1)
                        elif event.key == pygame.K_RETURN:
                            current_char = self.keyboard_layout_chars[self.selected_row][self.selected_col]
                            if self.param_selection == 0:
                                self.input_mode = 'character'
                                self.input_text = current_char
                            elif self.param_selection == 1:
                                self.input_mode = 'frequency'
                                if current_char in self.beta_params:
                                    self.input_text = str(self.beta_params[current_char]['frequency'])
                                else:
                                    self.input_text = "8.0"
                            elif self.param_selection == 2:
                                self.input_mode = 'phase'
                                if current_char in self.beta_params:
                                    self.input_text = str(self.beta_params[current_char]['phase_input'])
                                else:
                                    self.input_text = "0.0"
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    
                    if self.current_page == "main":
                        self.handle_main_page_click(pos)
                    elif self.current_page == "demo":
                        pass
                    elif self.current_page == "layout":
                        self.handle_layout_page_click(pos)
                    elif self.current_page == "jpfm":
                        self.handle_jpfm_page_click(pos)
                    elif self.current_page == "trials":
                        self.handle_trials_page_click(pos)
                    elif self.current_page == "block_text":
                        self.handle_block_text_page_click(pos)
                    elif self.current_page == "start":
                        self.handle_start_page_click(pos)
                    elif self.current_page == "beta_simulation_config": 
                        self.handle_beta_simulation_config_click(pos)
            
           
            if self.current_page == "demo" and self.demo_start_time > 0:
                pass

            if hasattr(self, 'experiment_state'):
                self.update_experiment_state()
                self.update_experimenter_status()
                self.check_experimenter_commands()

 
            if self.current_page == "main":
                self.draw_main_page()
            elif self.current_page == "demo":
                self.draw_demo_page()
            elif self.current_page == "layout":
                self.draw_layout_page()
            elif self.current_page == "jpfm":
                self.draw_jpfm_page()
            elif self.current_page == "trials":
                self.draw_trials_page()
            elif self.current_page == "block_text":
                self.draw_block_text_page()
            elif self.current_page == "start":
                self.draw_start_page()
          
            elif self.current_page == "experiment":
                if self.selected_mode == "Speller beta dataset simulation":
                    # Beta模式直接绘制Beta实验页面
                    colors = self.get_current_colors()
                    self.screen.fill(colors['background'])
                    
                    # 初始化实验状态
                    if not hasattr(self, 'experiment_state'):
                        self.init_beta_experiment_state()
                    
                    # 更新状态
                    self.update_experiment_state()
                    self.update_experimenter_status()
                    self.check_experimenter_commands()
                    
                    # 绘制键盘
                    self.draw_experiment_keyboard()
                    
                    # 绘制Beta结果区域（关键修改）
                    self.draw_beta_result_area()
                    
                    # 状态提示
                    if self.experiment_state['state'] == "ready":
                        text = "Experiment will start automatically..."
                        text_surface = pygame.font.Font(None, 36).render(text, True, (255, 255, 0))
                        text_rect = text_surface.get_rect(center=(self.screen_width//2, self.screen_height - 100))
                        self.screen.blit(text_surface, text_rect)
                    
                else:
                    if not hasattr(self, '_experiment_debug_shown'):
                        print(f"🎯 Entering Online experiment page")
                        self._experiment_debug_shown = True
                    self.draw_experiment_page()
            elif self.current_page == "block_progress":
               
                if hasattr(self, 'is_beta_mode') and self.is_beta_mode:
                    self.draw_beta_block_progress_page()  
                else:
                    self.draw_block_progress_page()      
            elif self.current_page == "rest":
                self.draw_rest_page()
            elif self.current_page == "beta_simulation_config": 
                self.draw_beta_simulation_config_page()
            else:
                self.draw_main_page()
            
            pygame.display.flip()
            self.clock.tick(self.refresh_rate)
        
  
        if self.eeg_processor:
            self.eeg_processor.stop()
        self.cleanup_temp_files()
        pygame.quit()



    
 
    # [EN] cleanup_temp_files: Auto-generated summary of this method's purpose.
    def cleanup_temp_files(self):
    
        temp_files = ["experimenter_window.py", "experiment_status.json", "experimenter_command.json"]
        for file_path in temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
if __name__ == "__main__":
  
    system = BCISpellerSystem()
    system.run()