import yt_dlp
import json
import os
import re
from pathlib import Path
from datetime import datetime

def load_config(config_file="youtube-video-config.json"):
    """加载配置文件"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"❌ 配置文件 {config_file} 不存在")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ 配置文件格式错误: {e}")
        return None

def clean_filename(filename):
    """清理文件名，与yt-dlp的清理方式保持一致"""
    # 移除或替换不合法的文件名字符
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = re.sub(r'\s+', ' ', filename).strip()
    return filename

def get_video_title(url):
    """获取视频标题，用于检查文件是否已存在"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return clean_filename(info.get('title', ''))
    except:
        return None

def check_video_exists(url, output_dir):
    """检查视频是否已经下载过"""
    title = get_video_title(url)
    if not title:
        return False, None
    
    output_path = Path(output_dir)
    if not output_path.exists():
        return False, None
    
    # 检查常见的视频格式
    video_extensions = ['.mp4', '.mkv', '.webm', '.avi', '.mov', '.flv']
    
    for ext in video_extensions:
        potential_file = output_path / f"{title}{ext}"
        if potential_file.exists():
            return True, potential_file
    
    # 也检查可能的部分匹配（因为文件名可能被截断或略有不同）
    for file in output_path.glob("*"):
        if file.is_file() and file.suffix.lower() in video_extensions:
            # 检查文件名是否包含标题的主要部分
            file_stem = file.stem.lower()
            title_lower = title.lower()
            # 如果标题的前30个字符匹配，认为是同一个视频
            if len(title_lower) > 30 and title_lower[:30] in file_stem:
                return True, file
            elif len(title_lower) <= 30 and title_lower in file_stem:
                return True, file
    
    return False, None

