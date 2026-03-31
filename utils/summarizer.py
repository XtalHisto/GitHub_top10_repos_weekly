from openai import OpenAI



class Client_Analysis:
    '''
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
    '''

    def __init__(self, cfg):
        self.cfg = cfg
        self.agent =  OpenAI(api_key = cfg.client.api_key, base_url = cfg.client.base_url) 
        self.thinking = False
    
    def create_prompt(self, repo, time_delta):
        name = repo["full_name"]
        desc = repo.get("description", "")
        stars = repo.get("stars", 0)
        weekly_stars = repo.get('weekly_stars', 0)
        url = repo.get("html_url", "")
        language = repo.get('language','')
        prompt = f"""
            你是一个技术分析助手，请分析下面这个 GitHub 项目，并用中文输出简洁总结：

            【项目信息】
            名称：{name}
            描述：{desc}
            Star数： {stars}
            链接：{url}
            语言：{language} 
            {time_delta['weeks']}周{time_delta["days"]}天内star数增加量： {weekly_stars}

            【要求】
            1. 用 2~3 句话说明这个项目是做什么的
            2. 说明它为什么在{time_delta['weeks']}周{time_delta["days"]}天内会开始受欢迎（{time_delta['weeks']}周{time_delta["days"]}天内star数增加量）
            3. 最后一句：适合谁使用
        """
        return prompt.strip()

    def get_response(self,results,time_delta):
        prompt = self.create_prompt(results, time_delta)

        response = self.agent.chat.completions.create(
            model=self.cfg.client.model[0].name,
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