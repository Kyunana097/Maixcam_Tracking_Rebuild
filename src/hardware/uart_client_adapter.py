#!/usr/bin/env python3
"""
UART 适配器：复用新串口客户端 SerialClient，保持主程序原有接口
API 兼容：connect()/disconnect()/send_alarm_status()/get_status()
"""

import time
from typing import Dict

from src.comm.serial_client import SerialClient


class UARTCommAdapter:
    def __init__(self, port: str = "/dev/serial0", baudrate: int = 115200, timeout: float = 3.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        # primary 使用传入端口，fallback 自动用 /dev/ttyS1
        fallback = "/dev/ttyS1" if port != "/dev/ttyS1" else "/dev/serial0"
        self.client = SerialClient(port_primary=port, port_fallback=fallback, baudrate=baudrate, timeout=0.1)
        self.connected = False
        # 协议常量
        self.ALARM_STATUS = 0x11

    def connect(self) -> bool:
        # 打开串口（含端口回退）
        if not self.client.connect():
            print("[UARTAdapter] 串口打开失败")
            self.connected = False
            return False

        # 握手（0x55 -> 0xAA），使用后台读线程缓冲保证不丢包
        print("[UARTAdapter] 开始握手 0x55 → 0xAA")
        ok = self.client.handshake(request=0x55, expect=0xAA, timeout_s=3.0)
        if not ok:
            # 快速重试一次
            import time as _t
            _t.sleep(0.2)
            self.client.clear_buffers()
            ok = self.client.handshake(request=0x55, expect=0xAA, timeout_s=3.0)
        self.connected = ok
        if ok:
            print("[UARTAdapter] ✅ 握手成功")
        else:
            print("[UARTAdapter] ❌ 握手失败")
            # 失败则断开，和原实现保持一致
            self.disconnect()
        return ok

    def disconnect(self):
        self.client.disconnect()
        self.connected = False
        print("[UARTAdapter] 已断开")

    def send_alarm_status(self, is_warning: bool) -> bool:
        if not self.connected:
            print("[UARTAdapter] 未连接，无法发送报警状态")
            return False
        payload = bytes([self.ALARM_STATUS, 0x01 if is_warning else 0x00])
        n = self.client.write(payload)
        print(f"[UARTAdapter] 发送报警状态: {'WARNING' if is_warning else 'SAFE'} -> {list(map(hex, payload))} (写入{n}字节)")
        return n == len(payload)

    def get_status(self) -> Dict[str, bool]:
        return {
            'connected': self.connected
        }

    def send_coordinates(self, x: int, y: int) -> bool:
        if not self.connected:
            print("[UARTAdapter] 未连接，无法发送坐标")
            return False
        # 限幅到相机分辨率（默认512x320）
        if x < 0: x = 0
        if y < 0: y = 0
        if x > 512: x = 512
        if y > 320: y = 320
        payload = bytes([
            0x22,
            (x >> 8) & 0xFF, x & 0xFF,
            (y >> 8) & 0xFF, y & 0xFF
        ])
        n = self.client.write(payload)
        # 可按需打开调试
        # print(f"[UARTAdapter] 发送坐标: ({x},{y}) -> {list(map(hex, payload))} (写入{n}字节)")
        return n == len(payload)


