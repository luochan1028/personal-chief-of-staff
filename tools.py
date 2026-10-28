"""工具箱：个人 AI 参谋可调用的工具（全部读写本地演示数据，不联网、不含真实个人信息）。"""

import json
import os


class ToolBox:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def _load(self, name, default):
        path = os.path.join(self.data_dir, name)
        if not os.path.exists(path):
            return default
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _save(self, name, data):
        with open(os.path.join(self.data_dir, name), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def call(self, name, args):
        fn = getattr(self, "tool_" + name, None)
        if fn is None:
            return {"ok": False, "error": "unknown tool: " + name}
        return fn(args)

    def tool_get_schedule(self, args):
        day = args.get("day", "tomorrow")
        sched = self._load("schedule.json", {})
        return {"ok": True, "day": day, "entries": sched.get(day, [])}

    def tool_list_todos(self, args):
        return {"ok": True, "todos": self._load("todos.json", [])}

    def tool_draft_quiz(self, args):
        """课前小测草稿：模板生成（演示用，正式版可接题库或大模型）。"""
        topic = args.get("topic", "C语言基础")
        n = int(args.get("n", 3))
        bank = [
            ("以下哪个是 C 语言的循环语句？", ["if", "for", "struct", "return"], "for"),
            ("for (int i = 0; i < 3; i++) 一共循环几次？", ["2", "3", "4", "0"], "3"),
            ("指针变量存放的是什么？", ["数值", "地址", "字符", "函数"], "地址"),
            ("break 在循环中的作用是？", ["跳过本次", "结束循环", "暂停", "报错"], "结束循环"),
        ]
        quiz = [{"q": q, "options": o, "answer": a} for q, o, a in bank[:n]]
        self._save("quiz_draft.json", {"topic": topic, "quiz": quiz})
        return {"ok": True, "topic": topic, "count": len(quiz), "saved": "quiz_draft.json"}

    def tool_create_note(self, args):
        notes = self._load("notes.json", [])
        notes.append({"title": args.get("title", ""), "body": args.get("body", "")})
        self._save("notes.json", notes)
        return {"ok": True, "note_title": args.get("title", ""), "total_notes": len(notes)}

    def tool_add_reminder(self, args):
        rems = self._load("reminders.json", [])
        rems.append({"text": args.get("text", ""), "time": args.get("time", "")})
        self._save("reminders.json", rems)
        return {"ok": True, "reminder": args, "total_reminders": len(rems)}
