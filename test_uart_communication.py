#!/usr/bin/env python3
import time
import serial
import os

def test_uart_communication():
    """测试UART通信"""
    print("🔍 UART通信测试")
    print("=" * 60)
    
    port = '/dev/serial0'
    
    if not os.path.exists(port):
        print(f"❌ 端口不存在: {port}")
        return False
        
    print(f"🧪 测试端口: {port}")
    print("-" * 40)
    
    try:
        # 创建串口连接
        ser = serial.Serial(
            port=port,
            baudrate=115200,
            timeout=3.0,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS
        )
        
        print(f"✅ 串口连接成功")
        
        # 清空缓冲区
        ser.flushInput()
        ser.flushOutput()
        time.sleep(0.5)
        
        # 发送握手请求
        print(f"📤 发送握手请求: 0x55")
        ser.write(bytes([0x55]))
        ser.flush()
        
        # 等待响应
        print(f"⏳ 等待响应...")
        time.sleep(2.0)
        
        # 检查响应
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"📥 收到响应: {[hex(b) for b in response]}")
            
            if len(response) > 0 and response[0] == 0xAA:
                print(f"✅ 握手成功！")
                ser.close()
                return True
            else:
                print(f"❌ 握手失败：期望0xAA，收到0x{response[0]:02X}")
        else:
            print(f"❌ 无响应 (in_waiting={ser.in_waiting})")
        
        ser.close()
        return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    print("🔍 请确保：")
    print("   1. 单片机程序已烧录并运行")
    print("   2. 硬件连接正确 (TX-RX, RX-TX, GND-GND)")
    print("   3. 观察单片机LED状态")
    print("\n⏳ 3秒后开始测试...")
    time.sleep(3)
    
    success = test_uart_communication()
    
    if success:
        print("\n🎉 UART通信测试成功！")
    else:
        print("\n❌ UART通信测试失败！")
        print("🔍 可能的问题：")
        print("   1. 硬件连接问题")
        print("   2. 串口配置问题")
        print("   3. 时序问题")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
