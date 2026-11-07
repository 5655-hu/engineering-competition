# Arduino 上传失败排查笔记（初学者版）

> 一次真实故障的完整复盘：从 `cannot set com-state for \\.\COM3` 到 Python 成功读到电压数据。
> 适用于：Arduino IDE 2.x + Windows 11 + CH340 克隆板（Nano/Uno）。

---

## 0. 一页速查（TL;DR）

| 你看到的报错 | 真正的意思 | 解决办法 |
|---|---|---|
| `cannot set com-state for \\.\COM3` | 驱动层拒绝了"修改串口参数"这个操作 | 换旧版 CH340 驱动（本文核心） |
| `unable to open port COM3 for programmer arduino` | 上一步失败的连带结果，不是独立的错 | 同上 |
| `PermissionError(13, '拒绝访问', None, 5)` | 端口被**别的程序**独占了 | 关掉 Arduino IDE 的串口监视器 |
| `not in sync: resp=0x00` | 端口通了，但 bootloader 没回应 | 板子型号/处理器（波特率）选错 |
| 端口号莫名其妙从 COM3 变 COM7 又变 COM8 | 换了 USB 口 → Windows 给新实例分配新号 | 正常现象，认准当前号即可 |

**一句话结论：这次一共踩了 4 个独立的坑，不是 1 个。**

---

## 1. 故障全景：4 个坑

```
坑 1：COM3 端口号被 CH340 和蓝牙串口同时占用     → 已修（改到 COM8）
坑 2：CH340 驱动 4.0.2026.2 有缺陷（真正的元凶）  → 已修（降级到 3.5.2019.1）
坑 3：串口被 IDE 串口监视器独占                   → 已修（关掉监视器）
坑 4：板子是 Nano 克隆板，要用 115200 新 bootloader → 已确认
```

> 新手最容易犯的错：看到第一个报错就去改代码、重装 IDE、换 USB 线，其实报错文本已经把方向指得很清楚了。

---

## 2. 必须先懂的 6 个概念

### 2.1 COM 口是什么

Windows 把每个串口抽象成一个名字，如 `COM8`。程序里写 `\\.\COM8` 就是在跟这个设备对话。

它其实是个"别名"，指向内核里的真实设备对象。查法：

```powershell
# 结果类似 \Device\Serial2
[System.IO.Ports.SerialPort]::GetPortNames()
```

用 PowerShell 看名字背后的真身（进阶，但很有用）：

```powershell
# COM8 => \Device\Serial2
# COM5 => \Device\BthModem0   ← 蓝牙串口是另一种设备对象
```

### 2.2 CH340 是什么

Arduino 原版板子用 ATmega16U2 做 USB 转串口。国产克隆板为了省钱，用 **WCH（南京沁恒）的 CH340 芯片**代替。

- 电脑看到的是 `USB-SERIAL CH340 (COMx)`
- VID/PID 是 `VID_1A86&PID_7523`（记住这串，排查时到处都能看到）
- **它不是标准 USB CDC 设备**，必须装厂商驱动才能用

### 2.3 驱动为什么"版本"很重要

驱动是芯片和 Windows 之间的翻译官。CH340 的驱动叫 `CH341SER`（注意是 341，因为它同时支持 CH340/CH341 系列）。

关键点：**厂商会在新驱动里加芯片校验/改动代码**，而克隆板上的 CH340 可能是"打磨片"（重新打标的山寨芯片）。新驱动遇到这种片子的表现五花八门——这次的症状就是"能读能写，但一改参数就报错"。

> 这是本文最重要的一条经验：**驱动不是越新越好，出问题要敢往回退。**

### 2.4 avrdude 上传时到底做了什么

Arduino IDE 背后用的是 `avrdude`。它上传一个 sketch 的流程是：

```
1. CreateFile("\\.\COM8")        打开端口
2. SetCommState(...)             设置波特率(115200)、8N1、DTR/RTS
3. 拉低 DTR → 板子复位进 bootloader
4. 用 STK500 协议握手，等 bootloader 回 0x14
5. 读芯片签名，确认是 ATmega328P
6. 擦除 flash → 写入 → 校验
```

**第 2 步失败，就是 `cannot set com-state`。** 后面那句 `unable to open port` 只是连带报错，别被它带偏。

### 2.5 为什么每次打开串口板子都会重启

Nano 的 DTR 引脚经过一个 100nF 电容接到复位脚。程序一打开串口，DTR 电平变化 → 复位脚被拉低 → 板子重启。

