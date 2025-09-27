# 报警LED控制功能说明

## 功能概述

实现了MaixCam视觉识别系统与MSPM0G3507单片机之间的报警状态通信，当检测到报警状态时，单片机会自动点亮LED指示灯。

## 系统架构

```
MaixCam (视觉识别) ←→ UART ←→ MSPM0G3507 (LED控制)
     ↓ 报警状态检测              ↓ LED状态控制
     WARNING/SAFE               LED点亮/熄灭
```

## 通信协议

### 报警状态帧格式
```
帧头: 0xBB 0xBB
状态: 0x00(安全) / 0x01(报警)
校验: 状态字节
帧尾: 0xEE 0xEE
```

**总长度：6字节**

### 状态定义
- `0x00`: 安全状态 (SAFE) - LED熄灭
- `0x01`: 报警状态 (WARNING) - LED点亮

## 实现功能

### 1. MaixCam端功能

#### UART通信模块 (`src/hardware/uart_communication.py`)
- **新增功能**:
  - `send_alarm_status(is_warning)`: 发送报警状态
  - `_build_alarm_frame(status)`: 构建报警状态帧
  - 支持报警状态帧格式 (0xBB 0xBB ... 0xEE 0xEE)

#### 主程序集成 (`main.py`)
- **报警状态检测**: 实时监控报警区内人物
- **状态变化触发**: 当报警状态改变时自动发送到单片机
- **云台控制器**: 通过云台控制器发送报警状态

### 2. 单片机端功能

#### K230_UART模块更新

**K230_UART.h 新增**:
```c
// 报警状态变量
volatile uint8_t alarm_status;

// LED控制函数
void LED_Control_Init(void);
void LED_Set_Alarm_Status(uint8_t status);
void LED_Update_Status(void);
```

**K230_UART.c 新增**:
- **报警状态帧接收**: 处理0xBB 0xBB ... 0xEE 0xEE格式
- **LED控制函数**: 根据报警状态控制LED
- **状态校验**: 确保数据完整性

#### 主程序集成 (`main.c`)
- **LED初始化**: 启动时初始化LED控制
- **状态同步**: 接收报警状态并更新LED

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
- **LED引脚**: `GPIO_LED_PIN_LED_B_PORT` (蓝色LED)

### 3. 操作流程

#### 启动系统
1. 运行MaixCam主程序：`python main.py`
2. 点击 **GIMBAL** 按钮启动云台通信
3. 切换到 **recognize** 模式
4. 点击 **START** 按钮启动报警系统

#### 报警状态控制
- **报警触发**: 当报警区内有人物时，LED自动点亮
- **安全状态**: 当报警区内无人物时，LED自动熄灭
- **状态同步**: 实时同步报警状态到单片机

## 代码结构

### MaixCam端
```python
# 发送报警状态
gimbal_controller.send_alarm_status(is_warning)

# 报警状态检测
def _update_alarm_status(self):
    # 检测报警区内人物
    # 更新报警状态
    # 发送状态到单片机
```

### 单片机端
```c
// LED控制初始化
LED_Control_Init();

// 接收报警状态
void UART_0_rx_DataFrame(void) {
    // 处理报警状态帧
    // 更新LED状态
}

// LED状态更新
void LED_Update_Status(void) {
    if(alarm_status == 0x01) {
        DL_GPIO_setPins(GPIO_LED_PIN_LED_B_PORT, GPIO_LED_PIN_LED_B_PIN);
    } else {
        DL_GPIO_clearPins(GPIO_LED_PIN_LED_B_PORT, GPIO_LED_PIN_LED_B_PIN);
    }
}
```

## 测试方法

### 1. 通信测试
```bash
# 运行测试脚本
python test_alarm_communication.py
```

### 2. 功能测试
1. **启动系统**: 运行主程序并激活云台通信
2. **启动报警**: 点击START按钮启动报警系统
3. **观察LED**: 当报警区内有人物时，LED应该点亮
4. **清除报警**: 点击STOP按钮停止报警系统，LED应该熄灭

### 3. 调试信息
- 查看控制台输出的报警状态信息
- 使用DEBUG按钮查看详细状态
- 检查UART连接状态

## 故障排除

### 1. LED不响应
- 检查UART连接是否正常
- 确认单片机程序是否运行
- 检查LED引脚配置

### 2. 报警状态不同步
- 检查报警系统是否激活
- 确认云台通信是否正常
- 查看调试信息中的状态变化

### 3. 通信失败
- 检查硬件连接
- 确认UART端口和波特率
- 查看错误日志

## 扩展功能

### 1. 多LED控制
可以扩展支持多个LED指示不同状态：
```c
// 支持多个LED
#define LED_ALARM_RED    GPIO_LED_PIN_LED_R_PIN
#define LED_ALARM_GREEN  GPIO_LED_PIN_LED_G_PIN
#define LED_ALARM_BLUE   GPIO_LED_PIN_LED_B_PIN
```

### 2. 状态指示
可以添加更多状态指示：
- 系统启动状态
- 通信连接状态
- 错误状态指示

### 3. 报警级别
可以支持多级报警：
- 低级别报警：闪烁
- 高级别报警：常亮
- 紧急报警：快速闪烁

## 注意事项

1. **状态同步**: 确保报警状态变化时及时发送到单片机
2. **错误处理**: 处理UART通信错误和超时
3. **资源管理**: 程序退出时正确清理资源
4. **硬件保护**: 避免频繁的LED开关操作

## 技术支持

如遇到问题，请检查：
1. 硬件连接是否正确
2. 软件配置是否匹配
3. 调试信息中的错误提示
4. 单片机端接收程序是否正常运行
