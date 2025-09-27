#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
虚拟按钮预设模块
提供常用的按钮布局和主题配置
"""

from .virtual_button import VirtualButton, VirtualButtonManager


class ButtonPresets:
    """
    虚拟按钮预设配置类
    """
    
    @staticmethod
    def create_camera_control_buttons(manager: VirtualButtonManager) -> dict:
        """
        创建摄像头控制按钮组
        
        Args:
            manager: 虚拟按钮管理器
            
        Returns:
            dict: 按钮ID到按钮对象的映射
        """
        width = manager.display_width
        height = manager.display_height
        
        button_width = 80
        button_height = 35
        margin = 10
        
        buttons = {}
        
        # 记录按钮
        record_btn = manager.create_button(
            button_id='record',
            x=width - button_width - margin,
            y=height - 2 * button_height - 2 * margin,
            width=button_width,
            height=button_height,
            text='Record'
        )
        record_btn.set_colors(
            normal=(0, 150, 0),      # 绿色
            active=(0, 255, 0),      # 亮绿色
            disabled=(80, 80, 80)    # 灰色
        )
        buttons['record'] = record_btn
        
        # 清除按钮
        clear_btn = manager.create_button(
            button_id='clear',
            x=width - button_width - margin,
            y=height - button_height - margin,
            width=button_width,
            height=button_height,
            text='Clear'
        )
        clear_btn.set_colors(
            normal=(150, 0, 0),      # 红色
            active=(255, 0, 0),      # 亮红色
            disabled=(80, 80, 80)    # 灰色
        )
        buttons['clear'] = clear_btn
        
        return buttons
    
    @staticmethod
    def create_mode_switch_buttons(manager: VirtualButtonManager) -> dict:
        """
        创建模式切换按钮组
        
        Args:
            manager: 虚拟按钮管理器
            
        Returns:
            dict: 按钮ID到按钮对象的映射
        """
        width = manager.display_width
        button_width = 60
        button_height = 30
        margin = 10
        
        buttons = {}
        
        # 模式按钮布局在顶部
        modes = [
            ('record_mode', 'REC', (255, 165, 0)),    # 橙色
            ('recognize_mode', 'RECOG', (0, 255, 255)), # 青色
            ('track_mode', 'TRACK', (255, 0, 255))      # 紫色
        ]
        
        for i, (btn_id, text, color) in enumerate(modes):
            btn = manager.create_button(
                button_id=btn_id,
                x=margin + i * (button_width + margin),
                y=margin,
                width=button_width,
                height=button_height,
                text=text
            )
            btn.set_colors(
                normal=color,
                active=tuple(min(255, c + 50) for c in color),
                disabled=(80, 80, 80)
            )
            buttons[btn_id] = btn
        
        return buttons
    
    @staticmethod
    def create_simple_control_buttons(manager: VirtualButtonManager) -> dict:
        """
        创建简化控制按钮组（更大的按钮，适合触摸）
        
        Args:
            manager: 虚拟按钮管理器
            
        Returns:
            dict: 按钮ID到按钮对象的映射
        """
        width = manager.display_width
        height = manager.display_height
        
        button_width = 80
        button_height = 60  # 更高的按钮
        margin = 15
        
        buttons = {}
        
        # 记录按钮（大）
        record_btn = manager.create_button(
            button_id='record',
            x=width - button_width - margin,
            y=height // 2 - button_height - margin // 2,
            width=button_width,
            height=button_height,
            text='REC'
        )
        record_btn.set_colors(
            normal=(0, 120, 0),
            active=(0, 200, 0),
            disabled=(60, 60, 60)
        )
        buttons['record'] = record_btn
        
        # 清除按钮（大）
        clear_btn = manager.create_button(
            button_id='clear',
            x=width - button_width - margin,
            y=height // 2 + margin // 2,
            width=button_width,
            height=button_height,
            text='CLR'
        )
        clear_btn.set_colors(
            normal=(120, 0, 0),
            active=(200, 0, 0),
            disabled=(60, 60, 60)
        )
        buttons['clear'] = clear_btn
        
        # 退出按钮
        exit_btn = manager.create_button(
            button_id='exit',
            x=margin,
            y=margin,
            width=button_width // 2,
            height=button_height // 2,
            text='EXIT'
        )
        exit_btn.set_colors(
            normal=(100, 100, 0),
            active=(150, 150, 0),
            disabled=(60, 60, 60)
        )
        buttons['exit'] = exit_btn
        
        return buttons


class ButtonThemes:
    """
    按钮主题配置类
    """
    
    DARK_THEME = {
        'normal': (60, 60, 60),
        'active': (100, 100, 100),
        'disabled': (30, 30, 30),
        'border': (200, 200, 200),
        'text': (255, 255, 255)
    }
    
    LIGHT_THEME = {
        'normal': (200, 200, 200),
        'active': (255, 255, 255),
        'disabled': (120, 120, 120),
        'border': (50, 50, 50),
        'text': (0, 0, 0)
    }
    
    GREEN_THEME = {
        'normal': (0, 120, 0),
        'active': (0, 200, 0),
        'disabled': (60, 60, 60),
        'border': (255, 255, 255),
        'text': (255, 255, 255)
    }
    
    RED_THEME = {
        'normal': (120, 0, 0),
        'active': (200, 0, 0),
        'disabled': (60, 60, 60),
        'border': (255, 255, 255),
        'text': (255, 255, 255)
    }
    
    BLUE_THEME = {
        'normal': (0, 0, 120),
        'active': (0, 0, 200),
        'disabled': (60, 60, 60),
        'border': (255, 255, 255),
        'text': (255, 255, 255)
    }
    
    @classmethod
    def apply_theme_to_button(cls, button: VirtualButton, theme_name: str):
        """
        应用主题到按钮
        
        Args:
            button: 虚拟按钮实例
            theme_name: 主题名称 ('dark', 'light', 'green', 'red', 'blue')
        """
        themes = {
            'dark': cls.DARK_THEME,
            'light': cls.LIGHT_THEME,
            'green': cls.GREEN_THEME,
            'red': cls.RED_THEME,
            'blue': cls.BLUE_THEME
        }
        
        theme = themes.get(theme_name.lower())
        if theme:
            button.set_colors(**theme)
        else:
            print(f"Unknown theme: {theme_name}")


# 使用示例
def create_example_button_layout(display_width: int, display_height: int) -> VirtualButtonManager:
    """
    创建示例按钮布局
    
    Args:
        display_width: 显示宽度
        display_height: 显示高度
        
    Returns:
        VirtualButtonManager: 配置好的按钮管理器
    """
    # 创建管理器
    manager = VirtualButtonManager(display_width, display_height)
    
    # 创建预设按钮
    if display_width >= 640:
        # 大屏幕：使用标准控制按钮
        buttons = ButtonPresets.create_camera_control_buttons(manager)
        mode_buttons = ButtonPresets.create_mode_switch_buttons(manager)
        buttons.update(mode_buttons)
    else:
        # 小屏幕：使用简化按钮
        buttons = ButtonPresets.create_simple_control_buttons(manager)
    
    # 应用主题
    if 'record' in buttons:
        ButtonThemes.apply_theme_to_button(buttons['record'], 'green')
    if 'clear' in buttons:
        ButtonThemes.apply_theme_to_button(buttons['clear'], 'red')
    
    return manager