所以：

- 串口监视器一打开，板子就重启
- Python 脚本一 `Serial()`，板子就重启
- **时间戳从 0 开始**，开头 1~2 秒的数据是垃圾，要丢掉

### 2.6 bootloader 与波特率

bootloader 是芯片里一段"出厂固件"，负责接收新程序。Nano 克隆板有两种：

| 类型 | bootloader 波特率 | IDE 里怎么选 |
|---|---|---|
| 新 bootloader（Optiboot） | **115200** | 处理器 → `ATmega328P` |
| 旧 bootloader（ATmegaBOOT） | **57600** | 处理器 → `ATmega328P (Old Bootloader)` |

**判断方法**：用 avrdude 的 `-n`（只读签名，不写芯片）分别试两个波特率，哪个能握手成功就是哪个。详见第 8 节。

---

## 3. 坑 1：COM3 被两个设备同时占用

### 现象

设备管理器里同时存在：

```
USB-SERIAL CH340 (COM3)
蓝牙链接上的标准串行 (COM3)
```

### 证据

Windows 的端口映射表（注册表 `HKLM\HARDWARE\DEVICEMAP\SERIALCOMM`）里出现了两条指向同一个号的记录：

```
\Device\Serial2   : COM3     ← CH340
\Device\BthModem1 : COM3     ← 蓝牙串口
```

一个号码只能给一个设备，两条记录打架，谁最后注册谁"赢"，于是打开端口时常拿到错的那个对象。

### 为什么会这样

用户之前**手动改过设备端口号**（设备管理器 → 端口属性 → 高级 → COM 端口号），在蓝牙已经占着 COM3 的情况下把 CH340 也设成了 COM3。Windows 的"COM 端口仲裁表"（ComDB）本来会防止重复，但手工改注册表可以绕过去。

另外还有一个**幽灵设备**：`USB-SERIAL CH340 (COM7)` —— 状态 `CM_PROB_PHANTOM`（设备已拔掉，但记录还在，还占着号）。这是同一个板子插到另一个 USB 口留下的旧记录，因为 USB 口不同 → 设备实例不同 → 各记各的号。

### 怎么修

1. 设备管理器 → 端口 → `USB-SERIAL CH340` → 属性 → 端口设置 → 高级 → 改成一个**没人用的号**（本次改成 COM8）
2. 不用的蓝牙串口直接**禁用**（右键 → 禁用设备）
3. 清理幽灵设备：设备管理器 → 查看 → **显示隐藏的设备** → 灰色条目右键卸载
4. 拔插 USB 线，让新号码生效

> ⚠️ **教训：不要手动改端口号。** 换 USB 口、重装驱动，Windows 自己会分配，改号只会制造冲突。

---

## 4. 坑 2：驱动 4.0 的"假故障"（本次核心）

### 症状矩阵——这是定位的关键

改完端口号后报错依旧。于是我逐层测试同一个 COM 口的各个能力：

| 操作 | 4.0 驱动 | 3.5 驱动 |
|---|---|---|
| `CreateFile` 打开端口 | ✅ 成功 | ✅ 成功 |
| `ReadFile` / `WriteFile` 收发数据 | ✅ 成功 | ✅ 成功 |
| `SetCommTimeouts` 设超时 | ✅ 成功 | ✅ 成功 |
| **`SetCommState` 改波特率** | ❌ **err=31 / 87** | ✅ OK |
| avrdude 握手 | ❌ `cannot set com-state` | ✅ `Device signature = 1E 95 0F` |

**结论：数据通道是好的，只有"改参数"这条路断了。** 而 avrdude 上传必须改波特率，所以卡死。

### 错误码翻译

| 数字 | 含义 | 说明 |
|---|---|---|
| 31 | `ERROR_GEN_FAILURE` "设备无法运行" | 驱动内部某步失败了 |
| 87 | `ERROR_INVALID_PARAMETER` "参数无效" | 但参数其实是对的 |
| 5 | `ERROR_ACCESS_DENIED` "拒绝访问" | 端口被别的程序占了（注意区分！） |

### 两个反常细节

**细节 1：设置明明生效了，却返回失败。**

```
第 1 次：设 115200 → 返回 FALSE（失败）
第 2 次：读当前值 → 竟然是 115200
```

说明驱动做完动作后，在某个收尾步骤上失败了，然后把整个调用标记为失败。这是驱动 bug 的典型特征——"执行了，但说自己没执行"。

