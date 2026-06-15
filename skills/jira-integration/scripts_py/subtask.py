"""
子任务管理脚本
支持创建、更新、删除子任务
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


def create_subtask(parent_key: str, payload: dict):
    """
    创建子任务
    :param parent_key: 父工单 KEY
    :param payload: 子任务字段 payload (不含 parent 字段)
    """
    # 确保 payload 中包含 parent 和 issuetype
    if 'fields' not in payload:
        payload = {'fields': payload}

    # 设置父工单
    payload['fields']['parent'] = {'key': parent_key}

    # 如果没有指定 issuetype，默认为子任务类型
    if 'issuetype' not in payload['fields']:
        payload['fields']['issuetype'] = {'id': '10003'}  # Jira 7.5.2 默认子任务类型 ID

    response = utils.api_request('issue', method='POST', data=payload)

    if not response['success']:
        utils.log_to_agent(response)
        sys.exit(1)

    data = response.get('data', {})
    utils.log_to_agent({
        'success': True,
        'message': '子任务创建成功！',
        'issue_key': data.get('key'),
        'issue_id': data.get('id'),
        'parent_key': parent_key,
        'link': f"{utils.get_config()['domain']}/browse/{data.get('key')}"
    })


def update_subtask(issue_key: str, payload: dict):
    """
    更新子任务（与普通工单更新相同）
    :param issue_key: 子任务 KEY
    :param payload: 更新字段 payload
    """
    if 'fields' not in payload:
        payload = {'fields': payload}

    response = utils.api_request(f'issue/{issue_key}', method='PUT', data=payload)

    if not response['success']:
        utils.log_to_agent(response)
        sys.exit(1)

    utils.log_to_agent({
        'success': True,
        'message': f'子任务 {issue_key} 更新成功！',
        'issue_key': issue_key
    })


def delete_subtask(issue_key: str):
    """
    删除子任务
    :param issue_key: 子任务 KEY
    """
    response = utils.api_request(f'issue/{issue_key}', method='DELETE')

    if not response['success']:
        utils.log_to_agent(response)
        sys.exit(1)

    utils.log_to_agent({
        'success': True,
        'message': f'子任务 {issue_key} 已成功删除！',
        'issue_key': issue_key
    })


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Jira 7.5.2 子任务管理')
    parser.add_argument('--action', type=str, required=True, choices=['create', 'update', 'delete'],
                        help='操作类型: create/update/delete')
    parser.add_argument('--parent', type=str, help='父工单 KEY (create 时必需)')
    parser.add_argument('--issue', type=str, help='子任务 KEY (update/delete 时必需)')
    parser.add_argument('--payload', type=str, help='JSON payload (create/update 时必需)')
    parser.add_argument('--workdir', type=str, required=True, help='工作目录(用户空间tmp路径)')

    args = parser.parse_args()
    utils.validate_workdir(args.workdir)
    utils.set_workdir(args.workdir)

    if args.action == 'create':
        if not args.parent or not args.payload:
            print(json.dumps({
                'success': False,
                'error': 'create 操作需要 --parent 和 --payload 参数'
            }, ensure_ascii=False, indent=2))
            sys.exit(1)
        try:
            payload = json.loads(args.payload)
        except json.JSONDecodeError as e:
            print(json.dumps({
                'success': False,
                'error': f'payload JSON 解析失败: {str(e)}'
            }, ensure_ascii=False, indent=2))
            sys.exit(1)
        create_subtask(args.parent, payload)

    elif args.action == 'update':
        if not args.issue or not args.payload:
            print(json.dumps({
                'success': False,
                'error': 'update 操作需要 --issue 和 --payload 参数'
            }, ensure_ascii=False, indent=2))
            sys.exit(1)
        try:
            payload = json.loads(args.payload)
        except json.JSONDecodeError as e:
            print(json.dumps({
                'success': False,
                'error': f'payload JSON 解析失败: {str(e)}'
            }, ensure_ascii=False, indent=2))
            sys.exit(1)
        update_subtask(args.issue, payload)

    elif args.action == 'delete':
        if not args.issue:
            print(json.dumps({
                'success': False,
                'error': 'delete 操作需要 --issue 参数'
            }, ensure_ascii=False, indent=2))
            sys.exit(1)
        delete_subtask(args.issue)
