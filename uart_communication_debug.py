#!/usr/bin/env python3
"""
重构的UART通信模块 - 调试增强版
包含详细的调试信息、状态监控和问题诊断功能
"""

import serial
import time
import struct
import threading
from typing import Optional, Tuple, List, Dict, Any
from enum import Enum

class UARTState(Enum):
    """UART连接状态枚举"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    HANDSHAKING = "handshaking"
    CONNECTED = "connected"
    ERROR = "error"

class UARTCommunicationDebug:
    """UART通信类 - 调试增强版"""
    
    def __init__(self, port: str = "/dev/serial0", baudrate: int = 115200, timeout: float = 3.0):
        """初始化UART通信"""
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn: Optional[serial.Serial] = None
        self.state = UARTState.DISCONNECTED
        
        # 通信协议定义
        self.HANDSHAKE_REQUEST = 0x55
        self.HANDSHAKE_RESPONSE = 0xAA
        self.DATA_REQUEST = 0x33
        self.DATA_RESPONSE = 0xCC
        self.ALARM_STATUS = 0x11
        self.COORDINATE_DATA = 0x22
        
        # 调试和统计信息
        self.debug_enabled = True
        self.stats = {
            'connection_attempts': 0,
            'successful_connections': 0,
            'handshake_attempts': 0,
            'successful_handshakes': 0,
            'bytes_sent': 0,
            'bytes_received': 0,
            'errors': 0,
            'last_error': None
        }
        
        # 状态监控
        self.last_handshake_time = 0
        self.last_send_time = 0
        self.last_receive_time = 0
        self.connection_start_time = 0
        
        # 调试日志
        self.debug_log = []
        self.max_log_entries = 100
        
        self.log(f"🔌 UART通信初始化: {port} @ {baudrate}bps", "INIT")
    
    def log(self, message: str, level: str = "INFO"):
        """记录调试信息"""
        if not self.debug_enabled:
            return
            
        timestamp = time.time()
        log_entry = {
            'time': timestamp,
            'level': level,
            'message': message,
            'state': self.state.value,
            'readable_time': time.strftime('%H:%M:%S.%f', time.localtime(timestamp))[:-3]
        }
        
        self.debug_log.append(log_entry)
        if len(self.debug_log) > self.max_log_entries:
            self.debug_log.pop(0)
        
        print(f"[{log_entry['readable_time']}] {level}: {message}")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """获取连接详细信息"""
        info = {
            'state': self.state.value,
            'port': self.port,
            'baudrate': self.baudrate,
            'is_connected': self.is_connected(),
            'stats': self.stats.copy()
        }
        
        if self.serial_conn:
            try:
                info.update({
                    'serial_open': self.serial_conn.is_open,
                    'serial_readable': self.serial_conn.readable(),
                    'serial_writable': self.serial_conn.writable(),
                    'in_waiting': self.serial_conn.in_waiting,
                    'timeout': self.serial_conn.timeout
                })
            except Exception as e:
                info['serial_error'] = str(e)
        
        return info
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return (self.state == UARTState.CONNECTED and 
                self.serial_conn and 
                self.serial_conn.is_open)
    
    def connect(self) -> bool:
        """连接到UART设备并进行握手"""
        self.stats['connection_attempts'] += 1
        self.state = UARTState.CONNECTING
        self.connection_start_time = time.time()
        
        self.log("🔌 开始连接UART设备", "CONNECT")
        
        try:
            # 如果已经连接，先断开
            if self.serial_conn and self.serial_conn.is_open:
                self.log("⚠️ 检测到已有连接，先断开", "WARNING")
                self.disconnect()
            
            # 建立串口连接
            self.log(f"📡 尝试打开串口: {self.port}", "CONNECT")
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
            
            if not self.serial_conn.is_open:
                raise Exception("串口未成功打开")
            
            self.log("✅ 串口连接成功", "SUCCESS")
            self.log(f"🔍 串口状态: readable={self.serial_conn.readable()}, writable={self.serial_conn.writable()}", "INFO")
            
            # 进行握手
            if self._handshake():
                self.state = UARTState.CONNECTED
                self.stats['successful_connections'] += 1
                connection_duration = time.time() - self.connection_start_time
                self.log(f"✅ UART连接成功并握手验证: {self.port} (耗时{connection_duration:.2f}s)", "SUCCESS")
                return True
            else:
                self.state = UARTState.ERROR
                self.log("❌ 握手失败，连接未建立", "ERROR")
                self.disconnect()
                return False
                
        except Exception as e:
            self.state = UARTState.ERROR
            self.stats['errors'] += 1
            self.stats['last_error'] = str(e)
            self.log(f"❌ UART连接失败: {e}", "ERROR")
            return False
    
    def _handshake(self) -> bool:
        """与单片机进行握手验证 - 调试增强版"""
        self.state = UARTState.HANDSHAKING
        self.stats['handshake_attempts'] += 1
        
        try:
            self.log(f"🔍 开始握手验证 - 端口: {self.port}", "HANDSHAKE")
            
            if not self.serial_conn or not self.serial_conn.is_open:
                self.log("❌ 串口未连接", "ERROR")
                return False
            
            # 记录握手开始状态
            initial_in_waiting = self.serial_conn.in_waiting
            self.log(f"🔍 握手开始状态: in_waiting={initial_in_waiting}", "DEBUG")
            
            # 清空缓冲区
            self.log("🧹 清空串口缓冲区", "DEBUG")
            flush_start = time.time()
            self.serial_conn.flushInput()
            self.serial_conn.flushOutput()
            flush_duration = (time.time() - flush_start) * 1000
            
            after_flush_in_waiting = self.serial_conn.in_waiting
            self.log(f"🔍 缓冲区清理完成: 耗时{flush_duration:.2f}ms, in_waiting={after_flush_in_waiting}", "DEBUG")
            
            # 发送握手请求
            self.log("📤 发送握手请求: 0x55", "HANDSHAKE")
            send_start = time.time()
            bytes_written = self.serial_conn.write(b'\x55')
            send_duration = (time.time() - send_start) * 1000
            
            self.stats['bytes_sent'] += bytes_written
            self.last_send_time = time.time()
            
            self.log(f"🔍 发送完成: {bytes_written}字节, 耗时{send_duration:.2f}ms", "DEBUG")
            
            # 短暂延迟确保数据发送
            time.sleep(0.1)
            
            # 详细监控响应过程
            self.log("⏳ 开始监控握手响应...", "HANDSHAKE")
            response_found = False
            total_response_data = b''
            
            for check_count in range(50):  # 最多检查5秒
                check_start = time.time()
                in_waiting = self.serial_conn.in_waiting
                
                if in_waiting > 0:
                    response = self.serial_conn.read(in_waiting)
                    receive_time = time.time()
                    response_delay = (receive_time - send_start) * 1000
                    
                    total_response_data += response
                    self.stats['bytes_received'] += len(response)
                    self.last_receive_time = receive_time
                    
                    self.log(f"📥 收到数据 #{check_count}: {[hex(b) for b in response]} (延迟{response_delay:.1f}ms)", "RECEIVE")
                    
                    # 检查是否包含握手响应
                    if 0xAA in response:
                        self.stats['successful_handshakes'] += 1
                        self.last_handshake_time = time.time()
                        total_handshake_time = (self.last_handshake_time - send_start) * 1000
                        
                        self.log(f"✅ 握手成功！收到0xAA响应 (总耗时{total_handshake_time:.1f}ms)", "SUCCESS")
                        return True
                    
                    # 如果收到数据但不是0xAA，记录并继续等待
                    self.log(f"⚠️ 收到非握手数据: {[hex(b) for b in response]}", "WARNING")
                
                # 每次检查的间隔
                time.sleep(0.1)
                
                # 每10次检查打印一次状态
                if check_count % 10 == 0 and check_count > 0:
                    elapsed = (time.time() - send_start) * 1000
                    self.log(f"⏱️ 握手等待中... ({elapsed:.0f}ms已过)", "INFO")
            
            # 握手超时
            total_wait_time = (time.time() - send_start) * 1000
            self.log(f"❌ 握手超时：等待{total_wait_time:.0f}ms未收到0xAA响应", "ERROR")
            
            if total_response_data:
                self.log(f"🔍 握手期间收到的所有数据: {[hex(b) for b in total_response_data]}", "DEBUG")
            else:
                self.log("🔍 握手期间未收到任何数据", "DEBUG")
            
            return False
            
        except Exception as e:
            self.stats['errors'] += 1
            self.stats['last_error'] = str(e)
            self.log(f"❌ 握手异常: {e}", "ERROR")
            return False
    
    def disconnect(self):
        """断开UART连接"""
        if self.serial_conn:
            try:
                if self.serial_conn.is_open:
                    self.serial_conn.close()
                    self.log("🔌 UART连接已断开", "DISCONNECT")
            except Exception as e:
                self.log(f"⚠️ 断开连接时出错: {e}", "WARNING")
            finally:
                self.serial_conn = None
        
        self.state = UARTState.DISCONNECTED
    
    def send_alarm_status(self, is_warning: bool) -> bool:
        """发送报警状态"""
        if not self.is_connected():
            self.log("❌ UART未连接，无法发送报警状态", "ERROR")
            return False
        
        try:
            # 构造报警状态数据包
            status_byte = 0x01 if is_warning else 0x00
            data_packet = bytes([self.ALARM_STATUS, status_byte])
            
            send_start = time.time()
            bytes_sent = self.serial_conn.write(data_packet)
            send_duration = (time.time() - send_start) * 1000
            
            self.stats['bytes_sent'] += bytes_sent
            self.last_send_time = time.time()
            
            status_text = "WARNING" if is_warning else "SAFE"
            self.log(f"📤 发送报警状态: {status_text} ({[hex(b) for b in data_packet]}, {bytes_sent}字节, {send_duration:.2f}ms)", "SEND")
            
            return True
            
        except Exception as e:
            self.stats['errors'] += 1
            self.stats['last_error'] = str(e)
            self.log(f"❌ 发送报警状态失败: {e}", "ERROR")
            return False
    
    def send_coordinates(self, x: int, y: int) -> bool:
        """发送坐标数据"""
        if not self.is_connected():
            self.log("❌ UART未连接，无法发送坐标", "ERROR")
            return False
        
        try:
            # 构造坐标数据包
            data_packet = struct.pack('<BHH', self.COORDINATE_DATA, x, y)
            
            send_start = time.time()
            bytes_sent = self.serial_conn.write(data_packet)
            send_duration = (time.time() - send_start) * 1000
            
            self.stats['bytes_sent'] += bytes_sent
            self.last_send_time = time.time()
            
            self.log(f"📤 发送坐标: ({x}, {y}) ({[hex(b) for b in data_packet]}, {bytes_sent}字节, {send_duration:.2f}ms)", "SEND")
            
            return True
            
        except Exception as e:
            self.stats['errors'] += 1
            self.stats['last_error'] = str(e)
            self.log(f"❌ 发送坐标失败: {e}", "ERROR")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取通信状态"""
        return {
            'connected': self.is_connected(),
            'state': self.state.value,
            'port': self.port,
            'baudrate': self.baudrate,
            'stats': self.stats.copy(),
            'last_handshake_time': self.last_handshake_time,
            'last_send_time': self.last_send_time,
            'last_receive_time': self.last_receive_time
        }
    
    def get_debug_summary(self) -> str:
        """获取调试摘要"""
        info = self.get_connection_info()
        
        summary = f"""
🔧 UART调试摘要
{'='*40}
📡 连接状态: {info['state']}
🔌 串口: {info['port']} @ {info['baudrate']}bps
📊 统计信息:
  • 连接尝试: {info['stats']['connection_attempts']}
  • 成功连接: {info['stats']['successful_connections']}
  • 握手尝试: {info['stats']['handshake_attempts']}
  • 成功握手: {info['stats']['successful_handshakes']}
  • 发送字节: {info['stats']['bytes_sent']}
  • 接收字节: {info['stats']['bytes_received']}
  • 错误次数: {info['stats']['errors']}
"""
        
        if info['stats']['last_error']:
            summary += f"  • 最后错误: {info['stats']['last_error']}\n"
        
        if 'serial_open' in info:
            summary += f"🔍 串口状态:\n"
            summary += f"  • 已打开: {info['serial_open']}\n"
            summary += f"  • 可读: {info['serial_readable']}\n"
            summary += f"  • 可写: {info['serial_writable']}\n"
            summary += f"  • 待读取: {info['in_waiting']} 字节\n"
        
        return summary
    
    def print_debug_summary(self):
        """打印调试摘要"""
        print(self.get_debug_summary())

def main():
    """测试函数"""
    print("🔧 UART通信调试版本测试")
    print("=" * 50)
    
    uart = UARTCommunicationDebug("/dev/serial0", 115200)
    
    # 测试连接
    if uart.connect():
        print("✅ 连接测试成功")
        
        # 测试发送报警状态
        uart.send_alarm_status(True)
        time.sleep(1)
        uart.send_alarm_status(False)
        
        # 测试发送坐标
        uart.send_coordinates(256, 160)
        
    else:
        print("❌ 连接测试失败")
    
    # 打印调试摘要
    uart.print_debug_summary()
    
    # 断开连接
    uart.disconnect()

if __name__ == "__main__":
    main()
