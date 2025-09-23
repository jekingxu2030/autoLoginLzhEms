import PyInstaller.__main__
import os
import shutil

def build_executable():
    """构建可执行文件"""
    
    # 项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # 清理旧的构建文件
    dist_dir = os.path.join(project_root, "dist")
    build_dir = os.path.join(project_root, "build")
    
    print("🧹 清理旧的构建文件...")
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    
    # PyInstaller参数
    args = [
        'autoLogin.py',  # 主程序文件
        '--name=autoLoginLzhEms',  # 可执行文件名称
        '--distpath=dist',  # 输出目录
        '--workpath=build',  # 工作目录
        '--specpath=build',  # spec文件目录
        '--onefile',  # 打包成单个文件
        '--windowed',  # Windows窗口模式（无控制台）
        '--clean',  # 清理临时文件
        '--noconfirm',  # 覆盖输出目录不确认
        
        # 添加数据文件 (Windows路径格式)
        f'--add-data={os.path.join(project_root, "config.json")};.',
        f'--add-data={os.path.join(project_root, "config.ini")};.',
        f'--add-data={os.path.join(project_root, "email_config.json")};.',
        f'--add-data={os.path.join(project_root, "readme.md")};.',
        f'--add-data={os.path.join(project_root, "dataLog")};dataLog',
        f'--add-data={os.path.join(project_root, "downloaded_js")};downloaded_js',
        
        # 添加图标（如果有的话）
        # '--icon=app.ico',
        
        # 隐藏导入的模块
        '--hidden-import=selenium',
        '--hidden-import=PIL',
        '--hidden-import=ddddocr',
        '--hidden-import=requests',
        '--hidden-import=PyQt5',
        '--hidden-import=PyQtWebEngine',
        '--hidden-import=webdriver_manager',
        '--hidden-import=websockets',
        '--hidden-import=aiohttp',
        '--hidden-import=pymysql',
        '--hidden-import=Crypto',
        '--hidden-import=websocket',
        '--hidden-import=psutil',
        '--hidden-import=tkinter',
        
        # 排除不必要的模块
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=pandas',
        '--exclude-module=scipy',
        
        # 其他选项
        '--upx-dir=upx',  # UPX压缩工具目录（如果有的话）
        '--log-level=INFO',  # 日志级别
    ]
    
    print("🔨 开始构建可执行文件...")
    print("📋 构建参数:")
    for arg in args:
        if arg.startswith('--'):
            print(f"  {arg}")
        else:
            print(f"    {arg}")
    
    try:
        # 运行PyInstaller
        PyInstaller.__main__.run(args)
        
        print("\n✅ 构建完成!")
        
        # 验证输出文件
        exe_path = os.path.join(dist_dir, "autoLoginLzhEms.exe")
        if os.path.exists(exe_path):
            file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
            print(f"📦 可执行文件路径: {exe_path}")
            print(f"📊 文件大小: {file_size:.2f} MB")
            
            # 列出dist目录内容
            print(f"\n📁 dist目录内容:")
            for item in os.listdir(dist_dir):
                item_path = os.path.join(dist_dir, item)
                if os.path.isfile(item_path):
                    size = os.path.getsize(item_path) / (1024 * 1024)  # MB
                    print(f"  📄 {item} ({size:.2f} MB)")
                else:
                    print(f"  📂 {item}/")
                    # 列出子目录内容
                    for subitem in os.listdir(item_path):
                        subitem_path = os.path.join(item_path, subitem)
                        if os.path.isfile(subitem_path):
                            size = os.path.getsize(subitem_path) / 1024  # KB
                            print(f"    📄 {subitem} ({size:.1f} KB)")
                        else:
                            print(f"    📂 {subitem}/")
            
            return exe_path
        else:
            print("❌ 构建失败: 未找到生成的可执行文件")
            return None
            
    except Exception as e:
        print(f"❌ 构建过程中出现错误: {e}")
        return None

if __name__ == "__main__":
    print("🚀 开始打包Python项目为可执行文件...")
    print("=" * 50)
    
    exe_path = build_executable()
    
    if exe_path:
        print("\n" + "=" * 50)
        print("🎉 打包成功!")
        print(f"📦 可执行文件: {exe_path}")
        print("\n📋 使用说明:")
        print("1. 运行 dist/autoLoginLzhEms.exe 即可启动程序")
        print("2. 首次运行会在当前目录生成必要的配置文件")
        print("3. 确保Chrome浏览器已安装")
        print("4. 检查config.json中的配置是否正确")
    else:
        print("\n❌ 打包失败，请检查错误信息")