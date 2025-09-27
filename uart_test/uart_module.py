#!/usr/bin/env python3
"""
独立的UART通信模块
用于测试和调试UART通信问题
"""

import time
import serial
from typing import Optional

class UARTModule:
    """独立的UART通信模块"""
    
    def __init__(self, port: str = "/dev/serial0", baudrate: int = 115200, timeout: float = 3.0):
        """
        初始化UART通信模块
        
        Args:
            port: 串口设备路径
            baudrate: 波特率
            timeout: 超时时间
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn: Optional[serial.Serial] = None
        self.is_connected = False
        
        # 通信协议定义
        self.HANDSHAKE_REQUEST = 0x55      # 握手请求
        self.HANDSHAKE_RESPONSE = 0xAA     # 握手响应
        self.ALARM_STATUS = 0x11           # 报警状态
        
        print(f"🔌 UART模块初始化: {port} @ {baudrate}bps")
    
    def connect(self) -> bool:
        """
        建立UART连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
            
            # 创建串口连接
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            
            # 等待串口稳定
            time.sleep(0.5)
            
            # 清空缓冲区
            self.serial_conn.flushInput()
            self.serial_conn.flushOutput()
            
            self.is_connected = True
            print(f"✅ UART连接成功: {self.port}")
            return True
            
        except Exception as e:
            print(f"❌ UART连接失败: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """断开UART连接"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.is_connected = False
            print("🔌 UART连接已断开")
    
    def handshake(self) -> bool:
        """
        与单片机进行握手验证
        
        Returns:
            bool: 握手是否成功
        """
        try:
            if not self.serial_conn or not self.serial_conn.is_open:
                print("❌ 串口未连接")
                return False
            
            print(f"🔍 串口状态: 已连接, 端口={self.port}")
            
            # 发送握手请求
            print(f"📤 发送握手请求: 0x{self.HANDSHAKE_REQUEST:02X}")
            self.serial_conn.write(bytes([self.HANDSHAKE_REQUEST]))
            self.serial_conn.flush()
            
            # 等待握手响应
            print("⏳ 等待握手响应...")
            time.sleep(2.0)
            
            # 检查响应
            if self.serial_conn.in_waiting > 0:
                response = self.serial_conn.read(self.serial_conn.in_waiting)
                print(f"📥 收到响应: {[hex(b) for b in response]}")
                
                if len(response) > 0 and response[0] == self.HANDSHAKE_RESPONSE:
                    print("✅ 握手成功！")
                    return True
                else:
                    print(f"❌ 握手失败：期望0x{self.HANDSHAKE_RESPONSE:02X}，收到0x{response[0]:02X}")
            else:
                print("❌ 无握手响应")
                print(f"🔍 调试信息: in_waiting={self.serial_conn.in_waiting}")
            
            return False
            
        except Exception as e:
            print(f"❌ 握手失败: {e}")
            return False
    
    def send_alarm_status(self, is_warning: bool) -> bool:
        """
        发送报警状态到单片机
        
        Args:
            is_warning: True表示报警状态，False表示安全状态
            
        Returns:
            bool: 发送是否成功
        """
        if not self.is_connected or not self.serial_conn:
            print("❌ UART未连接，无法发送报警状态")
            return False
        
        try:
            # 构建报警状态帧
            status_byte = 0x01 if is_warning else 0x00
            frame = bytes([
                self.ALARM_STATUS,  # 命令字节
                status_byte         # 状态字节
            ])
            
            # 发送数据
            self.serial_conn.write(frame)
            self.serial_conn.flush()
            
            status_text = "WARNING" if is_warning else "SAFE"
            print(f"🚨 发送报警状态: {status_text}")
            return True
            
        except Exception as e:
            print(f"❌ 发送报警状态失败: {e}")
            return False
    
    def get_status(self) -> dict:
        """
        获取UART状态
        
        Returns:
            dict: 状态信息
        """
        return {
            'is_connected': self.is_connected,
            'port': self.port,
            'baudrate': self.baudrate,
            'timeout': self.timeout
        }
