import requests
import json


def send_dingtalk_msg( content: str):
    """
    发送钉钉文本消息

    :param token: 钉钉机器人access_token
    :param content: 消息内容
    """
    Token = "2790e24fa6bb40ba86208e99c4b02223941b51a5b61d0f0e08820d3f461e330d"
    webhook = f"https://oapi.dingtalk.com/robot/send?access_token={Token}"
    headers = {"Content-Type": "application/json"}
    data = {"msgtype": "text", "text": {"content": content}}
    try:
        response = requests.post(
            webhook, headers=headers, data=json.dumps(data), timeout=5
        )
        if response.status_code == 200:
            print("✅ 钉钉消息推送成功")
        else:
            print(
                f"❌ 钉钉消息推送失败，状态码：{response.status_code}，响应内容：{response.text}"
            )
    except Exception as e:
        print(f"❌ 钉钉消息推送异常：{e}")
