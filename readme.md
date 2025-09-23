
## 环境要求


- 注意本项目需要调用谷歌浏览器使用，浏览器需要登录才能被调起！
- Python 3.8+
- Chrome浏览器

## 安装步骤
1. 安装依赖包：
```bash
pip install -r requirements.txt
```

2. 运行程序：
```bash
先进入虚拟环境   --本项目不需要虚拟环境
.\venv\Scripts\activate    
再运行程序
python autoLogin.py
```

## 📦 项目打包状态

✅ **打包已完成！**
- 可执行文件：`autoLoginLzhEms.exe` (81.97 MB)
- 分发包：`autoLoginLzhEms_Dist_20250923_121427.zip` (81.25 MB)
- 打包时间：2025-09-23 12:14:27

## 打包说明

### 方法一：基础打包（推荐）
```bash
# 使用PyInstaller打包成单个可执行文件
pyinstaller --clean --noconfirm autoLogin.spec

# 打包完成后，可执行文件在 dist\autoLoginLzhEms.exe
# 直接运行即可使用
```

### 方法二：完整分发包（包含配置）
```bash
# 创建包含配置文件和使用说明的完整分发包
python create_dist_package.py

# 生成的分发包格式：autoLoginLzhEms_Dist_YYYYMMDD_HHMMSS.zip
# 包含内容：
#   - autoLoginLzhEms.exe（主程序）
#   - config/（配置文件目录）
#   - start.bat（启动脚本）
#   - 使用说明.txt（详细使用说明）
#   - data/（数据目录结构）
```

### 打包参数说明
- `--clean`：清理临时文件
- `--noconfirm`：覆盖输出不询问
- `--onefile`：打包成单个文件（已在.spec中配置）

### 打包后使用
1. 解压分发包到任意目录
2. 编辑 `config/config.json` 配置账号信息
3. 双击 `start.bat` 启动程序
4. 或直接运行 `autoLoginLzhEms.exe`

### 打包注意事项
- **文件大小**：打包后exe文件约80MB，包含所有依赖库
- **运行环境**：打包后的程序可在Windows 7/8/10/11上直接运行，无需安装Python
- **首次运行**：首次运行时会自动下载Chrome驱动（如未安装）
- **杀毒软件**：部分杀毒软件可能误报，请添加信任或白名单
- **管理员权限**：建议以管理员身份运行，避免权限问题
- **配置文件**：确保config.json中的账号密码正确，否则无法登录

### 常见问题
1. **打包失败**：检查是否安装了所有依赖包 `pip install -r requirements.txt`
2. **运行闪退**：查看同目录下的日志文件，或从命令行运行查看错误信息
3. **驱动下载失败**：手动下载ChromeDriver并放在程序目录
4. **打包后文件太大**：这是正常现象，PyInstaller会打包所有依赖库
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


最佳时间参数配置
{
  "timing": {
    "load_wait_time": 10,
    "loop_interval": 3,
    "dingtalk_times": 38
  }
}


钉钉接口官例子：


