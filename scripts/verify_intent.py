"""Standalone check for the intent recognizer (no httpx required).

Exercises the local char-bigram matching branch and the clarify fallback
(low confidence + no LLM provider available). Two groups:
  - EXACT: queries that mirror the schema examples (sanity check)
  - PARAPHRASE: reworded queries NOT in the examples (generalization check)

    py scripts/verify_intent.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

from new.intent_recognizer import IntentRecognizer  # noqa: E402

rec = IntentRecognizer()
print(f"loaded intents: {len(rec._intents)}  local_threshold={rec._local_threshold}  global={rec._global_confidence}")

EXACT = [
    ("上月处理了多少吨", "ad_hoc_analysis"),
    ("画一个来源结构饼图", "visualization"),
    ("你好", "chitchat"),
    ("你能做什么", "help_guidance"),
    ("对比一下华东和华南的回收量", "comparison"),
    ("近半年入库量趋势怎么样", "trend"),
    ("把华东区的批次都列出来", "data_fetch"),
    ("帮我分析一下本月华东区的销售情况", "thematic_analysis"),
    ("总结一下我们刚才聊的结论", "summarization"),
    ("按目前趋势下个月大概能处理多少", "data_inference"),
    ("为什么上星期成本突然涨了", "anomaly_rootcause"),
    ("生成一份本月运营报告", "reporting_export"),
    ("asdkjfh lkj 随便说说", "clarify_abstain"),
]

PARAPHRASE = [
    ("这个月到底赚了多少钱", "ad_hoc_analysis"),
    ("做个图看看各树种的占比", "visualization"),
    ("华东和华南哪个更划算", "comparison"),
    ("明年估计能回收多少吨", "data_inference"),
    ("成本怎么突然就上去了", "anomaly_rootcause"),
    ("写个周报给我", "reporting_export"),
    ("列出 construction 来源的批次", "data_fetch"),
    ("天气真好啊", "chitchat"),
    ("这堆数据到底想说明什么", "summarization"),
    ("给我讲讲你能分析啥", "help_guidance"),
    ("把最近表现最差的批次挑出来", "data_fetch"),
    ("两个来源类型哪个利润高", "comparison"),
]


async def run(group, name):
    ok = 0
    for q, exp in group:
        m = await rec.recognize(q, provider=None)
        hit = m.intent_id == exp
        if hit:
            ok += 1
        flag = "OK " if hit else "XX "
        warn = " <-- below local_threshold, would route to LLM" if m.confidence < rec._local_threshold else ""
        print(f"[{flag}] {q!r:32} -> {m.intent_id:18} conf={m.confidence:.3f} src={m.source} exp={exp}{warn}")
    print(f"{name}: {ok}/{len(group)} matched\n")


async def main() -> None:
    await run(EXACT, "EXACT")
    await run(PARAPHRASE, "PARAPHRASE")


if __name__ == "__main__":
    asyncio.run(main())
