import zipfile
import os

def verify_package():
    """验证打包文件内容"""
    
    # 找到最新的压缩包
    zip_files = [f for f in os.listdir('.') if f.startswith('autoLoginLzhEms_') and f.endswith('.zip')]
    
    if not zip_files:
        print("❌ 未找到打包的压缩文件")
        return
    
    # 使用最新的压缩包
    latest_zip = sorted(zip_files)[-1]
    print(f"📦 验证压缩包: {latest_zip}")
    print(f"📊 文件大小: {os.path.getsize(latest_zip) / 1024 / 1024:.2f} MB")
    
    try:
        with zipfile.ZipFile(latest_zip, 'r') as zipf:
            print(f"📁 压缩包内文件总数: {len(zipf.namelist())}")
            print("\n📋 主要文件列表:")
            
            # 关键文件检查
            key_files = [
                'autoLogin.py',
                'config.json',
                'requirements.txt',
                '安装说明.txt',
                'readme.md'
            ]
            
            found_files = []
            for file_info in zipf.namelist():
                # 显示主要文件
                for key_file in key_files:
                    if key_file in file_info:
                        found_files.append(key_file)
                        print(f"  ✅ {file_info}")
                        break
                
                # 显示目录结构
                if '/' in file_info and file_info.count('/') == 1:
                    print(f"  📂 {file_info}")
            
            print(f"\n🔍 关键文件检查:")
            for key_file in key_files:
                if key_file in found_files:
                    print(f"  ✅ {key_file} - 已找到")
                else:
                    print(f"  ❌ {key_file} - 缺失")
            
            # 检查是否有数据文件
            data_files = [f for f in zipf.namelist() if f.startswith('dataLog/') or f.startswith('downloaded_js/')]
            if data_files:
                print(f"\n📊 数据文件:")
                print(f"  ✅ dataLog 目录 - {len([f for f in data_files if f.startswith('dataLog/')])} 个文件")
                print(f"  ✅ downloaded_js 目录 - {len([f for f in data_files if f.startswith('downloaded_js/')])} 个文件")
            
            print(f"\n🎉 压缩包验证完成!")
            print(f"💾 完整压缩包路径: {os.path.abspath(latest_zip)}")
            
    except zipfile.BadZipFile:
        print("❌ 压缩包文件损坏")
    except Exception as e:
        print(f"❌ 验证过程中出现错误: {e}")

if __name__ == "__main__":
    verify_package()