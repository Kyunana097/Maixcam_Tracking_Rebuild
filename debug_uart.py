#!/usr/bin/env python3
"""
UART调试脚本
用于调试MaixCam与单片机之间的连接问题
"""

import time
import serial

def debug_uart_connection():
    """调试UART连接"""
    print("🔍 UART连接调试")
    print("=" * 50)
    
    try:
        # 创建串口连接
        print("🔌 创建串口连接...")
        ser = serial.Serial(
            port='/dev/ttyS1',
            baudrate=115200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=2.0,
            write_timeout=2.0
        )
        
        print("✅ 串口连接成功")
        print(f"📊 串口信息: {ser.name} @ {ser.baudrate}")
        
        # 清空缓冲区
        print("🧹 清空缓冲区...")
        ser.flushInput()
        ser.flushOutput()
        time.sleep(0.1)
        
        # 检查初始状态
        print(f"📊 初始缓冲区状态: {ser.in_waiting} 字节")
        
        # 发送握手请求
        print("📤 发送握手请求: 0x55")
        ser.write(bytes([0x55]))
        ser.flush()
        
        # 等待响应
        print("⏳ 等待响应...")
        time.sleep(1.0)  # 等待1秒
        
        # 检查响应
        if ser.in_waiting > 0:
            print(f"📥 收到 {ser.in_waiting} 字节数据")
            response = ser.read(ser.in_waiting)
            print(f"📥 响应数据: {[hex(b) for b in response]}")
            
            if len(response) > 0 and response[0] == 0xAA:
                print("✅ 握手成功！")
                
                # 测试发送一些数据
                print("\n📤 测试数据发送...")
                test_data = [0x22, 0x01, 0x40, 0x00, 0xF0]  # 坐标数据
                ser.write(bytes(test_data))
                ser.flush()
                print(f"📤 发送数据: {[hex(b) for b in test_data]}")
                
                time.sleep(0.5)
                
                # 检查是否有响应
                if ser.in_waiting > 0:
                    response2 = ser.read(ser.in_waiting)
                    print(f"📥 数据响应: {[hex(b) for b in response2]}")
                
                ser.close()
                print("🎉 调试完成，连接正常！")
                return True
            else:
                print(f"❌ 握手失败：期望0xAA，收到0x{response[0]:02X}")
                ser.close()
                return False
        else:
            print("❌ 无响应数据")
            ser.close()
            return False
            
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        return False

def test_different_ports():
    """测试不同的UART端口"""
    print("\n🔍 测试不同UART端口")
    print("=" * 50)
    
    ports_to_test = ['/dev/ttyS0', '/dev/ttyS1', '/dev/ttyS2', '/dev/ttyUSB0', '/dev/ttyUSB1']
    
    for port in ports_to_test:
        try:
            print(f"🔌 测试端口: {port}")
            ser = serial.Serial(port=port, baudrate=115200, timeout=1.0)
            print(f"✅ 端口 {port} 可用")
            ser.close()
        except Exception as e:
            print(f"❌ 端口 {port} 不可用: {e}")

def main():
    """主函数"""
    print("🚀 UART连接调试工具")
    print("=" * 60)
    print("📋 调试步骤：")
    print("   1. 检查串口连接")
    print("   2. 清空缓冲区")
    print("   3. 发送握手请求")
    print("   4. 等待响应")
    print("   5. 分析响应数据")
    print("=" * 60)
    
    # 测试不同端口
    test_different_ports()
    
    print("\n" + "=" * 60)
    print("🔍 开始UART连接调试...")
    
    # 执行调试
    success = debug_uart_connection()
    
    if success:
        print("\n🎉 调试成功！UART连接正常")
        print("💡 现在可以运行主程序")
    else:
        print("\n❌ 调试失败！请检查：")
        print("   1. 硬件连接是否正确")
        print("   2. 单片机程序是否运行")
        print("   3. UART端口是否正确")
        print("   4. 波特率是否匹配")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
