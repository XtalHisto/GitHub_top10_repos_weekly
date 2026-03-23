import requests
from datetime import datetime, timedelta


class Github_Fetcher:
    def __init__(self ,cfg):
        self.cfg = cfg
        self.headers = {
            "Accept": self.cfg.github.headers.accept,
            "User-Agent": self.cfg.github.headers.usr_agent
        }
        github_token = self.cfg.github.token
        if github_token:
            self.headers["Authorization"] = f"Bearer {github_token}"
        self.stable = True
        
    # 产生激进和稳妥两种query
    def build_query(self):
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=self.cfg.query.time_period)
        created_after = today - timedelta(days=self.cfg.repo_lifespan)

        # 稳健query
        stable_query = {
            "q": (
                f"stars:>{self.cfg.query.stable_min_stars} "
                f"pushed:>={week_ago.isoformat()} "
                f"archived:false is:public"
            ),
            "sort": "stars",
            "order": "desc",
            "per_page": 100,
            "page": 10,
        }

        # 激进query
        burst_query = {
            "q": (
                f"stars:>20 "
                f"created:>={created_after.isoformat()} "
                f"pushed:>={week_ago.isoformat()} "
                f"archived:false is:public"
            ),
            "sort": "stars",
            "order": "desc",
            "per_page": 100,
            "page": 1,
        }
        return stable_query, burst_query   


    # def fetch_github_repos(self):
    #     self.stable_query, self.burst_query = self.build_query()      
    #     response = requests.get(
    #     self.cfg.github.url,
    #     headers=self.headers,
    #     params=self.query,
    #     timeout=30
    #     )
    #     data = response.json()
    #     items = data.get("items", [])
        
    #     return items
    
    # 利用单个query查询一次GitHub仓库
    def fetch_repos_by_query(self, query_params):
        all_items = []

        for page in range(1, self.cfg.query.max_pages + 1):
            params = dict(query_params)
            params["page"] = page

            response = requests.get(
                self.cfg.github.url,
                headers=self.headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            items = data.get("items", [])

            if not items:
                break

            all_items.extend(items)

        return all_items

    # 合并两个query的搜索结果
    def fetch_candidate_repos(self):
        self.stable_query, self.burst_query = self.build_query()

        stable_items = self.fetch_repos_by_query(self.stable_query)
        burst_items = self.fetch_repos_by_query(self.burst_query)

        repo_map = {}

        for repo in stable_items + burst_items:
            repo_map[repo["id"]] = {
                "id": repo["id"],
                "full_name": repo["full_name"],
                "html_url": repo["html_url"],
                "description": repo.get("description", ""),
                "language": repo.get("language", ""),
                "stargazers_count": repo["stargazers_count"],
            }

        result = list(repo_map.values())

        # 取消注释为按star数逆序排序
        # result = sorted(result, key=lambda x: x["stargazers_count"], reverse=True)
        return result

    
    def build_text(self, items):
        lines = []
        lines.append("GitHub 当前 Star 数前 10 项目\n")
        for _, repo in enumerate(items, start=1):
            lines.append(f"   {repo['full_name']}\n")
            repo_info = self.analyser.create_text(repo)
            lines.append(repo_info)

        return "\n".join(lines)

    def save_to_file(self, content: str):
        output_file = 'test.txt'
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"已写入 {output_file}")

    def run(self):
        items = self.fetch_github_repos()
        content = self.build_text(items)
        print(content)
        self.save_to_file(content)