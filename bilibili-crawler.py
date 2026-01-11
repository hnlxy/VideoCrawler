import os
import re
import json
import requests
import subprocess
from urllib.parse import quote
from datetime import datetime
import time

def sanitize_filename(title):
    """清理文件名中的非法字符"""
    return "".join([c if c.isalnum() or c in (' ', '_', '-', '.') else '_' for c in title])

def download_file(url, path, headers):
    """带进度显示的文件下载函数"""
    with requests.get(url, headers=headers, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        downloaded = 0
        
        with open(path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    print(f"\r下载进度: {downloaded/total_size:.1%}", end='')
    print(f"\n文件已保存到: {os.path.abspath(path)}")

def load_config(config_file="bilibili-video-config.json"):
    """加载配置文件"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"配置文件 {config_file} 不存在，请先创建配置文件")
        return None
    except json.JSONDecodeError as e:
        print(f"配置文件格式错误: {e}")
        return None

def create_sample_config():
    """创建示例配置文件"""
    sample_config = {
        "videos": [
            {
                "name": "示例视频1",
                "url": "https://www.bilibili.com/video/BV1xxxxxxxxx/",
                "cookie": "cookie内容"
            },
            {
                "name": "示例视频2", 
                "url": "https://www.bilibili.com/video/BV2xxxxxxxxx/",
                "cookie": "cookie内容"
            }
        ],
        "settings": {
            "output_directory": "downloads",
            "temp_directory": "temp",
            "ffmpeg_path": "ffmpeg",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    }
    
    with open("config.json", 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, ensure_ascii=False, indent=2)
    print("已创建示例配置文件 config.json，请修改其中的URL和Cookie")

def download_single_video(video_config, settings):
    """下载单个视频"""
    url = video_config['url']
    cookie = video_config['cookie']
    video_name = video_config.get('name', 'unknown_video')
    
    print(f"\n{'='*50}")
    print(f"开始下载: {video_name}")
    print(f"URL: {url}")
    print(f"{'='*50}")
    
    # 请求头配置
    headers = {
        "Referer": url,
        "User-Agent": settings['user_agent'],
        "Cookie": cookie,
        "Origin": "https://www.bilibili.com"
    }

    # 初始化变量
    video_path = None
    audio_path = None
    
    try:
        print("正在获取页面信息...")
        response = requests.get(url=url, headers=headers)
        response.raise_for_status()
        html = response.text

        # 提取视频标题
        title_patterns = [
            r'<title data-vue-meta="true">(.*?)_哔哩哔哩_bilibili</title>',
            r'<title>(.*?)_哔哩哔哩_bilibili</title>',
            r'"title":"(.*?)"',
            r'<h1[^>]*title="([^"]*)"',
        ]
        
        title = None
        for pattern in title_patterns:
            matches = re.findall(pattern, html)
            if matches:
                title = matches[0]
                break
        
        if not title:
            print("警告：无法提取视频标题，使用配置中的名称")
            title = video_name
        
        safe_title = sanitize_filename(title)
        print(f"视频标题: {title}")

        # 提取视频信息
        playinfo_patterns = [
            r'window\.__playinfo__=(.*?)</script>',
            r'window\.__playinfo__\s*=\s*(.*?);',
            r'"playInfo":(.*?),"videoData"',
        ]
        
        json_data = None
        for pattern in playinfo_patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            if matches:
                try:
                    json_data = json.loads(matches[0])
                    break
                except json.JSONDecodeError:
                    continue
        
        if not json_data:
            print("错误：无法提取视频播放信息")
            print("可能的原因：")
            print("1. Cookie已过期，请更新Cookie")
            print("2. 视频需要登录或有访问限制")
            print("3. B站页面结构发生变化")
            return False

        # 获取音视频URL
        try:
            video_url = json_data['data']['dash']['video'][0]['baseUrl']
            audio_url = json_data['data']['dash']['audio'][0]['baseUrl']
        except (KeyError, IndexError) as e:
            print(f"错误：无法获取视频/音频URL: {e}")
            print("视频可能需要大会员权限或有其他限制")
            return False
        
        # 视频下载头需要Range参数
        video_headers = headers.copy()
        video_headers["Range"] = "bytes=0-"

        # 创建目录
        temp_dir = settings['temp_directory']
        output_dir = settings['output_directory']
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # 下载视频和音频
        print("\n正在下载视频流...")
        video_path = os.path.join(temp_dir, f"video_{safe_title}.m4s")
        download_file(video_url, video_path, video_headers)

        print("\n正在下载音频流...")
        audio_path = os.path.join(temp_dir, f"audio_{safe_title}.m4s")
        download_file(audio_url, audio_path, headers)

        # 合并音视频
        print("\n正在合并音视频...")
        output_path = os.path.join(output_dir, f"{safe_title}.mp4")
        
        ffmpeg_cmd = [
            settings['ffmpeg_path'],
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-movflags', '+faststart',
            '-y',
            output_path
        ]
        
        subprocess.run(ffmpeg_cmd, check=True)
        print(f"\n✅ 下载完成！文件保存到: {os.path.abspath(output_path)}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg合并失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理临时文件
        if video_path and os.path.exists(video_path):
            os.remove(video_path)
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)

def main():
    """主函数"""
    print("B站视频批量下载器")
    print("=" * 50)
    
    # 加载配置
    config = load_config()
    if not config:
        print("是否创建示例配置文件？(y/n): ", end="")
        if input().lower() == 'y':
            create_sample_config()
        return
    
    videos = config.get('videos', [])
    settings = config.get('settings', {})
    
    # 设置默认值
    settings.setdefault('output_directory', 'downloads')
    settings.setdefault('temp_directory', 'temp')
    settings.setdefault('ffmpeg_path', 'ffmpeg')
    settings.setdefault('user_agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    if not videos:
        print("配置文件中没有视频信息")
        return
    
    print(f"找到 {len(videos)} 个视频待下载")
    
    # 统计信息
    success_count = 0
    failed_count = 0
    start_time = datetime.now()
    
    # 逐个下载视频
    for i, video in enumerate(videos, 1):
        print(f"\n进度: {i}/{len(videos)}")
        
        if download_single_video(video, settings):
            success_count += 1
        else:
            failed_count += 1
        
        # 如果不是最后一个视频，等待一段时间避免请求过于频繁
        if i < len(videos):
            print("等待3秒后继续下载下一个视频...")
            time.sleep(3)
    
    # 输出统计信息
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n{'='*50}")
    print("下载完成！")
    print(f"总计: {len(videos)} 个视频")
    print(f"成功: {success_count} 个")
    print(f"失败: {failed_count} 个")
    print(f"耗时: {duration}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()