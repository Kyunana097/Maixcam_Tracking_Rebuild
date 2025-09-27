#!/usr/bin/env python3
"""
握手测试脚本 - 主程序版本
专门用于测试MaixCam与单片机之间的握手功能
"""

import time
import serial

def test_handshake():
    """测试握手功能"""
    print("🤝 握手测试")
    print("=" * 40)
    
    try:
        # 创建串口连接
        print("🔌 创建串口连接...")
        ser = serial.Serial(
            port='/dev/ttyS1',
            baudrate=115200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=3.0,
            write_timeout=3.0
        )
        
        print("✅ 串口连接成功")
        
        # 清空缓冲区
        print("🧹 清空缓冲区...")
        ser.flushInput()
        ser.flushOutput()
        time.sleep(0.2)
        
        # 发送握手请求
        print("📤 发送握手请求: 0x55")
        ser.write(bytes([0x55]))
        ser.flush()
        
        # 等待响应
        print("⏳ 等待握手响应...")
        time.sleep(1.0)
        
        # 检查响应
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print(f"📥 收到响应: {[hex(b) for b in response]}")
            
            if len(response) > 0 and response[0] == 0xAA:
                print("✅ 握手成功！")
                ser.close()
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
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 握手测试工具")
    print("=" * 50)
    print("📋 测试步骤：")
    print("   1. 建立串口连接")
    print("   2. 清空缓冲区")
    print("   3. 发送握手请求 (0x55)")
    print("   4. 等待握手响应 (0xAA)")
    print("   5. 验证响应正确性")
    print("=" * 50)
    
    print("\n💡 请确保：")
    print("   - 硬件连接正确 (TX-RX, RX-TX, GND-GND)")
    print("   - 单片机程序正在运行")
    print("   - 观察单片机LED状态")
    print("\n⏳ 3秒后开始测试...")
    time.sleep(3)
    
    # 执行测试
    success = test_handshake()
    
    if success:
        print("\n🎉 握手测试成功！")
        print("💡 现在可以运行完整测试或主程序")
    else:
        print("\n❌ 握手测试失败！")
        print("🔍 请检查：")
        print("   1. 硬件连接是否正确")
        print("   2. 单片机程序是否运行")
        print("   3. UART端口是否正确")
        print("   4. 波特率是否匹配")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
