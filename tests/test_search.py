"""
HS Code MCP Server 搜索算法测试
运行：python tests/test_search.py
（无需安装mcp依赖，自动mock）
"""
import sys
import os

# Mock mcp模块，使测试无需安装依赖
from unittest.mock import MagicMock
sys.modules['mcp'] = MagicMock()
sys.modules['mcp.server'] = MagicMock()
sys.modules['mcp.server.fastmcp'] = MagicMock()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import fuzzy_search, HS_CODE_INDEX, _get_hs4

# 测试用例：(商品名, 期望HS编码前缀, 描述)
TEST_CASES = [
    ("口红", "3304.1000", "唇用化妆品"),
    ("笔记本电脑", "8471.3090", "便携式自动数据处理设备"),
    ("纯棉T恤", "6109.1000", "棉制T恤衫"),
    ("咖啡", "0901", "咖啡（未浸除/已浸除咖啡碱）"),
    ("不锈钢锅", "7323", "不锈钢制餐桌厨房用具"),
    ("红酒", "2204", "葡萄酒"),
    ("啤酒", "2203", "麦芽酿造啤酒"),
    ("手机", "8517.1300", "智能手机"),
    ("蓝牙耳机", "8518.3000", "无线耳机"),
    ("平板电脑", "8471.3010", "平板式电脑"),
    ("充电宝", "8507.6000", "锂离子蓄电池"),
    ("运动鞋", "6404", "运动鞋靴"),
    ("手表", "9102", "手表"),
    ("相机", "8525", "照相机"),
    ("巧克力", "1806", "巧克力及其他含可可制品"),
    ("奶粉", "0402", "浓缩乳粉"),
]

def run_tests():
    print("=" * 60)
    print("HS Code MCP Server 搜索算法测试")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for query, expected_prefix, desc in TEST_CASES:
        results = fuzzy_search(query, top_n=3)
        if not results:
            print(f"❌ {query}: 无结果（期望 {expected_prefix} - {desc}）")
            failed += 1
            continue
        
        top1 = results[0]
        top1_code = top1["hs_code"]
        # 检查top1是否匹配期望前缀
        if top1_code.startswith(expected_prefix.replace(".", "")[:4]) or top1_code == expected_prefix:
            print(f"✅ {query}: {top1_code} (分数: {top1['score']}) - {top1['name'][:30]}")
            passed += 1
        else:
            # 检查前3个结果中是否有匹配
            found = any(r["hs_code"].startswith(expected_prefix.replace(".", "")[:4]) for r in results)
            if found:
                print(f"⚠️  {query}: Top1={top1_code}, 但前3结果中有匹配（期望 {expected_prefix}）")
                passed += 1
            else:
                print(f"❌ {query}: Top1={top1_code}（期望 {expected_prefix} - {desc}）")
                print(f"   前3结果: {[r['hs_code'] for r in results]}")
                failed += 1
    
    print("=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败, 共 {len(TEST_CASES)} 项")
    print(f"通过率: {passed/len(TEST_CASES)*100:.1f}%")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
