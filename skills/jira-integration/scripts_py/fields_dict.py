import argparse
import sys
import os
import json
try:
    import utils
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import utils

CACHE_FILE_PATH = os.path.expanduser('~/.jira_all_fields_dict.json')

def fetch_and_cache_fields() -> list:
    utils.log_to_human("正在拉取 Jira 7.x 字段字典...", "INFO")
    response = utils.api_request('field', method='GET')
    if not response['success']:
        utils.log_to_agent(response)
        sys.exit(0)
    
    cleaned = []
    for f in response['data']:
        cleaned.append({
            "id": f.get("id"),
            "name": f.get("name"),
            "custom": f.get("custom"),
            "type": f.get("schema", {}).get("type")
        })
    
    try:
        with open(CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cleaned, f, ensure_ascii=False, indent=2)
    except Exception: pass
    return cleaned

def search_fields_dict(keyword: str = None, force_refresh: bool = False):
    fields = []
    if force_refresh or not os.path.exists(CACHE_FILE_PATH):
        fields = fetch_and_cache_fields()
    else:
        with open(CACHE_FILE_PATH, 'r', encoding='utf-8') as f:
            fields = json.load(f)
            
    if not keyword:
        utils.log_to_agent({"success": True, "total": len(fields)})
        return
        
    keyword = keyword.lower()
    matches = [f for f in fields if keyword in str(f.get("id")).lower() or keyword in str(f.get("name")).lower()]
    utils.log_to_agent({"success": True, "matches": matches})

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="查询 Jira 7.5.2 字段字典")
    parser.add_argument('--keyword', type=str)
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    search_fields_dict(args.keyword, args.refresh)
