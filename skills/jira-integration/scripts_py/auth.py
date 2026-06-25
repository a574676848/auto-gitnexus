import argparse
import json
import os
import sys

# 引入本模块的公共功能
try:
    import utils
except ImportError:
    # 允许作为顶层单独执行的后盾支持
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import utils

def setup_credentials(user: str, token: str, domain: str, workdir: str):
    """
    将认证凭证安全地保存至本地目录。
    如果用户级（~/{CREDENTIALS_FILENAME}）已存在凭证，则跳过写入 workdir；
    否则写入到 workdir 下（项目级隔离）。
    """
    utils.set_workdir(workdir)

    creds = {
        "user": user,
        "token": token,
        "domain": domain
    }

    # 检查用户级凭证是否已存在
    user_level_creds = os.path.expanduser(f'~/{utils.CREDENTIALS_FILENAME}')
    if os.path.exists(user_level_creds):
        try:
            with open(user_level_creds, 'r', encoding='utf-8') as f:
                existing = json.load(f)
                # 如果用户级凭证已存在且有效，跳过写入 workdir
                if existing.get('user') and existing.get('token') and existing.get('domain'):
                    utils.log_to_agent({
                        "success": True,
                        "message": f"检测到用户级凭证已存在（{user_level_creds}），已跳过写入 workdir。你可以继续之前被中断的工作。"
                    })
                    return
        except Exception:
            # 用户级凭证损坏或无法读取，继续写入 workdir
            pass

    # 写入到 workdir 下（项目级）
    creds_file = utils.get_credentials_file()

    try:
        # 在 Windows 和 Linux 上创建文件并设置权限
        with open(creds_file, 'w', encoding='utf-8') as f:
            json.dump(creds, f, ensure_ascii=False, indent=2)

        # 尽量限制文件权限 (类 Unix 环境适用)
        try:
            os.chmod(creds_file, 0o600)
        except Exception:
            pass # Windows 可能不支持 chmod 0600，忽略即可

        utils.log_to_agent({
            "success": True,
            "message": f"配置信息已成功保存至 {creds_file}，你可以继续之前被中断的工作。"
        })
    except Exception as e:
         utils.log_to_agent({
            "success": False,
            "error_type": "FS_WRITE_ERROR",
            "message": f"保存凭证文件失败：{e}"
        })

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="配置和保存 Jira 认证信息")
    parser.add_argument('--user', type=str, required=True, help="用户的登录邮箱/账号")
    parser.add_argument('--token', type=str, required=True, help="API Token 或密码")
    parser.add_argument('--domain', type=str, required=True, help="Jira 域名 (如 jira.example.com)")
    parser.add_argument('--workdir', type=str, required=True, help="工作目录(用户空间tmp路径)")
    
    args = parser.parse_args()
    utils.validate_workdir(args.workdir)
    setup_credentials(args.user, args.token, args.domain, args.workdir)
