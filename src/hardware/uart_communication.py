#!/usr/bin/env python3
"""
MaixCam与MSPM0G3507单片机的UART通信模块
用于发送跟踪目标的坐标数据到云台控制系统
"""

import serial
import time
import struct
from typing import Optional, Tuple

class UARTCommunication:
    """UART通信类，负责与单片机进行数据交换"""
    
    def __init__(self, port: str = "/dev/ttyS1", baudrate: int = 115200, timeout: float = 1.0):
        """
        初始化UART通信
        
        Args:
            port: 串口设备路径，默认/dev/ttyS1
            baudrate: 波特率，默认115200
            timeout: 超时时间，默认1秒
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn: Optional[serial.Serial] = None
        self.is_connected = False
        
        # 通信协议定义
        self.HANDSHAKE_REQUEST = 0x55      # 握手请求
        self.HANDSHAKE_RESPONSE = 0xAA     # 握手响应
        self.DATA_REQUEST = 0x33           # 数据请求
        self.DATA_RESPONSE = 0xCC          # 数据响应
        self.ALARM_STATUS = 0x11           # 报警状态
        self.COORDINATE_DATA = 0x22        # 坐标数据
        
        # 连接状态
        self.connection_verified = False
        self.last_handshake_time = 0
        
        print(f"🔌 UART通信初始化: {port} @ {baudrate}bps")
    
    def connect(self) -> bool:
        """
        建立UART连接并进行握手验证
        
        Returns:
            bool: 连接是否成功
        """
        try:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
            
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            
            # 等待串口稳定
            time.sleep(0.1)
            
            # 尝试握手验证
            if self._handshake():
                self.is_connected = True
                self.connection_verified = True
                print(f"✅ UART连接成功并握手验证: {self.port}")
                return True
            else:
                self.is_connected = False
                self.connection_verified = False
                print(f"⚠️ UART连接成功但握手失败: {self.port}")
                return False
            
        except Exception as e:
            print(f"❌ UART连接失败: {e}")
            self.is_connected = False
            self.connection_verified = False
            return False
    
    def disconnect(self):
        """断开UART连接"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.is_connected = False
            print("🔌 UART连接已断开")
    
    def _handshake(self) -> bool:
        """
        与单片机进行握手验证
        
        Returns:
            bool: 握手是否成功
        """
        try:
            # 发送握手请求
            self.serial_conn.write(bytes([self.HANDSHAKE_REQUEST]))
            self.serial_conn.flush()
            time.sleep(0.1)
            
            # 等待握手响应
            if self.serial_conn.in_waiting > 0:
                response = self.serial_conn.read(1)
                if response and response[0] == self.HANDSHAKE_RESPONSE:
                    self.last_handshake_time = time.time()
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ 握手失败: {e}")
            return False
    
    def send_coordinates(self, x: int, y: int) -> bool:
        """
        发送坐标数据到单片机
        
        Args:
            x: X坐标 (0-65535)
            y: Y坐标 (0-65535)
            
        Returns:
            bool: 发送是否成功
        """
        if not self.is_connected or not self.serial_conn:
            print("❌ UART未连接，无法发送数据")
            return False
        
        try:
            # 限制坐标范围
            x = max(0, min(65535, int(x)))
            y = max(0, min(65535, int(y)))
            
            # 构建坐标数据帧
            frame = bytes([
                self.COORDINATE_DATA,  # 命令字节
                (x >> 8) & 0xFF,       # X坐标高字节
                x & 0xFF,               # X坐标低字节
                (y >> 8) & 0xFF,       # Y坐标高字节
                y & 0xFF               # Y坐标低字节
            ])
            
            # 发送数据
            self.serial_conn.write(frame)
            self.serial_conn.flush()
            
            print(f"📤 发送坐标: ({x}, {y})")
            return True
            
        except Exception as e:
            print(f"❌ 发送坐标失败: {e}")
            return False
    
    def _build_frame(self, x: int, y: int) -> bytes:
        """
        构建数据帧
        
        Args:
            x: X坐标
            y: Y坐标
            
        Returns:
            bytes: 完整的数据帧
        """
        # 将坐标分解为高字节和低字节
        x_high = (x >> 8) & 0xFF
        x_low = x & 0xFF
        y_high = (y >> 8) & 0xFF
        y_low = y & 0xFF
        
        # 计算校验位
        checksum = (x_high + x_low + y_high + y_low) & 0xFF
        
        # 构建完整帧
        frame = (
            self.FRAME_HEADER +           # 帧头: 0xAA 0xAA
            bytes([x_high, x_low]) +      # X坐标: 高字节 低字节
            bytes([y_high, y_low]) +      # Y坐标: 高字节 低字节
            bytes([checksum]) +           # 校验位
            self.FRAME_TAIL               # 帧尾: 0xFF 0xFF
        )
        
        return frame
    
    def send_tracking_data(self, center_x: int, center_y: int, bbox: Tuple[int, int, int, int]) -> bool:
        """
        发送跟踪数据（包含坐标和边界框信息）
        
        Args:
            center_x: 中心点X坐标
            center_y: 中心点Y坐标
            bbox: 边界框 (x, y, w, h)
            
        Returns:
            bool: 发送是否成功
        """
        # 目前只发送中心点坐标，后续可以扩展
        return self.send_coordinates(center_x, center_y)
    
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
    
    def _build_alarm_frame(self, status: int) -> bytes:
        """
        构建报警状态帧
        
        Args:
            status: 报警状态 (0x00=安全, 0x01=报警)
            
        Returns:
            bytes: 完整的报警状态帧
        """
        # 构建报警状态帧: 帧头(2) + 状态(1) + 校验(1) + 帧尾(2) = 6字节
        checksum = status & 0xFF
        
        frame = (
            self.ALARM_HEADER +           # 帧头: 0xBB 0xBB
            bytes([status]) +             # 状态字节
            bytes([checksum]) +            # 校验位
            self.ALARM_TAIL               # 帧尾: 0xEE 0xEE
        )
        
        return frame
    
    def read_response(self) -> Optional[bytes]:
        """
        读取单片机响应数据
        
        Returns:
            Optional[bytes]: 响应数据，如果超时返回None
        """
        if not self.is_connected or not self.serial_conn:
            return None
        
        try:
            if self.serial_conn.in_waiting > 0:
                response = self.serial_conn.read(self.serial_conn.in_waiting)
                return response
        except Exception as e:
            print(f"❌ 读取响应失败: {e}")
        
        return None
    
    def test_connection(self) -> bool:
        """
        测试UART连接
        
        Returns:
            bool: 连接是否正常
        """
        if not self.is_connected:
            return False
        
        try:
            # 尝试重新握手
            if self._handshake():
                self.connection_verified = True
                return True
            else:
                self.connection_verified = False
                return False
        except Exception as e:
            print(f"❌ 连接测试失败: {e}")
            return False
    
    def check_connection_status(self) -> dict:
        """
        检查连接状态
        
        Returns:
            dict: 连接状态信息
        """
        current_time = time.time()
        time_since_handshake = current_time - self.last_handshake_time if self.last_handshake_time > 0 else float('inf')
        
        return {
            'connected': self.is_connected,
            'verified': self.connection_verified,
            'time_since_handshake': time_since_handshake,
            'port': self.port,
            'baudrate': self.baudrate
        }
    
    def get_status(self) -> dict:
        """
        获取UART连接状态
        
        Returns:
            dict: 状态信息
        """
        return {
            'connected': self.is_connected,
            'port': self.port,
            'baudrate': self.baudrate,
            'timeout': self.timeout
        }
    
    def __del__(self):
        """析构函数，确保连接被正确关闭"""
        self.disconnect()


