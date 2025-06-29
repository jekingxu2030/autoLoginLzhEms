
## 环境要求
- Python 3.8+
- Chrome浏览器

## 安装步骤
1. 安装依赖包：
```bash
pip install -r requirements.txt
```

2. 运行程序：
```bash
先进入虚拟环境
.\venv\Scripts\activate
再运行程序
python autoLogin.py
```
打包exe
```bash
pyinstaller autoLogin.py
执行打包后的程序
.\dist\XXX.exe
## 功能说明
1. 自动登录EMS管理后台
2. 自动识别验证码（失败后支持人工输入）
3. 实时获取并显示仪表盘数据
4. 提供图形界面，方便监控和操作

## 使用方法
1. 点击"启动监控"按钮开始监控
2. 程序会自动进行登录和数据获取
3. 如果验证码识别失败三次，会弹出输入框请求手动输入
4. 可以随时点击"停止监控"按钮结束监控
5. 所有操作日志都会实时显示在主界面
