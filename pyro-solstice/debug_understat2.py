import requests
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36'
}

# Try a direct team page
for url in [
    'https://understat.com/team/Manchester_City/2024',
    'https://understat.com/team/Arsenal/2024',
]:
    resp = requests.get(url, headers=headers, timeout=15)
    html = resp.text
    print(f'\n=== {url} ===')
    print('Status:', resp.status_code)
    print('HTML length:', len(html))

    # Check for datesData / teamsData
    for var in ['datesData', 'teamsData', 'playersData', 'statisticsData']:
        idx = html.find(var)
        if idx >= 0:
            print(f'{var} found at index {idx}:', repr(html[idx:idx+100]))

    # All JSON.parse occurrences
    patterns = re.findall(r"var\s+(\w+)\s*=\s*JSON\.parse\('", html)
    print('JSON.parse var names:', patterns)
