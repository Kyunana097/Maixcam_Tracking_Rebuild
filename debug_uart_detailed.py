#!/usr/bin/env python3
"""
详细的UART调试脚本
用于验证单片机是否真的在发送0xAA
"""

import time
import serial

def debug_uart_detailed():
    """详细调试UART通信"""
    print("🔍 详细UART调试")
    print("=" * 50)
    
    try:
        # 建立串口连接
        ser = serial.Serial(
            port="/dev/serial0",
            baudrate=115200,
            timeout=3.0,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS
        )
        
        time.sleep(0.5)
        ser.flushInput()
        ser.flushOutput()
        
        print("✅ 串口连接成功")
        print(f"🔍 串口状态: {ser.is_open}")
        print(f"🔍 初始in_waiting: {ser.in_waiting}")
        
        # 清空任何残留数据
        if ser.in_waiting > 0:
            junk = ser.read(ser.in_waiting)
            print(f"🗑️ 清理残留数据: {[hex(b) for b in junk]}")
        
        print("\n🚀 开始握手测试")
        print("-" * 30)
        
        # 发送握手请求
        print("📤 发送握手请求: 0x55")
        ser.write(bytes([0x55]))
        # 不要flush，避免影响接收
        
        print("⏳ 开始监控响应...")
        
        # 详细监控响应过程
        for i in range(50):  # 监控5秒
            time.sleep(0.1)
            waiting = ser.in_waiting
            
            if waiting > 0:
                print(f"📥 第{i*0.1:.1f}s: 检测到 {waiting} 字节")
                response = ser.read(waiting)
                print(f"📥 收到数据: {[hex(b) for b in response]}")
                
                if 0xAA in response:
                    print("✅ 找到0xAA！握手成功")
                    ser.close()
                    return True
                else:
                    print(f"⚠️ 收到其他数据: {[hex(b) for b in response]}")
            else:
                if i % 10 == 0:  # 每秒打印一次状态
                    print(f"⏱️ 第{i*0.1:.1f}s: 等待中... (in_waiting={waiting})")
        
        print("❌ 5秒内未收到任何响应")
        ser.close()
        return False
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        return False

def test_serial_loopback():
    """测试串口回环"""
    print("\n🔄 测试串口回环")
    print("-" * 30)
    
    try:
        ser = serial.Serial("/dev/serial0", 115200, timeout=1.0)
        time.sleep(0.5)
        
        # 发送测试数据
        test_data = bytes([0x01, 0x02, 0x03, 0x04, 0x05])
        print(f"📤 发送测试数据: {[hex(b) for b in test_data]}")
        ser.write(test_data)
        
        time.sleep(0.5)
        
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"📥 收到回环数据: {[hex(b) for b in response]}")
        else:
            print("❌ 未收到回环数据")
        
        ser.close()
        
    except Exception as e:
        print(f"❌ 回环测试失败: {e}")

def main():
    """主函数"""
    print("🔧 UART详细调试工具")
    print("=" * 50)
    print("🔍 目标:")
    print("1. 验证单片机是否真的发送0xAA")
    print("2. 检查数据传输时序")
    print("3. 排查硬件连接问题")
    print()
    
    # 主要测试
    success = debug_uart_detailed()
    
    if not success:
        print("\n🔧 可能的问题:")
        print("1. 单片机程序未正确烧录")
        print("2. TX/RX线接反")
        print("3. 波特率不匹配")
        print("4. 电平不匹配")
        print("5. 单片机未运行或死机")
        
        # 额外测试
        test_serial_loopback()
    
    return success

if __name__ == "__main__":
    main()