"""演示脚本：输入一句话，智能体自主完成“准备明天”全流程并输出量化指标。

运行：python3 demo.py
无需 API Key（演示模式）。设置 LLM_API_KEY / LLM_BASE_URL / LLM_MODEL 后走真实规划。
演示视频可直接按本脚本的输出顺序拍：指令 -> 规划 -> 工具执行 -> 成果 + 指标。
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent import PersonalAgent

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")


def main():
    agent = PersonalAgent(DATA)
    report = agent.run("帮我准备明天")
    print("=== 个人AI参谋 · 演示 ===")
    print("目标：", report["goal"])
    print()
    for i, step in enumerate(report["trace"], 1):
        if step["step"] == "llm_plan_failed":
            print(f"[注] 大模型规划调用失败，已回落规则规划：{step['detail']}")
            continue
        print(f"步骤{i} [{step['tool']}] {step['step']}")
        print("  ->", json.dumps(step["result"], ensure_ascii=False))
    print()
    print("=== 量化指标（演示结尾字幕用）===")
    print(f"人工干预次数：{report['interventions']}")
    print(f"任务完成率：{report['steps_done']}/{report['steps_planned']} 步")
    print(f"耗时：{report['elapsed_sec']} 秒（人工约 40 分钟）")
    print("产物：data/notes.json（明日计划备忘）、data/quiz_draft.json（课前小测）、"
          "data/reminders.json（提醒）")


if __name__ == "__main__":
    main()
