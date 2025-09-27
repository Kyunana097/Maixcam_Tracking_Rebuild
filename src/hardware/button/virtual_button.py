#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
虚拟按钮模块
提供触摸屏虚拟按钮功能，支持按钮绘制、触摸检测和事件处理
"""

import time
from typing import Dict, List, Tuple, Optional, Callable

try:
    from maix import image, touchscreen
    HAS_MAIX = True
except ImportError:
    HAS_MAIX = False
    print("[Warn] MaixPy modules not available, virtual buttons will use simulation mode")


class VirtualButton:
    """
    单个虚拟按钮类
    """
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 text: str, button_id: str, enabled: bool = True):
        """
        初始化虚拟按钮
        
        Args:
            x: 按钮X坐标
            y: 按钮Y坐标  
            width: 按钮宽度
            height: 按钮高度
            text: 按钮文字
            button_id: 按钮唯一标识
            enabled: 是否启用
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.button_id = button_id
        self.enabled = enabled
        
        # 状态管理
        self.active = False  # 是否被按下（视觉反馈）
        self.last_click_time = 0.0  # 上次点击时间
        self.click_cooldown = 0.5  # 点击冷却时间（秒）
        
        # 外观配置
        self.colors = {
            'normal': (100, 100, 100),      # 正常状态颜色 (R,G,B)
            'active': (150, 150, 150),      # 激活状态颜色
            'disabled': (50, 50, 50),       # 禁用状态颜色
            'border': (255, 255, 255),      # 边框颜色
            'text': (255, 255, 255)         # 文字颜色
        }
        
        # 事件回调
        self.on_click: Optional[Callable] = None
    
    def set_position(self, x: int, y: int):
        """设置按钮位置"""
        self.x, self.y = x, y
    
    def set_size(self, width: int, height: int):
        """设置按钮大小"""
        self.width, self.height = width, height
    
    def set_text(self, text: str):
        """设置按钮文字"""
        self.text = text
    
    def set_enabled(self, enabled: bool):
        """设置按钮启用状态"""
        self.enabled = enabled
    
    def set_colors(self, **colors):
        """设置按钮颜色主题"""
        self.colors.update(colors)
    
    def set_click_callback(self, callback: Callable):
        """设置点击回调函数"""
        self.on_click = callback
    
    def is_point_inside(self, x: int, y: int) -> bool:
        """
        检查点是否在按钮区域内
        
        Args:
            x: 点的X坐标
            y: 点的Y坐标
            
        Returns:
            bool: 是否在按钮内
        """
        return (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height and 
                self.enabled)
    
    def can_click(self) -> bool:
        """检查是否可以点击（冷却时间限制）"""
        return time.time() - self.last_click_time >= self.click_cooldown
    
    def trigger_click(self) -> bool:
        """
        触发按钮点击
        
        Returns:
            bool: 是否成功触发
        """
        if not self.enabled or not self.can_click():
            return False
        
        self.last_click_time = time.time()
        self.active = True
        
        # 执行回调
        if self.on_click:
            try:
                self.on_click(self.button_id)
            except Exception as e:
                print(f"Button callback error: {e}")
        
        return True
    
    def update(self):
        """更新按钮状态（重置激活状态等）"""
        if self.active and time.time() - self.last_click_time > 0.2:
            self.active = False
    
    def draw(self, img):
        """
        绘制按钮到图像上
        
        Args:
            img: MaixPy图像对象
        """
        if not HAS_MAIX:
            return
        
        try:
            # 选择颜色
            if not self.enabled:
                bg_color = image.Color.from_rgb(*self.colors['disabled'])
            elif self.active:
                bg_color = image.Color.from_rgb(*self.colors['active'])
            else:
                bg_color = image.Color.from_rgb(*self.colors['normal'])
            
            border_color = image.Color.from_rgb(*self.colors['border'])
            text_color = image.Color.from_rgb(*self.colors['text'])
            
            # 绘制按钮背景
            img.draw_rect(self.x, self.y, self.width, self.height, 
                         color=bg_color, thickness=-1)
            
            # 绘制边框
            img.draw_rect(self.x, self.y, self.width, self.height, 
                         color=border_color, thickness=2)
            
            # 绘制文字（居中）
            text_x = self.x + (self.width - len(self.text) * 8) // 2
            text_y = self.y + (self.height - 16) // 2
            img.draw_string(text_x, text_y, self.text, 
                          color=text_color, scale=0.8)
            
            # 激活状态的额外效果
            if self.active:
                inner_color = image.Color.from_rgb(255, 255, 255)
                img.draw_rect(self.x + 2, self.y + 2, 
                             self.width - 4, self.height - 4, 
                             color=inner_color, thickness=1)
        
        except Exception as e:
            print(f"Button draw error: {e}")


