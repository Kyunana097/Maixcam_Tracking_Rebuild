#!/usr/bin/env python3
"""
UART端口调试脚本
检查所有可用的UART端口并测试连接
"""

import time
import serial
import os

def test_uart_port(port, baudrate=115200):
    """测试单个UART端口"""
    try:
        print(f"🔌 测试端口: {port}")
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=1.0
        )
        
        print(f"✅ 端口 {port} 可用")
        
        # 清空缓冲区
        ser.flushInput()
        ser.flushOutput()
        time.sleep(0.1)
        
        # 发送握手请求
        print(f"📤 发送握手请求到 {port}")
        ser.write(bytes([0x55]))
        ser.flush()
        
        # 等待响应
        time.sleep(0.5)
        
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"📥 {port} 收到响应: {[hex(b) for b in response]}")
            
            if len(response) > 0 and response[0] == 0xAA:
                print(f"✅ {port} 握手成功！")
                ser.close()
                return True
            else:
                print(f"❌ {port} 握手失败：期望0xAA，收到0x{response[0]:02X}")
        else:
            print(f"❌ {port} 无响应")
        
        ser.close()
        return False
        
    except Exception as e:
        print(f"❌ {port} 测试失败: {e}")
        return False

def find_uart_ports():
    """查找所有可能的UART端口"""
    possible_ports = [
        '/dev/ttyS0',
        '/dev/ttyS1', 
        '/dev/ttyS2',
        '/dev/ttyS3',
        '/dev/ttyUSB0',
        '/dev/ttyUSB1',
        '/dev/ttyUSB2',
        '/dev/ttyAMA0',
        '/dev/ttyAMA1',
        '/dev/serial0',
        '/dev/serial1',
        '/dev/serial2'
    ]
    
    available_ports = []
    
    for port in possible_ports:
        if os.path.exists(port):
            available_ports.append(port)
            print(f"✅ 发现端口: {port}")
        else:
            print(f"❌ 端口不存在: {port}")
    
    return available_ports

def main():
    """主函数"""
    print("🚀 UART端口调试工具")
    print("=" * 60)
    
    # 查找可用端口
    print("🔍 查找可用UART端口...")
    available_ports = find_uart_ports()
    
    if not available_ports:
        print("❌ 没有找到可用的UART端口")
        return False
    
    print(f"\n📋 找到 {len(available_ports)} 个可用端口")
    print("=" * 60)
    
    # 测试每个端口
    success_ports = []
    for port in available_ports:
        print(f"\n🧪 测试端口: {port}")
        print("-" * 40)
        
        if test_uart_port(port):
            success_ports.append(port)
        
        time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    
    if success_ports:
        print(f"✅ 握手成功的端口: {success_ports}")
        print("💡 请使用这些端口进行UART通信")
    else:
        print("❌ 没有端口握手成功")
        print("🔍 请检查：")
        print("   1. 硬件连接是否正确")
        print("   2. 单片机程序是否运行")
        print("   3. 波特率是否匹配")
        print("   4. 单片机是否在正确的UART端口上")
    
    return len(success_ports) > 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
