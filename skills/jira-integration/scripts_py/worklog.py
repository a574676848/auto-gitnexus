import argparse
import sys
import os
from datetime import datetime, timedelta
try:
    import utils
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import utils

def format_time_spent(seconds: int) -> str:
    """将秒数格式化为人类可读的工时 (如 1h 30m)"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s" if secs > 0 else f"{minutes}m"
    else:
        hours = seconds / 3600
        if hours == int(hours):
            return f"{int(hours)}h"
        return f"{hours:.1f}h"

def get_worklogs_by_user_and_date(username: str = None, from_date: str = None, to_date: str = None, issue_key: str = None, max_results: int = 100):
    """
    根据用户、时间范围或工单查询工时信息
    支持四种模式：
    1. 按用户查询 (默认最近 7 天)
    2. 按时间范围查询 (所有用户)
    3. 按用户 + 时间查询
    4. 按工单查询 (所有工时)
    """
    
    # 构建 JQL 查询
    jql_parts = []
    
    if issue_key:
        # 模式 4：查询单个工单的所有工时
        jql_parts.append(f"key = '{issue_key}'")
    else:
        # 模式 1/2/3：按用户和/或时间查询
        if username:
            jql_parts.append(f'worklogAuthor = "{username}"')
        
        if from_date:
            jql_parts.append(f'worklogDate >= "{from_date}"')
        
        if to_date:
            jql_parts.append(f'worklogDate <= "{to_date}"')
        
        # 如果都没提供，默认查询最近 7 天
        if not username and not from_date and not to_date:
            default_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            jql_parts.append(f'worklogDate >= "{default_from}"')
            from_date = default_from
    
    if not jql_parts:
        utils.log_to_agent({
            "success": False,
            "error_type": "MISSING_PARAMETERS",
            "message": "请至少提供一个参数：--user、--from、--to 或 --issue"
        })
        sys.exit(0)
    
    jql = " AND ".join(jql_parts)
    
    # 调用 search API，带上 worklog 字段
    params = {
        'jql': jql,
        'maxResults': max_results,
        'fields': 'id,key,summary,worklog'
    }
    
    response = utils.api_request('search', method='GET', params=params)
    
    if not response['success']:
        utils.log_to_agent(response)
        sys.exit(0)
    
    data = response['data']
    total = data.get('total', 0)
    issues_raw = data.get('issues', [])
    
    # 提取和聚合工时数据
    all_worklogs = []
    total_seconds = 0
    
    for issue in issues_raw:
        fields = issue.get('fields', {})
        worklog_data = fields.get('worklog', {})
        worklogs = worklog_data.get('worklogs', [])
        
        for worklog in worklogs:
            # 如果指定了用户，客户端再次过滤（确保精确）
            if username:
                author = worklog.get('author', {})
                author_name = author.get('name') or author.get('displayName', '')
                if author_name != username:
                    continue
            
            # 如果指定了时间范围，客户端再次过滤
            if from_date or to_date:
                started = worklog.get('started', '')
                if started:
                    log_date = started[:10]  # 提取 YYYY-MM-DD
                    if from_date and log_date < from_date:
                        continue
                    if to_date and log_date > to_date:
                        continue
            
            time_spent_seconds = worklog.get('timeSpentSeconds', 0)
            total_seconds += time_spent_seconds
            
            worklog_entry = {
                "issue_key": issue.get('key'),
                "issue_summary": fields.get('summary'),
                "time_spent_seconds": time_spent_seconds,
                "time_spent": format_time_spent(time_spent_seconds),
                "comment": worklog.get('comment'),
                "started": worklog.get('started'),
                "created": worklog.get('created'),
                "author": worklog.get('author', {}).get('displayName') or worklog.get('author', {}).get('name'),
                "link": utils.get_browse_url(issue.get('key'))
            }
            all_worklogs.append(worklog_entry)
    
    # 按日期排序
    all_worklogs.sort(key=lambda x: x.get('started', ''), reverse=True)
    
    # 构建统计摘要
    summary = {
        "total_issues": len(set(w['issue_key'] for w in all_worklogs)),
        "total_worklog_count": len(all_worklogs),
        "total_worklog_seconds": total_seconds,
        "total_worklog_formatted": format_time_spent(total_seconds)
    }
    
    # 构建查询信息
    query_info = {}
    if username:
        query_info['user'] = username
    if from_date:
        query_info['from'] = from_date
    if to_date:
        query_info['to'] = to_date
    if issue_key:
        query_info['issue'] = issue_key
    
    utils.log_to_agent({
        "success": True,
        "query": query_info,
        "summary": summary,
        "total_matches": total,
        "returned_count": len(all_worklogs),
        "worklogs": all_worklogs
    })

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="查询 Jira 工时信息 (Jira 7.5.2)")
    
    # 查询条件参数
    parser.add_argument('--user', type=str, help="按用户查询 (用户名)")
    parser.add_argument('--from', type=str, dest='from_date', help="开始日期 (YYYY-MM-DD)")
    parser.add_argument('--to', type=str, dest='to_date', help="结束日期 (YYYY-MM-DD)")
    parser.add_argument('--issue', type=str, help="按工单查询 (工单 KEY)")
    
    # 通用参数
    parser.add_argument('--max', type=int, default=100, help="最大返回工单数量 (默认 100)")
    parser.add_argument('--workdir', type=str, required=True, help="工作目录 (用户空间 tmp 路径)")
    
    args = parser.parse_args()
    
    # 验证工作目录
    utils.validate_workdir(args.workdir)
    utils.set_workdir(args.workdir)
    
    # 参数冲突检查
    if args.issue and (args.user or args.from_date or args.to_date):
        utils.log_to_human("⚠️  参数冲突：--issue 不能与 --user/--from/--to 同时使用", "WARNING")
        utils.log_to_agent({
            "success": False,
            "error_type": "PARAMETER_CONFLICT",
            "message": "--issue 参数不能与 --user/--from/--to 同时使用，请只选择一种查询模式"
        })
        sys.exit(0)
    
    # 执行查询
    get_worklogs_by_user_and_date(
        username=args.user,
        from_date=args.from_date,
        to_date=args.to_date,
        issue_key=args.issue,
        max_results=args.max
    )
