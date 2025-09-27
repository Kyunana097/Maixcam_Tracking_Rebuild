#!/usr/bin/env python3
"""
UART双向通信测试脚本
用于测试MaixCam与单片机之间的握手和通信功能
"""

import sys
import time
import serial
from src.hardware.uart_communication import UARTCommunication

def test_handshake():
    """测试握手功能"""
    print("🤝 测试握手功能")
    print("-" * 40)
    
    uart = UARTCommunication()
    
    # 尝试连接
    if uart.connect():
        print("✅ 握手成功！连接已建立")
        
        # 检查连接状态
        status = uart.check_connection_status()
        print(f"📊 连接状态: {status}")
        
        uart.disconnect()
        return True
    else:
        print("❌ 握手失败！连接未建立")
        return False

def test_data_transmission():
    """测试数据传输"""
    print("\n📡 测试数据传输")
    print("-" * 40)
    
    uart = UARTCommunication()
    
    if not uart.connect():
        print("❌ 无法建立连接，跳过数据传输测试")
        return False
    
    # 测试坐标发送
    test_coordinates = [
        (100, 100),
        (200, 150),
        (300, 200),
        (400, 250)
    ]
    
    success_count = 0
    for x, y in test_coordinates:
        print(f"📤 发送坐标: ({x}, {y})")
        if uart.send_coordinates(x, y):
            success_count += 1
            print(f"✅ 坐标发送成功")
        else:
            print(f"❌ 坐标发送失败")
        time.sleep(0.5)
    
    # 测试报警状态发送
    print("\n🚨 测试报警状态发送")
    alarm_tests = [False, True, False, True]
    for is_warning in alarm_tests:
        status_text = "WARNING" if is_warning else "SAFE"
        print(f"📤 发送报警状态: {status_text}")
        if uart.send_alarm_status(is_warning):
            print(f"✅ 报警状态发送成功")
        else:
            print(f"❌ 报警状态发送失败")
        time.sleep(0.5)
    
    uart.disconnect()
    print(f"\n📊 数据传输测试完成: {success_count}/{len(test_coordinates)} 成功")
    return success_count == len(test_coordinates)

def test_connection_robustness():
    """测试连接稳定性"""
    print("\n🔄 测试连接稳定性")
    print("-" * 40)
    
    uart = UARTCommunication()
    
    # 多次连接测试
    success_count = 0
    test_count = 5
    
    for i in range(test_count):
        print(f"🔄 连接测试 {i+1}/{test_count}")
        
        if uart.connect():
            print(f"✅ 连接 {i+1} 成功")
            success_count += 1
            
            # 发送测试数据
            uart.send_coordinates(100 + i*10, 100 + i*10)
            uart.send_alarm_status(i % 2 == 0)
            
            uart.disconnect()
            time.sleep(0.5)
        else:
            print(f"❌ 连接 {i+1} 失败")
    
    print(f"\n📊 连接稳定性测试: {success_count}/{test_count} 成功")
    return success_count == test_count

def test_led_feedback():
    """测试LED反馈功能"""
    print("\n💡 测试LED反馈功能")
    print("-" * 40)
    
    uart = UARTCommunication()
    
    if not uart.connect():
        print("❌ 无法建立连接，跳过LED测试")
        return False
    
    print("🔍 请观察单片机上的LED状态：")
    print("   - 绿色LED常亮：连接成功")
    print("   - 红色LED闪烁：连接失败")
    print("   - 蓝色LED：报警状态指示")
    
    # 发送报警状态测试LED
    print("\n📤 发送安全状态（蓝色LED应该熄灭）")
    uart.send_alarm_status(False)
    time.sleep(2)
    
    print("📤 发送报警状态（蓝色LED应该点亮）")
    uart.send_alarm_status(True)
    time.sleep(2)
    
    print("📤 发送安全状态（蓝色LED应该熄灭）")
    uart.send_alarm_status(False)
    time.sleep(2)
    
    uart.disconnect()
    print("✅ LED反馈测试完成")
    return True

def main():
    """主测试函数"""
    print("🚀 MaixCam与单片机UART通信测试")
    print("=" * 60)
    print("📋 测试项目：")
    print("   1. 握手功能测试")
    print("   2. 数据传输测试")
    print("   3. 连接稳定性测试")
    print("   4. LED反馈测试")
    print("=" * 60)
    
    try:
        # 测试1：握手功能
        handshake_success = test_handshake()
        
        # 测试2：数据传输
        data_success = test_data_transmission()
        
        # 测试3：连接稳定性
        robustness_success = test_connection_robustness()
        
        # 测试4：LED反馈
        led_success = test_led_feedback()
        
        # 总结测试结果
        print("\n" + "=" * 60)
        print("📊 测试结果总结:")
        print(f"   握手功能: {'✅ 通过' if handshake_success else '❌ 失败'}")
        print(f"   数据传输: {'✅ 通过' if data_success else '❌ 失败'}")
        print(f"   连接稳定性: {'✅ 通过' if robustness_success else '❌ 失败'}")
        print(f"   LED反馈: {'✅ 通过' if led_success else '❌ 失败'}")
        
        all_success = handshake_success and data_success and robustness_success and led_success
        
        if all_success:
            print("\n🎉 所有测试通过！UART通信功能正常")
            print("💡 现在可以运行主程序进行云台追踪")
        else:
            print("\n⚠️ 部分测试失败，请检查：")
            print("   - 硬件连接是否正确")
            print("   - UART端口配置是否正确")
            print("   - 单片机程序是否正常运行")
        
        return all_success
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
