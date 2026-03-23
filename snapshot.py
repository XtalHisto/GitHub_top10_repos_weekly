import sqlite3
import requests
from datetime import datetime, timedelta
from omegaconf import OmegaConf

class Repo_Snapshot:
    '''
    
    '''
    def __init__(self, cfg):
        self.db_path = cfg.app.db_path
        self.init_db()

    def get_conn(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        conn = self.get_conn()
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS repo_snapshots (
            repo_id INTEGER,
            full_name TEXT,
            html_url TEXT,
            description TEXT,
            language TEXT,
            stars INTEGER,
            snapshot_date TEXT,
            PRIMARY KEY (repo_id, snapshot_date)
        )
        """)

        conn.commit()
        conn.close()

    def save_snapshot(self, repos, snapshot_date):
        conn = self.get_conn()
        cursor = conn.cursor()

        for repo in repos:
            cursor.execute("""
            INSERT OR REPLACE INTO repo_snapshots
            (repo_id, full_name, html_url, description, language, stars, snapshot_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                repo["id"],
                repo["full_name"],
                repo["html_url"],
                repo.get("description", ""),
                repo.get("language", ""),
                repo["stargazers_count"],
                snapshot_date
            ))

        conn.commit()
        conn.close()

    def get_latest_snapshot_date(self):
        conn = self.get_conn()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT MAX(snapshot_date) FROM repo_snapshots
        """)
        row = cursor.fetchone()

        conn.close()
        return row[0] if row and row[0] else None

    def get_previous_snapshot_date(self, current_date):
        conn = self.get_conn()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT MAX(snapshot_date)
        FROM repo_snapshots
        WHERE snapshot_date < ?
        """, (current_date,))
        row = cursor.fetchone()

        conn.close()
        return row[0] if row and row[0] else None

    def get_top_growth_repos(self, current_date, previous_date, top_n=10):
        conn = self.get_conn()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT
            c.repo_id,
            c.full_name,
            c.html_url,
            c.description,
            c.language,
            c.stars AS current_stars,
            p.stars AS previous_stars,
            (c.stars - p.stars) AS weekly_growth
        FROM repo_snapshots c
        JOIN repo_snapshots p
            ON c.repo_id = p.repo_id
        WHERE c.snapshot_date = ?
          AND p.snapshot_date = ?
        ORDER BY weekly_growth DESC, current_stars DESC
        LIMIT ?
        """, (current_date, previous_date, top_n))

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            results.append({
                "repo_id": row[0],
                "full_name": row[1],
                "html_url": row[2],
                "description": row[3],
                "language": row[4],
                "stargazers_count": row[5],
                "previous_stars": row[6],
                "weekly_stars": row[7]
            })

        return results
    def fetch_and_save_snapshot(self, response):
        response.raise_for_status()

        data = response.json()
        items = data.get("items", [])

        repos = []
        for repo in items:
            repos.append({
                "id": repo["id"],
                "full_name": repo["full_name"],
                "html_url": repo["html_url"],
                "description": repo.get("description", ""),
                "language": repo.get("language", ""),
                "stargazers_count": repo["stargazers_count"]
            })

        repos = sorted(repos, key=lambda x: x["stargazers_count"], reverse=True)

        snapshot_date = datetime.now().strftime("%Y-%m-%d")
        self.store.save_snapshot(repos, snapshot_date)

        print(f"snapshot saved: {snapshot_date}, count={len(repos)}")
        return repos


# # def mock_repos(stars_offset=0):
#     """
#     构造假的 GitHub 数据
#     """
#     return [
#         {
#             "id": 1,
#             "full_name": "test/repo1",
#             "html_url": "https://github.com/test/repo1",
#             "description": "repo1 desc",
#             "language": "Python",
#             "stargazers_count": 100 + stars_offset
#         },
#         {
#             "id": 2,
#             "full_name": "test/repo2",
#             "html_url": "https://github.com/test/repo2",
#             "description": "repo2 desc",
#             "language": "Go",
#             "stargazers_count": 200 + stars_offset
#         }
#     ]



if __name__ == "__main__":
    cfg = OmegaConf.load('config.yaml')
