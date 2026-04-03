from datetime import datetime
from html import escape
from typing import Any


class Email_Builder:
    def __init__(self, cfg: Any):
        self.cfg = cfg

    def build_header(self) -> str:
        return f"""
        <div style="padding: 24px 0 16px 0; border-bottom: 1px solid #e5e5e5;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <img src="cid:{escape(self.cfg.img.cid)}" style="height: 28px; width: auto; display: block;" alt="logo">
                <div style="font-size: 32px; color: #666; font-weight: 700;">GitHub 热门项目简报</div>
            </div>
        </div>
        """.strip()

    def build_report_period(self, repos: list[dict[str, Any]]) -> tuple[str | None, str | None]:
        if not repos:
            return None, None

        previous_dates = [
            item.get("previous_snapshot_date")
            for item in repos
            if item.get("previous_snapshot_date")
        ]
        current_dates = [
            item.get("current_snapshot_date")
            for item in repos
            if item.get("current_snapshot_date")
        ]

        if not previous_dates or not current_dates:
            return None, None

        return min(previous_dates), max(current_dates)

    def build_greeting(self, recipient_name: str | None = None, group_mode: bool = False) -> str:
        if group_mode:
            return "<p style='margin: 24px 0 0 0;'>各位好：</p>"
        if recipient_name:
            return f"<p style='margin: 24px 0 0 0;'>{escape(recipient_name)}，你好：</p>"
        return "<p style='margin: 24px 0 0 0;'>你好：</p>"

    def build_intro(self) -> str:
        return """
        <p>
            以下是本期 GitHub 热门项目简报。报告基于一段时间内项目的 Star 增长情况整理，
            并结合项目描述生成简要分析，帮助你快速了解近期值得关注的开源项目。
        </p>
        """.strip()

    def build_notice(self) -> str:
        return """
        <p>
            本邮件中的项目列表按 Star 增量排序，仅供技术趋势参考。
            如果你正在关注 AI、开发工具、自动化、数据工程或开源基础设施，这些项目可能值得留意。
        </p>
        """.strip()

    def build_repo_section(self, repos: list[dict[str, Any]]) -> str:
        if not repos:
            return """
            <div style="margin: 20px 0; padding: 16px; border: 1px solid #dddddd; border-radius: 8px;">
                <p style="margin: 0;">本期暂无可展示的项目数据。</p>
            </div>
            """.strip()

        blocks = []
        for idx, repo in enumerate(repos, start=1):
            name = escape(repo.get("full_name", "Unknown Repository"))
            url = escape(repo.get("html_url", ""))
            stars = repo.get("stars", 0)
            weekly_stars = repo.get("weekly_stars", 0)
            summary = escape(repo.get("summary", "暂无总结"))
            description = escape(repo.get("description") or "暂无描述")

            block = f"""
            <div style="margin: 20px 0; padding: 16px; border: 1px solid #dddddd; border-radius: 8px;">
                <h3 style="margin: 0 0 10px 0;">#{idx} {name}</h3>
                <p style="margin: 4px 0;"><b>项目链接：</b><a href="{url}">{url}</a></p>
                <p style="margin: 4px 0;"><b>当前 Stars：</b>{stars}</p>
                <p style="margin: 4px 0;"><b>新增 Stars：</b>{weekly_stars}</p>
                <p style="margin: 4px 0;"><b>项目描述：</b>{description}</p>
                <p style="margin: 8px 0 0 0; white-space: pre-wrap;"><b>项目总结：</b>{summary}</p>
            </div>
            """.strip()
            blocks.append(block)

        return "\n".join(blocks)

    def build_footer(self) -> str:
        contributor_url = escape(self.cfg.contributor.github_address)
        repo_url = escape(self.cfg.contributor.project_repo)
        data_source_url = escape(self.cfg.contributor.data_source)
        contributor_name = escape(self.cfg.contributor.name)
        current_year = datetime.now().year

        return f"""
        <p style="margin-top: 24px;">此致</p>
        <p style="margin-top: 8px;">GitHub 简报系统</p>

        <div style="margin-top:20px;padding-top:32px;border-top:1px solid #e5e5e5;text-align:center;color:#666;font-size:14px;">
            <div style="margin-top: 12px; text-align: center;">
                <img src="cid:{escape(self.cfg.img.cid)}" style="height:20px; opacity:0.8; margin-bottom: 16px;" alt="logo">
            </div>

            <div style="margin-bottom:8px;">
                <a href="{contributor_url}" style="color:#007aff;text-decoration:none;">贡献者</a>
                &nbsp;|&nbsp;
                <a href="{repo_url}" style="color:#007aff;text-decoration:none;">项目源码</a>
                &nbsp;|&nbsp;
                <a href="{data_source_url}" style="color:#007aff;text-decoration:none;">数据来源</a>
            </div>

            <div style="margin-top:8px;font-size:12px;color:#999;">
                Copyright © {current_year} GitHub Weekly Report by {contributor_name}. All rights reserved.
            </div>
        </div>
        """.strip()

    def build_html(
        self,
        repos: list[dict[str, Any]],
        recipient_name: str | None = None,
        group_mode: bool = False,
    ) -> str:
        start_date, end_date = self.build_report_period(repos)
        if start_date and end_date:
            report_period = f"{escape(start_date)} 至 {escape(end_date)}"
        else:
            report_period = "暂无数据"

        repo_section = self.build_repo_section(repos)

        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.8; color: #333; max-width: 760px; margin: 0 auto; padding: 20px;">
            {self.build_header()}
            {self.build_greeting(recipient_name=recipient_name, group_mode=group_mode)}
            {self.build_intro()}
            {self.build_notice()}
            <p><b>统计时间：</b>{report_period}</p>
            {repo_section}
            {self.build_footer()}
        </body>
        </html>
        """.strip()
