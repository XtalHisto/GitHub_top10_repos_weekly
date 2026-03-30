from datetime import datetime
from omegaconf import OmegaConf


class Email_Builder:
    def __init__(self, cfg):
        self.cfg = cfg
        self.recipient_name = self.cfg.recipient.name
        

    def build_header(self) -> str:
        return f"""
        <div style="padding: 24px 0 20px 0; border-bottom: 1px solid #e5e5e5;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <img src={self.cfg.img.path} style="height: 42px; width: auto; display: block;">
            <div style="font-size: 48px; color: #999; font-weight: 300; line-height: 1;">
                本周周报
            </div>
        </div>
    </div>
        """.strip()
    
    # 时间区间
    def build_report_period(self, repos: list[dict]) -> str:
        if not repos:
            return "统计时间：暂无数据"

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

        if previous_dates and current_dates:
            self.start_date = min(previous_dates)
            self.end_date = max(current_dates)
            return f"统计时间：{self.start_date} 至 {self.end_date}"

        return "统计时间：暂无数据"



    def build_greeting(self) -> str:
        return f"<p style='margin: 24px 0 0 0;'>{self.recipient_name}，你好：</p>"

    def build_intro(self) -> str:
        return """
        <p>
            以下是本周GitHub热门项目周报。该报告基于最近一周内项目的star增长情况整理，
            并结合项目描述生成简要总结，方便你快速了解近期值得关注的开源项目。
        </p>
        """.strip()

    def build_notice(self) -> str:
        return """
        <p>
            本邮件中的项目榜单按“最近7天star增量”排序，仅用于技术信息参考。
            若你正在跟踪AI、开发工具、自动化、数据工程或开源基础设施方向，可以重点关注这些项目。
        </p>
        """.strip()



 # 仓库描述分块
    def build_repo_section(self, repos: list[dict]) -> str:
        '''
    repos = []
        for row in rows:
            repos.append({
                "repo_id": row["repo_id"],
                "full_name": row["full_name"],
                "html_url": row["html_url"],
                "description": row["description"],
                "language": row["language"],
                "stars": row["current_stars"],
                "previous_stars": row["previous_stars"],
                "weekly_stars": row["weekly_growth"],
                "current_snapshot_date": row["current_snapshot_date"],
                "previous_snapshot_date": row["previous_snapshot_date"],
            })
    '''
        
        blocks = []

        for idx, repo in enumerate(repos, start=1):
            name = repo.get("full_name", "")
            url = repo.get("html_url", "")
            stars = repo.get("stars", 0)
            weekly_stars = repo.get("weekly_stars", 0)
            summary = repo.get("summary", "暂无总结")
            description = repo.get("description", "暂无描述")
            

            block = f"""
            <div style="margin: 20px 0; padding: 16px; border: 1px solid #dddddd; border-radius: 8px;">
                <h3 style="margin: 0 0 10px 0;">#{idx} {name}</h3>
                <p style="margin: 4px 0;"><b>项目链接：</b><a href="{url}">{url}</a></p>
                <p style="margin: 4px 0;"><b>当前star：</b>{stars}</p>
                <p style="margin: 4px 0;"><b>本周新增star：</b>{weekly_stars}</p>
                <p style="margin: 4px 0;"><b>项目描述：</b>{description}</p>
                <p style="margin: 8px 0 0 0;"><b>项目总结：</b>{summary}</p>
            </div>
            """
            blocks.append(block)

        return "\n".join(blocks)



    def build_footer(self) -> str:
        contributor_url = self.cfg.contributor.github_address
        repo_url = self.cfg.contributor.project_repo
        data_source_url = self.cfg.contributor.data_source

        return f"""
            <p style="margin-top: 24px;">
            此致<br>
            敬礼
            </p>

            <p style="margin-top: 8px;">
                GitHub 周报系统
            </p>

        <div style="margin-top:20px;padding-top:60px;border-top:1px solid #e5e5e5;text-align:center;color:#666;font-size:14px;">
            

        <div style="margin-top: 30px; text-align: center;">
            <img src={self.cfg.img.path} style="height:20px; opacity:0.8;margin-bottom: 16px;">
        </div>

        
            <div style="margin-bottom:8px;">
                <a href="{contributor_url}" style="color:#007aff;text-decoration:none;">贡献者</a>
                &nbsp;·&nbsp;
                <a href="{repo_url}" style="color:#007aff;text-decoration:none;">项目源码</a>
                &nbsp;·&nbsp;
                <a href="{data_source_url}" style="color:#007aff;text-decoration:none;">数据来源</a>
            </div>

            <div style="margin-top:8px;font-size:12px;color:#999;">
                Copyright © {datetime.now().year} GitHub Weekly Report by {self.cfg.contributor.name}. All rights reserved.
            </div>

        </div>
        """.strip()


    def build_html(self, repos: list[dict]) -> str:
        repo_section = self.build_repo_section(repos)
        date = self.build_report_period(repos)
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.8; color: #333; max-width: 760px; margin: 0 auto; padding: 20px;">
            {self.build_header()}
            {self.build_greeting()}
            {self.build_intro()}
            {self.build_notice()}
            <p><b>统计时间：</b>{self.start_date} 至 {self.end_date}</p>
            {repo_section}
            {self.build_footer()}
        </body>
        </html>
        """.strip()
    

if __name__ == "__main__":

    cfg = OmegaConf.load("config.yaml")
    fake_repos = [
    {
        "name": "langchain-ai/langchain",
        "html_url": "https://github.com/langchain-ai/langchain",
        "stars": 102345,
        "weekly_stars": 5230,
        "description": "Building applications with LLMs through composability.",
        "summary": "这是一个面向大语言模型应用开发的框架，帮助开发者快速构建具备检索、代理和工作流能力的 AI 应用。本周增长较快，主要因为 LLM 应用开发需求持续上升。适合谁：AI 应用开发者。",
        "current_snapshot_date": '2026-03-28',
        "previous_snapshot_date": '2026-03-21',
    },
    {
        "name": "microsoft/autogen",
        "html_url": "https://github.com/microsoft/autogen",
        "stars": 56789,
        "weekly_stars": 4100,
        "description": "A framework for building multi-agent AI applications.",
        "summary": "这是一个多智能体 AI 应用框架，适合构建复杂协作式任务系统。近期受欢迎与多 Agent 工作流热度上升有关。适合谁：多智能体系统开发者。",
        "current_snapshot_date": '2026-03-28',
        "previous_snapshot_date": '2026-03-21',
    }
]

    builder = Email_Builder(cfg)

    html_content = builder.build_html(fake_repos)

    with open("weekly_report_email.html", "w", encoding="utf-8") as f:
        f.write(html_content)

