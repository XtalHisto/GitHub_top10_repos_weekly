from typing import Any

from openai import OpenAI


class Client_Analysis:
    def __init__(self, cfg: Any):
        self.cfg = cfg
        self.agent = OpenAI(
            api_key=cfg.client.api_key,
            base_url=cfg.client.base_url,
        )
        self.thinking = False

    def create_prompt(self, repo: dict[str, Any], time_delta: dict[str, int]) -> str:
        name = repo.get("full_name", "Unknown Repository")
        desc = repo.get("description") or "暂无描述"
        stars = repo.get("stars", 0)
        weekly_stars = repo.get("weekly_stars", 0)
        url = repo.get("html_url", "")
        language = repo.get("language") or "未知"
        weeks = time_delta.get("weeks", 0)
        days = time_delta.get("days", 0)

        return f"""
你是一名技术趋势分析助手，请基于下面的 GitHub 项目信息，用简洁中文输出一段总结。

项目信息：
- 名称：{name}
- 描述：{desc}
- 当前 Stars：{stars}
- 近 {weeks} 周 {days} 天 Star 增量：{weekly_stars}
- 主要语言：{language}
- 链接：{url}

输出要求：
1. 用 2 到 3 句话说明这个项目是做什么的。
2. 结合项目类型和近期 Star 增长，分析它最近受欢迎的可能原因。
3. 最后单独补一句“适合谁使用：...”
4. 不要使用 Markdown 列表。
""".strip()

    def get_response(self, repo: dict[str, Any], time_delta: dict[str, int]) -> str:
        prompt = self.create_prompt(repo, time_delta)

        response = self.agent.chat.completions.create(
            model=self.cfg.client.model[0].name,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            extra_body={
                "enable_thinking": self.thinking,
                "thinking_budget": 81920,
            },
        )

        answer_content = ""
        for chunk in response:
            if not getattr(chunk, "choices", None):
                continue

            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if isinstance(content, str):
                answer_content += content
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        answer_content += item.get("text", "")

        final_answer = answer_content.strip()
        if not final_answer:
            raise RuntimeError("模型返回了空摘要。")

        return final_answer

    def create_text(self, repo: dict[str, Any], time_delta: dict[str, int] | None = None) -> str:
        summary = (
            self.get_response(repo, time_delta)
            if time_delta is not None
            else repo.get("summary", "")
        )
        return (
            f"   {repo.get('full_name', 'Unknown Repository')}\n"
            f"   Stars: {repo.get('stars', 0)}\n"
            f"   Link: {repo.get('html_url', '')}\n"
            f"   Summary: {summary}\n"
        )
