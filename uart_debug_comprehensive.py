#!/usr/bin/env python3
"""
全面的UART调试工具
包含详细的硬件测试、时序分析、数据完整性检查等功能
"""

import serial
import time
import threading
import sys
from typing import List, Dict, Any

class UARTDebugger:
    """全面的UART调试器"""
    
    def __init__(self, port: str = "/dev/serial0", baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.debug_log = []
        self.timing_data = []
        self.is_monitoring = False
        
    def log(self, message: str, level: str = "INFO"):
        """记录调试信息"""
        timestamp = time.time()
        log_entry = {
            'time': timestamp,
            'level': level,
            'message': message,
            'readable_time': time.strftime('%H:%M:%S.%f', time.localtime(timestamp))[:-3]
        }
        self.debug_log.append(log_entry)
        print(f"[{log_entry['readable_time']}] {level}: {message}")
    
    def test_serial_port_availability(self) -> bool:
        """测试串口可用性"""
        self.log("🔍 测试串口可用性", "TEST")
        try:
            test_ser = serial.Serial(self.port, self.baudrate, timeout=0.1)
            self.log(f"✅ 串口 {self.port} 可用", "SUCCESS")
            self.log(f"🔍 串口参数: 波特率={test_ser.baudrate}, 超时={test_ser.timeout}s", "INFO")
            self.log(f"🔍 串口状态: 打开={test_ser.is_open}, 可读={test_ser.readable()}, 可写={test_ser.writable()}", "INFO")
            test_ser.close()
            return True
        except Exception as e:
            self.log(f"❌ 串口不可用: {e}", "ERROR")
            return False
    
    def test_buffer_operations(self) -> Dict[str, Any]:
        """测试缓冲区操作"""
        self.log("🔍 测试缓冲区操作", "TEST")
        results = {}
        
        try:
            ser = serial.Serial(self.port, self.baudrate, timeout=1.0)
            
            # 测试初始状态
            initial_in_waiting = ser.in_waiting
            initial_out_waiting = ser.out_waiting if hasattr(ser, 'out_waiting') else 'N/A'
            self.log(f"🔍 初始缓冲区状态: in_waiting={initial_in_waiting}, out_waiting={initial_out_waiting}", "INFO")
            
            # 测试缓冲区清理
            ser.flushInput()
            ser.flushOutput()
            after_flush_in = ser.in_waiting
            self.log(f"🔍 清理后缓冲区: in_waiting={after_flush_in}", "INFO")
            
            # 测试写入操作
            test_data = b'\x55'
            bytes_written = ser.write(test_data)
            self.log(f"🔍 写入测试: 尝试写入{len(test_data)}字节, 实际写入{bytes_written}字节", "INFO")
            
            # 等待并检查
            time.sleep(0.1)
            after_write_in = ser.in_waiting
            self.log(f"🔍 写入后缓冲区: in_waiting={after_write_in}", "INFO")
            
            results = {
                'initial_in_waiting': initial_in_waiting,
                'after_flush_in_waiting': after_flush_in,
                'bytes_written': bytes_written,
                'after_write_in_waiting': after_write_in
            }
            
            ser.close()
            return results
            
        except Exception as e:
            self.log(f"❌ 缓冲区测试失败: {e}", "ERROR")
            return {'error': str(e)}
    
    def test_timing_precision(self) -> Dict[str, float]:
        """测试时序精度"""
        self.log("🔍 测试时序精度", "TEST")
        
        # 测试sleep精度
        target_delays = [0.01, 0.05, 0.1, 0.5, 1.0]
        timing_results = {}
        
        for target_delay in target_delays:
            start_time = time.time()
            time.sleep(target_delay)
            actual_delay = time.time() - start_time
            error = abs(actual_delay - target_delay)
            timing_results[f'sleep_{target_delay}s'] = {
                'target': target_delay,
                'actual': actual_delay,
                'error': error,
                'error_percent': (error / target_delay) * 100
            }
            self.log(f"🔍 延迟测试: 目标{target_delay}s, 实际{actual_delay:.4f}s, 误差{error*1000:.2f}ms", "INFO")
        
        return timing_results
    
    def monitor_serial_activity(self, duration: float = 5.0) -> List[Dict]:
        """监控串口活动"""
        self.log(f"🔍 开始监控串口活动 ({duration}s)", "TEST")
        
        activity_log = []
        try:
            ser = serial.Serial(self.port, self.baudrate, timeout=0.1)
            ser.flushInput()
            ser.flushOutput()
            
            start_time = time.time()
            last_check = start_time
            
            while (time.time() - start_time) < duration:
                current_time = time.time()
                in_waiting = ser.in_waiting
                
                if in_waiting > 0:
                    data = ser.read(in_waiting)
                    activity_log.append({
                        'time': current_time,
                        'relative_time': current_time - start_time,
                        'bytes_available': in_waiting,
                        'data': [hex(b) for b in data]
                    })
                    self.log(f"📥 检测到数据: {in_waiting}字节 {[hex(b) for b in data]} (时间: {current_time-start_time:.3f}s)", "DATA")
                
                # 每0.1秒记录一次状态
                if current_time - last_check >= 0.1:
                    last_check = current_time
                
                time.sleep(0.01)  # 高频率检查
            
            ser.close()
            self.log(f"🔍 监控完成，共检测到 {len(activity_log)} 次数据活动", "INFO")
            return activity_log
            
        except Exception as e:
            self.log(f"❌ 监控失败: {e}", "ERROR")
            return []
    
    def test_handshake_with_detailed_timing(self) -> Dict[str, Any]:
        """详细时序的握手测试"""
        self.log("🔍 开始详细握手测试", "TEST")
        
        try:
            ser = serial.Serial(self.port, self.baudrate, timeout=3.0)
            
            # 记录开始时间
            test_start = time.time()
            
            # 清空缓冲区
            flush_start = time.time()
            ser.flushInput()
            ser.flushOutput()
            flush_duration = time.time() - flush_start
            self.log(f"🔍 缓冲区清理耗时: {flush_duration*1000:.2f}ms", "TIMING")
            
            # 发送握手请求
            send_start = time.time()
            bytes_sent = ser.write(b'\x55')
            send_duration = time.time() - send_start
            self.log(f"📤 发送握手请求: 0x55 ({bytes_sent}字节, 耗时{send_duration*1000:.2f}ms)", "SEND")
            
            # 详细监控响应
            self.log("⏳ 开始详细响应监控...", "INFO")
            response_data = []
            
            for i in range(100):  # 监控10秒，每0.1秒检查一次
                check_start = time.time()
                in_waiting = ser.in_waiting
                
                if in_waiting > 0:
                    data = ser.read(in_waiting)
                    receive_time = time.time()
                    response_delay = receive_time - send_start
                    
                    response_data.append({
                        'check_index': i,
                        'receive_time': receive_time,
                        'response_delay': response_delay,
                        'bytes_count': len(data),
                        'data': [hex(b) for b in data],
                        'raw_data': data
                    })
                    
                    self.log(f"📥 收到响应 #{i}: {[hex(b) for b in data]} (延迟{response_delay*1000:.2f}ms)", "RECEIVE")
                    
                    # 检查是否包含0xAA
                    if 0xAA in data:
                        self.log("✅ 发现握手响应 0xAA!", "SUCCESS")
                        ser.close()
                        return {
                            'success': True,
                            'total_duration': time.time() - test_start,
                            'flush_duration': flush_duration,
                            'send_duration': send_duration,
                            'response_delay': response_delay,
                            'response_data': response_data
                        }
                    else:
                        self.log(f"⚠️ 收到数据但不是0xAA: {[hex(b) for b in data]}", "WARNING")
                
                time.sleep(0.1)
            
            # 没有收到响应
            ser.close()
            self.log("❌ 握手超时，未收到0xAA响应", "ERROR")
            return {
                'success': False,
                'total_duration': time.time() - test_start,
                'flush_duration': flush_duration,
                'send_duration': send_duration,
                'response_delay': None,
                'response_data': response_data
            }
            
        except Exception as e:
            self.log(f"❌ 握手测试异常: {e}", "ERROR")
            return {'success': False, 'error': str(e)}
    
    def test_continuous_communication(self, count: int = 5) -> Dict[str, Any]:
        """测试连续通信"""
        self.log(f"🔍 开始连续通信测试 ({count}次)", "TEST")
        
        results = []
        success_count = 0
        
        try:
            ser = serial.Serial(self.port, self.baudrate, timeout=2.0)
            
            for i in range(count):
                self.log(f"🔄 第 {i+1}/{count} 次测试", "INFO")
                
                # 清空缓冲区
                ser.flushInput()
                ser.flushOutput()
                
                # 发送测试数据
                test_byte = 0x55 + i  # 发送不同的字节
                send_time = time.time()
                ser.write(bytes([test_byte]))
                
                # 等待响应
                received = False
                for j in range(20):  # 2秒超时
                    time.sleep(0.1)
                    if ser.in_waiting > 0:
                        response = ser.read(ser.in_waiting)
                        receive_time = time.time()
                        delay = receive_time - send_time
                        
                        result = {
                            'test_index': i,
                            'sent_byte': hex(test_byte),
                            'response': [hex(b) for b in response],
                            'delay_ms': delay * 1000,
                            'success': 0xAA in response
                        }
                        
                        results.append(result)
                        if result['success']:
                            success_count += 1
                            self.log(f"✅ 测试 {i+1} 成功: 发送{hex(test_byte)} 收到{[hex(b) for b in response]} 延迟{delay*1000:.1f}ms", "SUCCESS")
                        else:
                            self.log(f"❌ 测试 {i+1} 失败: 发送{hex(test_byte)} 收到{[hex(b) for b in response]}", "ERROR")
                        
                        received = True
                        break
                
                if not received:
                    results.append({
                        'test_index': i,
                        'sent_byte': hex(test_byte),
                        'response': [],
                        'delay_ms': None,
                        'success': False
                    })
                    self.log(f"❌ 测试 {i+1} 超时: 发送{hex(test_byte)} 无响应", "ERROR")
                
                time.sleep(0.5)  # 测试间隔
            
            ser.close()
            
            success_rate = (success_count / count) * 100
            self.log(f"📊 连续通信测试完成: {success_count}/{count} 成功 ({success_rate:.1f}%)", "SUMMARY")
            
            return {
                'total_tests': count,
                'success_count': success_count,
                'success_rate': success_rate,
                'results': results
            }
            
        except Exception as e:
            self.log(f"❌ 连续通信测试异常: {e}", "ERROR")
            return {'error': str(e)}
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """运行全面测试"""
        self.log("🚀 开始全面UART调试测试", "START")
        self.log("=" * 60, "INFO")
        
        all_results = {}
        
        # 1. 串口可用性测试
        self.log("📋 第1步: 串口可用性测试", "STEP")
        all_results['port_availability'] = self.test_serial_port_availability()
        
        if not all_results['port_availability']:
            self.log("❌ 串口不可用，终止测试", "FATAL")
            return all_results
        
        # 2. 缓冲区操作测试
        self.log("📋 第2步: 缓冲区操作测试", "STEP")
        all_results['buffer_operations'] = self.test_buffer_operations()
        
        # 3. 时序精度测试
        self.log("📋 第3步: 时序精度测试", "STEP")
        all_results['timing_precision'] = self.test_timing_precision()
        
        # 4. 串口活动监控
        self.log("📋 第4步: 串口活动监控 (5秒)", "STEP")
        all_results['activity_monitor'] = self.monitor_serial_activity(5.0)
        
        # 5. 详细握手测试
        self.log("📋 第5步: 详细握手测试", "STEP")
        all_results['handshake_test'] = self.test_handshake_with_detailed_timing()
        
        # 6. 连续通信测试
        self.log("📋 第6步: 连续通信测试", "STEP")
        all_results['continuous_test'] = self.test_continuous_communication(5)
        
        # 生成总结报告
        self.generate_summary_report(all_results)
        
        return all_results
    
    def generate_summary_report(self, results: Dict[str, Any]):
        """生成总结报告"""
        self.log("=" * 60, "INFO")
        self.log("📊 测试总结报告", "SUMMARY")
        self.log("=" * 60, "INFO")
        
        # 串口状态
        port_status = "✅ 正常" if results.get('port_availability', False) else "❌ 异常"
        self.log(f"🔌 串口状态: {port_status}", "SUMMARY")
        
        # 缓冲区状态
        buffer_results = results.get('buffer_operations', {})
        if 'error' not in buffer_results:
            self.log(f"📦 缓冲区操作: ✅ 正常", "SUMMARY")
        else:
            self.log(f"📦 缓冲区操作: ❌ 异常 - {buffer_results['error']}", "SUMMARY")
        
        # 握手测试结果
        handshake_results = results.get('handshake_test', {})
        if handshake_results.get('success', False):
            delay = handshake_results.get('response_delay', 0) * 1000
            self.log(f"🤝 握手测试: ✅ 成功 (响应延迟: {delay:.1f}ms)", "SUMMARY")
        else:
            self.log(f"🤝 握手测试: ❌ 失败", "SUMMARY")
        
        # 连续通信结果
        continuous_results = results.get('continuous_test', {})
        if 'success_rate' in continuous_results:
            rate = continuous_results['success_rate']
            status = "✅" if rate >= 80 else "⚠️" if rate >= 50 else "❌"
            self.log(f"🔄 连续通信: {status} 成功率 {rate:.1f}%", "SUMMARY")
        else:
            self.log(f"🔄 连续通信: ❌ 测试失败", "SUMMARY")
        
        # 问题诊断
        self.log("🔍 问题诊断建议:", "SUMMARY")
        
        if not results.get('port_availability', False):
            self.log("  • 串口设备不可用，检查硬件连接", "ADVICE")
        elif not handshake_results.get('success', False):
            self.log("  • 握手失败，可能原因:", "ADVICE")
            self.log("    - 单片机程序未运行或死机", "ADVICE")
            self.log("    - TX/RX线接反", "ADVICE")
            self.log("    - 波特率不匹配", "ADVICE")
            self.log("    - 电平标准不兼容", "ADVICE")
        elif continuous_results.get('success_rate', 0) < 80:
            self.log("  • 通信不稳定，可能原因:", "ADVICE")
            self.log("    - 信号干扰", "ADVICE")
            self.log("    - 连接松动", "ADVICE")
            self.log("    - 时序问题", "ADVICE")
        else:
            self.log("  • 硬件连接正常，问题可能在软件逻辑", "ADVICE")
        
        self.log("=" * 60, "INFO")

def main():
    """主函数"""
    print("🔧 UART全面调试工具")
    print("=" * 60)
    
    debugger = UARTDebugger("/dev/serial0", 115200)
    results = debugger.run_comprehensive_test()
    
    print("\n🎯 测试完成！")
    print(f"📝 共记录 {len(debugger.debug_log)} 条调试信息")
    
    return results

if __name__ == "__main__":
    main()
