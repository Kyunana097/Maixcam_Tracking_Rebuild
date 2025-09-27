#!/usr/bin/env python3
"""
基于自训练YOLO模型的人脸识别主程序 - 独立版本
整合了person_detector和cnn_recognizer的功能
包含独立的UART通信模块
"""

from maix import camera, display, image, nn, app
import sys
import os
import time
import serial

# 添加src路径
sys.path.append('/root/src')
sys.path.append('/root/src/vision')
sys.path.append('/root/src/vision/detection')
sys.path.append('/root/src/vision/recognition')

# 导入，失败则报错
from src.vision.detection.person_detector import PersonDetector
from src.vision.recognition.cnn_recognizer import CNNRecognizer
from src.hardware.button import VirtualButtonManager
print("✓ 成功导入所有模块")

class UARTCommunication:
    """UART通信类 - 独立版本"""
    
    def __init__(self, port='/dev/ttyS1', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.is_connected = False
        self.connection_verified = False
        self.last_handshake_time = 0
        
        # 通信协议定义
        self.HANDSHAKE_REQUEST = 0x55      # 握手请求
        self.HANDSHAKE_RESPONSE = 0xAA     # 握手响应
        self.DATA_REQUEST = 0x33           # 数据请求
        self.DATA_RESPONSE = 0xCC          # 数据响应
        self.ALARM_STATUS = 0x11           # 报警状态
        self.COORDINATE_DATA = 0x22        # 坐标数据
        
    def connect(self) -> bool:
        """建立UART连接并进行握手验证"""
        try:
            # 创建串口连接
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0,
                write_timeout=1.0
            )
            
            # 清空缓冲区
            self.serial_conn.flushInput()
            self.serial_conn.flushOutput()
            
            print(f"🔌 尝试连接UART: {self.port} @ {self.baudrate}")
            
            # 进行握手验证
            if self._handshake():
                self.is_connected = True
                self.connection_verified = True
                print(f"✅ UART连接成功并握手验证: {self.port}")
                return True
            else:
                self.is_connected = False
                self.connection_verified = False
                print(f"⚠️ UART连接成功但握手失败: {self.port}")
                return False
                
        except Exception as e:
            print(f"❌ UART连接失败: {e}")
            self.is_connected = False
            self.connection_verified = False
            return False
    
    def _handshake(self) -> bool:
        """与单片机进行握手验证"""
        try:
            # 发送握手请求
            self.serial_conn.write(bytes([self.HANDSHAKE_REQUEST]))
            self.serial_conn.flush()
            time.sleep(0.1)
            
            # 等待握手响应
            if self.serial_conn.in_waiting > 0:
                response = self.serial_conn.read(1)
                if response and response[0] == self.HANDSHAKE_RESPONSE:
                    self.last_handshake_time = time.time()
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ 握手失败: {e}")
            return False
    
    def send_coordinates(self, x: int, y: int) -> bool:
        """发送坐标数据到单片机"""
        if not self.is_connected or not self.connection_verified:
            return False
        
        try:
            # 限制坐标范围
            x = max(0, min(640, x))
            y = max(0, min(480, y))
            
            # 构建数据帧
            frame = bytes([
                self.COORDINATE_DATA,  # 命令字节
                (x >> 8) & 0xFF,       # X坐标高字节
                x & 0xFF,               # X坐标低字节
                (y >> 8) & 0xFF,       # Y坐标高字节
                y & 0xFF               # Y坐标低字节
            ])
            
            # 发送数据
            self.serial_conn.write(frame)
            self.serial_conn.flush()
            return True
            
        except Exception as e:
            print(f"❌ 发送坐标失败: {e}")
            return False
    
    def send_alarm_status(self, is_warning: bool) -> bool:
        """发送报警状态到单片机"""
        if not self.is_connected or not self.connection_verified:
            return False
        
        try:
            # 构建报警状态帧
            status_byte = 0x01 if is_warning else 0x00
            frame = bytes([
                self.ALARM_STATUS,  # 命令字节
                status_byte         # 状态字节
            ])
            
            # 发送数据
            self.serial_conn.write(frame)
            self.serial_conn.flush()
            return True
            
        except Exception as e:
            print(f"❌ 发送报警状态失败: {e}")
            return False
    
    def disconnect(self):
        """断开UART连接"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        
        self.is_connected = False
        self.connection_verified = False

class GimbalController:
    """云台控制器 - 独立版本"""
    
    def __init__(self):
        self.uart = UARTCommunication()
        self.tracking_active = False
        self.last_coordinates = None
        
    def start_tracking(self) -> bool:
        """启动云台跟踪"""
        if self.uart.connect():
            self.tracking_active = True
            print("🎯 云台跟踪已启动")
            return True
        else:
            print("❌ 云台跟踪启动失败，请检查UART连接")
            return False
    
    def stop_tracking(self):
        """停止云台跟踪"""
        self.tracking_active = False
        self.uart.disconnect()
        print("⏹️ 云台跟踪已停止")
    
    def update_target(self, x: int, y: int, bbox=None):
        """更新跟踪目标坐标"""
        if self.tracking_active:
            self.last_coordinates = (x, y)
            self.uart.send_coordinates(x, y)
    
    def send_alarm_status(self, is_warning: bool):
        """发送报警状态"""
        if self.tracking_active:
            self.uart.send_alarm_status(is_warning)
    
    def get_status(self) -> dict:
        """获取云台状态"""
        return {
            'tracking_active': self.tracking_active,
            'last_coordinates': self.last_coordinates,
            'uart': {
                'connected': self.uart.is_connected,
                'verified': self.uart.connection_verified
            }
        }

class YOLOFaceRecognitionSystem:
    def __init__(self):
        """初始化YOLO人脸识别系统"""
        print("🚀 初始化YOLO人脸识别系统")
        print("=" * 50)
        
        # 初始化组件
        self.person_detector = PersonDetector()
        self.recognizer = CNNRecognizer()
        self.button_manager = VirtualButtonManager()
        self.gimbal_controller = GimbalController()
        
        # 系统状态
        self.frame_count = 0
        self.detection_count = 0
        self.current_target_name = None
        self.last_tracked_coordinates = None
        self.alarm_status = "SAFE"
        self.alarm_start_time = None
        
        # 初始化按钮
        self._init_buttons()
        
        print("✅ 系统初始化完成")
    
    def _init_buttons(self):
        """初始化虚拟按钮"""
        # 开始/停止按钮
        start_btn = self.button_manager.create_button(
            button_id='start_stop', x=20, y=20, width=80, height=30, text='START'
        )
        start_btn.set_colors(normal=(0, 200, 0), active=(0, 255, 0), disabled=(60, 60, 60))
        start_btn.set_click_callback(self._on_button_click)
        
        # 报警按钮
        alarm_btn = self.button_manager.create_button(
            button_id='alarm', x=20, y=60, width=80, height=30, text='ALARM'
        )
        alarm_btn.set_colors(normal=(200, 0, 0), active=(255, 0, 0), disabled=(60, 60, 60))
        alarm_btn.set_click_callback(self._on_button_click)
        
        # 云台按钮
        gimbal_btn = self.button_manager.create_button(
            button_id='gimbal', x=20, y=100, width=80, height=30, text='GIMBAL'
        )
        gimbal_btn.set_colors(normal=(0, 100, 200), active=(0, 150, 255), disabled=(60, 60, 60))
        gimbal_btn.set_click_callback(self._on_button_click)
    
    def _on_button_click(self, button_id):
        """按钮点击处理"""
        if button_id == 'start_stop':
            self._handle_start_stop_button()
        elif button_id == 'alarm':
            self._handle_alarm_button()
        elif button_id == 'gimbal':
            self._handle_gimbal_button()
    
    def _handle_start_stop_button(self):
        """开始/停止按钮处理"""
        if self.alarm_status == "SAFE":
            self._handle_start_alarm()
        else:
            self._handle_stop_alarm()
    
    def _handle_alarm_button(self):
        """报警按钮处理"""
        if self.alarm_status == "SAFE":
            self._handle_start_alarm()
        else:
            self._handle_stop_alarm()
    
    def _handle_gimbal_button(self):
        """云台控制按钮处理"""
        gimbal_status = self.gimbal_controller.get_status()
        if gimbal_status['tracking_active']:
            self.gimbal_controller.stop_tracking()
            print("⏹️ 云台跟踪已停止")
        else:
            if self.gimbal_controller.start_tracking():
                print("🎯 云台跟踪已启动")
            else:
                print("❌ 云台跟踪启动失败，请检查UART连接")
    
    def _handle_start_alarm(self):
        """开始报警"""
        self.alarm_status = "WARNING"
        self.alarm_start_time = time.time()
        print("🚨 报警已启动")
        
        # 发送报警状态到云台
        gimbal_status = self.gimbal_controller.get_status()
        if gimbal_status['tracking_active']:
            is_warning = (self.alarm_status == "WARNING")
            self.gimbal_controller.send_alarm_status(is_warning)
    
    def _handle_stop_alarm(self):
        """停止报警"""
        self.alarm_status = "SAFE"
        self.alarm_start_time = None
        print("✅ 报警已停止")
        
        # 发送安全状态到云台
        gimbal_status = self.gimbal_controller.get_status()
        if gimbal_status['tracking_active']:
            self.gimbal_controller.send_alarm_status(False)
    
    def _output_tracking_coordinates_from_data(self, person_data):
        """从person_data输出跟踪坐标并发送到云台"""
        x, y, w, h = person_data['bbox']
        center_x = x + w // 2
        center_y = y + h // 2
        print(f"📍 跟踪坐标 [{person_data['name']}]: 中心点({center_x}, {center_y}) | 边界框({x}, {y}, {w}, {h})")
        
        # 发送坐标到云台
        gimbal_status = self.gimbal_controller.get_status()
        if gimbal_status['tracking_active']:
            self.gimbal_controller.update_target(center_x, center_y, (x, y, w, h))
    
    def _output_last_coordinates(self):
        """输出上次记录的坐标并发送到云台"""
        if self.last_tracked_coordinates:
            center_x, center_y, bbox = self.last_tracked_coordinates
            x, y, w, h = bbox
            print(f"📍 跟踪坐标 [{self.current_target_name}]: 中心点({center_x}, {center_y}) | 边界框({x}, {y}, {w}, {h}) [LOST]")
            
            # 发送坐标到云台
            gimbal_status = self.gimbal_controller.get_status()
            if gimbal_status['tracking_active']:
                self.gimbal_controller.update_target(center_x, center_y, bbox)
    
    def _update_alarm_status(self):
        """更新报警状态"""
        old_status = self.alarm_status
        
        if self.alarm_status == "WARNING" and self.alarm_start_time:
            # 检查是否超时
            if time.time() - self.alarm_start_time > 10:  # 10秒超时
                self.alarm_status = "SAFE"
                self.alarm_start_time = None
                print("⏰ 报警超时，自动停止")
        
        # 如果状态改变，发送到云台
        if old_status != self.alarm_status:
            gimbal_status = self.gimbal_controller.get_status()
            if gimbal_status['tracking_active']:
                is_warning = (self.alarm_status == "WARNING")
                self.gimbal_controller.send_alarm_status(is_warning)
    
    def run(self):
        """运行主循环"""
        print("🎬 开始运行主循环")
        print("=" * 50)
        
        try:
            while True:
                # 更新报警状态
                self._update_alarm_status()
                
                # 获取摄像头图像
                img = camera.capture()
                if img is None:
                    continue
                
                self.frame_count += 1
                
                # 检测人脸
                detections = self.person_detector.detect(img)
                
                if detections:
                    self.detection_count += len(detections)
                    
                    # 处理每个检测到的人脸
                    for detection in detections:
                        # 识别身份
                        person_data = self.recognizer.recognize(img, detection)
                        
                        if person_data:
                            # 更新当前目标
                            self.current_target_name = person_data['name']
                            self.last_tracked_coordinates = (
                                person_data['bbox'][0] + person_data['bbox'][2] // 2,
                                person_data['bbox'][1] + person_data['bbox'][3] // 2,
                                person_data['bbox']
                            )
                            
                            # 输出跟踪坐标并发送到云台
                            self._output_tracking_coordinates_from_data(person_data)
                            
                            # 绘制检测框和标签
                            x, y, w, h = person_data['bbox']
                            img.draw_rectangle(x, y, x + w, y + h, color=image.Color.from_rgb(0, 255, 0), thickness=2)
                            img.draw_string(x, y - 20, person_data['name'], color=image.Color.from_rgb(255, 255, 255), scale=1.0)
                else:
                    # 没有检测到人脸，输出上次坐标
                    if self.last_tracked_coordinates:
                        self._output_last_coordinates()
                        self.last_tracked_coordinates = None
                        self.current_target_name = None
                
                # 绘制UI
                self._draw_ui(img)
                
                # 显示图像
                display.show(img)
                
                # 处理按钮事件
                self.button_manager.update()
                
        except KeyboardInterrupt:
            print("\n⏹️ 用户中断程序")
        except Exception as e:
            print(f"\n❌ 程序运行出错: {e}")
        finally:
            print("🔚 程序结束")
            print(f"📊 总帧数: {self.frame_count}")
            print(f"📊 总检测数: {self.detection_count}")
            self.gimbal_controller.stop_tracking()
            print("🎯 云台跟踪已停止")
    
    def _draw_ui(self, img):
        """绘制用户界面"""
        # 显示状态信息
        status_text = f"STATUS: {self.alarm_status}"
        status_color = image.Color.from_rgb(255, 0, 0) if self.alarm_status == "WARNING" else image.Color.from_rgb(0, 255, 0)
        img.draw_string(20, 150, status_text, color=status_color, scale=0.8)
        
        # 显示云台状态
        gimbal_status = self.gimbal_controller.get_status()
        if gimbal_status['tracking_active']:
            gimbal_text = "GIMBAL: ACTIVE"
            gimbal_color = image.Color.from_rgb(0, 255, 0)  # 绿色
        else:
            gimbal_text = "GIMBAL: INACTIVE"
            gimbal_color = image.Color.from_rgb(128, 128, 128)  # 灰色
        img.draw_string(20, 180, gimbal_text, color=gimbal_color, scale=0.8)
        
        # 显示统计信息
        stats_text = f"FRAMES: {self.frame_count} | DETECTIONS: {self.detection_count}"
        img.draw_string(20, 210, stats_text, color=image.Color.from_rgb(255, 255, 255), scale=0.6)
        
        # 显示当前目标
        if self.current_target_name:
            target_text = f"TARGET: {self.current_target_name}"
            img.draw_string(20, 240, target_text, color=image.Color.from_rgb(255, 255, 0), scale=0.6)
        
        # 绘制按钮
        self.button_manager.draw(img)

def main():
    """主函数"""
    print("🚀 启动YOLO人脸识别系统 (独立版本)")
    print("=" * 60)
    
    try:
        # 创建系统实例
        system = YOLOFaceRecognitionSystem()
        
        # 运行系统
        system.run()
        
    except Exception as e:
        print(f"❌ 系统启动失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
