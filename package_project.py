import os
import shutil
import zipfile
import datetime

def create_project_package():
    """创建项目打包文件"""
    
    # 项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # 创建打包目录
    package_name = f"autoLoginLzhEms_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    package_dir = os.path.join(project_root, package_name)
    
    # 需要打包的文件和目录
    items_to_package = [
        # Python源文件
        'autoLogin.py',
        'dingtalk_notify.py',
        'email_sender_qq.py',
        'email_sender_wy.py',
        'ems_ws_monitor.py',
        'page_status_checker.py',
        'settings_window.py',
        
        # 配置文件
        'config.json',
        'config.ini',
        'email_config.json',
        'requirements.txt',
        
        # 文档文件
        'readme.md',
        
        # 数据目录
        'dataLog',
        'downloaded_js',
        
        # Git忽略文件
        '.gitignore'
    ]
    
    try:
        # 创建打包目录
        os.makedirs(package_dir, exist_ok=True)
        print(f"创建打包目录: {package_dir}")
        
        # 复制文件和目录
        for item in items_to_package:
            source_path = os.path.join(project_root, item)
            dest_path = os.path.join(package_dir, item)
            
            if os.path.exists(source_path):
                if os.path.isfile(source_path):
                    # 复制文件
                    shutil.copy2(source_path, dest_path)
                    print(f"复制文件: {item}")
                elif os.path.isdir(source_path):
                    # 复制目录
                    shutil.copytree(source_path, dest_path)
                    print(f"复制目录: {item}")
            else:
                print(f"警告: 文件/目录不存在: {item}")
        
        # 创建requirements.txt（如果不存在）
        requirements_path = os.path.join(package_dir, 'requirements.txt')
        if not os.path.exists(requirements_path):
            requirements_content = """selenium==4.16.0
pillow==10.1.0
ddddocr==1.4.7
requests==2.31.0
PyQt5==5.15.10
PyQtWebEngine==5.15.6
webdriver_manager==4.0.1
websockets==12.0
aiohttp==3.9.1
pymysql==1.1.0
pycryptodome==3.20.0
websocket-client==1.7.0
psutil==5.9.6"""
            
            with open(requirements_path, 'w', encoding='utf-8') as f:
                f.write(requirements_content)
            print("创建requirements.txt文件")
        
        # 创建安装说明
        install_guide_path = os.path.join(package_dir, '安装说明.txt')
        install_guide_content = f"""自动登录监控系统 - 安装说明

项目打包时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== 系统要求 ===
1. Python 3.8 或更高版本
2. Windows操作系统
3. Chrome浏览器及对应版本的ChromeDriver

=== 安装步骤 ===
1. 解压本压缩包到任意目录
2. 打开命令行，进入解压后的目录
3. 安装依赖包:
   pip install -r requirements.txt
4. 配置config.json文件中的账号信息
5. 运行程序:
   python autoLogin.py

=== 配置文件说明 ===
- config.json: 主配置文件，包含账号、定时器、加密密钥等
- config.ini: 运行时生成的配置文件，保存WebSocket地址等
- email_config.json: 邮件发送配置

=== 主要功能 ===
- 自动登录EMS系统
- 实时监控WebSocket数据
- 钉钉消息通知
- 邮件通知
- 数据记录和统计

=== 注意事项 ===
- 首次运行需要配置正确的账号密码
- 确保网络连接正常
- 定期检查日志文件debug.log

如有问题，请查看readme.md文件或联系开发团队。
"""
        
        with open(install_guide_path, 'w', encoding='utf-8') as f:
            f.write(install_guide_content)
        print("创建安装说明文件")
        
        # 创建ZIP压缩包
        zip_path = f"{package_dir}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, package_dir)
                    zipf.write(file_path, arcname)
        
        print(f"\n打包完成!")
        print(f"打包目录: {package_dir}")
        print(f"压缩文件: {zip_path}")
        print(f"\n打包内容:")
        
        # 显示打包内容
        for root, dirs, files in os.walk(package_dir):
            level = root.replace(package_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
        
        return zip_path
        
    except Exception as e:
        print(f"打包过程中出现错误: {e}")
        return None
    
    finally:
        # 清理临时目录
        if os.path.exists(package_dir):
            shutil.rmtree(package_dir)
            print(f"清理临时目录: {package_dir}")

if __name__ == "__main__":
    print("开始打包项目...")
    zip_file = create_project_package()
    
    if zip_file:
        print(f"\n✅ 项目打包成功!")
        print(f"📦 压缩包路径: {zip_file}")
        print(f"📊 文件大小: {os.path.getsize(zip_file) / 1024 / 1024:.2f} MB")
    else:
        print("\n❌ 项目打包失败!")