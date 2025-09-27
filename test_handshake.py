#!/usr/bin/env python3
import serial
import time

port = '/dev/serial0'
baudrate = 115200

try:
    ser = serial.Serial(port, baudrate, timeout=3.0)
    time.sleep(0.5)
    ser.flushInput()
    ser.flushOutput()

    print("📤 发送 0x55")
    ser.write(b'\x55')
    time.sleep(0.1)

    print("⏳ 等待响应...")
    for i in range(20):
        time.sleep(0.1)
        if ser.in_waiting > 0:
            rsp = ser.read(ser.in_waiting)
            print(f"📥 收到: {[hex(b) for b in rsp]}")
            if 0xAA in rsp:
                print("✅ 握手成功")
            else:
                print("❌ 收到但不是 0xAA")
            break
    else:
        print("❌ 无响应")

    ser.close()
except Exception as e:
    print(f"❌ 异常: {e}")