import sqlite3
import requests
from datetime import datetime, timedelta
from omegaconf import OmegaConf
from typing import Any
from utils.fetcher import Github_Fetcher
from utils.summarizer import Client_Analysis


class Repo_Snapshot:
    def __init__(self, cfg):
        self.db_path = cfg.app.db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS repo_snapshots (
            repo_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            html_url TEXT NOT NULL,
            description TEXT DEFAULT '',
            language TEXT DEFAULT '',
            stars INTEGER NOT NULL,
            snapshot_date TEXT NOT NULL,
            PRIMARY KEY (repo_id, snapshot_date)
        )
        """)

        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_snapshot_date
        ON repo_snapshots(snapshot_date)
        """)

        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_repo_id
        ON repo_snapshots(repo_id)
        """)

        conn.commit()
        conn.close()

    def save_snapshot(self, repos: list[dict[str, Any]]) -> None:
        """
        批量保存某一次抓取的仓库快照。
        要求 repos 中每个 dict 都包含：
        repo_id, full_name, html_url, description, language, stars, snapshot_date
        """
        if not repos:
            return

        conn = self._get_conn()
        cur = conn.cursor()

        rows = []

        # 将fetcher中抓取到的仓库list转化成sqlite3插入格式
        for repo in repos:
            rows.append((
                repo["repo_id"],
                repo["full_name"],
                repo["html_url"],
                repo.get("description", ""),
                repo.get("language", ""),
                repo["stars"],
                repo["snapshot_date"],
            ))

        # insert or replace保证没有重复数据
        cur.executemany("""
        INSERT OR REPLACE INTO repo_snapshots
        (repo_id, full_name, html_url, description, language, stars, snapshot_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, rows)

        conn.commit()
        conn.close()

    # 保存快照日期，使用仓库中元素snapshot_date中的最大值
    def get_all_snapshot_dates(self) -> list[str]:
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute("""
        SELECT DISTINCT snapshot_date
        FROM repo_snapshots
        ORDER BY snapshot_date DESC
        """)

        dates = [row["snapshot_date"] for row in cur.fetchall()]
        conn.close()
        return dates

    # 找最新快照日期
    def get_latest_snapshot_date(self) -> str | None:
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute("""
        SELECT MAX(snapshot_date) AS snapshot_date
        FROM repo_snapshots
        """)

        row = cur.fetchone()
        conn.close()
        return row["snapshot_date"] if row and row["snapshot_date"] else None

    # 找上一次快照时间
    def get_previous_snapshot_date(self, current_date: str) -> str | None:
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute("""
        SELECT MAX(snapshot_date) AS snapshot_date
        FROM repo_snapshots
        WHERE snapshot_date < ?
        """, (current_date,))

        row = cur.fetchone()
        conn.close()
        return row["snapshot_date"] if row and row["snapshot_date"] else None

    # 找某一天的快照
    def get_repos_by_snapshot_date(self, snapshot_date: str) -> list[dict[str, Any]]:
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute("""
        SELECT repo_id, full_name, html_url, description, language, stars, snapshot_date
        FROM repo_snapshots
        WHERE snapshot_date = ?
        ORDER BY stars DESC, full_name ASC
        """, (snapshot_date,))

        rows = cur.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    # 查找某一天的快照内有多少条仓库数据记录
    def count_repos_by_snapshot_date(self, snapshot_date: str) -> int:
        """
        统计某一天快照里共有多少个仓库
        """
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute("""
        SELECT COUNT(*) AS cnt
        FROM repo_snapshots
        WHERE snapshot_date = ?
        """, (snapshot_date,))

        row = cur.fetchone()
        conn.close()
        return row["cnt"] if row else 0


    def count_common_repos(self, current_date: str, previous_date: str) -> int:
        """
        统计两天共同存在的仓库数量
        """
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute("""
        SELECT COUNT(*) AS cnt
        FROM repo_snapshots c
        JOIN repo_snapshots p
        ON c.repo_id = p.repo_id
        WHERE c.snapshot_date = ?
        AND p.snapshot_date = ?
        """, (current_date, previous_date))

        row = cur.fetchone()
        conn.close()
        return row["cnt"] if row else 0


    def get_snapshot_comparison_stats(self, current_date: str, previous_date: str) -> dict[str, Any]:
        """
        返回两个快照日期的对比统计信息
        """
        current_count = self.count_repos_by_snapshot_date(current_date)
        previous_count = self.count_repos_by_snapshot_date(previous_date)
        common_count = self.count_common_repos(current_date, previous_date)

        return {
            "current_date": current_date,
            "previous_date": previous_date,
            "current_count": current_count,
            "previous_count": previous_count,
            "common_count": common_count,
            "current_only_count": max(current_count - common_count, 0),
            "previous_only_count": max(previous_count - common_count, 0),
        }
    
    # 计算差值
    def get_top_growth_repos(
        self,
        current_date: str,
        previous_date: str,
        top_n: int = 10
    ) -> list[dict[str, Any]]:
        """
        对比两个快照日期，计算 stars 增长 Top N
        """
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute("""
        SELECT
            c.repo_id,
            c.full_name,
            c.html_url,
            c.description,
            c.language,
            c.stars AS current_stars,
            p.stars AS previous_stars,
            (c.stars - p.stars) AS weekly_growth,
            c.snapshot_date AS current_snapshot_date,
            p.snapshot_date AS previous_snapshot_date
        FROM repo_snapshots c
        JOIN repo_snapshots p
          ON c.repo_id = p.repo_id
        WHERE c.snapshot_date = ?
          AND p.snapshot_date = ?
        ORDER BY weekly_growth DESC, current_stars DESC
        LIMIT ?
        """, (current_date, previous_date, top_n))

        rows = cur.fetchall()
        conn.close()

        results = []
        for row in rows:
            results.append({
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

        return results
    
    def diff_in_weeks_days(self,t1, t2) -> dict:
        format = "%Y-%m-%d"
        t1 = datetime.strptime(t1, format)
        t2 = datetime.strptime(t2, format)
        delta = abs(t2 - t1)
        days = delta.days
        weeks = days // 7
        remain_days = days % 7
        time_delta = {}
        time_delta['days'] = remain_days
        time_delta['weeks'] = weeks
        return time_delta

    
    def get_top_growth_repos_safe(self, current_date, previous_date, top_n: int = 10,
            min_common_ratio: float = 0.7, min_common_count: int = 1,) -> dict[str, Any]:
        """
        安全版 Top Growth 查询。

        参数说明：
        - current_date: 当前快照日期；不传则自动取最新日期
        - previous_date: 上一个快照日期；不传则自动取 current_date 之前最近的日期
        - top_n: 返回前 N 个
        - min_common_ratio: 两天交集仓库数 / 较小那天仓库总数 的最小比例要求
        - min_common_count: 至少要有多少共同仓库，否则认为不能比较

        返回：
        {
            "ok": bool,
            "message": str,
            "stats": {...},
            "results": [...]
        }
        """
        if current_date is None:
            current_date = self.get_latest_snapshot_date()

        if current_date is None:
            return {
                "ok": False,
                "message": "数据库中没有任何快照数据",
                "stats": None,
                "results": [],
            }

        if previous_date is None:
            previous_date = self.get_previous_snapshot_date(current_date)

        if previous_date is None:
            return {
                "ok": False,
                "message": f"当前日期 {current_date} 没有可比较的上一个快照日期",
                "stats": None,
                "results": [],
            }

        stats = self.get_snapshot_comparison_stats(current_date, previous_date)

        current_count = stats["current_count"]
        previous_count = stats["previous_count"]
        common_count = stats["common_count"]

        if current_count == 0:
            return {
                "ok": False,
                "message": f"当前快照日期 {current_date} 没有数据",
                "stats": stats,
                "results": [],
            }

        if previous_count == 0:
            return {
                "ok": False,
                "message": f"上一个快照日期 {previous_date} 没有数据",
                "stats": stats,
                "results": [],
            }

        if common_count < min_common_count:
            return {
                "ok": False,
                "message": (
                    f"两天共同仓库数过少，无法可靠比较："
                    f"common_count={common_count}, min_common_count={min_common_count}"
                ),
                "stats": stats,
                "results": [],
            }

        base_count = min(current_count, previous_count)
        common_ratio = common_count / base_count if base_count > 0 else 0.0
        stats["common_ratio"] = common_ratio

        if common_ratio < min_common_ratio:
            return {
                "ok": False,
                "message": (
                    f"两天共同仓库占比过低，比较结果可能不可靠："
                    f"common_ratio={common_ratio:.2%}, min_common_ratio={min_common_ratio:.2%}"
                    f'common_count={common_count:}'
                ),
                "stats": stats,
                "results": [],
            }

        results = self.get_top_growth_repos(
            current_date=current_date,
            previous_date=previous_date,
            top_n=top_n,
        )
        time_delta = self.diff_in_weeks_days(current_date, previous_date)


        return {
            "ok": True,
            "message": "查询成功",
            "stats": stats,
            "results": results,
            "time_delta": time_delta
        }



    def debug_print_all(self) -> None:
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute("""
        SELECT repo_id, full_name, html_url, description, language, stars, snapshot_date
        FROM repo_snapshots
        ORDER BY snapshot_date DESC, stars DESC
        """)

        rows = cur.fetchall()
        conn.close()

        for row in rows:
            print(dict(row))


if __name__ == '__main__':

    cfg = OmegaConf.load("config.yaml")
    fetcher = Github_Fetcher(cfg)
    snapshoter = Repo_Snapshot(cfg)
    analysier = Client_Analysis(cfg)
    repos = fetcher.fetch_candidate_repos()
    snapshoter.save_snapshot(repos)
    ltst_date = snapshoter.get_latest_snapshot_date()
    all_date = snapshoter.get_all_snapshot_dates()
    # for item in all_date:
    #     print(item)
    diff = snapshoter.get_top_growth_repos_safe()
    for item in diff['results']:
        summary = analysier.get_response(item)

    snapshoter.debug_print_all()