import requests
from openai import OpenAI
from omegaconf import OmegaConf


class Client_Analysis:
    def __init__(self, cfg):
        self.cfg = cfg
        self.agent =  OpenAI(api_key = cfg.client.api_key, base_url = cfg.client.base_url) 
        self.thinking = False
    
    def create_prompt(self, repo):
        name = repo["full_name"]
        desc = repo.get("description", "")
        stars = repo.get("stargazers_count", 0)
        url = repo.get("html_url", "")
        prompt = f"""
你是一个技术分析助手，请分析下面这个 GitHub 项目，并用中文输出简洁总结：

【项目信息】
名称：{name}
描述：{desc}
Star数：{stars}
链接：{url}

【要求】
1. 用 2~3 句话说明这个项目是做什么的
2. 说明它为什么会受欢迎（结合star数）
3. 最后一句：适合谁使用


"""
        return prompt.strip()

    def get_response(self,repo):
        prompt = self.create_prompt(repo)

        response = self.agent.chat.completions.create(
            model="qwen3-vl-235b-a22b-thinking",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                    ],
                },
            ],
            stream=True,
            # enable_thinking 参数开启思考过程，thinking_budget 参数设置最大推理过程 Token 数
            extra_body={
                'enable_thinking': self.thinking,
                "thinking_budget": 81920}
    )
        answer_content = ""

        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                answer_content += delta.content
        return answer_content.strip()
   
    
    def create_text(self, repo):
        summary = self.get_response(repo)
        block = (
            f"   {repo['full_name']}\n"
            f"   Stars: {repo['stargazers_count']}\n"
            f"   Link: {repo['html_url']}\n"
            f"   Summary: {summary}\n"
        )
        return block

class Github_Top_List:
    def __init__(self ,cfg):
        self.cfg = cfg
        self.headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "github-top10-script"
        }
        github_token = self.cfg.github.token
        if github_token:
            self.headers["Authorization"] = f"Bearer {github_token}"
        self.analyser  = Client_Analysis(cfg)
    
    def fetch_github_repos(self):      
        response = requests.get(
        self.cfg.github.url,
        headers=self.headers,
        params=self.cfg.query,
        timeout=30
        )
        data = response.json()
        items = data.get("items", [])
        items = sorted(items, key=lambda x: x["stargazers_count"], reverse=True)
        return items
    
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



if __name__ == '__main__':
   cfg = OmegaConf.load("config.yaml")
   app = Github_Top_List(cfg)
   app.run()
   