class VirtualButtonManager:
    """
    虚拟按钮管理器
    负责管理多个虚拟按钮和触摸屏交互
    """
    
    def __init__(self, display_width: int, display_height: int):
        """
        初始化按钮管理器
        
        Args:
            display_width: 显示屏宽度
            display_height: 显示屏高度
        """
        self.display_width = display_width
        self.display_height = display_height
        self.buttons: Dict[str, VirtualButton] = {}
        
        # 触摸屏初始化
        self.touchscreen = None
        self.has_touchscreen = False
        self._init_touchscreen()
        
        # 触摸状态跟踪
        self.touch_pressed_already = False
        self.last_touch_x = 0
        self.last_touch_y = 0
        self.last_touch_pressed = False
        
        # 触摸坐标映射参数
        self.touch_mapping = {
            'scale_x': 1.0,
            'scale_y': 1.0,
            'offset_x': 0.0,
            'offset_y': 0.0
        }
        
        # 自动检测触摸映射
        self._detect_touch_mapping()
    
    def _init_touchscreen(self):
        """初始化触摸屏"""
        if not HAS_MAIX:
            return
        
        try:
            self.touchscreen = touchscreen.TouchScreen()
            self.has_touchscreen = True
            print("✓ Touchscreen initialized for virtual buttons")
        except Exception as e:
            print(f"✗ Touchscreen initialization failed: {e}")
            self.has_touchscreen = False
    
    def _detect_touch_mapping(self):
        """
        自动检测触摸坐标映射参数
        基于显示分辨率应用预设的校准参数
        """
        if self.display_width == 640 and self.display_height == 480:
            # 已校准的精确参数
            self.touch_mapping.update({
                'scale_x': 1.6615,
                'scale_y': 1.7352,
                'offset_x': -197.74,
                'offset_y': -140.00
            })
        elif self.display_width == 512 and self.display_height == 320:
            # 已校准的精确参数（用户完成校准）
            self.touch_mapping.update({
                'scale_x': 0.80,  # 手动校准完成的参数
                'scale_y': 0.67,
                'offset_x': 0,
                'offset_y': 0
            })
    
    def set_touch_mapping(self, scale_x: float, scale_y: float, 
                         offset_x: float = 0, offset_y: float = 0):
        """
        手动设置触摸坐标映射参数
        
        Args:
            scale_x: X轴缩放系数
            scale_y: Y轴缩放系数
            offset_x: X轴偏移
            offset_y: Y轴偏移
        """
        self.touch_mapping.update({
            'scale_x': scale_x,
            'scale_y': scale_y,
            'offset_x': offset_x,
            'offset_y': offset_y
        })
    
    def _map_touch_coordinates(self, raw_x: int, raw_y: int) -> Tuple[int, int]:
        """
        映射原始触摸坐标到显示坐标
        
        Args:
            raw_x: 原始触摸X坐标
            raw_y: 原始触摸Y坐标
            
        Returns:
            tuple: (映射后X坐标, 映射后Y坐标)
        """
        mapped_x = int((raw_x + self.touch_mapping['offset_x']) * self.touch_mapping['scale_x'])
        mapped_y = int((raw_y + self.touch_mapping['offset_y']) * self.touch_mapping['scale_y'])
        
        # 限制在显示范围内
        mapped_x = max(0, min(mapped_x, self.display_width - 1))
        mapped_y = max(0, min(mapped_y, self.display_height - 1))
        
        return mapped_x, mapped_y
    
    def add_button(self, button: VirtualButton):
        """
        添加虚拟按钮
        
        Args:
            button: VirtualButton实例
        """
        self.buttons[button.button_id] = button
    
    def remove_button(self, button_id: str):
        """移除虚拟按钮"""
        if button_id in self.buttons:
            del self.buttons[button_id]
    
    def get_button(self, button_id: str) -> Optional[VirtualButton]:
        """获取指定按钮"""
        return self.buttons.get(button_id)
    
    
    def create_button(self, button_id: str, x: int, y: int, width: int, height: int, 
                     text: str, enabled: bool = True) -> VirtualButton:
        """
        创建并添加新按钮
        
        Args:
            button_id: 按钮唯一标识
            x, y: 按钮位置
            width, height: 按钮大小
            text: 按钮文字
            enabled: 是否启用
            
        Returns:
            VirtualButton: 创建的按钮实例
        """
        button = VirtualButton(x, y, width, height, text, button_id, enabled)
        self.add_button(button)
        return button
    
    def update(self):
        """更新所有按钮状态"""
        for button in self.buttons.values():
            button.update()
    
    def draw_all(self, img):
        """
        绘制所有按钮
        
        Args:
            img: MaixPy图像对象
        """
        for button in self.buttons.values():
            button.draw(img)
    
    def check_touch_input(self) -> Optional[str]:
        """
        检查触摸输入并返回被点击的按钮ID
        
        Returns:
            str: 被点击的按钮ID，没有则返回None
        """
        if not self.has_touchscreen:
            return None
        
        try:
            # 读取触摸屏状态
            raw_x, raw_y, pressed = self.touchscreen.read()
            
            # 映射触摸坐标
            x, y = self._map_touch_coordinates(raw_x, raw_y)
            
            self.last_touch_x = x
            self.last_touch_y = y
            self.last_touch_pressed = pressed
            
            # 处理触摸事件
            if pressed:
                self.touch_pressed_already = True
            else:
                # 触摸释放时检查按钮点击
                if self.touch_pressed_already:
                    self.touch_pressed_already = False
                    return self._check_button_hit(x, y)
        
        except Exception as e:
            if self.debug_mode:
                print(f"Touch input error: {e}")
        
        return None
    
    def _check_button_hit(self, x: int, y: int) -> Optional[str]:
        """
        检查坐标是否击中某个按钮
        
        Args:
            x: 触摸X坐标
            y: 触摸Y坐标
            
        Returns:
            str: 被击中的按钮ID，没有则返回None
        """
        for button in self.buttons.values():
            if button.is_point_inside(x, y) and button.trigger_click():
                return button.button_id
        
        return None
    
    def draw_touch_indicator(self, img):
        """
        绘制触摸指示器（如果正在触摸）
        
        Args:
            img: MaixPy图像对象
        """
        if (self.has_touchscreen and self.touch_pressed_already and 
            HAS_MAIX and hasattr(self, 'last_touch_x')):
            try:
                img.draw_circle(self.last_touch_x, self.last_touch_y, 5, 
                              image.Color.from_rgb(255, 255, 255), 2)
            except:
                pass


