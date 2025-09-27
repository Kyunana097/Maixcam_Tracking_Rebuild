#!/usr/bin/env python3
"""
UART模块测试脚本
用于测试独立的UART通信模块
"""

import time
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from uart_module import UARTModule

def test_uart_module():
    """测试UART模块"""
    print("🔍 UART模块测试")
    print("=" * 60)
    
    # 创建UART模块实例
    uart = UARTModule(port="/dev/serial0", baudrate=115200, timeout=3.0)
    
    try:
        # 测试连接
        print("\n🔌 测试连接...")
        if not uart.connect():
            print("❌ 连接失败")
            return False
        
        # 测试握手
        print("\n🤝 测试握手...")
        if not uart.handshake():
            print("❌ 握手失败")
            return False
        
        # 测试报警状态发送
        print("\n🚨 测试报警状态发送...")
        
        # 发送WARNING状态
        if uart.send_alarm_status(True):
            print("✅ WARNING状态发送成功")
        else:
            print("❌ WARNING状态发送失败")
        
        time.sleep(1.0)
        
        # 发送SAFE状态
        if uart.send_alarm_status(False):
            print("✅ SAFE状态发送成功")
        else:
            print("❌ SAFE状态发送失败")
        
        # 显示状态
        print("\n📊 UART状态:")
        status = uart.get_status()
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    finally:
        # 断开连接
        uart.disconnect()

def main():
    print("🔍 请确保：")
    print("   1. 单片机程序已烧录并运行")
    print("   2. 硬件连接正确 (TX-RX, RX-TX, GND-GND)")
    print("   3. 观察单片机LED状态")
    print("\n⏳ 3秒后开始测试...")
    time.sleep(3)
    
    success = test_uart_module()
    
    if success:
        print("\n🎉 UART模块测试成功！")
    else:
        print("\n❌ UART模块测试失败！")
        print("🔍 可能的问题：")
        print("   1. 硬件连接问题")
        print("   2. 串口配置问题")
        print("   3. 单片机程序问题")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
