"""email_sender.py – WIC‑Power SMTP 发信模块（v3）
================================================
此版本在你给出的基础上新增：
1. **自动补全发件人域名** (`@wic-power.cn`)，避免外部服务器拒收。
2. **可传入自定义 `from_addr`**（既作 Envelope‑From 亦作 `From:` 头）。
3. 连接调试更完善，打印 Message‑ID 与队列码。

示例::

    from email_sender import send_email

    # 外部
    send_email("jekingxu@163.com", "主题", "正文...", from_addr="notice@wic-power.cn")

    # 内部，username 无 @ 也可
    send_email("it@wic-power.cn", "内部", "hello")

依赖全为标准库。
"""

import email.utils
import os
import smtplib
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional, Union, List

# from autoLogin import thread_safe_update_debug_label

###############################################################################
# 默认 SMTP 配置，可通过环境变量覆盖
###############################################################################

# SMTP_HOST = os.getenv("SMTP_HOST", "email.wic-power.cn")
# SMTP_HOST = os.getenv("SMTP_HOST", "smtp.163.com")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.qq.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
# SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "531556397@qq.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "kjsqxtoiwqumbhjb")  # qq
# SMTP_USERNAME = os.getenv("SMTP_USERNAME", "jekingxu@163.com")
# SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "KNwjzDdvVh29NdV") #163

# TLS和SSL只能同时开一种
USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
DEBUG = os.getenv("SMTP_DEBUG", "false").lower() == "true"
DEFAULT_DOMAIN = os.getenv("SMTP_DEFAULT_DOMAIN", "qq.com")
# DEFAULT_DOMAIN = os.getenv("SMTP_DEFAULT_DOMAIN", "163.com")

###############################################################################
# 核心类
###############################################################################


class EmailSender:
    """封装简易 SMTP 邮件发送。"""

    def __init__(
        self,
        smtp_host: str = SMTP_HOST,
        smtp_port: int = SMTP_PORT,
        username: str = SMTP_USERNAME,
        password: str = SMTP_PASSWORD,
        use_tls: bool = USE_TLS,
        debug: bool = DEBUG,
        default_domain: str = DEFAULT_DOMAIN,
    ) -> None:
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.debug = debug
        self.default_domain = default_domain

    # ------------------------------------------------------------------
    def _auto_addr(self, addr: str) -> str:
        """确保地址含 @；若缺失则追加默认域。"""
        return addr if "@" in addr else f"{addr}@{self.default_domain}"

    # ------------------------------------------------------------------
    def _make_msg(
        self,
        from_addr: str,
        to_addr: str,
        subject: str,
        body: str,
    ) -> MIMEMultipart:
        msg = MIMEMultipart()
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg["Date"] = email.utils.formatdate(localtime=True)
        msg["Message-ID"] = email.utils.make_msgid(domain=self.default_domain)
        msg.attach(MIMEText(body, "plain", "utf-8"))
        return msg

    # ------------------------------------------------------------------
    def send(
        self,
        to_addr: Union[str, List[str]],
        subject: str,
        body: str,
        from_addr: Optional[str] = None,
    ) -> Dict[str, Any]:
        """发送邮件并返回 ``success`` 与 ``response``。

        参数:
            to_addr: 可以是单个收件人地址字符串，或收件人地址列表
        """
        from_real = self._auto_addr(from_addr or self.username)
        to_real = [self._auto_addr(addr) for addr in ([to_addr] if isinstance(to_addr, str) else to_addr)]

        if self.debug:
            print(
                f"⚡ SMTP服务器配置 → 主机: {self.smtp_host}, 端口: {self.smtp_port}, TLS: {self.use_tls}\n"
                f"用户名: {self.username}, 默认域名: {self.default_domain}\n"
                f"⚡ Connecting → {self.smtp_host}:{self.smtp_port} (TLS={self.use_tls})\n"
                f"Envelope‑From: {from_real} → To: {to_real}"
            )

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                if self.debug:
                    server.set_debuglevel(1)

                code, reply = server.ehlo()
                if self.debug:
                    print(f"EHLO → {code} {reply.decode(errors='ignore')}")

                if self.use_tls:
                    if self.debug:
                        print("⚡ STARTTLS …")
                    code, reply = server.starttls()
                    if self.debug:
                        print(f"STARTTLS → {code} {reply.decode(errors='ignore')}")
                    code, reply = server.ehlo()
                    if self.debug:
                        print(f"EHLO (TLS) → {code} {reply.decode(errors='ignore')}")

                if self.debug:
                    print("⚡ LOGIN …")
                code, reply = server.login(self._auto_addr(self.username), self.password)
                if self.debug:
                    print(f"LOGIN → {code} {reply.decode(errors='ignore')}")

                msg = self._make_msg(from_real, to_real[0], subject, body)
                if self.debug:
                    print("⚡ SENDMAIL …")
                response = server.sendmail(from_real, to_real, msg.as_string())

                if response == {}:
                    print("✔ 邮件发送成功！Message‑ID:", msg["Message-ID"])
                    return {"success": True, "response": "250 Queued"}
                else:
                    print("✖ 部分收件人失败:", response)
                    return {"success": False, "response": str(response)}

        except Exception as e:
            if self.debug:
                tb = traceback.format_exc()
                print("！ 发送过程中出现异常:\n", tb)
            return {"success": False, "response": str(e)}


###############################################################################
# 对外函数
###############################################################################

_default_sender = EmailSender()


def send_email(
    to_addr: Union[str, List[str]],
    subject: str,
    body: str,
    from_addr: Optional[str] = None,
) -> Dict[str, Any]:
    """快捷函数：直接发信，可自定义发件人。

    参数:
        to_addr: 可以是单个收件人地址字符串，或收件人地址列表
    """
    return _default_sender.send(to_addr, subject, body, from_addr=from_addr)


__all__ = ["send_email", "EmailSender"]

###############################################################################
# CLI 测试
###############################################################################

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Quick email sender for WIC‑Power")
    parser.add_argument("--to", required=True, help="Recipient email address")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--body", required=True, help="Email body text")
    parser.add_argument("--from_addr", help="Override From address")
    args = parser.parse_args()

    result = send_email(args.to, args.subject, args.body, from_addr=args.from_addr)
    print("Result:", result)
