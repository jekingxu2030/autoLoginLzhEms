import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii


def derive_key_from_pubkey(pubkey: str, method: str = "md5") -> bytes:
    """
    从RSA公钥字符串派生出AES密钥。
    可选方式：
        - md5
        - sha256_head（前16字节）
        - sha256_tail（后16字节）
    """
    pubkey_bytes = pubkey.encode()

    if method == "md5":
        return hashlib.md5(pubkey_bytes).digest()
    elif method == "sha256_head":
        return hashlib.sha256(pubkey_bytes).digest()[:16]
    elif method == "sha256_tail":
        return hashlib.sha256(pubkey_bytes).digest()[-16:]
    else:
        raise ValueError("不支持的 key 派生方法")


def encrypt_token(
    user_id: str, sa_token: str, locale: str, pubkey: str, method: str = "md5"
) -> str:
    """
    使用 AES/ECB/PKCS7 加密明文："userId;saToken;locale"
    输出十六进制格式的密文（用于 URL token）
    """
    plain_text = f"{user_id};{sa_token};{locale}"
    key = derive_key_from_pubkey(pubkey, method)

    cipher = AES.new(key, AES.MODE_ECB)
    padded_data = pad(plain_text.encode(), AES.block_size)
    encrypted_bytes = cipher.encrypt(padded_data)

    return encrypted_bytes.hex()


# ==== 示例使用 ====

if __name__ == "__main__":
    user_id = "47"
    sa_token = "CeN8ZB8ckcgKu9SMidqu3pcQRSlLFHdTN3gCFd6Usg64Qv4jz3WA4SMRncF3364z"  # ← 你需要替换成实际抓包获取的 token
    locale = "zh_CN"

    pubkey = (
        "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA19NGKxVdUVZOM/zJBY/oP0UE+"
        "OCNA4+1jL4rmi+wQUUP6LjuAY+tHV2uoxlH9363CjYlledG5rwguoC5Dy+p6Hp2YJ6b0mi"
        "g9z2j0kD36y+lSr6I84wKU1SmapuJ40lHV7vf359z+XgnGR/p8XpApT3ObrS9gv4L9Ntn4"
        "DsRN7bEzbojsZcHUFTUNytj6P2TRzPbMaHz7Xdxa1o1+9xR5vCokTavR+t0sxuHidDkLrj"
        "Gij3ehAEGFPzWqGnwGn97ROAmRuVcB8ROIifh7VC8XrpCE0ElVwsWjRace/23toRPPaHlr"
        "IiHlcQWEYL5mZkYtOjsEwggT4vBHEm8RU3H3QIDAQAB"
    )

    print("=== 尝试不同派生方式 ===")
    for method in ["md5", "sha256_head", "sha256_tail"]:
        encrypted_hex = encrypt_token(user_id, sa_token, locale, pubkey, method)
        print(f"[{method}] 加密后的 token：{encrypted_hex}")


# 实际网站生成WS Token：
# 20ff328a0366e2487cbc5a7564129a4c3cecf1279bb5d7347bbd0716a56e5226c12e1fba7a2851f44e562eae67f70dc4cbd1e173634370812163a4bb9eefdcc56fdc208caa081042c32cf1723e8571db: 