"""个人 AI 参谋 · 原型骨架（迪拜 Create AI Agents Championship，Best Personal AI Agent 方向）

设计要点：
- 零外部依赖（只用 Python 标准库），无需 API Key 即可跑通演示模式。
- 规划器分两档：demo 模式用内置规则规划（不冒充大模型）；设置 LLM_API_KEY +
  LLM_BASE_URL 后可走 OpenAI 兼容接口做真实规划，失败自动回落到规则规划。
- 所有工具调用记入执行轨迹（trace），演示结尾输出可量化指标：人工干预次数、任务完成率。
- 数据全部是演示用的虚构数据（data/ 目录），不含任何真实个人信息。
"""

import json
import os
import time
from tools import ToolBox


class PersonalAgent:
    """一句话指令 -> 自主规划 -> 工具执行 -> 成果汇总。"""

    def __init__(self, data_dir):
        self.tools = ToolBox(data_dir)
        self.trace = []
        self.interventions = 0  # 人工干预次数：自主运行恒为 0

    def _demo_plan(self, goal):
        """规则规划：识别“准备明天”类目标，生成固定多步骤计划。"""
        g = goal.lower()
        if "明天" in goal or "tomorrow" in g or "准备" in goal:
            return [
                ("get_schedule", {"day": "tomorrow"}, "查看明日课表与日程"),
                ("list_todos", {}, "列出待办事项"),
                ("draft_quiz", {"topic": "C语言循环", "n": 3}, "生成课前小测草稿"),
                ("create_note", {"title": "明日计划", "body": "见执行结果汇总"}, "整理明日计划备忘"),
                ("add_reminder", {"text": "明日计划已就绪，出门前复核", "time": "07:30"}, "设置出门前提醒"),
            ]
        return [("list_todos", {}, "列出待办事项")]

    def _llm_plan(self, goal):
        """真实大模型规划（需环境变量，未配置或调用失败时返回 None）。"""
        api_key = os.environ.get("LLM_API_KEY", "")
        base_url = os.environ.get("LLM_BASE_URL", "")
        model = os.environ.get("LLM_MODEL", "")
        if not (api_key and base_url and model):
            return None
        try:
            import urllib.request
            payload = json.dumps({
                "model": model,
                "messages": [
                    {"role": "system", "content": (
                        "你是个人AI参谋的规划器。把用户目标拆解为工具调用步骤，"
                        "只输出 JSON 数组，每项含 tool 与 args。可用工具："
                        "get_schedule, list_todos, draft_quiz, create_note, add_reminder。")},
                    {"role": "user", "content": goal},
                ],
                "temperature": 0.2,
            }).encode()
            req = urllib.request.Request(
                base_url.rstrip("/") + "/chat/completions", data=payload,
                headers={"Authorization": "Bearer " + api_key,
                         "Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                text = json.loads(resp.read())["choices"][0]["message"]["content"]
            steps = json.loads(text)
            return [(s["tool"], s.get("args", {}), s["tool"]) for s in steps]
        except Exception as exc:  # 调用失败不中断演示，回落规则规划
            self.trace.append({"step": "llm_plan_failed", "detail": str(exc)})
            return None

    def run(self, goal):
        """执行一轮自主任务，返回执行报告。"""
        started = time.time()
        plan = self._llm_plan(goal) or self._demo_plan(goal)
        results = []
        for tool_name, args, label in plan:
            out = self.tools.call(tool_name, args)
            self.trace.append({"step": label, "tool": tool_name, "result": out})
            results.append(out)
        elapsed = round(time.time() - started, 1)
        return {
            "goal": goal,
            "steps_planned": len(plan),
            "steps_done": len(results),
            "interventions": self.interventions,
            "elapsed_sec": elapsed,
            "results": results,
            "trace": self.trace,
        }
