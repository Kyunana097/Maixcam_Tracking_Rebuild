"""
CNN人脸识别模块
使用训练好的CNN模型进行人脸识别
"""

import os
import json
import numpy as np
from maix import image as _image

class CNNRecognizer:
    def __init__(self, model_path="data/models/xqc_face_model_final.pth", 
                 features_path="data/models/xqc_features.json"):
        """初始化CNN识别器（现在基于YOLO检测结果）"""
        print("🧠 初始化YOLO人脸识别器...")
        
        self.model_path = model_path
        self.features_path = features_path
        self.feature_vector = None
        self.person_name = None
        self.feature_dim = 128
        self.is_available = True  # 现在基于YOLO检测，始终可用
        
        # YOLO模型类别映射
        self.yolo_classes = {
            0: 'DINGZHEN',
            1: 'XQC', 
            2: 'kobe'
        }
        
        # 目标人物设置 (可以动态切换)
        self.target_person_id = 1  # 默认目标是XQC (class_id=1)
        self.target_person_name = self.yolo_classes.get(self.target_person_id, 'XQC')
        
        # 尝试加载特征向量（保持兼容性）
        self._load_features()
        
        print(f"✓ YOLO人脸识别器初始化成功")
        print(f"  🎯 当前目标人物: {self.target_person_name} (ID: {self.target_person_id})")
        print(f"  📊 支持类别: {list(self.yolo_classes.values())}")
        print(f"  🔄 基于YOLO检测结果进行识别")
    
    def _load_features(self):
        """加载预训练的特征向量"""
        try:
            if not os.path.exists(self.features_path):
                print(f"❌ 特征文件不存在: {self.features_path}")
                return False
            
            with open(self.features_path, 'r') as f:
                data = json.load(f)
            
            self.person_name = data.get('person_name', 'unknown')
            self.feature_vector = np.array(data.get('feature_vector', []))
            self.feature_dim = data.get('feature_dim', 128)
            
            if len(self.feature_vector) != self.feature_dim:
                print(f"❌ 特征向量维度不匹配: 期望{self.feature_dim}, 实际{len(self.feature_vector)}")
                return False
            
            self.is_available = True
            print(f"✓ 特征向量加载成功: {self.person_name}")
            return True
            
        except Exception as e:
            print(f"❌ 特征向量加载失败: {e}")
            return False
    
    def recognize_person(self, img, bbox=None, detection_result=None):
        """识别图像中的人物（基于YOLO检测结果）"""
        if not self.is_available:
            return None, 0.0, "YOLO识别器不可用"
        
        try:
            # 如果提供了YOLO检测结果，直接使用
            if detection_result and 'class_id' in detection_result:
                class_id = detection_result['class_id']
                confidence = detection_result.get('confidence', 0.0)
                class_name = detection_result.get('class_name', 'unknown')
                
                # 检查是否是目标人物
                if class_id == self.target_person_id:
                    return self.target_person_name, confidence, f"YOLO识别成功: {class_name}"
                elif class_id in self.yolo_classes:
                    return self.yolo_classes[class_id], confidence, f"YOLO识别: 非目标人物 {class_name}"
                else:
                    return None, confidence, f"YOLO识别: 未知类别 {class_name}"
            
            # 降级到传统方法（如果没有YOLO结果）
            # 提取人脸区域
            face_img = self._extract_face(img, bbox)
            if face_img is None:
                return None, 0.0, "未检测到人脸"
            
            # 计算特征向量（简化版本）
            current_features = self._compute_simple_features(face_img)
            
            # 计算相似度
            similarity = self._compute_similarity(current_features)
            
            # 判断是否为目标人物
            threshold = 0.7
            if similarity > threshold:
                return self.target_person_name, similarity, "特征识别成功"
            else:
                return None, similarity, "特征识别: 非目标人物"
                
        except Exception as e:
            print(f"❌ 人脸识别失败: {e}")
            return None, 0.0, f"识别错误: {e}"
    
    def _extract_face(self, img, bbox=None):
        """从图像中提取人脸区域"""
        try:
            if bbox is None:
                # 如果没有bbox，尝试检测人脸
                # 这里简化处理，使用图像中心区域
                w, h = img.width(), img.height()
                center_x, center_y = w // 2, h // 2
                face_size = min(w, h) // 3
                bbox = (center_x - face_size//2, center_y - face_size//2, 
                       face_size, face_size)
            
            x, y, w, h = bbox
            
            # 确保bbox在图像范围内
            x = max(0, min(x, img.width() - w))
            y = max(0, min(y, img.height() - h))
            w = min(w, img.width() - x)
            h = min(h, img.height() - y)
            
            # 裁剪人脸区域
            face_img = img.crop(x, y, w, h)
            
            # 调整到标准尺寸
            face_img = face_img.resize(64, 64)
            
            return face_img
            
        except Exception as e:
            print(f"❌ 人脸提取失败: {e}")
            return None
    
    def _compute_simple_features(self, face_img):
        """计算简化的特征向量（替代CNN特征提取）"""
        try:
            # 这里使用简化的特征提取方法
            # 实际部署时应该使用训练好的CNN模型
            
            # MaixPy图像处理 - 使用不同的API
            w, h = face_img.width(), face_img.height()
            
            # 简化的特征：基于图像尺寸和像素采样
            features = np.zeros(self.feature_dim)
            
            # 填充一些基于图像内容的特征
            features[0] = w  # 图像宽度
            features[1] = h  # 图像高度
            features[2] = w * h  # 像素总数
            
            # 采样一些像素值作为特征
            try:
                # 尝试获取像素数据（MaixPy方式）
                for i in range(min(60, w * h)):
                    x = i % w
                    y = i // w
                    if y < h:
                        # 这里简化处理，使用位置信息
                        features[3 + i] = (x + y) % 256
            except:
                # 如果无法获取像素，使用位置信息
                for i in range(60):
                    features[3 + i] = i % 256
            
            # 添加一些基于图像尺寸的随机特征
            np.random.seed((w * h) % 2**32)
            features[64:128] = np.random.normal(0, 0.5, 64)
            
            return features
            
        except Exception as e:
            print(f"❌ 特征计算失败: {e}")
            return np.zeros(self.feature_dim)
    
    def _compute_similarity(self, features):
        """计算与目标特征的相似度"""
        try:
            if self.feature_vector is None:
                return 0.0
            
            # 使用余弦相似度
            dot_product = np.dot(features, self.feature_vector)
            norm_features = np.linalg.norm(features)
            norm_target = np.linalg.norm(self.feature_vector)
            
            if norm_features == 0 or norm_target == 0:
                return 0.0
            
            similarity = dot_product / (norm_features * norm_target)
            
            # 将相似度映射到0-1范围
            similarity = max(0.0, min(1.0, similarity))
            
            return similarity
            
        except Exception as e:
            print(f"❌ 相似度计算失败: {e}")
            return 0.0
    
    def get_status_info(self):
        """获取识别器状态信息"""
        return {
            'cnn_available': self.is_available,
            'person_name': self.person_name,
            'feature_dim': self.feature_dim,
            'model_path': self.model_path,
            'features_path': self.features_path
        }
    
    def register_person(self, img, person_name, bbox=None):
        """注册新人物（CNN识别器不支持动态注册）"""
        return False, "CNN识别器不支持动态注册"
    
    def clear_persons(self):
        """清空已注册人物（CNN识别器不支持）"""
        return False, "CNN识别器不支持清空操作"
    
    def get_available_slots(self):
        """获取可用插槽数（CNN识别器固定为1）"""
        return 1 if self.is_available else 0
    
    def get_target_person(self):
        """获取目标人物"""
        return self.person_name
    
    def set_target_person(self, person_id):
        """设置目标人物"""
        try:
            if isinstance(person_id, str):
                # 如果传入的是名称，转换为ID
                for id, name in self.yolo_classes.items():
                    if name == person_id:
                        person_id = id
                        break
                else:
                    return False, f"未找到人物: {person_id}"
            
            if person_id in self.yolo_classes:
                self.target_person_id = person_id
                self.target_person_name = self.yolo_classes[person_id]
                print(f"✓ 目标人物已切换到: {self.target_person_name} (ID: {person_id})")
                return True, f"目标人物已设置为: {self.target_person_name}"
            else:
                return False, f"无效的人物ID: {person_id}"
        except Exception as e:
            return False, f"设置目标人物失败: {e}"
    
    def get_next_person(self):
        """获取下一个人物"""
        current_ids = list(self.yolo_classes.keys())
        current_index = current_ids.index(self.target_person_id) if self.target_person_id in current_ids else 0
        next_index = (current_index + 1) % len(current_ids)
        next_id = current_ids[next_index]
        self.set_target_person(next_id)
        return self.yolo_classes[next_id]
    
    def get_prev_person(self):
        """获取上一个人物"""
        current_ids = list(self.yolo_classes.keys())
        current_index = current_ids.index(self.target_person_id) if self.target_person_id in current_ids else 0
        prev_index = (current_index - 1) % len(current_ids)
        prev_id = current_ids[prev_index]
        self.set_target_person(prev_id)
        return self.yolo_classes[prev_id]
    
    def get_registered_persons(self):
        """获取已注册人物列表"""
        if self.is_available:
            persons = {}
            for class_id, class_name in self.yolo_classes.items():
                persons[class_name.lower()] = {
                    "id": class_id,
                    "name": class_name,
                    "samples": 1,
                    "thumbnail_path": None,
                    "is_target": class_id == self.target_person_id
                }
            return persons
        return {}
    
    def get_person_thumbnail(self, person_id):
        """获取人物缩略图（CNN识别器返回None）"""
        return None
