# HS Code MCP Server

> 让 AI Agent 会查海关编码、算进口税费 —— 8972 条 2026 税则，品目 100% 覆盖

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Data: 2026 Tariff](https://img.shields.io/badge/Data-2026%20Tariff-blue.svg)](https://gss.mof.gov.cn/)
[![HS4 Coverage: 100%](https://img.shields.io/badge/HS4%20Coverage-100%25-green.svg)]()
[![MCP Version: 1.x](https://img.shields.io/badge/MCP-1.x-orange.svg)]()
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)]()

将海关进出口税则封装为 MCP 工具，让 AI Agent 能够智能查询 HS 编码、计算进口税费、浏览商品分类。基于2026年最新税则数据，品目描述100%覆盖。

## 🎯 它解决什么问题

跨境卖家和报关行每天都在做的事：查 HS 编码、算进口关税和增值税、判断要不要许可证。以前靠人肉翻 200 多页税则，或者买付费 API。这个 MCP 让 AI Agent 直接查 8972 条 2026 年税则，返回编码、关税税率、增值税率和依据。

## 💡 为什么做

我自己是海关专业大三学生，做课设和实习时发现归类这件事对 AI 来说不难，但缺一份干净、结构化、能直接查的税则数据。所以把 2026 税则库拆成了 MCP 工具。

---

## ✨ 功能特性

| 工具 | 说明 |
|------|------|
| `search_hs_code` | 商品名称模糊搜索，返回Top N候选（品目描述加权 + 同义词词典 + HS编码前缀直匹配 + 8位精确编码优先） |
| `get_hs_detail` | 按HS编码查询详细信息（税率、监管条件、类别、品目描述、商品名称） |
| `calculate_import_tax` | 计算进口税费（关税 + 消费税 + 增值税），支持CIF价格和数量 |
| `get_categories` | 获取22个商品分类列表及对应品目范围 |
| `get_stats` | 数据库统计信息（条目数、品目数、分类数、数据版本） |

## 🔍 搜索算法

采用多维度加权评分，确保归类准确性：

| 匹配维度 | 权重 | 说明 |
|----------|------|------|
| 8位HS编码精确匹配 | +300分 | 同义词中包含完整8位编码时直接命中 |
| 4位品目编码匹配 | +100分 | 同义词中包含品目前缀时给该品目下所有编码加分 |
| 品目描述包含 | +100分 | 查询词出现在品目官方描述中 |
| 商品名称相似度 | 0-100分 | 基于SequenceMatcher的文本相似度 |
| 类别匹配 | +30分 | 查询词命中商品分类名称 |
| 子串匹配 | +50分 | 查询词与商品名称互为子串 |

**短词优化**：2字及以下搜索词采用精确key匹配，避免子串反向匹配导致错判（如"咖啡"不会匹配到"生咖啡豆"的编码）。

## 📊 数据规模

- **税则条目**：8,972 条（2026年版）
- **品目描述**：1,228 个（**100% 覆盖**，从财政部官方PDF提取）
- **商品分类**：22 类
- **同义词词典**：20+ 条常见商品映射（含HS编码前缀直匹配）
- **数据来源**：[财政部《2026年进出口税则》](https://gss.mof.gov.cn/gzdt/zhengcefabu/202512/P020251231607833453633.pdf)

## ✅ 测试结果

16个常见商品归类测试，**100% 通过**：

| 商品 | 正确HS编码 | 搜索结果 |
|------|-----------|----------|
| 口红 | 3304.1000 | ✅ |
| 笔记本电脑 | 8471.3090 | ✅ |
| 纯棉T恤 | 6109.1000 | ✅ |
| 咖啡（烘焙豆） | 0901.2100 | ✅ |
| 不锈钢锅 | 7323.9300 | ✅ |
| 红酒 | 2204.2100 | ✅ |
| 啤酒 | 2203.0000 | ✅ |
| 手机 | 8517.1300 | ✅ |
| 蓝牙耳机 | 8518.3000 | ✅ |
| 平板电脑 | 8471.3010 | ✅ |
| 充电宝 | 8507.6000 | ✅ |
| 运动鞋 | 6404.1100 | ✅ |
| 手表 | 9102.1100 | ✅ |
| 相机 | 8525.8920 | ✅ |
| 巧克力 | 1806.3200 | ✅ |
| 奶粉 | 0402.2100 | ✅ |

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/dcd887/hs-code-mcp-server.git
cd hs-code-mcp-server

# 安装依赖
pip install -r requirements.txt
```

### 配置到 Claude Desktop

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

重启 Claude Desktop 后即可使用。

### 配置到其他 MCP 客户端

支持任何兼容 MCP 1.x 协议的客户端，如：
- Cursor
- Trae
- 豆包
- Cline
- Continue.dev

## 📝 使用示例

### 搜索商品编码

```
用户：帮我查一下纯棉T恤的HS编码
Agent调用 search_hs_code(product_name="纯棉T恤")
返回：
{
  "status": "ok",
  "query": "纯棉T恤",
  "count": 5,
  "results": [
    {
      "hs_code": "6109.1000",
      "name": "棉制T恤衫、汗衫及其他背心",
      "import_tariff": 14,
      "vat_rate": 13,
      "score": 450.5
    },
    ...
  ]
}
```

### 计算进口税费

```
用户：进口100台笔记本电脑，CIF单价5000元，算一下税费
Agent调用 calculate_import_tax(hs_code="8471.3090", cif_price=5000, quantity=100)
返回：
{
  "status": "ok",
  "total_cif": 500000,
  "tariff": 0,
  "vat": 65000,
  "total_tax": 65000,
  "tax_rate_overall": 13.0
}
```

## 📁 项目结构

```
hs-code-mcp-server/
├── server.py              # MCP Server 主程序
├── requirements.txt       # Python 依赖
├── README.md              # 项目说明
├── LICENSE                # MIT 协议
├── .gitignore             # Git 忽略文件
├── data/
│   ├── hs_codes_full.json     # 完整税则数据（8972条）
│   └── hs4_descriptions.json  # 品目描述（1228个）
├── tests/
│   └── test_search.py     # 搜索算法测试
└── examples/
    └── claude_config.json # Claude Desktop 配置示例
```

## ⚠️ 免责声明

本工具提供的HS编码、税率及监管条件**仅供参考，不构成法律意见或报关依据**。商品归类的最终认定以海关官方裁定为准。建议对重要商品向海关申请预归类裁定。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

- 发现归类错误？请提交 Issue 说明商品名称和正确编码
- 想添加同义词？修改 `server.py` 中的 `SYNONYMS` 字典
- 数据更新？每年税则更新后替换 `data/` 目录下的JSON文件

## 📮 联系方式

- 邮箱：hq15012670635@163.com
- GitHub：https://github.com/dcd887
