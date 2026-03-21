# -*- coding: utf8 -*-
# Sync issues from GitHub to index.md

import json
import logging
import os
import urllib.request
import urllib.parse
import datetime

logging.basicConfig(level=logging.INFO)

GITHUB_TOKEN = os.environ.get('GH_TOKEN', '')
REPO = 'fxyzbtc/fxyz.github.io'
ISSUES_URL = f'https://api.github.com/repos/{REPO}/issues'

def gh_api(url):
    """Fetch data from GitHub API"""
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'token {GITHUB_TOKEN}')
    req.add_header('Accept', 'application/vnd.github.v3+json')
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def get_issues(state='open'):
    """Get all issues without 'draft' label"""
    issues = []
    page = 1
    while True:
        url = f'{ISSUES_URL}?state={state}&per_page=100&page={page}'
        data = gh_api(url)
        if not data:
            break
        issues.extend(data)
        page += 1
        if len(data) < 100:
            break
    return issues

def extract_date_from_title(title):
    """Extract date from [YYYY-MM-DD] title format"""
    import re
    match = re.match(r'\[(\d{4}-\d{2}-\d{2})\]', title)
    if match:
        return match.group(1)
    return None

def main():
    issues = get_issues('all')
    
    # Filter out draft issues and format for index
    items = []
    for issue in issues:
        # Skip pull requests
        if 'pull_request' in issue:
            continue
        
        title = issue['title']
        labels = [l['name'] for l in issue.get('labels', [])]
        url = issue['html_url']
        number = issue['number']
        
        # Skip draft issues
        if 'draft' in labels:
            continue
        
        # Skip pages index issue
        if title.startswith('[Pages]'):
            continue
        
        # Extract date from title
        issue_date = extract_date_from_title(title)
        if not issue_date:
            # Use created date as fallback
            issue_date = issue['created_at'][:10]
        
        items.append((issue_date, title, url, labels))
    
    # Sort by date descending (parse as date for proper sorting)
    items.sort(key=lambda x: datetime.datetime.strptime(x[0], '%Y-%m-%d'), reverse=True)
    
    # Generate index.md
    updated_time = datetime.datetime.now().strftime('%Y-%m-%d')
    lines = [
        f'> Last Update: {updated_time}',
        '',
        '## Issues',
        ''
    ]
    
    for issue_date, title, url, labels in items:
        # Format labels as clickable tag links
        tag_str = ''
        if labels:
            tag_links = []
            for label in labels:
                # Link to GitHub label filter
                label_url = f'https://github.com/{REPO}/labels/{urllib.parse.quote(label)}'
                tag_links.append(f'[{label}]({label_url})')
            tag_str = ' [' + ', '.join(tag_links) + ']'
        lines.append(f'1. {issue_date}, [{title}]({url}){tag_str}')
    
    # Write index.md
    with open('index.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    logging.info(f'index.md updated with {len(items)} issues')

if __name__ == '__main__':
    main()
