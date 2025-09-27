#!/usr/bin/env python3
"""
简单UART测试脚本
用于快速测试MaixCam与单片机之间的连接
"""

import time
import serial

def test_uart_connection():
    """测试UART连接"""
    print("🔌 测试UART连接")
    print("=" * 40)
    
    try:
        # 创建串口连接
        ser = serial.Serial(
            port='/dev/ttyS1',
            baudrate=115200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1.0,
            write_timeout=1.0
        )
        
        print("✅ 串口连接成功")
        
        # 清空缓冲区
        ser.flushInput()
        ser.flushOutput()
        
        # 发送握手请求
        print("📤 发送握手请求: 0x55")
        ser.write(bytes([0x55]))  # 握手请求
        ser.flush()
        time.sleep(0.5)  # 等待更长时间
        
        # 等待响应
        if ser.in_waiting > 0:
            response = ser.read(1)
            print(f"📥 收到响应: 0x{response[0]:02X}")
            if response and response[0] == 0xAA:  # 握手响应
                print("✅ 握手成功！连接已建立")
                
                # 测试坐标发送
                print("📤 测试坐标发送...")
                x, y = 320, 240
                frame = bytes([
                    0x22,  # 坐标数据命令
                    (x >> 8) & 0xFF,  # X高字节
                    x & 0xFF,          # X低字节
                    (y >> 8) & 0xFF,  # Y高字节
                    y & 0xFF          # Y低字节
                ])
                ser.write(frame)
                ser.flush()
                print(f"✅ 坐标发送成功: ({x}, {y})")
                
                # 测试报警状态发送
                print("📤 测试报警状态发送...")
                alarm_frame = bytes([0x11, 0x01])  # 报警状态
                ser.write(alarm_frame)
                ser.flush()
                print("✅ 报警状态发送成功")
                
                time.sleep(1)
                
                # 发送安全状态
                print("📤 发送安全状态...")
                safe_frame = bytes([0x11, 0x00])  # 安全状态
                ser.write(safe_frame)
                ser.flush()
                print("✅ 安全状态发送成功")
                
                ser.close()
                print("🎉 所有测试通过！")
                return True
            else:
                print(f"❌ 握手失败：期望0xAA，收到0x{response[0]:02X}")
                ser.close()
                return False
        else:
            print("❌ 握手失败：无响应数据")
            # 尝试读取所有可用数据
            if ser.in_waiting > 0:
                all_data = ser.read(ser.in_waiting)
                print(f"📥 缓冲区数据: {[hex(b) for b in all_data]}")
            ser.close()
            return False
            
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 简单UART连接测试")
    print("=" * 40)
    print("📋 测试步骤：")
    print("   1. 建立串口连接")
    print("   2. 发送握手请求")
    print("   3. 等待握手响应")
    print("   4. 测试坐标发送")
    print("   5. 测试报警状态发送")
    print("=" * 40)
    
    # 观察LED状态说明
    print("\n💡 请观察单片机上的LED状态：")
    print("   - 绿色LED常亮：连接成功")
    print("   - 红色LED闪烁：连接失败")
    print("   - 蓝色LED：报警状态指示")
    print("\n按任意键开始测试...")
    input()
    
    # 执行测试
    success = test_uart_connection()
    
    if success:
        print("\n🎉 测试成功！UART通信正常")
        print("💡 现在可以运行主程序进行云台追踪")
    else:
        print("\n❌ 测试失败！请检查：")
        print("   - 硬件连接是否正确")
        print("   - 单片机程序是否正常运行")
        print("   - UART端口配置是否正确")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
