#!/usr/bin/env python3
"""
报警状态通信测试脚本
用于测试MaixCam与单片机之间的报警状态通信
"""

import sys
import time
import serial
from src.hardware.uart_communication import UARTCommunication

def test_alarm_communication():
    """测试报警状态通信"""
    print("🧪 开始报警状态通信测试")
    print("=" * 50)
    
    # 创建UART通信实例
    uart = UARTCommunication()
    
    # 测试连接
    if not uart.connect():
        print("❌ UART连接失败，请检查硬件连接")
        return False
    
    print("✅ UART连接成功")
    
    # 测试报警状态发送
    test_cases = [
        (False, "安全状态"),
        (True, "报警状态"),
        (False, "安全状态"),
        (True, "报警状态"),
        (False, "安全状态")
    ]
    
    for is_warning, status_text in test_cases:
        print(f"\n📤 发送状态: {status_text}")
        success = uart.send_alarm_status(is_warning)
        
        if success:
            print(f"✅ 发送成功: {status_text}")
        else:
            print(f"❌ 发送失败: {status_text}")
        
        # 等待单片机处理
        time.sleep(1)
    
    # 断开连接
    uart.disconnect()
    print("\n✅ 报警状态通信测试完成")
    return True

def test_coordinate_communication():
    """测试坐标通信"""
    print("\n🧪 开始坐标通信测试")
    print("=" * 50)
    
    # 创建UART通信实例
    uart = UARTCommunication()
    
    # 测试连接
    if not uart.connect():
        print("❌ UART连接失败，请检查硬件连接")
        return False
    
    print("✅ UART连接成功")
    
    # 测试坐标发送
    test_coordinates = [
        (100, 100),
        (200, 150),
        (300, 200),
        (400, 250),
        (500, 300)
    ]
    
    for x, y in test_coordinates:
        print(f"\n📤 发送坐标: ({x}, {y})")
        success = uart.send_coordinates(x, y)
        
        if success:
            print(f"✅ 坐标发送成功: ({x}, {y})")
        else:
            print(f"❌ 坐标发送失败: ({x}, {y})")
        
        # 等待单片机处理
        time.sleep(0.5)
    
    # 断开连接
    uart.disconnect()
    print("\n✅ 坐标通信测试完成")
    return True

def main():
    """主测试函数"""
    print("🚀 MaixCam与单片机通信测试")
    print("=" * 60)
    
    try:
        # 测试报警状态通信
        alarm_success = test_alarm_communication()
        
        # 测试坐标通信
        coord_success = test_coordinate_communication()
        
        # 总结测试结果
        print("\n" + "=" * 60)
        print("📊 测试结果总结:")
        print(f"  报警状态通信: {'✅ 成功' if alarm_success else '❌ 失败'}")
        print(f"  坐标通信: {'✅ 成功' if coord_success else '❌ 失败'}")
        
        if alarm_success and coord_success:
            print("\n🎉 所有测试通过！通信功能正常")
            return True
        else:
            print("\n⚠️ 部分测试失败，请检查硬件连接和配置")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
