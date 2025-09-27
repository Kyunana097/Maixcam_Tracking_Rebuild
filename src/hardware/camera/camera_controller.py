#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
摄像头控制模块
负责摄像头初始化和图像采集
"""
from maix import camera
import time

class CameraController:
    """
    摄像头控制器类
    """
    
    def __init__(self, width=512, height=320):
        """
        初始化摄像头控制器
        
        Args:
            width: 图像宽度
            height: 图像高度
        """
        self.width = width
        self.height = height
        self.camera = None
    
    def initialize_camera(self):
        """
        初始化摄像头
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 使用初始化时设置的分辨率
            self.camera = camera.Camera(self.width, self.height)
            return True
        except Exception:
            self.camera = None
            return False
    
    def capture_image(self):
        """
        采集图像
        
        Returns:
            image: 采集到的图像
        """
        if self.camera is None:
            return None
        try:
            img = self.camera.read()
            # 轻微限速，避免占满CPU（单位：秒）
            time.sleep(0.001)
            return img
        except Exception:
            return None
    
    def release_camera(self):
        """
        释放摄像头资源
        """
        try:
            if self.camera is not None:
                if hasattr(self.camera, "close"):
                    self.camera.close()
        finally:
            self.camera = None

    def set_resolution(self, width, height):
        """
        设置摄像头分辨率
        
        Args:
            width: 图像宽度
            height: 图像高度
        """
        self.width = width
        self.height = height
        if self.camera is not None:
            # 重新初始化以应用新分辨率
            self.release_camera()
            self.initialize_camera()

    def get_resolution(self):
        """
        获取当前分辨率
        
        Returns:
            tuple[int, int]: (width, height)
        """
        return self.width, self.height
