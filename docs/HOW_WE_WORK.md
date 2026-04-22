# How We Work
Human: owner, makes all decisions
Claude (browser): code reviewer, architecture guardian
GPT: executor (plans, analysis)
Codex: executor (code in repo)

Review checklist (Claude applies every stage):
- pytest green
- authority rules preserved
- no cross-service imports in money path
- DB persistence where needed
- no sync httpx in async handlers
- alembic migration if new table
- correlation_id propagated