# POST https://oapi.dingtalk.com/robot/send?access_token=ACCESS_TOKEN
# {
#   "msgtype": "text", // 消息类型，可为 text、link、markdown、actionCard、feedCard
#   "text": {
#     "content": "这是一条文本消息内容"
#   },
#   "link": {
#     "messageUrl": "https://www.example.com", // 跳转链接
#     "picUrl": "https://example.com/image.png", // 图片链接
#     "text": "这是一条链接消息内容", // 消息内容
#     "title": "链接消息标题" // 消息标题
#   },
#   "markdown": {
#     "title": "Markdown消息标题",
#     "text": "#### 这是Markdown消息内容 \n ![图片](https://example.com/image.png)"
#   },
#   "actionCard": {
#     "title": "ActionCard消息标题",
#     "text": "#### 这是ActionCard内容 \n ![图片](https://example.com/image.png)",
#     "btnOrientation": "0", // 0-按钮竖直排列，1-按钮横向排列
#     "singleTitle": "阅读全文", // 单个按钮标题
#     "singleURL": "https://www.example.com", // 单个按钮跳转链接
#     "btns": [
#       {
#         "title": "按钮1",
#         "actionURL": "https://www.example.com/btn1"
#       },
#       {
#         "title": "按钮2",
#         "actionURL": "https://www.example.com/btn2"
#       }
#     ]
#   },
#   "feedCard": {
#     "links": [
#       {
#         "title": "FeedCard标题1",
#         "messageURL": "https://www.example.com/1",
#         "picURL": "https://example.com/image1.png"
#       },
#       {
#         "title": "FeedCard标题2",
#         "messageURL": "https://www.example.com/2",
#         "picURL": "https://example.com/image2.png"
#       }
#     ]
#   },
#   "at": {
#     "isAtAll": false, // 是否@所有人
#     "atUserIds": ["user001", "user002"], // 被@的用户ID列表
#     "atMobiles": ["15xxx", "18xxx"] // 被@的手机号列表
#   }
# }




   # Content = {
                        #     "title": "EMS 状态检查通知",
                        #     "text": (
                        #         f"Event: BY-01-EMS_StatusCheck\n"
                        #         f"State: Normal!\n"
                        #         f"CheckUrl: {driver.current_url}\n"
                        #         f"Message:网站数据正常，收到真实数据，请检查！\n"
                        #         f"Result: {result[:20]}\n"
                        #         f"WebSiteState: Accessible！"
                        #     ),
                        #     "messageUrl": "http://ems.hy-power.net:8114/login",  # 点击跳转链接
                        #     "picUrl": "http://ems.hy-power.net:8114/favicon.ico",  # 可以留空或者放图片链接
                        # }
                        
                        
                        
 # return (function() {
                  #     if (!window.echarts || !window.echarts.getInstanceByDom) {
                  #         return 'ECharts 未定义或未加载';
                  #     }
                  #     const charts = [];
                  #     document.querySelectorAll('div').forEach(el => {
                  #         try {
                  #             const chart = window.echarts.getInstanceByDom(el);
                  #             if (chart) charts.push(chart);
                  #         } catch (e) {
                  #         return e;
                  #         }
                  #     });
                  #     if (charts.length === 0) return '未找到图表实例';
                  #     let allDefault = true;
                  #     charts.forEach(chart => {
                  #         const option = chart.getOption();
                  #         if (option && option.series) {
                  #             option.series.forEach(series => {
                  #                 if (series.data) {
                  #                     const data = Array.isArray(series.data) ? series.data : [series.data];
                  #                     data.forEach(item => {
                  #                         const value = typeof item === 'object' ? item.value : item;
                  #                         if (value !== 87) allDefault = false;
                  #                     });
                  #                 }
                  #             });
                  #         }
                  #     });
                  #     return allDefault ? '所有数据均为默认值87' : '检测到真实数据';
                  # })();
                  
                  # -----测试OK的
                        # return (function () {
                        #     const result = [];
                        #     document.querySelectorAll('div').forEach((el, idx) => {
                        #         try {
                        #             const inst = window.echarts.getInstanceByDom(el);
                        #             if (!inst) return;
                        #             const opt = inst.getOption();
                        #             if (!opt.series) return;
                        #             opt.series.forEach((s, sIdx) => {
                        #                 // 取前 10 个点做样本
                        #                 const sample = (Array.isArray(s.data) ? s.data : [s.data])
                        #                                 .slice(0, 10)
                        #                                 .map(d => (typeof d === 'object' ? d.value : d));
                        #                 result.push({ chart: idx, series: sIdx, sample });
                        #             });
                        #         } catch (e) { /* 忽略 */ }
                        #     });
                        #     return JSON.stringify(result);
                        # })();
                        
                        
                        
                        
                        
                        