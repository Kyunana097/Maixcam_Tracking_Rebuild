#!/usr/bin/env python3
import time
import serial
import os

def debug_uart_timing():
    """调试UART时序问题"""
    print("🔍 UART时序调试")
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
            timeout=3.0
        )
        
        print(f"✅ 端口 {port} 连接成功")
        
        # 清空缓冲区
        ser.flushInput()
        ser.flushOutput()
        time.sleep(0.5)
        
        # 发送握手请求
        print(f"📤 发送握手请求: 0x55")
        ser.write(bytes([0x55]))
        ser.flush()
        
        # 分步等待响应
        print(f"⏳ 等待握手响应...")
        for i in range(20):  # 等待2秒，每100ms检查一次
            time.sleep(0.1)
            if ser.in_waiting > 0:
                response = ser.read(ser.in_waiting)
                print(f"📥 收到响应: {[hex(b) for b in response]} (等待时间: {i*0.1:.1f}s)")
                
                if len(response) > 0 and response[0] == 0xAA:
                    print(f"✅ 握手成功！")
                    ser.close()
                    return True
                else:
                    print(f"❌ 握手失败：期望0xAA，收到0x{response[0]:02X}")
                    ser.close()
                    return False
        
        print(f"❌ 无响应 (等待时间: 2.0s)")
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
    
    success = debug_uart_timing()
    
    if success:
        print("\n🎉 握手调试成功！")
    else:
        print("\n❌ 握手调试失败！")
        print("🔍 可能的问题：")
        print("   1. 单片机程序未正确烧录")
        print("   2. 硬件连接问题")
        print("   3. 时序问题")
        print("   4. 单片机代码中的握手处理有问题")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
