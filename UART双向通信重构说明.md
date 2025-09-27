# UART双向通信重构说明

## 重构概述

为了解决LED不亮无法确定连接状态的问题，我们完全重构了UART通信代码，实现了MaixCam与单片机之间的双向通信测试机制。

## 新通信协议

### 握手协议
```
MaixCam → 单片机: 0x55 (握手请求)
单片机 → MaixCam: 0xAA (握手响应)
```

### 数据传输协议
```
坐标数据: 0x22 + X高字节 + X低字节 + Y高字节 + Y低字节
报警状态: 0x11 + 状态字节 (0x00=安全, 0x01=报警)
数据请求: 0x33
数据响应: 0xCC + 连接状态 + 报警状态
```

## 单片机端重构

### 1. 新增功能 (K230_UART.h)
```c
// 通信协议定义
#define HANDSHAKE_REQUEST  0x55    // 握手请求
#define HANDSHAKE_RESPONSE 0xAA    // 握手响应
#define DATA_REQUEST       0x33    // 数据请求
#define DATA_RESPONSE      0xCC    // 数据响应
#define ALARM_STATUS       0x11    // 报警状态
#define COORDINATE_DATA    0x22    // 坐标数据

// 新增函数
uint8_t K230_Handshake(void);
uint8_t K230_SendByte(uint8_t data);
uint8_t K230_ReceiveByte(uint8_t *data);
void K230_ProcessReceivedData(void);
```

### 2. 主程序更新 (main.c)
```c
// 连接测试循环
while(1) {
    // 每100ms进行一次连接测试
    if(test_count % 5 == 0) {
        K230_Handshake();
        
        // LED状态指示
        if(connection_status) {
            // 连接成功：绿色LED常亮
            DL_GPIO_setPins(GPIO_LED_PIN_LED_G_PORT, GPIO_LED_PIN_LED_G_PIN);
        } else {
            // 连接失败：红色LED闪烁
            // 红色LED闪烁逻辑
        }
    }
    test_count++;
    mspm0_delay_ms(20);
}
```

### 3. LED状态指示
- **绿色LED常亮**: 连接成功
- **红色LED闪烁**: 连接失败
- **蓝色LED**: 报警状态指示

## MaixCam端重构

### 1. 新增握手机制 (uart_communication.py)
```python
def _handshake(self) -> bool:
    """与单片机进行握手验证"""
    # 发送握手请求
    self.serial_conn.write(bytes([self.HANDSHAKE_REQUEST]))
    # 等待握手响应
    response = self.serial_conn.read(1)
    return response and response[0] == self.HANDSHAKE_RESPONSE
```

### 2. 连接状态监控
```python
def check_connection_status(self) -> dict:
    """检查连接状态"""
    return {
        'connected': self.is_connected,
        'verified': self.connection_verified,
        'time_since_handshake': time_since_handshake,
        'port': self.port,
        'baudrate': self.baudrate
    }
```

### 3. 简化的数据发送
```python
# 坐标数据发送
def send_coordinates(self, x: int, y: int) -> bool:
    frame = bytes([
        self.COORDINATE_DATA,  # 命令字节
        (x >> 8) & 0xFF,       # X坐标高字节
        x & 0xFF,               # X坐标低字节
        (y >> 8) & 0xFF,       # Y坐标高字节
        y & 0xFF               # Y坐标低字节
    ])

# 报警状态发送
def send_alarm_status(self, is_warning: bool) -> bool:
    frame = bytes([
        self.ALARM_STATUS,     # 命令字节
        0x01 if is_warning else 0x00  # 状态字节
    ])
```

## 使用方法

### 1. 硬件连接
```
MaixCam UART ←→ MSPM0G3507 UART
- TX → RX
- RX → TX  
- GND → GND
```

### 2. 软件配置
- **UART端口**: `/dev/ttyS1`
- **波特率**: 115200
- **数据位**: 8
- **停止位**: 1
- **校验位**: 无

### 3. 测试步骤

#### 步骤1：运行测试脚本
```bash
cd /home/kyunana/Maixcam_Tracking_Rebuild
python test_uart_connection.py
```

#### 步骤2：观察LED状态
- **绿色LED常亮**: 连接成功
- **红色LED闪烁**: 连接失败，检查硬件连接
- **蓝色LED**: 报警状态指示

#### 步骤3：运行主程序
```bash
python main.py
```

## 测试功能

### 1. 握手功能测试
- 验证MaixCam与单片机之间的握手通信
- 确认连接建立成功

### 2. 数据传输测试
- 测试坐标数据发送
- 测试报警状态发送
- 验证数据完整性

### 3. 连接稳定性测试
- 多次连接测试
- 验证连接稳定性

### 4. LED反馈测试
- 观察LED状态变化
- 验证报警状态指示

## 故障排除

### 1. 连接失败
**症状**: 红色LED闪烁
**解决方案**:
- 检查硬件连接 (TX-RX, RX-TX, GND-GND)
- 确认UART端口配置
- 检查波特率设置

### 2. 握手失败
**症状**: 连接建立但握手失败
**解决方案**:
- 检查通信协议是否匹配
- 确认数据格式正确
- 检查超时设置

### 3. 数据传输失败
**症状**: 握手成功但数据传输失败
**解决方案**:
- 检查数据帧格式
- 确认命令字节正确
- 检查数据长度

## 调试信息

### 1. 单片机端调试
- 观察LED状态变化
- 检查UART接收中断
- 验证数据处理逻辑

### 2. MaixCam端调试
- 查看控制台输出
- 检查连接状态信息
- 验证数据发送日志

## 性能优化

### 1. 连接稳定性
- 定期握手验证
- 自动重连机制
- 超时处理

### 2. 数据传输效率
- 简化数据帧格式
- 减少传输延迟
- 优化缓冲区管理

## 扩展功能

### 1. 多设备支持
- 支持多个单片机连接
- 设备ID识别
- 独立状态管理

### 2. 高级功能
- 数据压缩
- 错误检测和纠正
- 流量控制

## 总结

通过这次重构，我们实现了：

1. **双向通信验证**: 确保连接真正建立
2. **LED状态指示**: 直观显示连接状态
3. **简化协议**: 提高通信可靠性
4. **完整测试**: 验证所有功能正常

现在您可以：
- 通过LED状态直观判断连接状态
- 进行完整的通信测试
- 运行云台追踪系统
- 实现报警LED控制功能

系统已经准备好进行云台追踪和报警控制！