**细节 2：`GetCommState` 读回来的结构体里有垃圾数据。**

```
XonLim = -31124    XoffLim = 8603     ← 本该是合理的缓冲区阈值
```

这两个字段是驱动应该填好返回给调用方的，出现乱码说明驱动根本没正确初始化这个结构体。

### 官方结论

Arduino 官方文档写得很直接（[原文](https://support.arduino.cc/hc/en-us/articles/13148652511260-avrdude-ser_open-can-t-set-com-state-for-COMn)）：

> 这个错误发生在使用**特定批次 WCH CH340 芯片**的兼容板上。**问题只在最新版 CH340 驱动下出现**，安装旧版本驱动即可解决。

对应的 avrdude 项目 issue 也有记录：[avrdudes/avrdude#1328](https://github.com/avrdudes/avrdude/issues/1328)。

### 怎么修

把驱动从 `4.0.2026.2` 降到 `3.5.2019.1`（官方推荐的另一版本是 3.7.2022.01，思路相同）：

```powershell
# 以管理员身份运行（pnputil 需要提权）

# 1. 删除有问题的驱动包（oem88.inf 是它的发布名）
pnputil /delete-driver oem88.inf /uninstall /force

# 2. 安装旧版（INF 文件所在目录）
pnputil /add-driver "D:\ch341_v37\extracted\CH341SER.INF" /install

# 3. 重新枚举设备
pnputil /scan-devices
```

**装驱动前一定要验证签名**，防止被篡改的包：

```powershell
Get-AuthenticodeSignature "D:\ch341_v37\extracted\CH341S64.SYS" | Select Status, SignerCertificate
# 期望 Status = Valid，签名者 = Microsoft Windows Hardware Compatibility Publisher
```

### 防止 Windows 自动升回去

Windows Update 会把驱动偷偷更新回 4.0，然后你又崩了。用一个官方策略挡住：

```powershell
$k = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate'
if (-not (Test-Path $k)) { New-Item -Path $k -Force | Out-Null }
Set-ItemProperty -Path $k -Name 'ExcludeWUDriversInQualityUpdate' -Value 1 -Type DWord
```

### 怎么确认当前驱动版本

```powershell
Get-PnpDeviceProperty -InstanceId 'USB\VID_1A86&PID_7523\6&36ACB724&0&1' `
  -KeyName 'DEVPKEY_Device_DriverVersion'
```

或者：设备管理器 → 端口 → 右键属性 → **驱动程序** 选项卡。

---

## 5. 坑 3：Python 报 `PermissionError(13, '拒绝访问', None, 5)`

### 这是什么意思

`WinError 5 = ERROR_ACCESS_DENIED`，在 Python 里显示为 `PermissionError`（errno 13）。

**Windows 的串口是独占资源**：一个程序打开了，第二个程序就只能吃闭门羹——哪怕只是"看看数据"。

### 谁占着？怎么查

```powershell
# 1. 看有没有串口监视器在跑（Arduino IDE 2.x 的监视器是独立进程）
Get-Process -Name serial-monitor

# 2. 亲自试一次独占打开，err=5 就说明被占用
$p = New-Object System.IO.Ports.SerialPort 'COM8'
try { $p.Open(); "可以打开"; $p.Close() } catch { "打不开：" + $_.Exception.Message }
```

本次抓到的元凶：

```
PID 41732   serial-monitor.exe   23:16:35 启动
```

就是 IDE 里点开的**串口监视器**。它把 COM8 锁死了，Python 自然打不开。

### 怎么修

关掉 IDE 的串口监视器面板（或直接关 IDE），再跑 Python。

### 必须记住的规则

```
上传（avrdude） / IDE 串口监视器 / Python 脚本
        ↑ 三者同一时刻只能有一个用这个 COM 口
```

---

## 6. 坑 4：板子型号与 bootloader 波特率

这块是 **Arduino Nano 克隆板**（不是 Uno），IDE 里要：

- 开发板：**Arduino Nano**
- 处理器：**ATmega328P**（新 bootloader，115200）
- 端口：**COM8**

如果选了 `(Old Bootloader)`（57600），会得到：

```
Warning: attempt 1 of 10: not in sync: resp=0x00
```

> 顺带一个坑：Uno 和 Nano 的 flash 都是 32256 字节上限，所以**光看编译信息分不出 Uno 还是 Nano**，必须看板子丝印。

---

## 7. 排查方法论：五步定位法

遇到"串口/上传"问题，按顺序往下走，**每一步都有明确判据**，不要跳步：

| 步骤 | 问题 | 怎么查 | 不通说明 |
|---|---|---|---|
| ① 端口存在吗 | 设备管理器里有没有 `USB-SERIAL CH340 (COMx)`？ | 设备管理器 / `arduino-cli board list` | USB 线、供电、驱动没装 |
| ② 能打开吗 | 独占打开报错是 5 吗？ | 上面那段 PowerShell | 被别的程序占用 / 号码冲突 |
| ③ 能改参数吗 | `SetCommState` 成功吗？ | `mode COM8:` 看是否报"不支持指定选项" | **驱动问题**（本文核心） |
| ④ 能握手吗 | avrdude `-n` 能读到签名吗？ | 见第 8 节 | bootloader 波特率 / 板子型号 |
| ⑤ 数据对吗 | 读到的是不是你 sketch 打印的格式？ | 串口监视器看一眼 | 板子上跑的是别的程序 |

本次故障正好是 ①→②→③ 逐层暴露的：先修号码冲突（①②），才发现驱动问题（③）。

---

## 8. 工具与命令速查

### 8.1 `mode COM8:` —— 看端口状态

```cmd
mode COM8:
```

正常会打印 Baud / Parity / DTR 状态。如果不正常会报：

```
The specified options are not supported by this serial device
```

### 8.2 avrdude 干跑（`-n`）—— 最安全的验证手段

`-n` 表示 **No-write**：只读芯片签名，绝不修改 flash。适合反复测试。

```cmd
"C:\Users\Lenovo\AppData\Local\Arduino15\packages\arduino\tools\avrdude\8.0.0-arduino1\bin\avrdude.exe" ^
  -C "C:\Users\Lenovo\AppData\Local\Arduino15\packages\arduino\tools\avrdude\8.0.0-arduino1\etc\avrdude.conf" ^
  -p atmega328p -c arduino -P COM8 -b 115200 -n -v
```

健康输出长这样：

```
Using port            : COM8
Setting baud rate     : 115200
HW Version            : 3
FW Version            : 4.4
AVR device initialized and ready to accept instructions
Device signature = 1E 95 0F (ATmega328P, ATA6614Q, LGT8F328P)
```

### 8.3 `arduino-cli board list` —— 看 IDE 能认出哪些口

```powershell
& 'E:\Arduino\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe' board list
```

注意 `Type` 列：`Serial Port (USB)` 才是你的板子，纯 `Serial Port` 多半是蓝牙/虚拟串口。

### 8.4 查驱动包

```powershell
pnputil /enum-drivers | Select-String -Pattern 'ch341' -Context 0,7
```

### 8.5 设备管理器隐藏开关

**查看 → 显示隐藏的设备**。不打开这个，看不到幽灵设备（`CM_PROB_PHANTOM`）。

---

## 9. 本次最终改动清单 & 回滚方法

| 改动 | 新状态 | 怎么回滚 |
|---|---|---|
| CH340 驱动 | `4.0.2026.2` → `3.5.2019.1` | 运行 `D:\CH341SER.EXE`（4.0，不建议） |
| CH340 端口号 | COM3 → **COM8** | 设备管理器 → 端口设置 → 高级 → 改号 |
| 蓝牙串口 COM3 | 已禁用 | 设备管理器 → 右键 → 启用设备 |
| 幽灵 CH340 COM7 | 已删除 | 插入对应 USB 口会自动重建 |
| Windows Update 驱动策略 | `ExcludeWUDriversInQualityUpdate=1` | 删掉该注册表值 |
| `sketch_nov3a.ino` | **未修改**（本来就是对的） | — |

**旧驱动备份位置**：`D:\ch341_v37\extracted\`（CH341SER.INF + CH341S64.SYS + CAT）

---

## 10. 避坑清单（建议贴在显示器边上）

- [ ] **驱动不是越新越好**：CH340 出怪问题，第一反应是退回旧版（3.5 / 3.7 / 3.8）
- [ ] **不要手动改 COM 口号**：换 USB 口让 Windows 自己分配
- [ ] **同一时刻只有一个程序能用串口**：上传 / 监视器 / Python 三者互斥
- [ ] **看到 `cannot set com-state` 先想到驱动**，别去改代码
- [ ] **看到 `PermissionError 5` 先想到"被占用"**，不是权限不够（不用管理员运行）
- [ ] **换 USB 口后口号会变**，IDE 里要重新选端口
- [ ] **Nano 克隆板注意 Old Bootloader**：115200 不通就试 57600
- [ ] **每个 USB 口对应一个设备实例**，会各占一个 COM 号（所以会出现幽灵设备）
- [ ] **不要用错误的编码判断文件内容**：Windows PowerShell 5.1 的 `Get-Content` 默认按 ANSI(GBK) 读，UTF-8 的中文会变乱码，从而误判代码（本次就误判过一次 `delay(1000)` 被注释掉了，实际文件是好的）

---

## 11. 完整可用的 Python 读取脚本

相比最初的 9 行版本，这个版本加了：等复位完成、过滤半行数据、Ctrl+C 优雅退出、串口异常提示。

```python
import time

import serial

PORT = "COM8"        # 换 USB 口后要改这里
BAUD = 9600


def main():
    with serial.Serial(PORT, BAUD, timeout=1) as ser:
        # 打开串口会拉 DTR 触发板子复位，等它重启完
        print(f"已连接 {PORT}，等待板子重启…")
        time.sleep(2)
        ser.reset_input_buffer()

        while True:
            raw = ser.readline()
            if not raw:
                continue

            line = raw.decode("utf-8", errors="ignore").strip()
            if "," not in line:          # 过滤复位瞬间的半行
                continue

            voltage, ts = line.split(",", 1)
            try:
                print(f"电压: {float(voltage):.3f} V, 时间戳: {ts}")
            except ValueError:
                continue


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已停止")
    except serial.SerialException as e:
        print(f"串口错误：{e}")
        print("提示：检查 IDE 串口监视器是否开着、端口号是否变了")
```

`with` 语句保证异常退出时也会调用 `close()`，不会留下"下次打不开"的坑。

---

## 12. 术语表

| 术语 | 通俗解释 |
|---|---|
| COM 口 | Windows 给串口起的名字，如 COM8 |
| CH340 | 国产 USB 转串口芯片，克隆 Arduino 板常用 |
| 驱动 (driver) | 让 Windows 能跟芯片对话的翻译程序 |
| avrdude | Arduino 背后真正执行烧录的命令行工具 |
| bootloader | 芯片里的"接收新程序的固件" |
| DTR | 串口的一个控制信号，接到复位脚实现自动重启 |
| 幽灵设备 | 已拔掉但系统还留着的设备记录（`CM_PROB_PHANTOM`） |
| 独占访问 | 一个程序打开串口后，别的程序就打不开 |
| DCB | Windows 里保存串口参数（波特率/数据位等）的结构体 |
| `SetCommState` | 把 DCB 参数"写"进串口的系统调用——本次的失败点 |

---

## 13. 本次关键证据留档

| 时间 | 证据 | 说明 |
|---|---|---|
| 22:52 | `SERIALCOMM` 里 `\Device\Serial2→COM3` 和 `\Device\BthModem1→COM3` 并存 | 端口号冲突铁证 |
| 22:52 | `USB-SERIAL CH340 (COM7)` 状态 `CM_PROB_PHANTOM` | 幽灵设备 |
| 22:57 | `SetCommState` 报 err=31，`GetCommState` 返回 `XonLim=-31124` | 驱动缺陷 |
| 23:07 | 卸载设备 + 重新枚举后仍失败 | 排除"注册表状态污染" |
| 23:11 | 降级到 3.5.2019.1 → `SetCommState OK` | 确认为驱动问题 |
| 23:11 | avrdude 握手成功，签名 `1E 95 0F`，HW 3 / FW 4.4 | 端口链路完全正常 |
| 23:19 | `serial-monitor.exe` PID 41732 占用 COM8 → err=5 | Python 打不开的原因 |
| 23:20 | 杀掉监视器后读到 `2.16,0`，脚本输出 9 行正常数据 | 全链路打通 |

---

## 参考链接

- Arduino 官方：*avrdude: ser_open(): can't set com-state for COMn* — <https://support.arduino.cc/hc/en-us/articles/13148652511260-avrdude-ser_open-can-t-set-com-state-for-COMn>
- avrdude issue #1328：WCH CH340 serial port issue under Windows — <https://github.com/avrdudes/avrdude/issues/1328>
- WCH 官网（驱动下载）— <https://www.wch.cn/downloads/CH341SER_EXE.html>
- pyserial 文档 — <https://pyserial.readthedocs.io/>

---

*文档生成时间：2026-11-03 · 基于本次真实排查过程整理*
