"""
Loop 主循环 — XHS Loop Engineer
小红书内容自动化工作流

Loop Engineering 核心理念：
  不要手动提示 Agent。设计一个系统自动调度 Agent。
"""

import yaml
import json
import time
from pathlib import Path
from datetime import datetime

from agents.topic_finder import TopicFinder
from agents.content_writer import ContentWriter
from agents.quality_checker import QualityChecker
from agents.archiver import Archiver


class XHSLoopEngineer:
    def __init__(self, config_path: str = "config/schedule.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        self.topic_finder = TopicFinder(config_path)
        self.content_writer = ContentWriter(config_path)
        self.quality_checker = QualityChecker()
        self.archiver = Archiver(config_path)

        self.state_file = Path("state/loop_state.json")
        self.state = self._load_state()

    def _load_state(self) -> dict:
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {"iterations": 0, "articles_generated": 0}

    def _save_state(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state["iterations"] = self.state.get("iterations", 0) + 1
        self.state_file.write_text(json.dumps(self.state, indent=2, ensure_ascii=False))

    def verify_completion(self) -> tuple[bool, str]:
        """
        验证本轮是否完成。
        Loop Engineering 的核心：用验证函数驱动循环，而不是无限运行。
        """
        # 检查是否已达到今日配额
        today = datetime.now().strftime("%Y-%m-%d")
        last_run = self.state.get("last_run_date", "")
        if last_run == today:
            return True, f"今日已完成（{today}），等待明天触发"

        # 检查是否有待处理任务
        pending_dir = Path("output")
        pending = list(pending_dir.glob("*.md")) if pending_dir.exists() else []
        if pending:
            return False, f"有 {len(pending)} 个待发布内容"

        return False, "等待用户选择选题"

    def step_1_find_topics(self) -> dict:
        """Step 1: 选题发现"""
        print("\n🔍 Agent 1: 选题发现...")
        result = self.topic_finder.run()
        print(f"   {result['message']}")
        return result

    def step_2_user_select(self, topic_result: dict) -> str:
        """Step 2: 用户选择选题（人工介入点）"""
        print("\n⚡ 请在以下选题中选择：")
        print(f"   选题池共 {len(topic_result['topic_pool'])} 个待写选题")
        for i, topic in enumerate(topic_result["topic_pool"][:5], 1):
            print(f"   {i}. {topic}")

        choice = input("\n👉 输入选题编号（或输入新选题）: ").strip()

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(topic_result["topic_pool"]):
                return topic_result["topic_pool"][idx]
        except ValueError:
            pass

        return choice  # 用户输入的新选题

    def step_3_generate_content(self, topic: str) -> dict:
        """Step 3: 内容生成"""
        print(f"\n✍️ Agent 2: 内容生成...")
        print(f"   选题: {topic}")

        # 判断类型
        article_type = "deep_tech" if any(
            kw in topic.lower() for kw in ["源码", "架构", "深度", "拆解", "技术"]
        ) else "xiaobai"

        result = self.content_writer.run(topic, article_type)
        print(f"   Prompt 已构建，类型: {article_type}")

        return {**result, "article_type": article_type}

    def step_4_verify_quality(self, content: str, article_type: str) -> dict:
        """Step 4: 质量验证"""
        print(f"\n🔍 Agent 3: 质量验证...")
        result = self.quality_checker.run(content, article_type)

        if result["pass"]:
            print(f"   ✅ 通过 (评分: {result['score']}/10)")
        else:
            print(f"   ❌ 未通过 (评分: {result['score']}/10)")
            for issue in result["issues"]:
                print(f"      - {issue}")

        return result

    def step_5_archive(self, content: str, topic: str, article_type: str) -> dict:
        """Step 5: 归档通知"""
        print(f"\n📦 Agent 4: 归档...")
        result = self.archiver.run(content, topic, article_type)
        print(f"   {result['message']}")
        return result

    def run_loop(self, max_iterations: int = 3):
        """
        主循环。

        Loop Engineering 的核心结构：
        1. 选题 → 2. 确认 → 3. 生成 → 4. 验证 → 5. 归档
        如果验证不通过 → 反馈 → 重新生成（最多 3 轮）
        """
        print("=" * 50)
        print("🔄 XHS Loop Engineer 启动")
        print(f"   当前迭代: {self.state.get('iterations', 0)}")
        print(f"   已生成文章: {self.state.get('articles_generated', 0)}")
        print("=" * 50)

        # Step 1: 选题发现
        topics = self.step_1_find_topics()

        # Step 2: 用户确认
        selected_topic = self.step_2_user_select(topics)

        # Step 3-5: 生成 → 验证 → 归档（带重试循环）
        for attempt in range(max_iterations):
            print(f"\n--- 第 {attempt + 1}/{max_iterations} 轮 ---")

            # Step 3: 生成
            gen_result = self.step_3_generate_content(selected_topic)

            # 获取实际内容（从用户输入）
            print("\n📋 请将 Claude 生成的内容粘贴到下方（输入 END 结束）:")
            lines = []
            while True:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
            content = "\n".join(lines)

            # Step 4: 验证
            verify_result = self.step_4_verify_quality(content, gen_result["article_type"])

            if verify_result["pass"]:
                # Step 5: 归档
                archive_result = self.step_5_archive(
                    content, selected_topic, gen_result["article_type"]
                )
                self.state["articles_generated"] = (
                    self.state.get("articles_generated", 0) + 1
                )
                self.state["last_run_date"] = datetime.now().strftime("%Y-%m-%d")
                self._save_state()

                print(f"\n✅ Loop 完成！")
                print(f"   文件: {archive_result['filepath']}")
                return archive_result
            else:
                print(f"\n🔄 验证未通过，进入下一轮重试...")
                if attempt < max_iterations - 1:
                    feedback = input("💬 输入修改意见（回车跳过）: ").strip()
                    if feedback:
                        self.state["feedback"] = feedback

        print(f"\n⚠️ 达到最大迭代次数 ({max_iterations})，请手动处理")
        return {"status": "max_iterations_reached"}


def main():
    loop = XHSLoopEngineer()
    result = loop.run_loop()
    print(f"\n结果: {json.dumps(result, indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
