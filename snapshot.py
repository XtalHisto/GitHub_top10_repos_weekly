import sqlite3
import requests
from datetime import datetime, timedelta
from omegaconf import OmegaConf
from typing import Any
from fetcher import Github_Fetcher





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
    repos = fetcher.fetch_candidate_repos()
    snapshoter.save_snapshot(repos)
    snapshoter.debug_print_all()