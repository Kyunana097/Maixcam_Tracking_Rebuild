#!/usr/bin/env python3
"""
测试调试版UART通信模块
"""

from uart_communication_debug import UARTCommunicationDebug
import time

def main():
    print("🚀 测试调试版UART通信模块")
    print("=" * 50)
    
    # 创建调试版UART实例
    uart = UARTCommunicationDebug("/dev/serial0", 115200)
    
    try:
        # 显示初始状态
        print("\n📊 初始状态:")
        uart.print_debug_summary()
        
        # 测试连接
        print("\n🔌 测试连接...")
        if uart.connect():
            print("✅ 连接成功！")
            
            # 显示连接后状态
            print("\n📊 连接后状态:")
            uart.print_debug_summary()
            
            # 测试报警状态发送
            print("\n📤 测试报警状态发送...")
            uart.send_alarm_status(True)  # WARNING
            time.sleep(2)
            uart.send_alarm_status(False)  # SAFE
            time.sleep(1)
            
            # 测试坐标发送
            print("\n📤 测试坐标发送...")
            uart.send_coordinates(256, 160)
            time.sleep(1)
            uart.send_coordinates(100, 200)
            
        else:
            print("❌ 连接失败！")
        
        # 最终状态
        print("\n📊 最终状态:")
        uart.print_debug_summary()
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
    finally:
        # 断开连接
        uart.disconnect()
        print("\n🔚 测试完成")

if __name__ == "__main__":
    main()
