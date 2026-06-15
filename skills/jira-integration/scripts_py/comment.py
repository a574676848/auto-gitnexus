"""
评论管理脚本
支持获取、创建、更新、删除工单评论
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


def get_issue_comments(issue_key: str):
    """
    获取单个工单的评论列表
    """
    response = utils.api_request(f'issue/{issue_key}/comment', method='GET')

    if not response['success']:
        utils.log_to_agent(response)
        sys.exit(1)

    data = response.get('data', {})
    comments = data.get('comments', [])
    clean_comments = []
    for c in comments:
        author = c.get('author', {}) or {}
        update_author = c.get('updateAuthor', {}) or {}
        clean_comments.append({
            'id': c.get('id'),
            'body': c.get('body'),
            'author': author.get('displayName') or author.get('name'),
            'author_key': author.get('name'),
            'update_author': update_author.get('displayName') or update_author.get('name'),
            'created': c.get('created'),
            'updated': c.get('updated')
        })

    utils.log_to_agent({
        'success': True,
        'issue': issue_key,
        'total_comments': len(clean_comments),
        'comments': clean_comments
    })


def add_comment(issue_key: str, comment_body: str):
    """
    给工单添加评论
    :param issue_key: 工单 KEY
    :param comment_body: 评论内容
    """
    payload = {
        "body": comment_body
    }

    response = utils.api_request(f'issue/{issue_key}/comment', method='POST', data=payload)

    if not response['success']:
        utils.log_to_agent(response)
        sys.exit(1)

    data = response.get('data', {})
    utils.log_to_agent({
        'success': True,
        'message': f'评论已成功添加到工单 {issue_key}',
        'issue': issue_key,
        'comment_id': data.get('id')
    })


def update_comment(issue_key: str, comment_id: str, comment_body: str):
    """
    更新工单评论
    :param issue_key: 工单 KEY
    :param comment_id: 评论 ID
    :param comment_body: 新的评论内容
    """
    payload = {
        "body": comment_body
    }

    response = utils.api_request(f'issue/{issue_key}/comment/{comment_id}', method='PUT', data=payload)

    if not response['success']:
        utils.log_to_agent(response)
        sys.exit(1)

    utils.log_to_agent({
        'success': True,
        'message': f'工单 {issue_key} 的评论 {comment_id} 已成功更新',
        'issue': issue_key,
        'comment_id': comment_id
    })


def delete_comment(issue_key: str, comment_id: str):
    """
    删除工单评论
    :param issue_key: 工单 KEY
    :param comment_id: 评论 ID
    """
    response = utils.api_request(f'issue/{issue_key}/comment/{comment_id}', method='DELETE')

    if not response['success']:
        utils.log_to_agent(response)
        sys.exit(1)

    utils.log_to_agent({
        'success': True,
        'message': f'工单 {issue_key} 的评论 {comment_id} 已成功删除',
        'issue': issue_key,
        'comment_id': comment_id
    })


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Jira 7.5.2 评论管理')
    parser.add_argument('--action', type=str, required=True,
                        choices=['list', 'add', 'update', 'delete'],
                        help='操作类型: list/add/update/delete')
    parser.add_argument('--issue', type=str, required=True, help='工单 KEY')
    parser.add_argument('--comment-id', type=str, help='评论 ID (update/delete 时必需)')
    parser.add_argument('--body', type=str, help='评论内容 (add/update 时必需)')
    parser.add_argument('--workdir', type=str, required=True, help='工作目录(用户空间tmp路径)')

    args = parser.parse_args()
    utils.validate_workdir(args.workdir)
    utils.set_workdir(args.workdir)

    if args.action == 'list':
        get_issue_comments(args.issue)

    elif args.action == 'add':
        if not args.body:
            print(json.dumps({
                'success': False,
                'error': 'add 操作需要 --body 参数'
            }, ensure_ascii=False, indent=2))
            sys.exit(1)
        add_comment(args.issue, args.body)

    elif args.action == 'update':
        if not args.comment_id or not args.body:
            print(json.dumps({
                'success': False,
                'error': 'update 操作需要 --comment-id 和 --body 参数'
            }, ensure_ascii=False, indent=2))
            sys.exit(1)
        update_comment(args.issue, args.comment_id, args.body)

    elif args.action == 'delete':
        if not args.comment_id:
            print(json.dumps({
                'success': False,
                'error': 'delete 操作需要 --comment-id 参数'
            }, ensure_ascii=False, indent=2))
            sys.exit(1)
        delete_comment(args.issue, args.comment_id)
