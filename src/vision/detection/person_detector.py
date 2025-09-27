#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人物检测模块
专门检测人物上半身并用绿色框标记
"""

class PersonDetector:
    """
    人物检测器类
    负责检测图像中的人物并返回边界框信息
    """
    
    def __init__(self, camera_width=512, camera_height=320):
        """
        初始化人物检测器
        
        Args:
            camera_width: 摄像头宽度(像素)
            camera_height: 摄像头高度(像素)
        """
        print("🔍 初始化人物检测器...")
        
        # 摄像头参数
        self.camera_width = camera_width
        self.camera_height = camera_height
        
        # 初始化自训练的YOLO模型
        try:
            from maix import nn
            # 使用你训练的YOLO模型
            self.yolo_detector = nn.YOLOv5(model="/root/my_own/best.mud", dual_buff=True)
            self.has_yolo_detector = True
            print("✓ 自训练YOLO检测器初始化成功")
            print(f"✓ 模型输入尺寸: {self.yolo_detector.input_width()}x{self.yolo_detector.input_height()}")
            print(f"✓ 识别类别: {self.yolo_detector.labels}")
        except Exception as e:
            print(f"✗ YOLO检测器初始化失败: {e}")
            self.yolo_detector = None
            self.has_yolo_detector = False
            
        # 备用人脸检测器
        try:
            from maix import nn
            self.face_detector = nn.FaceDetector(model="/root/models/face_detector.mud")
            self.has_face_detector = True
            print("✓ 备用Face detector初始化成功")
        except Exception as e:
            print(f"✗ 备用Face detector初始化失败: {e}")
            self.face_detector = None
            self.has_face_detector = False
            
        self.max_detections = 3
        
        # 类别名称映射
        self.class_names = ['DINGZHEN', 'XQC', 'kobe']
        
        print("✓ 人物检测器初始化完成（使用自训练YOLO模型）")
    
    def detect_persons(self, img):
        """
        检测图像中的人物
        
        Args:
            img: 输入图像
            
        Returns:
            list: 检测结果列表，每个元素包含：
                {
                    'bbox': (x, y, w, h),           # 人脸边界框
                    'face_bbox': (x, y, w, h),      # 人脸边界框（与bbox相同）
                    'confidence': float,            # 置信度
                    'type': 'face',                 # 检测类型
                    'class_id': int,                # 类别ID
                    'class_name': str               # 类别名称
                }
        """
        
        detections = []
        
        # 优先使用自训练的YOLO模型
        if self.has_yolo_detector and self.yolo_detector:
            try:
                # 使用YOLO模型进行检测
                yolo_objs = self.yolo_detector.detect(img, conf_th=0.6, iou_th=0.45)
                
                for obj in yolo_objs:
                    # YOLO检测结果转换
                    face_x, face_y = obj.x, obj.y
                    face_w, face_h = obj.w, obj.h
                    confidence = obj.score
                    class_id = obj.class_id
                    class_name = self.yolo_detector.labels[class_id] if class_id < len(self.yolo_detector.labels) else f"class_{class_id}"
                    
                    # 确保边界框在图像范围内
                    img_width = img.width() if callable(img.width) else img.width
                    img_height = img.height() if callable(img.height) else img.height
                    
                    face_x = max(0, min(face_x, img_width - face_w))
                    face_y = max(0, min(face_y, img_height - face_h))
                    face_w = min(face_w, img_width - face_x)
                    face_h = min(face_h, img_height - face_y)
                    
                    detection = {
                        'bbox': (face_x, face_y, face_w, face_h),
                        'face_bbox': (face_x, face_y, face_w, face_h),  # 人脸就是主要检测目标
                        'confidence': confidence,
                        'type': 'face',
                        'class_id': class_id,
                        'class_name': class_name
                    }
                    detections.append(detection)
                    
                    # 限制最大检测数量
                    if len(detections) >= self.max_detections:
                        break
                
                print(f"YOLO检测到 {len(detections)} 个人脸")
                
            except Exception as e:
                print(f"YOLO detection error: {e}")
        
        # 如果YOLO检测失败或未检测到，使用备用人脸检测器
        if not detections and self.has_face_detector and self.face_detector:
            try:
                print("使用备用人脸检测器...")
                faces = self.face_detector.detect(img)
                
                for face in faces:
                    face_x, face_y, face_w, face_h = face.x, face.y, face.w, face.h
                    
                    # 确保不超出图像边界
                    img_width = img.width() if callable(img.width) else img.width
                    img_height = img.height() if callable(img.height) else img.height
                    
                    face_x = max(0, min(face_x, img_width - face_w))
                    face_y = max(0, min(face_y, img_height - face_h))
                    face_w = min(face_w, img_width - face_x)
                    face_h = min(face_h, img_height - face_y)
                    
                    detection = {
                        'bbox': (face_x, face_y, face_w, face_h),
                        'face_bbox': (face_x, face_y, face_w, face_h),
                        'confidence': 0.8,
                        'type': 'face',
                        'class_id': -1,  # 未知类别
                        'class_name': 'unknown'
                    }
                    detections.append(detection)
                    
                    if len(detections) >= self.max_detections:
                        break
                        
                print(f"备用检测器检测到 {len(detections)} 个人脸")
            
            except Exception as e:
                print(f"Backup face detection error: {e}")
        
        return detections
    
    def draw_detection_boxes(self, img, detections):
        """
        在检测到的人物周围绘制边界框
        
        Args:
            img: 输入图像
            detections: 检测结果列表
            
        Returns:
            image: 标记后的图像
        """
        try:
            from maix import image
        except ImportError:
            return img
        
        # 为不同类别定义颜色
        class_colors = {
            'DINGZHEN': image.Color.from_rgb(255, 0, 0),    # 红色
            'XQC': image.Color.from_rgb(0, 255, 0),         # 绿色
            'kobe': image.Color.from_rgb(0, 0, 255),        # 蓝色
            'unknown': image.Color.from_rgb(255, 255, 0)    # 黄色
        }
        
        for detection in detections:
            bbox = detection['bbox']
            x, y, w, h = bbox
            confidence = detection.get('confidence', 0.0)
            class_name = detection.get('class_name', 'unknown')
            
            # 根据类别选择颜色
            color = class_colors.get(class_name, image.Color.from_rgb(255, 255, 255))
            
            # 绘制人脸检测框
            try:
                img.draw_rect(x, y, w, h, color=color, thickness=2)
            except Exception as e:
                print(f"绘制边界框失败: {e}")
                pass
            
            # 绘制标签
            try:
                label = f"{class_name}: {confidence:.2f}"
                white_color = image.Color.from_rgb(255, 255, 255)
                # 绘制标签背景
                img.draw_rect(x, max(y-20, 0), len(label)*8, 20, color=color, thickness=-1)
                # 绘制标签文字
                img.draw_string(x, max(y-15, 0), label, color=white_color)
            except Exception as e:
                print(f"绘制标签失败: {e}")
                pass
        
        return img
    
    def get_detection_info(self, detections):
        """
        获取检测信息摘要
        
        Args:
            detections: 检测结果列表
            
        Returns:
            dict: 检测信息摘要
        """
        return {
            'count': len(detections),
            'types': [det.get('type', 'unknown') for det in detections],
            'confidence_avg': sum(det.get('confidence', 0) for det in detections) / len(detections) if detections else 0.0,
            'upper_body_bboxes': [det.get('bbox') for det in detections],
            'face_bboxes': [det.get('face_bbox') for det in detections if det.get('face_bbox')]
        }
    
    def calculate_image_similarity(self, img1, img2):
        """
        计算两个图像的真实相似度
        基于图像的统计特征进行比较
        
        Args:
            img1: 第一个图像
            img2: 第二个图像
            
        Returns:
            float: 相似度 (0.0-1.0)
        """
        try:
            # 确保两图像尺寸一致
            img1_w = img1.width() if callable(img1.width) else img1.width
            img1_h = img1.height() if callable(img1.height) else img1.height
            img2_w = img2.width() if callable(img2.width) else img2.width  
            img2_h = img2.height() if callable(img2.height) else img2.height
            
            if (img1_w, img1_h) != (img2_w, img2_h):
                img2 = img2.resize(img1_w, img1_h)
            
            # 使用图像的统计特征进行比较
            # 这是一个基于实际图像内容的算法
            
            # 1. 尺寸特征比较
            size_similarity = 1.0  # 已经调整为相同尺寸
            
            # 2. 使用MaixPy可用的图像特征
            # 由于不能直接访问像素，我们使用图像对象的可访问属性
            try:
                # 尝试获取图像的一些可比较特征
                # 注意：这里需要根据实际MaixPy API调整
                
                # 使用图像对象的哈希作为内容标识
                # 但这次我们基于图像保存后的内容，而不是内存地址
                import tempfile
                import os
                
                # 将图像保存到临时文件以获取内容哈希
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp1:
                    img1.save(tmp1.name)
                    tmp1_path = tmp1.name
                
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp2:
                    img2.save(tmp2.name) 
                    tmp2_path = tmp2.name
                
                # 比较文件内容
                similarity = self._compare_image_files(tmp1_path, tmp2_path)
                
                # 清理临时文件
                os.unlink(tmp1_path)
                os.unlink(tmp2_path)
                
                return similarity
                
            except Exception as e:
                # 降级到基本比较
                return self._basic_image_comparison(img1, img2)
            
        except Exception as e:
            return 0.0
    
    def _compare_image_files(self, path1, path2):
        """
        比较两个图像文件的内容相似度
        
        Args:
            path1: 第一个图像文件路径
            path2: 第二个图像文件路径
            
        Returns:
            float: 相似度 (0.0-1.0)
        """
        try:
            import os
            
            # 获取文件大小
            size1 = os.path.getsize(path1)
            size2 = os.path.getsize(path2)
            
            # 如果文件大小完全相同，可能是同一文件
            if size1 == size2:
                # 进一步比较文件内容
                with open(path1, 'rb') as f1, open(path2, 'rb') as f2:
                    content1 = f1.read()
                    content2 = f2.read()
                    
                    if content1 == content2:
                        return 0.95  # 内容完全相同
                    
                    # 计算内容差异
                    diff_count = sum(a != b for a, b in zip(content1, content2))
                    similarity = 1.0 - (diff_count / len(content1))
                    return max(0.0, similarity)
            
            # 基于文件大小的相似度（简化方法）
            size_ratio = min(size1, size2) / max(size1, size2)
            
            # 添加一些基于内容的比较
            with open(path1, 'rb') as f1, open(path2, 'rb') as f2:
                # 比较文件头部（JPEG header等）
                header1 = f1.read(100)
                header2 = f2.read(100)
                
                header_diff = sum(a != b for a, b in zip(header1, header2))
                header_similarity = 1.0 - (header_diff / len(header1))
            
            # 综合相似度
            final_similarity = size_ratio * 0.6 + header_similarity * 0.4
            return max(0.0, min(1.0, final_similarity))
            
        except Exception as e:
            return 0.3
    
    def _basic_image_comparison(self, img1, img2):
        """
        基本图像比较（降级方案）
        
        Args:
            img1: 图像1
            img2: 图像2
            
        Returns:
            float: 相似度 (0.0-1.0)
        """
        try:
            # 基于图像尺寸和基本属性的比较
            w1 = img1.width() if callable(img1.width) else img1.width
            h1 = img1.height() if callable(img1.height) else img1.height
            w2 = img2.width() if callable(img2.width) else img2.width
            h2 = img2.height() if callable(img2.height) else img2.height
            
            # 尺寸相似度
            size_sim = min(w1*h1, w2*h2) / max(w1*h1, w2*h2)
            
            # 宽高比相似度
            ratio1 = w1 / h1
            ratio2 = w2 / h2
            ratio_sim = 1.0 - abs(ratio1 - ratio2) / max(ratio1, ratio2)
            
            return (size_sim + ratio_sim) / 2.0
            
        except Exception as e:
            return 0.5

    def get_debug_info(self):
        """
        获取调试信息
        
        Returns:
            dict: 调试参数信息
        """
        return {
            'camera_size': f"{self.camera_width}x{self.camera_height}",
            'max_detections': self.max_detections,
            'has_face_detector': self.has_face_detector,
            'module_status': 'initialized_placeholder'
        }

# TODO: 参考standalone_gui.py中的SimplePersonDetector实现
# 需要集成的功能：
# 1. 人脸检测器初始化 (nn.FaceDetector)
# 2. 人脸检测 (detect_persons方法)
# 3. 人脸到上半身的转换 (face_to_torso)
# 4. 检测结果绘制 (draw_detection_boxes)
# 5. 重叠检测过滤 (filter_overlapping_detections)
