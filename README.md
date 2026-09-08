# HS Code MCP Server

> 海关商品归类智能体工具 — 基于2026年进出口税则的MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Data: 2026 Tariff](https://img.shields.io/badge/Data-2026%20Tariff-blue.svg)](https://gss.mof.gov.cn/)
[![HS4 Coverage: 100%](https://img.shields.io/badge/HS4%20Coverage-100%25-green.svg)]()
[![MCP Version: 1.x](https://img.shields.io/badge/MCP-1.x-orange.svg)]()
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)]()

将海关进出口税则封装为 MCP（Model Context Protocol）工具，让 AI Agent 能够智能查询 HS 编码、计算进口税费、浏览商品分类。基于2026年最新税则数据，品目描述100%覆盖。

## ✨ 功能特性

| 工具 | 说明 |
|------|------|
| `search_hs_code` | 商品名称模糊搜索，返回Top N候选（品目描述加权 + 同义词词典 + HS编码前缀直匹配 + 8位精确编码优先） |
| `get_hs_detail` | 按HS编码查询详细信息（税率、监管条件、类别、品目描述、商品名称） |
| `calculate_import_tax` | 计算进口税费（关税 + 消费税 + 增值税），支持CIF价格和数量 |
| `get_categories` | 获取22个商品分类列表及对应品目范围 |
| `get_stats` | 数据库统计信息（条目数、品目数、分类数、数据版本） |

## 🎯 搜索算法

采用多维度加权评分，确保归类准确性：

| 匹配维度 | 权重 | 说明 |
|----------|------|------|
| 8位HS编码精确匹配 | +400分 | 同义词中包含完整8位编码时直接命中 |
| 4位品目编码匹配 | +150分 | 同义词中包含品目前缀时给该品目下所有编码加分 |
| 品目描述包含 | +100分 | 查询词出现在品目官方描述中 |
| 商品名称相似度 | 0-100分 | 基于SequenceMatcher的文本相似度 |
| 类别匹配 | +30分 | 查询词命中商品分类名称 |
| 子串匹配 | +50分 | 查询词与商品名称互为子串 |

**短词优化**：2字及以下搜索词采用精确key匹配，避免子串反向匹配导致误判（如"咖啡"不会匹配到"生咖啡豆"的编码）。

## 📊 数据规模

- **税则条目**：8,972 条（2026年版）
- **品目描述**：1,228 个（**100% 覆盖**，从财政部官方PDF提取）
- **商品分类**：22 类
- **同义词词典**：70+ 条常见商品映射（含HS编码前缀直匹配）
- **数据来源**：[财政部《2026年进出口税则》](https://gss.mof.gov.cn/gzdt/zhengcefabu/202512/P020251231607833453633.pdf)

## ✅ 测试结果

14个常见商品归类测试 **100% 通过**：

| 商品 | 正确HS编码 | 搜索结果 |
|------|-----------|----------|
| 口红 | 3304.1000 | ✅ |
| 笔记本电脑 | 8471.3090 | ✅ |
| 纯棉T恤 | 6109.1000 | ✅ |
| 咖啡（烘焙豆） | 0901.2100 | ✅ |
| 不锈钢锅 | 7323.9300 | ✅ |
| 红酒 | 2204.2100 | ✅ |
| 啤酒 | 2203.0000 | ✅ |
| 巧克力 | 1806.3200 | ✅ |
| 手表 | 9102.1100 | ✅ |
| 充电宝 | 8507.6000 | ✅ |
| 水杯 | 3924.1000 | ✅ |
| 手机 | 8517.1300 | ✅ |
| 耳机 | 8518.3000 | ✅ |
| 平板电脑 | 8471.3010 | ✅ |

## 🚀 快速开始

### 环境要求

- Python 3.10+
- mcp >= 1.2.0, < 2.0.0

### 安装

```bash
git clone https://github.com/dcd887/hs-code-mcp-server.git
cd hs-code-mcp-server
pip install -r requirements.txt
```

### 运行

```bash
python server.py
```

### 在 MCP 客户端中配置

#### Claude Desktop

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）或 `%APPDATA%\Claude\claude_desktop_config.json`（Windows）：

```json
{
  "mcpServers": {
    "hs-code": {
      "command": "python",
      "args": ["C:/path/to/hs-code-mcp-server/server.py"]
    }
  }
}
```

#### 豆包 / Cursor / 其他 MCP 客户端

在MCP配置中添加：

```json
{
  "mcpServers": {
    "hs-code": {
      "command": "python",
      "args": ["C:/path/to/hs-code-mcp-server/server.py"]
    }
  }
}
```

## 📖 使用示例

### 搜索商品编码

```
用户：帮我查一下口红的HS编码
Agent调用 search_hs_code(product_name="口红", top_n=3)
→ 返回：
  1. 3304.1000 唇用化妆品 - 关税5%，增值税13%
  2. 3304.2000 眼用化妆品 - 关税10%，增值税13%
  3. 3304.3000 指(趾)甲化妆品 - 关税15%，增值税13%
```

### 计算进口税费

```
用户：进口10台笔记本电脑，CIF单价5000元，要交多少税？
Agent调用 calculate_import_tax(hs_code="8471.3090", cif_price=5000, quantity=10)
→ 返回：
  关税：0元（零关税）
  消费税：0元
  增值税：6,500元
  税费总计：6,500元
  综合税率：13%
```

### 查询编码详情

```
用户：8517.1300是什么商品？
Agent调用 get_hs_detail(hs_code="8517.1300")
→ 返回：
  商品名称：手机
  关税：0%
  增值税：13%
  消费税：0%
  类别：第十六类 机器、机械器具...
  品目描述：电话机，包括蜂窝网络...
```

### 浏览商品分类

```
用户：海关商品有哪些大类？
Agent调用 get_categories()
→ 返回22个分类：
  第一类：活动物；动物产品（01-05章）
  第二类：植物产品（06-14章）
  ...
  第十六类：机器、机械器具（84-85章）
  ...
```

## 🏗️ 项目结构

```
hs-code-mcp-server/
├── server.py                  # MCP Server 主程序（FastMCP，5个工具）
├── requirements.txt           # Python 依赖（mcp>=1.2.0,<2.0.0）
├── README.md                  # 项目说明
├── .gitignore                 # Git 忽略（.venv/__pycache__/.env等）
└── data/
    ├── hs_codes_full.json     # 8972条2026税则数据
    └── hs4_descriptions.json  # 1228个品目官方描述（100%覆盖）
```

## 🏆 比赛与荣誉

- **2026上海开源软件应用创新大赛** 参赛项目（截止10/11）
- 基于作者**上海海关学院海关稽查专业**背景开发，数据经专业核对
- 姊妹项目：[税则通（微信小程序版）]()、[稽查眼（海关稽查风险自查）]()

## ⚠️ 免责声明

- 本工具数据基于2026年进出口税则，**仅供参考，不构成法律意见**
- 实际归类和税费以海关官方裁定为准
- 税率计算基于最惠国税率，未考虑协定税率、特惠税率、反倾销税、报复性关税等特殊情况
- 建议结合海关总署公告、归类决定、预裁定等官方文件使用
- 商品归类存在主观性，本工具返回多个候选供参考，最终归类需专业判断

## 🔄 数据更新

数据基于2026年版进出口税则。海关总署/财政部发布新公告时，可通过以下方式更新：

1. 下载最新税则PDF
2. 使用PyMuPDF提取品目描述
3. 更新 `data/hs_codes_full.json` 和 `data/hs4_descriptions.json`
4. 重启MCP Server

## 📄 License

MIT License - 可自由使用、修改、分发，需保留版权声明。

## 👤 作者

**黄谦** | 上海海关学院 海关稽查专业 | GitHub: [dcd887](https://github.com/dcd887)

- 9个MCP Server开源项目作者
- 微信小程序「税则通」开发者
- 补天/TSRC白帽
- 国考目标：深圳海关

## 🔗 相关项目

- [mc-mcp-toolchain](https://github.com/dcd887/mc-mcp-toolchain) — Minecraft MCP 工具链（M8ven收录，评分89/100）
- [minecraft-mcp-server](https://github.com/dcd887/minecraft-mcp-server) — Minecraft MCP Server
- [langchain-mcp-agent-demo](https://github.com/dcd887/langchain-mcp-agent-demo) — LangChain MCP Agent 演示
- [game-translator-mcp](https://github.com/dcd887/game-translator-mcp) — 游戏翻译 MCP
- [mc-changelog-mcp](https://github.com/dcd887/mc-changelog-mcp) — Minecraft 更新日志 MCP
