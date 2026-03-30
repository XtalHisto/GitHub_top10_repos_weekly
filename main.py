from omegaconf import OmegaConf

from utils.html_maker import Email_Builder
from utils.snapshot import Repo_Snapshot
from utils.summarizer import Client_Analysis
from utils.fetcher import Github_Fetcher
from utils.emailer import Emailer



cfg = OmegaConf.load("config.yaml")
fetcher = Github_Fetcher(cfg)
snapshoter = Repo_Snapshot(cfg)
analysier = Client_Analysis(cfg)
builder = Email_Builder(cfg)
emailer = Emailer(cfg)

repos = fetcher.fetch_candidate_repos()
snapshoter.save_snapshot(repos)
ltst_date = snapshoter.get_latest_snapshot_date()
all_date = snapshoter.get_all_snapshot_dates()
curr_date  = snapshoter.get_latest_snapshot_date()
pre_date = snapshoter.get_previous_snapshot_date(curr_date)
diff = snapshoter.get_top_growth_repos_safe(current_date=curr_date, previous_date=pre_date)
for item in diff['results']:
    item['summary'] = analysier.get_response(item)
html_content = builder.build_html(diff['results']) 
# with open("test.html", "w", encoding="utf-8") as f:
#     f.write(html_content)
emailer.email_send(html_content)
