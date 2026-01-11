# VideoCrawler

视频爬虫系统，支持批量下载 B 站和 YouTube 视频。

## 项目简介

VideoCrawler 是一个功能强大的视频批量下载工具，主要用于从 B 站和 YouTube 下载视频资源。该项目采用模块化设计，包含完整的配置管理、下载逻辑和错误处理机制，支持高质量视频下载和批量操作。

## 环境要求

### 依赖项
- Python 3.9+
- requests (用于 B 站爬虫)
- yt-dlp (用于 YouTube 下载)
- FFmpeg (用于音视频合并)

### 快速安装

#### 使用 Conda
```bash
# 创建并激活环境
conda env create -f environment.yml
conda activate videocrawler
```

## 使用方法

### 1. B 站视频下载

#### 配置文件准备
1. 复制或修改 `bilibili-video-config.json` 文件
2. 添加要下载的视频信息（名称、URL、Cookie）
3. 配置下载设置（输出目录、临时目录等）

#### 获取 B 站 Cookie
1. 登录 B 站网页版
2. 打开浏览器开发者工具（按 F12）
3. 切换到 "Network" 标签
4. 刷新 B 站页面，找到一个请求
5. 在请求头中找到 `Cookie` 字段，复制其值
6. 将 Cookie 粘贴到配置文件中

#### 运行脚本
```bash
# 运行 B 站爬虫
python bilibili-crawler.py
```

### 2. YouTube 视频下载

#### 配置文件准备
1. 复制或修改 `youtube-video-config.json` 文件
2. 添加要下载的视频信息（URL、描述、分类）
3. 配置下载设置（输出目录、视频质量等）

#### 运行脚本
```bash
# 运行 YouTube 下载器
python youtube-downloader-ytdlp.py
```

## 配置说明

### B 站配置文件 (bilibili-video-config.json)

```json
{
  "videos": [
    {
      "name": "视频名称",
      "url": "https://www.bilibili.com/video/BV1xxxxxxxxx/",
      "cookie": "B站Cookie"
    }
  ],
  "settings": {
    "output_directory": "downloads",
    "temp_directory": "temp",
    "ffmpeg_path": "ffmpeg",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
  }
}
```

### YouTube 配置文件 (youtube-video-config.json)

```json
{
  "download_settings": {
    "output_directory": "downloads",
    "video_quality": "best[height<=1080]/best",
    "download_subtitles": false,
    "download_info": false,
    "skip_existing": true
  },
  "videos": [
    {
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "description": "视频描述",
      "category": "分类"
    }
  ]
}
```

## 项目结构

```
VideoCrawler/
├── bilibili-crawler.py          # B 站视频爬虫脚本
├── bilibili-video-config.json   # B 站爬虫配置文件
├── youtube-downloader-ytdlp.py  # YouTube 视频下载脚本
├── youtube-video-config.json    # YouTube 下载配置文件
├── checklist.md                 # 舰船视频下载清单
├── environment.yml              # Conda 环境配置文件
└── README.md                    # 项目说明文档
```

## 常见问题

### 1. B 站爬虫无法下载视频
- **问题**：提示 "无法提取视频播放信息"
- **解决方案**：
  1. 检查 Cookie 是否过期，重新获取最新的 Cookie
  2. 确保视频 URL 格式正确
  3. 确保网络连接正常

### 2. YouTube 下载器报错
- **问题**：提示 "Private video" 或 "Video unavailable"
- **解决方案**：
  1. 私有视频需要登录才能访问
  2. 视频不可用可能是因为已被删除或受地区限制

### 3. FFmpeg 相关错误
- **问题**：提示 "FFmpeg 合并失败"
- **解决方案**：
  1. 确保已正确安装 FFmpeg
  2. 确保 FFmpeg 已添加到环境变量
  3. 在配置文件中指定正确的 FFmpeg 路径

## 注意事项

1. **遵守法律法规**：请遵守相关法律法规，不要下载和传播盗版内容
2. **尊重版权**：下载的视频仅用于个人学习和研究，不得用于商业用途
3. **合理使用**：不要过度请求，以免对视频平台造成负担
4. **隐私保护**：配置文件中包含 Cookie 等敏感信息，请妥善保管，不要分享给他人
5. **定期更新**：视频平台可能会更新其 API 和页面结构，需要定期更新爬虫代码

## 许可证

本项目仅供学习和研究使用，请勿用于商业用途。
