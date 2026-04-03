from pathlib import Path
from typing import Any

from omegaconf import OmegaConf

from utils.emailer import Emailer
from utils.fetcher import Github_Fetcher
from utils.html_maker import Email_Builder
from utils.snapshot import Repo_Snapshot
from utils.summarizer import Client_Analysis


OUTPUT_DIR = Path("output")


def sanitize_filename(name: str) -> str:
    invalid_chars = '<>:"/\\|?*'
    sanitized = "".join("_" if char in invalid_chars else char for char in name).strip()
    return sanitized or "recipient"


def build_services(cfg: Any) -> dict[str, Any]:
    return {
        "fetcher": Github_Fetcher(cfg),
        "snapshot": Repo_Snapshot(cfg),
        "analyzer": Client_Analysis(cfg),
        "builder": Email_Builder(cfg),
        "emailer": Emailer(cfg),
    }


def collect_report_data(fetcher: Github_Fetcher, snapshot: Repo_Snapshot) -> dict[str, Any]:
    repos = fetcher.fetch_candidate_repos()
    if not repos:
        raise RuntimeError("未获取到任何 GitHub 仓库数据。")

    snapshot.save_snapshot(repos)

    current_date = snapshot.get_latest_snapshot_date()
    if not current_date:
        raise RuntimeError("快照保存后仍未找到最新快照日期。")

    previous_date = snapshot.get_previous_snapshot_date(current_date)
    if not previous_date:
        raise RuntimeError(f"当前日期 {current_date} 没有可比较的上一期快照。")

    diffs = snapshot.get_top_growth_repos_safe(
        current_date=current_date,
        previous_date=previous_date,
    )
    if not diffs.get("ok"):
        raise RuntimeError(diffs.get("message", "增长仓库分析失败。"))

    if not diffs.get("results"):
        raise RuntimeError("没有可用于生成报告的增长仓库结果。")

    return diffs


def populate_summaries(analyzer: Client_Analysis, diffs: dict[str, Any]) -> None:
    time_delta = diffs.get("time_delta")
    if not time_delta:
        raise RuntimeError("缺少 time_delta，无法生成项目摘要。")

    for repo in diffs["results"]:
        try:
            repo["summary"] = analyzer.get_response(repo, time_delta)
        except Exception as exc:
            repo_name = repo.get("full_name", "unknown")
            print(f"[warn] 项目 {repo_name} 摘要生成失败: {exc}")
            repo["summary"] = "摘要生成失败，请稍后重试。"


def send_reports(builder: Email_Builder, emailer: Emailer, repos: list[dict[str, Any]], recipients: Any) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    for recipient in recipients:
        recipient_name = recipient["name"]
        email_address = recipient["email_address"]
        html_content = builder.build_html(repos, recipient_name)

        output_path = OUTPUT_DIR / f"{sanitize_filename(recipient_name)}_report.html"
        output_path.write_text(html_content, encoding="utf-8")

        try:
            emailer.email_send(html_content, email_address)
            print(f"[info] 已生成并发送报告: {recipient_name} <{email_address}>")
        except Exception as exc:
            print(f"[warn] 邮件发送失败: {recipient_name} <{email_address}>: {exc}")


def main() -> None:
    cfg = OmegaConf.load("config.yaml")
    services = build_services(cfg)

    diffs = collect_report_data(services["fetcher"], services["snapshot"])
    populate_summaries(services["analyzer"], diffs)
    send_reports(
        services["builder"],
        services["emailer"],
        diffs["results"],
        cfg.recipient,
    )


if __name__ == "__main__":
    main()
