import os
import shutil
import zipfile
import datetime

def create_distribution_package():
    """创建完整的分发包，包含可执行文件和必要配置"""
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # 创建dist_package目录
    dist_package_dir = os.path.join(project_root, "dist_package")
    if os.path.exists(dist_package_dir):
        shutil.rmtree(dist_package_dir)
    os.makedirs(dist_package_dir)
    
    print("📦 创建分发包...")
    
    # 1. 复制可执行文件
    exe_source = os.path.join(project_root, "dist", "autoLoginLzhEms.exe")
    exe_dest = os.path.join(dist_package_dir, "autoLoginLzhEms.exe")
    
    if os.path.exists(exe_source):
        shutil.copy2(exe_source, exe_dest)
        print(f"✅ 复制可执行文件: {os.path.getsize(exe_dest) / 1024 / 1024:.2f} MB")
    else:
        print("❌ 未找到可执行文件")
        return None
    
    # 2. 创建配置目录
    config_dir = os.path.join(dist_package_dir, "config")
    os.makedirs(config_dir)
    
    # 复制配置文件
    config_files = [
        "config.json",      # 主配置
        "email_config.json", # 邮件配置
        "readme.md"         # 说明文档
    ]
    
    for config_file in config_files:
        source = os.path.join(project_root, config_file)
        if os.path.exists(source):
            shutil.copy2(source, os.path.join(config_dir, config_file))
            print(f"✅ 复制配置文件: {config_file}")
    
    # 3. 创建数据目录结构
    data_dir = os.path.join(dist_package_dir, "data")
    os.makedirs(data_dir)
    
    # 创建空的dataLog和downloaded_js目录
    os.makedirs(os.path.join(data_dir, "dataLog"))
    os.makedirs(os.path.join(data_dir, "downloaded_js"))
    print("✅ 创建数据目录结构")
    
    # 4. 创建启动脚本
    start_script_content = """@echo off
echo 正在启动自动登录监控系统...
echo.

REM 检查配置文件
if not exist config\config.json (
    echo [错误] 配置文件 config\config.json 不存在
    echo 请配置您的账号信息后重新运行
    pause
    exit /b 1
)

REM 运行主程序
echo [成功] 正在启动程序...
start autoLoginLzhEms.exe

echo.
echo 程序已启动！请查看系统托盘或任务管理器确认运行状态。
echo 按任意键关闭此窗口...
pause > nul
"""
    
    with open(os.path.join(dist_package_dir, "start.bat"), 'w', encoding='utf-8') as f:
        f.write(start_script_content)
    print("✅ 创建启动脚本")
    
    # 5. 创建使用说明
    readme_content = f"""自动登录监控系统 - 分发包
版本: 2.0
打包时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== 文件结构 ===
autoLoginLzhEms.exe      # 主程序可执行文件
start.bat               # Windows启动脚本
config/                 # 配置文件目录
  ├── config.json       # 主配置文件（需要修改）
  ├── email_config.json # 邮件配置（可选）
  └── readme.md         # 项目说明
data/                   # 数据目录
  ├── dataLog/         # 日志数据目录
  └── downloaded_js/   # JavaScript文件目录

=== 快速开始 ===
1. 配置账号信息：
   - 编辑 config/config.json 文件
   - 填入您的用户名和密码
   - 配置钉钉通知token（可选）

2. 启动程序：
   - 双击 start.bat
   - 或直接运行 autoLoginLzhEms.exe

3. 程序特点：
   - 自动登录EMS系统
   - 实时监控WebSocket数据
   - 支持钉钉和邮件通知
   - 数据自动记录和统计

=== 系统要求 ===
- Windows 7/8/10/11
- Chrome浏览器（自动下载驱动）
- 网络连接正常

=== 注意事项 ===
- 首次运行需要配置正确的账号密码
- 确保网络连接正常
- 程序会在系统托盘运行
- 日志文件会保存在 data/dataLog/ 目录

=== 技术支持 ===
如有问题，请查看项目说明文档或联系开发团队。
"""
    
    with open(os.path.join(dist_package_dir, "使用说明.txt"), 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("✅ 创建使用说明")
    
    # 6. 创建压缩包
    zip_filename = f"autoLoginLzhEms_Dist_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_path = os.path.join(project_root, zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dist_package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, dist_package_dir)
                zipf.write(file_path, arcname)
    
    print(f"✅ 创建分发压缩包: {zip_filename}")
    print(f"📊 压缩包大小: {os.path.getsize(zip_path) / 1024 / 1024:.2f} MB")
    
    # 清理临时目录
    shutil.rmtree(dist_package_dir)
    print("✅ 清理临时文件")
    
    return zip_path

if __name__ == "__main__":
    print("🚀 创建完整分发包...")
    print("=" * 50)
    
    zip_path = create_distribution_package()
    
    if zip_path:
        print("\n" + "=" * 50)
        print("🎉 分发包创建成功!")
        print(f"📦 压缩包路径: {zip_path}")
        print("\n📋 分发包内容:")
        print("  ✓ 可执行文件 (.exe)")
        print("  ✓ 配置文件 (.json)")
        print("  ✓ 启动脚本 (.bat)")
        print("  ✓ 使用说明 (.txt)")
        print("  ✓ 数据目录结构")
        print("\n🎯 用户只需:")
        print("1. 解压压缩包")
        print("2. 修改config/config.json中的账号")
        print("3. 双击 start.bat 启动程序")
    else:
        print("\n❌ 分发包创建失败!")