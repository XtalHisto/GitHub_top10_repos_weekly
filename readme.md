# GitHub Weekly Star Tracker

## Current Progress

- [x] Fetch top GitHub repositories via GitHub Search API
- [x] Summarize repository info with LLM
- [x] Export report to txt
- [x] Add snapshot storage with SQLite
- [x] Support dual-query candidate collection and deduplication
- [ ] Generate weekly growth ranking from snapshot diffs
- [ ] Export final report to HTML
- [ ] Automate weekly scheduled execution

## Notes

Current strategy uses:
1. dual-query candidate collection
2. weekly snapshot storage
3. snapshot diff to estimate weekly star growth

This is not a full GitHub-wide exact ranking yet, but a practical candidate-based weekly tracker.
