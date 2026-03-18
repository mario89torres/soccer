import requests
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36'
}
url = 'https://understat.com/league/EPL/2024'
resp = requests.get(url, headers=headers, timeout=15)
html = resp.text

print('Status:', resp.status_code)
print('HTML length:', len(html))

# Check for teamsData
idx = html.find('teamsData')
print('teamsData found at index:', idx)
if idx >= 0:
    print('Context:', repr(html[idx-10:idx+120]))

# All JSON.parse occurrences
patterns = re.findall(r"var\s+\w+\s*=\s*JSON\.parse\(.{0,60}", html)
print('\nJSON.parse patterns found:', len(patterns))
for p in patterns[:5]:
    print(' ', repr(p))

# All var = ... patterns
var_patterns = re.findall(r"var\s+(\w+)\s*=", html)
print('\nVar names found:', var_patterns[:20])
