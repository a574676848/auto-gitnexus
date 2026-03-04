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

def setup_credentials(user: str, token: str, domain: str):
    """
    将认证凭证安全地保存至用户本地目录下
    """
    creds = {
        "user": user,
        "token": token,
        "domain": domain
    }
    
    try:
        # 在 Windows 和 Linux 上创建文件并设置权限
        with open(utils.CREDENTIALS_FILE, 'w', encoding='utf-8') as f:
            json.dump(creds, f, ensure_ascii=False, indent=2)
            
        # 尽量限制文件权限 (类 Unix 环境适用)
        try:
            os.chmod(utils.CREDENTIALS_FILE, 0o600)
        except Exception:
            pass # Windows 可能不支持 chmod 0600，忽略即可
            
        utils.log_to_agent({
            "success": True,
            "message": f"配置信息已成功保存至 {utils.CREDENTIALS_FILE}，你可以继续之前被中断的工作。"
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
    
    args = parser.parse_args()
    setup_credentials(args.user, args.token, args.domain)
