from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

def add_title(doc, text, level=1):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = "微软雅黑"
    if level == 0:
        run.font.size = Pt(18)
        p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    elif level == 1:
        run.font.size = Pt(14)
    else:
        run.font.size = Pt(12)
    run.font.bold = True
    return p

def add_text(doc, text, indent=False):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.left_indent = Pt(20)
    run = p.add_run(text)
    run.font.name = "微软雅黑"
    run.font.size = Pt(11)
    return p

def add_bullet(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Pt(20)
    run = p.add_run("• " + text)
    run.font.name = "微软雅黑"
    run.font.size = Pt(11)
    return p

def add_num(doc, idx, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Pt(20)
    run = p.add_run(f"{idx}. " + text)
    run.font.name = "微软雅黑"
    run.font.size = Pt(11)
    return p


def gen_internal_log():
    doc = Document()
    
    add_title(doc, "项目开发日志 · 2026-10-24", level=0)
    doc.add_paragraph()

    add_title(doc, "当日里程碑", level=1)
    add_text(doc, "软件端模拟全链路正式跑通，硬件执行层独立闭环预演完成，工程模块化结构与联调环境全部就绪，超声波到货后可直接进入软硬件联调阶段。")

    add_title(doc, "团队分工与当日完成", level=1)
    
    add_title(doc, "一、软件端（B）", level=2)
    add_title(doc, "1. 工程模块化重构完成", level=3)
    add_text(doc, "四层解耦架构落地，模拟/真实硬件无缝切换，联调仅需修改一行代码：")
    add_bullet(doc, "sensor_layer.py：传感器抽象层，统一模拟/真实硬件接口，延迟加载串口依赖，模拟模式零第三方库")
    add_bullet(doc, "debounce.py：去抖防抖模块 + 全局参数统一入口，支持 DEMO/PRODUCTION 双模式")
    add_bullet(doc, "judge.py：存量状态判定核心算法，三态判定逻辑稳定")
    add_bullet(doc, "main.py：全链路主程序入口，距离换算、状态判定、盲区容错、自动日志完整闭环")
    add_bullet(doc, "serial_test.py：串口通道单测脚本，联调排障专用")
    
    add_title(doc, "2. 核心功能全部验证通过", level=3)
    add_bullet(doc, "距离 → 存量线性换算准确，三态（缺车/正常/堆积）判定逻辑无误")
    add_bullet(doc, "盲区、超量程容错机制生效，异常数据不触发状态跳变")
    add_bullet(doc, "双模式防抖验证：DEMO 即时响应 / PRODUCTION 连续3次判定才触发状态变更")
    add_bullet(doc, "CSV 运行日志自动生成，记录完整可回溯")
    
    add_title(doc, "3. 工程规范与联调环境就绪", level=3)
    add_bullet(doc, "串口依赖 pyserial 安装完成，虚拟环境联调条件齐备")
    add_bullet(doc, "精简 requirements.txt 依赖清单，团队一键装齐环境")
    add_bullet(doc, "补充 .gitignore 规则，运行日志与缓存文件不入库，仓库保持干净")
    add_bullet(doc, "所有可调参数集中收口到配置文件，联调调参仅需修改单文件")
    
    add_title(doc, "4. 代码状态", level=3)
    add_text(doc, "本地仓库所有提交完整保存，因当前网络环境限制暂未推送至远程，代码与提交记录安全，网络正常后可一次性同步。")
    
    add_title(doc, "二、硬件端（A）", level=2)
    add_title(doc, "1. 执行层独立闭环预演完成", level=3)
    add_bullet(doc, "LED 执行链路验证：接线正确，信号触发亮灭逻辑正常")
    add_bullet(doc, "蜂鸣器验证：有源蜂鸣器接 D12 引脚，与 LED 同步动作")
    add_bullet(doc, "假数据全链路预演：Arduino 输出 5~50cm 随机距离，小于阈值自动触发灯亮+蜂鸣器响，完整「判定→执行」链路验证通过")
    add_bullet(doc, "硬件环境就绪：Arduino IDE 与 USB 驱动安装完成，反复插拔可稳定识别开发板与串口号")
    
    add_title(doc, "2. 进行中", level=3)
    add_bullet(doc, "物理限位与标定装置：纸板+积木停车挡板制作中")
    add_bullet(doc, "硬件接线图、标定记录表整理中")
    
    add_title(doc, "三、测试/文档端（C）", level=2)
    add_bullet(doc, "完成项目仓库克隆与代码拉取，本地模拟全链路运行正常")
    add_bullet(doc, "对齐模块化工程结构，明确各文件职责与运行方式")
    add_bullet(doc, "开发日志记录规范对齐，联调测试用例梳理中")
    
    add_title(doc, "待办清单（硬件到货前）", level=1)
    add_num(doc, 1, "网络环境正常后，执行 git push 同步全部代码与提交记录")
    add_num(doc, 2, "补充 README 上手指南、联调测试清单、排障手册")
    add_num(doc, 3, "硬件端 A 接好超声波电路，完成硬件独立闭环自测")
    add_num(doc, 4, "软件端 B 完成串口通道验证，接入主程序全链路联调")
    add_num(doc, 5, "联合标定实验：校准距离转存量系数与判定阈值")
    add_num(doc, 6, "稳定性测试：连续运行 5 分钟无崩溃、无异常跳变")
    
    add_title(doc, "联调流程（到货后执行）", level=1)
    add_num(doc, 1, "硬件独立闭环：UNO 单独通电，测距、LED、蜂鸣器全部正常")
    add_num(doc, 2, "串口单测：运行 serial_test.py，确认 Python 稳定读取距离数据")
    add_num(doc, 3, "主程序接入：修改 main.py 传感器类型为真实串口，接入全链路")
    add_num(doc, 4, "参数校准：配合标定实验，调整换算系数与判定阈值")
    add_num(doc, 5, "全项验证：按测试清单完成所有测试项，输出测试报告")
    
    doc.save("内部开发日志_20261024.docx")


def gen_report():
    doc = Document()
    
    add_title(doc, "项目进度汇报 · 2026年10月24日", level=0)
    doc.add_paragraph()
    
    add_title(doc, "一、项目概述", level=1)
    add_text(doc, "本项目为基于超声波测距的站点状态智能监测系统，面向工程场景数字化赛道开发，通过非接触式测距实现站点存量的实时感知、自动判定与实体化反馈，具备软硬件一体化演示能力。")
    
    add_title(doc, "二、当前整体进度", level=1)
    add_text(doc, "项目已完成软件端核心算法与工程结构搭建，硬件执行层预演验证通过，整体处于「等待核心传感器到货、软硬件联调准备就绪」阶段，团队分工明确、并行推进，开发节奏符合预期。")
    
    add_title(doc, "三、近期完成工作", level=1)
    
    add_title(doc, "1. 软件算法与工程化", level=2)
    add_bullet(doc, "完成模块化工程架构拆分，实现传感器层、算法层、防抖容错层、应用层四层解耦，代码可维护性与扩展性提升，硬件接入仅需修改一行配置")
    add_bullet(doc, "模拟全链路功能跑通验证：距离换算、三态智能判定、盲区异常容错、运行日志自动记录全部达到预期效果")
    add_bullet(doc, "完成串口通信环境配置与联调脚本开发，硬件接入的软件侧环境全部就绪")
    add_bullet(doc, "规范团队协作标准：统一依赖清单、版本忽略规则，确保团队协同开发一致性")
    
    add_title(doc, "2. 硬件原型预研", level=2)
    add_bullet(doc, "完成执行层电路搭建与验证：LED 指示灯、蜂鸣器报警模块全部调试正常")
    add_bullet(doc, "完成假数据全链路预演：通过模拟测距数据验证硬件端自动判定与外设响应逻辑，执行层闭环稳定")
    add_bullet(doc, "完成开发环境与驱动配置，硬件识别与串口通信基础环境就绪")
    add_bullet(doc, "同步推进物理标定装置与实体原型制作")
    
    add_title(doc, "3. 团队协同", level=2)
    add_bullet(doc, "完成代码仓库同步，全员本地开发环境对齐")
    add_bullet(doc, "明确三角色分工：硬件负责人、软件负责人、测试文档负责人，并行推进无阻塞")
    
    add_title(doc, "四、下一步计划", level=1)
    add_num(doc, 1, "超声波传感器到货后，第一时间完成硬件独立闭环测试与真实场景阈值标定")
    add_num(doc, 2, "开展软硬件全链路联调，校准算法参数，验证系统稳定性与准确率")
    add_num(doc, 3, "补充可视化界面、扩展外设等演示件，提升项目展示效果")
    add_num(doc, 4, "整理测试报告与开发文档，完善项目交付材料")
    
    add_title(doc, "五、当前卡点", level=1)
    add_text(doc, "超声波测距模块尚未到货，是当前唯一阻塞项。团队已同步准备替代方案，优先通过本地电子市场、同城渠道获取传感器，确保联调工作尽早启动。")
    
    doc.save("项目进度汇报_20261024.docx")


if __name__ == "__main__":
    gen_internal_log()
    gen_report()
    print("两份Word文档已生成：")
    print("1. 内部开发日志_20261024.docx（团队留存）")
    print("2. 项目进度汇报_20261024.docx（指导老师版）")