def download_youtube_video(url, output_dir="downloads", video_quality="best[height<=720]/best", 
                          download_subtitles=False, download_info=False, skip_existing=True):
    """使用yt-dlp下载YouTube视频"""
    
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # 检查视频是否已存在
    if skip_existing:
        exists, existing_file = check_video_exists(url, output_dir)
        if exists:
            print(f"⏭️ 视频已存在，跳过下载: {existing_file.name}")
            return True
    
    # 配置yt-dlp选项
    ydl_opts = {
        'format': video_quality,
        'outtmpl': str(output_path / '%(title)s.%(ext)s'),
        'writeinfojson': download_info,
        'writesubtitles': download_subtitles,
        'ignoreerrors': False,
        'no_warnings': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"🔍 正在分析: {url}")
            
            # 先获取视频信息
            info = ydl.extract_info(url, download=False)
            
            # 检查视频可用性
            availability = info.get('availability')
            if availability == 'private':
                print("❌ 私有视频，需要登录才能访问")
                return False
            elif availability == 'premium_only':
                print("❌ 付费视频")
                return False
            elif availability == 'subscriber_only':
                print("❌ 仅限订阅者的视频")
                return False
            
            print(f"📹 标题: {info.get('title', 'N/A')}")
            print(f"👤 频道: {info.get('uploader', 'N/A')}")
            print(f"⏱️ 时长: {info.get('duration', 'N/A')}秒")
            print(f"👀 观看次数: {info.get('view_count', 'N/A')}")
            
            # 开始下载
            print("⬇️ 开始下载...")
            ydl.download([url])
            print("✅ 下载完成！")
            return True
            
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if 'Private video' in error_msg:
            print("❌ 私有视频：需要登录才能访问")
        elif 'Video unavailable' in error_msg:
            print("❌ 视频不可用：可能已被删除或受地区限制")
        elif 'Sign in to confirm your age' in error_msg:
            print("❌ 年龄限制：需要登录确认年龄")
        else:
            print(f"❌ 下载错误: {error_msg}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

def batch_download_videos(config):
    """批量下载视频"""
    
    # 获取设置
    settings = config.get('download_settings', {})
    output_dir = settings.get('output_directory', 'downloads')
    video_quality = settings.get('video_quality', 'best[height<=720]/best')
    download_subtitles = settings.get('download_subtitles', False)
    download_info = settings.get('download_info', False)
    skip_existing = settings.get('skip_existing', True)  # 新增：是否跳过已存在的视频
    
    # 获取视频列表
    videos = config.get('videos', [])
    
    if not videos:
        print("❌ 配置文件中没有找到视频列表")
        return
    
    print(f"📋 找到 {len(videos)} 个视频待下载")
    print(f"📁 输出目录: {output_dir}")
    print(f"🎬 视频质量: {video_quality}")
    print(f"⏭️ 跳过已存在: {'是' if skip_existing else '否'}")
    print("=" * 60)
    
    # 统计信息
    success_count = 0
    failed_count = 0
    skipped_count = 0
    failed_videos = []
    
    # 逐个下载视频
    for i, video in enumerate(videos, 1):
        url = video.get('url', '')
        description = video.get('description', '未知视频')
        category = video.get('category', '未分类')
        
        if not url:
            print(f"❌ 第 {i} 个视频缺少URL，跳过")
            failed_count += 1
            continue
        
        print(f"\n📺 [{i}/{len(videos)}] {description}")
        print(f"🏷️ 分类: {category}")
        print(f"🔗 URL: {url}")
        print("-" * 40)
        
        # 为不同分类创建子目录
        if category and category != '未分类':
            category_output_dir = os.path.join(output_dir, category)
        else:
            category_output_dir = output_dir
        
        # 检查是否已存在（用于统计）
        if skip_existing:
            exists, existing_file = check_video_exists(url, category_output_dir)
            if exists:
                skipped_count += 1
                print(f"⏭️ 第 {i} 个视频已存在，跳过")
                print("-" * 40)
                continue
        
        success = download_youtube_video(
            url, 
            category_output_dir, 
            video_quality, 
            download_subtitles, 
            download_info,
            skip_existing
        )
        
        if success:
            success_count += 1
            print(f"✅ 第 {i} 个视频下载成功")
        else:
            failed_count += 1
            failed_videos.append({
                'index': i,
                'description': description,
                'url': url
            })
            print(f"❌ 第 {i} 个视频下载失败")
        
        print("-" * 40)
    
    # 显示最终统计
    print("\n" + "=" * 60)
    print("📊 下载统计")
    print(f"✅ 成功: {success_count}")
    print(f"⏭️ 跳过: {skipped_count}")
    print(f"❌ 失败: {failed_count}")
    print(f"📋 总计: {len(videos)}")
    
    if failed_videos:
        print("\n❌ 失败的视频:")
        for video in failed_videos:
            print(f"  {video['index']}. {video['description']}")
            print(f"     {video['url']}")

def create_sample_config():
    """创建示例配置文件"""
    sample_config = {
        "download_settings": {
            "output_directory": "downloads",
            "video_quality": "best[height<=720]/best",
            "download_subtitles": False,
            "download_info": False,
            "skip_existing": True
        },
        "videos": [
            {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "description": "Rick Astley - Never Gonna Give You Up",
                "category": "music"
            },
            {
                "url": "https://www.youtube.com/watch?v=9bZkp7q19f0",
                "description": "PSY - GANGNAM STYLE",
                "category": "music"
            }
        ]
    }
    
    with open("youtube-video-config.json", 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, indent=2, ensure_ascii=False)
    
    print("✅ 示例配置文件已创建: youtube-video-config.json")

def main():
    """主函数"""
    print("🎬 YouTube批量视频下载器")
    print("=" * 60)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    config_file = "youtube-video-config.json"
    
    # 检查配置文件是否存在
    if not os.path.exists(config_file):
        print(f"❌ 配置文件 {config_file} 不存在")
        print("🔧 正在创建示例配置文件...")
        create_sample_config()
        print("\n💡 请编辑配置文件添加你想下载的视频URL，然后重新运行脚本")
        return
    
    # 加载配置
    config = load_config(config_file)
    if not config:
        return
    
    # 开始批量下载
    batch_download_videos(config)
    
    print(f"\n⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎉 批量下载任务完成！")

if __name__ == "__main__":
    main()