"""
工时管理脚本
支持添加、更新、删除工时记录
"""
import argparse
import json
import sys
import os
try:
    import utils
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import utils


def add_worklog(issue_key: str, time_spent: str, comment: str = None, started: str = None):
    """
    添加工时记录
    :param issue_key: 工单 KEY
    :param time_spent: 工时（如 "2h", "1d 4h", "30m"）
    :param comment: 工时说明（可选）
    :param started: 开始时间（格式：YYYY-MM-DDThh:mm:ss.SSS+0000，可选，默认当前时间）
    """
    payload = {
        "timeSpent": time_spent
    }

    if comment:
        payload["comment"] = comment

    if started:
        payload["started"] = started

    response = utils.api_request(f'issue/{issue_key}/worklog', method='POST', data=payload)

    if not response['success']:
        utils.log_to_agent(response)
        sys.exit(1)

    data = response.get('data', {})
    utils.log_to_agent({
        'success': True,
        'message': f'工时记录已成功添加到工单 {issue_key}',
        'issue': issue_key,
        'worklog_id': data.get('id'),
        'time_spent': time_spent
    })


def update_worklog(issue_key: str, worklog_id: str, time_spent: str = None, comment: str = None):
    """
    更新工时记录
    :param issue_key: 工单 KEY
    :param worklog_id: 工时记录 ID
    :param time_spent: 新的工时（可选）
    :param comment: 新的工时说明（可选）
    """
    payload = {}

    if time_spent:
        payload["timeSpent"] = time_spent

    if comment:
        payload["comment"] = comment

    if not payload:
        print(json.dumps({
            'success': False,
            'error': '必须提供 --time-spent 或 --comment 至少一个参数'
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    response = utils.api_request(f'issue/{issue_key}/worklog/{worklog_id}', method='PUT', data=payload)

    if not response['success']:
        utils.log_to_agent(response)
        sys.exit(1)

    utils.log_to_agent({
        'success': True,
        'message': f'工单 {issue_key} 的工时记录 {worklog_id} 已成功更新',
        'issue': issue_key,
        'worklog_id': worklog_id
    })


def delete_worklog(issue_key: str, worklog_id: str):
    """
    删除工时记录
    :param issue_key: 工单 KEY
    :param worklog_id: 工时记录 ID
    """
    response = utils.api_request(f'issue/{issue_key}/worklog/{worklog_id}', method='DELETE')

    if not response['success']:
        utils.log_to_agent(response)
        sys.exit(1)

    utils.log_to_agent({
        'success': True,
        'message': f'工单 {issue_key} 的工时记录 {worklog_id} 已成功删除',
        'issue': issue_key,
        'worklog_id': worklog_id
    })


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Jira 7.5.2 工时管理')
    parser.add_argument('--action', type=str, required=True,
                        choices=['add', 'update', 'delete'],
                        help='操作类型: add/update/delete')
    parser.add_argument('--issue', type=str, required=True, help='工单 KEY')
    parser.add_argument('--worklog-id', type=str, help='工时记录 ID (update/delete 时必需)')
    parser.add_argument('--time-spent', type=str, help='工时时长（如 "2h", "1d", "30m"）')
    parser.add_argument('--comment', type=str, help='工时说明')
    parser.add_argument('--started', type=str, help='开始时间（格式：YYYY-MM-DDThh:mm:ss.SSS+0000）')
    parser.add_argument('--workdir', type=str, required=True, help='工作目录(用户空间tmp路径)')

    args = parser.parse_args()
    utils.validate_workdir(args.workdir)
    utils.set_workdir(args.workdir)

    if args.action == 'add':
        if not args.time_spent:
            print(json.dumps({
                'success': False,
                'error': 'add 操作需要 --time-spent 参数'
            }, ensure_ascii=False, indent=2))
            sys.exit(1)
        add_worklog(args.issue, args.time_spent, args.comment, args.started)

    elif args.action == 'update':
        if not args.worklog_id:
            print(json.dumps({
                'success': False,
                'error': 'update 操作需要 --worklog-id 参数'
            }, ensure_ascii=False, indent=2))
            sys.exit(1)
        update_worklog(args.issue, args.worklog_id, args.time_spent, args.comment)

    elif args.action == 'delete':
        if not args.worklog_id:
            print(json.dumps({
                'success': False,
                'error': 'delete 操作需要 --worklog-id 参数'
            }, ensure_ascii=False, indent=2))
            sys.exit(1)
        delete_worklog(args.issue, args.worklog_id)
