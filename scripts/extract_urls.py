import re, json
from pathlib import Path
p = Path(r"C:\Users\ronal\AppData\Roaming\Code\User\workspaceStorage\d5ebb91c4f4856b1755f79ddd077abd0\GitHub.copilot-chat\transcripts\62ca4b34-bb3a-491e-9e41-8b75cef1499f.jsonl")
t = p.read_text(encoding="utf-8", errors="ignore")
# supports plain and JSON-escaped URLs
pat = re.compile(r"https:(?:\\/\\/|//)static\\.wixstatic\\.com(?:\\/|/)media(?:\\/|/)[^\"'\\s<>]+")
u = pat.findall(t)
# normalize escaped slashes
u = [x.replace('\\/','/') for x in u]
uniq = list(dict.fromkeys(u))
Path("scripts/live_urls_all.json").write_text(json.dumps(uniq, indent=2), encoding="utf-8")
print('matches', len(u), 'unique', len(uniq))
print('first', uniq[:6])
