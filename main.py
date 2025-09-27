#!/usr/bin/env python3
"""
基于自训练YOLO模型的人脸识别主程序
整合了person_detector和cnn_recognizer的功能
"""

from maix import camera, display, image, nn, app
import sys
import os
import time

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

class YOLOFaceRecognitionSystem:
    def __init__(self):
        """初始化YOLO人脸识别系统"""
        print("🚀 初始化YOLO人脸识别系统")
        print("=" * 50)
        
        # 初始化YOLO检测器
            self.detector = nn.YOLOv5(model="/root/my_own/best.mud", dual_buff=True)
            print("✓ YOLO检测器初始化成功")
            print(f"  输入尺寸: {self.detector.input_width()}x{self.detector.input_height()}")
            print(f"  识别类别: {self.detector.labels}")
        
        # 初始化摄像头
            self.cam = camera.Camera(
                self.detector.input_width(), 
                self.detector.input_height(), 
                self.detector.input_format()
            )
            print(f"✓ 摄像头初始化成功: {self.detector.input_width()}x{self.detector.input_height()}")
        
        # 初始化显示器
            self.dis = display.Display()
            print("✓ 显示器初始化成功")
        
        # 初始化人物检测器和识别器
                self.person_detector = PersonDetector(
                    camera_width=self.detector.input_width(),
                    camera_height=self.detector.input_height()
                )
                self.recognizer = CNNRecognizer()
                print("✓ 高级模块初始化成功")
        
        # 动态人物注册系统
        self.registered_persons = {}  # {person_id: {'name': 'A', 'features': [...], 'yolo_class': 0}}
        self.next_person_name = 'A'  # 下一个分配的名称
        self.current_detections = []  # 当前帧的检测结果
        self.selected_detection_index = 0  # 当前选中的检测框索引
        print("✓ 动态注册系统初始化成功")
        
        # 报警系统
        self.alarm_zone_persons = set()  # 报警区内的人物ID集合
        self.is_alarm_active = False  # 报警是否激活
        self.alarm_status = "SAFE"  # 当前报警状态: SAFE/WARNING
        print("✓ 报警系统初始化成功")
        
        # 初始化虚拟按钮
        self.button_manager = VirtualButtonManager(
            self.detector.input_width(),
            self.detector.input_height()
        )
        print("✓ 虚拟按钮初始化成功")
        
        # 检测参数
        self.conf_threshold = 0.6
        self.iou_threshold = 0.45
        
        # 系统状态
        self.frame_count = 0
        self.detection_count = 0
        self.running = False
        self.mode = "recognize"  # record | recognize | track
        self.button_click_count = 0
        self.current_thumbnail_person = None
        
        # FPS计算
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0.0
        self.last_fps_update = time.time()
        
        # 颜色定义
        self.class_colors = {
            0: image.Color.from_rgb(255, 0, 0),    # DINGZHEN - 红色
            1: image.Color.from_rgb(0, 255, 0),    # XQC - 绿色
            2: image.Color.from_rgb(0, 0, 255),    # kobe - 蓝色
        }
        
        # 设置虚拟按钮
        self._setup_buttons()
        
        print("✅ 系统初始化完成")
        print("=" * 50)
    
    def _setup_buttons(self):
        """设置虚拟按钮"""
        width = self.detector.input_width()
        height = self.detector.input_height()
        
        # DEBUG按钮
        debug_btn = self.button_manager.create_button(
            button_id='debug', x=width - 100, y=20, width=80, height=40, text='DEBUG'
        )
        debug_btn.set_colors(normal=(100, 100, 200), active=(150, 150, 255), disabled=(60, 60, 60))
        debug_btn.set_click_callback(self._on_button_click)
        
        # MODE按钮
        mode_btn = self.button_manager.create_button(
            button_id='mode', x=width - 100, y=70, width=80, height=40, text=self.mode.upper()
        )
        mode_btn.set_colors(normal=(200, 100, 0), active=(255, 150, 0), disabled=(60, 60, 60))
        mode_btn.set_click_callback(self._on_button_click)
        
        # 功能按钮
        func1_text, func2_text = self._get_mode_button_texts()
        func1_btn = self.button_manager.create_button(
            button_id='func1', x=width - 100, y=120, width=70, height=35, text=func1_text
        )
        func1_btn.set_colors(normal=(0, 150, 100), active=(0, 200, 150), disabled=(60, 60, 60))
        func1_btn.set_click_callback(self._on_button_click)
        
        func2_btn = self.button_manager.create_button(
            button_id='func2', x=width - 100, y=160, width=70, height=35, text=func2_text
        )
        func2_btn.set_colors(normal=(150, 0, 150), active=(200, 0, 200), disabled=(60, 60, 60))
        func2_btn.set_click_callback(self._on_button_click)
        
        # EXIT按钮
        exit_btn = self.button_manager.create_button(
            button_id='exit', x=20, y=20, width=60, height=30, text='EXIT'
        )
        exit_btn.set_colors(normal=(150, 0, 0), active=(200, 0, 0), disabled=(60, 60, 60))
        exit_btn.set_click_callback(self._on_button_click)
    
    def _get_mode_button_texts(self):
        """根据模式返回按钮文本"""
        if self.mode == "recognize":
            return "START", "STOP"
        elif self.mode == "record":
            return "ADD", "CLEAR"
        elif self.mode == "track":
            return "PREV", "NEXT"
        else:
            return "FUNC1", "FUNC2"
    
    def _on_button_click(self, button_id: str):
        """按钮点击处理"""
        self.button_click_count += 1
        print(f"🔘 按钮点击: {button_id} (总点击: {self.button_click_count})")
        
        if button_id == 'debug':
            self._handle_debug_button()
        elif button_id == 'mode':
            self._handle_mode_button()
        elif button_id == 'exit':
            self._handle_exit_button()
        elif button_id == 'func1':
            self._handle_func1_button()
        elif button_id == 'func2':
            self._handle_func2_button()
    
    def _handle_debug_button(self):
        """调试按钮处理"""
        print("=" * 50)
        print("🐛 === 动态注册系统调试信息 ===")
        print(f"  模式: {self.mode}")
        print(f"  帧数: {self.frame_count}")
        print(f"  FPS: {self.current_fps:.2f}")
        print(f"  分辨率: {self.detector.input_width()}x{self.detector.input_height()}")
        print(f"  检测数: {self.detection_count}")
        print(f"  当前检测: {len(self.current_detections)} 人")
        print(f"  选中索引: {self.selected_detection_index}")
        print(f"  下一个名称: {self.next_person_name}")
        print(f"  已注册人数: {len(self.registered_persons)}")
        if self.registered_persons:
            print("  注册人员:")
            for person_id, data in self.registered_persons.items():
                print(f"    {data['name']}: 已授权 (基于class_{data['yolo_class']})")
        print(f"  报警系统: {'激活' if self.is_alarm_active else '未激活'}")
        if self.is_alarm_active:
            print(f"  报警状态: {self.alarm_status}")
            print(f"  报警区类别数: {len(self.alarm_zone_persons)}")
            print(f"  报警区包含: {list(self.alarm_zone_persons)}")
            # 检查当前检测中的报警区人物
            current_alarm_count = 0
            for obj in self.current_detections:
                if obj.class_id in self.alarm_zone_persons:
                    current_alarm_count += 1
            print(f"  当前报警区人物: {current_alarm_count}")
        print("=" * 50)
    
    def _handle_mode_button(self):
        """模式切换处理"""
        modes = ["record", "recognize", "track"]
        current_idx = modes.index(self.mode)
        self.mode = modes[(current_idx + 1) % len(modes)]
        print(f"🔄 模式切换到: {self.mode}")
        
        # 更新按钮文字
        mode_btn = self.button_manager.get_button('mode')
        if mode_btn:
            mode_btn.set_text(self.mode.upper())
        
        func1_text, func2_text = self._get_mode_button_texts()
        func1_btn = self.button_manager.get_button('func1')
        func2_btn = self.button_manager.get_button('func2')
        if func1_btn:
            func1_btn.set_text(func1_text)
        if func2_btn:
            func2_btn.set_text(func2_text)
    
    def _handle_exit_button(self):
        """退出按钮处理"""
        print("🚪 退出按钮按下")
        self.running = False
    
    def _handle_func1_button(self):
        """功能按钮1处理"""
        if self.mode == "recognize":
            self._handle_start_alarm()
        elif self.mode == "record":
            self._handle_add_person()
        elif self.mode == "track":
            self._handle_prev_person()
    
    def _handle_func2_button(self):
        """功能按钮2处理"""
        if self.mode == "recognize":
            self._handle_stop_alarm()
        elif self.mode == "record":
            self._handle_clear_persons()
        elif self.mode == "track":
            self._handle_next_person()
    
    def _update_fps(self):
        """更新FPS"""
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.last_fps_update >= 0.5:
            time_diff = current_time - self.fps_start_time
            if time_diff > 0:
                self.current_fps = self.fps_counter / time_diff
            self.fps_counter = 0
            self.fps_start_time = current_time
            self.last_fps_update = current_time
    
    def _draw_ui_info(self, img):
        """绘制界面信息"""
        # 标题
        title = f"YOLOv5m {self.mode.upper()}"
        white_color = image.Color.from_rgb(255, 255, 255)
        img.draw_string(200, 10, title, color=white_color, scale=1.0)
        
        # FPS
        fps_text = f"FPS: {self.current_fps:.1f}"
        yellow_color = image.Color.from_rgb(255, 255, 0)
        img.draw_string(20, 105, fps_text, color=yellow_color, scale=1.2)
        
        # 系统状态
        if self.mode == "record":
            status_text = f"Recording Mode - Next: {self.next_person_name}"
        elif self.mode == "recognize":
            if self.is_alarm_active:
                status_text = f"Recognize Mode - Alarm: {self.alarm_status}"
            else:
                registered_count = len(self.registered_persons)
                status_text = f"Recognize Mode - {registered_count} persons"
        else:
            status_text = f"Track Mode"
        
        cyan_color = image.Color.from_rgb(0, 255, 255)
        img.draw_string(20, 130, status_text, color=cyan_color, scale=1.0)
        
        # 注册人员信息
        if self.registered_persons:
            registered_text = f"Registered: {', '.join([p['name'] for p in self.registered_persons.values()])}"
            green_color = image.Color.from_rgb(0, 255, 0)
            img.draw_string(20, 170, registered_text, color=green_color, scale=0.8)
        
        # Record模式下显示选中框
        if self.mode == "record" and self.current_detections:
            selection_text = f"Selected: {self.selected_detection_index + 1}/{len(self.current_detections)}"
            orange_color = image.Color.from_rgb(255, 165, 0)
            img.draw_string(20, 190, selection_text, color=orange_color, scale=0.8)
        
        # Recognize模式下显示报警状态
        if self.mode == "recognize" and self.is_alarm_active:
            if self.alarm_status == "WARNING":
                alarm_color = image.Color.from_rgb(255, 0, 0)  # 红色
                alarm_text = "WARNING"
            else:
                alarm_color = image.Color.from_rgb(0, 255, 0)  # 绿色
                alarm_text = "SAFE"
            
            img.draw_string(200, 190, alarm_text, color=alarm_color, scale=1.5)
    
    def process_frame(self, img):
        """处理单帧图像"""
        # 处理虚拟按钮输入
        clicked_button = self.button_manager.check_touch_input()
        self.button_manager.update()
        
            # YOLO检测
            detections = self.detector.detect(img, conf_th=self.conf_threshold, iou_th=self.iou_threshold)
            
        # 更新当前检测结果
        self.current_detections = detections if detections else []
        
        # 确保选中索引在有效范围内
        if self.current_detections and self.selected_detection_index >= len(self.current_detections):
            self.selected_detection_index = 0
        
            # 更新统计
            self.frame_count += 1
            if detections:
                self.detection_count += len(detections)
            
        # 更新报警状态
        if self.mode == "recognize":
            self._update_alarm_status()
        
        # 绘制检测结果（使用新的动态注册逻辑）
        if detections:
            self._draw_detection_with_selection(img, detections)
        
        # 绘制界面信息
        self._draw_ui_info(img)
        
        # 绘制虚拟按钮
        self.button_manager.draw_all(img)
        self.button_manager.draw_touch_indicator(img)
        
        # 更新FPS
        self._update_fps()
        
        return img
    
    def _get_next_person_name(self):
        """获取下一个人物名称 A, B, C, ..."""
        name = self.next_person_name
        if self.next_person_name == 'Z':
            self.next_person_name = 'A'  # 循环回A
            else:
            self.next_person_name = chr(ord(self.next_person_name) + 1)
        return name
    
    def _handle_add_person(self):
        """添加当前选中的检测框为新人物"""
        if not self.current_detections:
            print("❌ 没有检测到人物")
            return
        
        if self.selected_detection_index >= len(self.current_detections):
            print("❌ 选中索引超出范围")
            return
        
        selected_obj = self.current_detections[self.selected_detection_index]
        person_name = self._get_next_person_name()
        
        # 创建人物ID（基于YOLO类别和置信度）
        person_id = f"yolo_{selected_obj.class_id}_{int(selected_obj.score * 1000)}"
        
        # 注册新人物
        self.registered_persons[person_id] = {
            'name': person_name,
            'yolo_class': selected_obj.class_id,
            'yolo_class_name': self.detector.labels[selected_obj.class_id],
            'confidence_threshold': 0.5,
            'registered_time': time.time()
        }
        
        print(f"✅ 注册新人物: {person_name}")
        print(f"📊 当前已注册: {len(self.registered_persons)} 人")
    
    def _handle_clear_persons(self):
        """清除所有注册的人物"""
        count = len(self.registered_persons)
        self.registered_persons.clear()
        self.next_person_name = 'A'
        print(f"🗑️ 已清除 {count} 个注册人物")
    
    def _handle_prev_person(self):
        """选择上一个检测框"""
        if self.current_detections:
            self.selected_detection_index = (self.selected_detection_index - 1) % len(self.current_detections)
            print(f"⬅️ 选中检测框: {self.selected_detection_index + 1}/{len(self.current_detections)}")
    
    def _handle_next_person(self):
        """选择下一个检测框"""
        if self.current_detections:
            self.selected_detection_index = (self.selected_detection_index + 1) % len(self.current_detections)
            print(f"➡️ 选中检测框: {self.selected_detection_index + 1}/{len(self.current_detections)}")
    
    def _recognize_registered_person(self, yolo_class_id, confidence):
        """识别已注册的人物"""
        for person_id, person_data in self.registered_persons.items():
            if (person_data['yolo_class'] == yolo_class_id and 
                confidence >= person_data['confidence_threshold']):
                return person_data['name'], confidence
        return None, 0.0
    
    def _draw_detection_with_selection(self, img, detections):
        """绘制检测结果，报警区红框，安全区绿框，未授权黄框"""
        for i, obj in enumerate(detections):
            x, y, w, h = obj.x, obj.y, obj.w, obj.h
            class_id = obj.class_id
            confidence = obj.score
            
            # 检查是否为已注册人物
            person_name, similarity = self._recognize_registered_person(class_id, confidence)
            is_registered = person_name is not None
            
            # 确定框的颜色和粗细
            if self.mode == "recognize" and self.is_alarm_active and class_id in self.alarm_zone_persons:
                # 报警区内的人物：红色框
                color = image.Color.from_rgb(255, 0, 0)
                thickness = 3
            elif is_registered:
                # 已授权人物（安全区）：绿色框
                color = image.Color.from_rgb(0, 255, 0)
                thickness = 3
            else:
                # 未授权人物：黄色框
                color = image.Color.from_rgb(255, 255, 0)
                thickness = 2
            
            # 绘制边界框
            img.draw_rect(x, y, w, h, color=color, thickness=thickness)
            
            # 确定标签内容和颜色
            if is_registered:
                # 已注册人物：显示字母名称
                label = f'{person_name}: {similarity:.2f}'
                if self.mode == "recognize" and self.is_alarm_active and class_id in self.alarm_zone_persons:
                    label_color = image.Color.from_rgb(255, 0, 0)  # 报警区：红色文字
                else:
                    label_color = image.Color.from_rgb(0, 255, 0)  # 安全区：绿色文字
            else:
                # 未注册人物：显示Unknown
                label = f'Unknown: {confidence:.2f}'
                label_color = image.Color.from_rgb(255, 255, 0)  # 黄色文字
            
            # 绘制标签
            img.draw_string(x, y - 20 if y > 20 else y + h + 5, label, color=label_color)
    
    def _handle_start_alarm(self):
        """启动报警系统：将当前屏幕内人物移入报警区"""
        if not self.current_detections:
            print("❌ 没有检测到人物，无法启动报警")
            return
        
        # 清空报警区
        self.alarm_zone_persons.clear()
        
        # 将当前所有检测到的人物的类别加入报警区（使用类别ID而不是位置）
        for obj in self.current_detections:
            # 使用类别ID作为报警区标识，这样人物移动时仍能被识别
            class_id = obj.class_id
            self.alarm_zone_persons.add(class_id)
        
        self.is_alarm_active = True
        # 立即更新状态
        self._update_alarm_status()
        
        print(f"🚨 报警系统启动")
        print(f"📊 报警区类别数: {len(self.alarm_zone_persons)}")
        print(f"📊 报警区包含类别: {list(self.alarm_zone_persons)}")
        print(f"📊 当前状态: {self.alarm_status}")
    
    def _handle_stop_alarm(self):
        """停止报警系统：清空报警区"""
        self.alarm_zone_persons.clear()
        self.is_alarm_active = False
        self.alarm_status = "SAFE"
        
        print("⏹️ 报警系统已停止")
        print("🔓 报警区已清空")
    
    def _update_alarm_status(self):
        """更新报警状态"""
        if not self.is_alarm_active:
            return
        
        # 检查报警区内是否还有人物（基于类别ID）
        current_alarm_classes = set()
        for obj in self.current_detections:
            class_id = obj.class_id
            if class_id in self.alarm_zone_persons:
                current_alarm_classes.add(class_id)
        
        # 更新报警状态
        if current_alarm_classes:
            self.alarm_status = "WARNING"
        else:
            self.alarm_status = "SAFE"
    
    def run(self):
        """运行主循环"""
        print("🎬 开始运行...")
        print("按 EXIT 按钮或 Ctrl+C 退出")
        
        self.running = True
        try:
            while self.running and not app.need_exit():
                # 读取图像
                img = self.cam.read()
                if img is None:
                    continue
                
                # 处理图像
                img = self.process_frame(img)
                
                # 显示图像
                self.dis.show(img)
                
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\n⏹️ 用户中断")
        except Exception as e:
            print(f"❌ 运行时错误: {e}")
        finally:
            print("🔚 程序结束")
            print(f"📊 总帧数: {self.frame_count}")
            print(f"📊 总检测数: {self.detection_count}")

def main():
    """主函数"""
        system = YOLOFaceRecognitionSystem()
        system.run()

if __name__ == "__main__":
    main()
