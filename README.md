# HS Code MCP Server

> 海关商品归类智能体工具 — 基于2026年进出口税则的MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Data: 2026 Tariff](https://img.shields.io/badge/Data-2026%20Tariff-blue.svg)](https://gss.mof.gov.cn/)
[![HS4 Coverage: 100%](https://img.shields.io/badge/HS4%20Coverage-100%25-green.svg)]()

将海关进出口税则封装为 MCP（Model Context Protocol）工具，让 AI Agent 能够智能查询 HS 编码、计算进口税费、浏览商品分类。

## ✨ 功能特性

| 工具 | 说明 |
|------|------|
| `search_hs_code` | 商品名称模糊搜索，返回Top N候选（含品目描述加权+同义词+HS前缀直匹配） |
| `get_hs_detail` | 按HS编码查询详细信息（税率、监管条件、类别、品目描述） |
| `calculate_import_tax` | 计算进口税费（关税+消费税+增值税），支持CIF价格和数量 |
| `get_categories` | 获取22个商品分类列表 |
| `get_stats` | 数据库统计信息 |

## 📊 数据规模

- **税则条目**：8,972 条（2026年版）
- **品目描述**：1,228 个（100% 覆盖，从财政部官方PDF提取）
- **商品分类**：22 类
- **数据来源**：[财政部《2026年进出口税则》](https://gss.mof.gov.cn/gzdt/zhengcefabu/202512/P020251231607833453633.pdf)

## 🚀 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 运行

```bash
python server.py
```

### 在 Claude Desktop / 豆包 / Cursor 中配置

在 MCP 配置文件中添加：

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

### 搜索商品

```
用户：帮我查一下口红的HS编码
Agent调用 search_hs_code(product_name="口红")
→ 返回 3304.1000 唇用化妆品，关税5%，增值税13%
```

### 计算税费

```
用户：进口10台笔记本电脑，CIF单价5000元，要交多少税？
Agent调用 calculate_import_tax(hs_code="8471.3090", cif_price=5000, quantity=10)
→ 关税0元（零关税），增值税6500元，总计6500元
```

### 查询编码详情

```
用户：8517.1300是什么商品？
Agent调用 get_hs_detail(hs_code="8517.1300")
→ 返回手机详情：关税0%，增值税13%，类别第十六类
```

## 🏗️ 项目结构

```
hs-code-mcp-server/
├── server.py              # MCP Server 主程序（FastMCP）
├── requirements.txt       # Python 依赖
├── README.md              # 项目说明
├── .gitignore             # Git 忽略
└── data/
    ├── hs_codes_full.json     # 8972条税则数据
    └── hs4_descriptions.json  # 1228个品目描述
```

## ⚠️ 免责声明

- 本工具数据基于2026年进出口税则，**仅供参考，不构成法律意见**
- 实际归类和税费以海关官方裁定为准
- 税率计算基于最惠国税率，未考虑协定税率、特惠税率、反倾销税等特殊情况
- 建议结合海关总署公告、归类决定等官方文件使用

## 📄 License

MIT License

## 👤 作者

黄谦 | 上海海关学院 海关稽查专业 | GitHub: [dcd887](https://github.com/dcd887)

## 🔗 相关项目

- [税则通](https://github.com/dcd887) — 微信小程序版HS编码归类工具
- [稽查眼](https://github.com/dcd887) — 海关稽查风险自查工具
- [mc-mcp-toolchain](https://github.com/dcd887) — Minecraft MCP 工具链