# TODO 列表
class VirtualButtonTODO:
    """
    虚拟按钮模块 TODO 列表
    """
    
    COMPLETED = [
        "✅ 创建 VirtualButton 类 - 单个按钮管理",
        "✅ 创建 VirtualButtonManager 类 - 多按钮管理",
        "✅ 实现触摸屏初始化和坐标映射",
        "✅ 实现按钮绘制和视觉反馈",
        "✅ 实现触摸检测和点击处理",
        "✅ 添加调试模式和日志输出",
        "✅ 添加按钮状态管理（启用/禁用/冷却）"
    ]
    
    PENDING = [
        "🔲 添加配置文件支持 - 从JSON加载按钮布局",
        "🔲 添加按钮主题系统 - 多种颜色方案",
        "🔲 添加按钮动画效果 - 点击动画、渐变等",
        "🔲 添加长按检测 - 支持长按事件",
        "🔲 添加滑动手势 - 支持滑动操作",
        "🔲 添加按钮组管理 - 单选、多选按钮组",
        "🔲 添加自适应布局 - 根据屏幕大小自动调整",
        "🔲 添加触摸校准工具 - 交互式校准界面",
        "🔲 添加按钮音效支持",
        "🔲 添加国际化支持 - 多语言按钮文字"
    ]
    
    INTEGRATION = [
        "🔲 与main.py集成 - 替换现有虚拟按钮实现",
        "🔲 创建预设按钮模板 - 录制、清除、模式切换等",
        "🔲 添加单元测试 - 测试按钮功能",
        "🔲 添加性能优化 - 减少绘制开销",
        "🔲 添加文档和使用示例"
    ]
