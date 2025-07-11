

import requests
import json


def send_dingtalk_msg(content: str) -> bool:

# def send_dingtalk_msg(content:dict) -> bool:
    """
        发送钉钉文本消息，返回是否成功
        """
    # Token = "2790e24fa6bb40ba86208e99c4b02223941b51a5b61d0f0e08820d3f461e330d"
    Token = "aa0366d18f2307daa196c4f96546ed629a92b110448ed104614fe9566dfa1b14"
    webhook = f"https://oapi.dingtalk.com/robot/send?access_token={Token}"
    headers = {"Content-Type": "application/json"}
    data = {"msgtype": "text", "text": {"content": content}} #纯文本
    # data = {"msgtype": "link", "link":  content}
    try:
        response = requests.post(
            webhook, headers=headers, data=json.dumps(data), timeout=5
        )
        print(f"钉钉接口返回状态码: {response.status_code}")
        # print(f"钉钉接口返回内容: {response.text}")
        if response.status_code == 200:
            result = response.json()
            if result.get("errcode") == 0:
                print("✅ 钉钉消息推送成功")
                return True
            else:
                print(
                    f"❌ 钉钉接口错误: errcode={result.get('errcode')}, errmsg={result.get('errmsg')}"
                )
        else:
            print(f"❌ 钉钉消息推送失败，状态码：{response.status_code}")
    except Exception as e:
        print(f"❌ 钉钉消息推送异常：{e}")
    return False
