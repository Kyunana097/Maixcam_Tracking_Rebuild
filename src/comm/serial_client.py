#!/usr/bin/env python3
"""
串口客户端（重构版）
- 端口回退: /dev/serial0 → /dev/ttyS1
- 后台读线程: 非阻塞接收，缓冲环形队列
- 明确API: connect/handshake/read/write/get_bytes/clear/disconnect
- 调试强化: 关键动作打印、统计、最近数据窗口
"""

import serial
import threading
import time
from collections import deque
from typing import Optional, Deque, Tuple


class SerialClient:
    def __init__(self, port_primary: str = "/dev/serial0", port_fallback: str = "/dev/ttyS1", baudrate: int = 115200, timeout: float = 0.1, rx_buffer_size: int = 1024):
        self.port_primary = port_primary
        self.port_fallback = port_fallback
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser: Optional[serial.Serial] = None
        self.rx_buffer: Deque[int] = deque(maxlen=rx_buffer_size)
        self._rx_thread: Optional[threading.Thread] = None
        self._rx_running = False
        self.stats = {
            "connect_attempts": 0,
            "handshake_attempts": 0,
            "bytes_tx": 0,
            "bytes_rx": 0,
        }

    # ---------- low-level ----------
    def _open(self, port: str) -> bool:
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
            )
            time.sleep(0.3)
            return self.ser.is_open
        except Exception as e:
            print(f"[SerialClient] 打开端口失败: {port} -> {e}")
            self.ser = None
            return False

    def _start_rx_thread(self):
        if not self.ser or not self.ser.is_open:
            return
        self._rx_running = True
        self._rx_thread = threading.Thread(target=self._rx_loop, daemon=True)
        self._rx_thread.start()

    def _rx_loop(self):
        while self._rx_running and self.ser and self.ser.is_open:
            try:
                waiting = self.ser.in_waiting
                if waiting > 0:
                    data = self.ser.read(waiting)
                    for b in data:
                        self.rx_buffer.append(b)
                    self.stats["bytes_rx"] += len(data)
                else:
                    time.sleep(0.01)
            except Exception:
                time.sleep(0.05)

    # ---------- public API ----------
    def connect(self) -> bool:
        self.stats["connect_attempts"] += 1
        # 依次尝试两个端口
        if self._open(self.port_primary):
            print(f"[SerialClient] 已连接: {self.port_primary}")
        elif self._open(self.port_fallback):
            print(f"[SerialClient] 已连接(回退): {self.port_fallback}")
        else:
            print("[SerialClient] 两个端口均无法打开")
            return False

        # 清空缓冲
        self.clear_buffers()
        # 启动后台接收
        self._start_rx_thread()
        return True

    def clear_buffers(self):
        if self.ser and self.ser.is_open:
            try:
                self.ser.reset_input_buffer()
                self.ser.reset_output_buffer()
            except Exception:
                # 兼容旧API
                try:
                    self.ser.flushInput()
                    self.ser.flushOutput()
                except Exception:
                    pass
        self.rx_buffer.clear()

    def write(self, data: bytes) -> int:
        if not self.ser or not self.ser.is_open:
            print("[SerialClient] 未连接，无法发送")
            return 0
        try:
            n = self.ser.write(data)
            self.stats["bytes_tx"] += n
            return n
        except Exception as e:
            print(f"[SerialClient] 发送失败: {e}")
            return 0

    def get_bytes(self, maxlen: int = 1024) -> bytes:
        out = bytearray()
        for _ in range(min(maxlen, len(self.rx_buffer))):
            out.append(self.rx_buffer.popleft())
        return bytes(out)

    def peek_all(self) -> bytes:
        return bytes(self.rx_buffer)

    def disconnect(self):
        self._rx_running = False
        if self._rx_thread and self._rx_thread.is_alive():
            self._rx_thread.join(timeout=0.2)
        if self.ser:
            try:
                if self.ser.is_open:
                    self.ser.close()
            except Exception:
                pass
            finally:
                self.ser = None

    # ---------- high-level helpers ----------
    def handshake(self, request: int = 0x55, expect: int = 0xAA, timeout_s: float = 3.0) -> bool:
        if not self.ser or not self.ser.is_open:
            print("[SerialClient] 未连接，无法握手")
            return False
        self.stats["handshake_attempts"] += 1

        # 清空残留
        self.clear_buffers()
        time.sleep(0.1)

        # 发送请求
        self.write(bytes([request]))

        # 轮询等待
        deadline = time.time() + timeout_s
        last_len = -1
        while time.time() < deadline:
            buf = self.peek_all()
            if len(buf) != last_len:
                print(f"[SerialClient] 握手读取: {list(map(hex, buf))}")
                last_len = len(buf)
            if expect in buf:
                # 抽走缓冲区内容，避免污染后续
                _ = self.get_bytes()
                return True
            time.sleep(0.02)
        return False

    def request_and_wait(self, payload: bytes, expect_any: Tuple[int, ...], timeout_s: float = 1.0) -> bytes:
        self.clear_buffers()
        self.write(payload)
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            buf = self.peek_all()
            if any(token in buf for token in expect_any):
                return self.get_bytes()
            time.sleep(0.01)
        return self.get_bytes()