class GimbalController:
    """云台控制器，封装UART通信和云台控制逻辑"""
    
    def __init__(self, uart_port: str = "/dev/ttyS1", uart_baudrate: int = 115200):
        """
        初始化云台控制器
        
        Args:
            uart_port: UART端口
            uart_baudrate: UART波特率
        """
        self.uart = UARTCommunication(uart_port, uart_baudrate)
        self.last_coordinates = None
        self.tracking_active = False
        
        print("🎯 云台控制器初始化完成")
    
    def start_tracking(self) -> bool:
        """
        开始跟踪模式
        
        Returns:
            bool: 是否成功启动
        """
        if not self.uart.connect():
            return False
        
        self.tracking_active = True
        print("🎯 云台跟踪模式已启动")
        return True
    
    def stop_tracking(self):
        """停止跟踪模式"""
        self.tracking_active = False
        self.uart.disconnect()
        print("⏹️ 云台跟踪模式已停止")
    
    def update_target(self, center_x: int, center_y: int, bbox: Tuple[int, int, int, int] = None) -> bool:
        """
        更新跟踪目标坐标
        
        Args:
            center_x: 目标中心X坐标
            center_y: 目标中心Y坐标
            bbox: 边界框信息（可选）
            
        Returns:
            bool: 是否成功发送
        """
        if not self.tracking_active:
            return False
        
        # 记录坐标
        self.last_coordinates = (center_x, center_y)
        
        # 发送到云台
        success = self.uart.send_tracking_data(center_x, center_y, bbox or (0, 0, 0, 0))
        
        if success:
            print(f"🎯 云台目标更新: 中心点({center_x}, {center_y})")
        
        return success
    
    def send_alarm_status(self, is_warning: bool) -> bool:
        """
        发送报警状态到单片机控制LED
        
        Args:
            is_warning: True表示报警状态，False表示安全状态
            
        Returns:
            bool: 是否成功发送
        """
        if not self.tracking_active:
            return False
        
        success = self.uart.send_alarm_status(is_warning)
        
        if success:
            status_text = "WARNING" if is_warning else "SAFE"
            print(f"🚨 云台报警状态: {status_text}")
        
        return success
    
    def get_status(self) -> dict:
        """
        获取云台状态
        
        Returns:
            dict: 状态信息
        """
        uart_status = self.uart.get_status()
        return {
            'tracking_active': self.tracking_active,
            'last_coordinates': self.last_coordinates,
            'uart': uart_status
        }


# 测试函数
def test_uart_communication():
    """测试UART通信功能"""
    print("🧪 开始UART通信测试")
    
    # 创建UART通信实例
    uart = UARTCommunication()
    
    # 测试连接
    if not uart.connect():
        print("❌ 连接测试失败")
        return False
    
    # 测试发送坐标
    test_coordinates = [
        (100, 100),
        (200, 150),
        (300, 200),
        (400, 250)
    ]
    
    for x, y in test_coordinates:
        success = uart.send_coordinates(x, y)
        print(f"发送坐标 ({x}, {y}): {'成功' if success else '失败'}")
        time.sleep(0.5)
    
    # 断开连接
    uart.disconnect()
    print("✅ UART通信测试完成")
    return True


if __name__ == "__main__":
    # 运行测试
    test_uart_communication()
