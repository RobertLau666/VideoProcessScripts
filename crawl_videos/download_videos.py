import os
import time
import subprocess
from googleapiclient.discovery import build
from yt_dlp import YoutubeDL

# 替换为你的 YouTube Data API Key
API_KEY = "AIzaSyCKQUyFjuOT7uHn-yrnPtJzfbwn7b4hTUY"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# 创建 YouTube API 客户端
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

def search_videos(query_str, max_results=50, next_page_token=None):
    """搜索视频"""
    search_response = youtube.search().list(
        q=query_str,
        part="id,snippet",
        maxResults=max_results,
        type="video",
        pageToken=next_page_token
    ).execute()

    videos = []
    for item in search_response.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        videos.append({
            "video_id": video_id,
            "title": title
        })
    return videos, search_response.get("nextPageToken")

def convert_to_mp4(output_path):
    """
    将给定的视频文件转换为 MP4 格式，并删除原始文件。
    
    参数:
        output_path (str): 需要转换的视频文件路径。
    
    返回:
        new_path (str): 转换后 MP4 文件的路径（如果转换成功）。
    """
    # 获取文件名和扩展名
    base_name, ext = os.path.splitext(output_path)
    
    # 如果已经是 mp4，直接返回
    if ext.lower() == ".mp4":
        print(f"文件已是 MP4，无需转换: {output_path}")
        return output_path
    
    # 设置新文件路径
    new_path = f"{base_name}.mp4"
    
    # 使用 ffmpeg 进行转换（保留音视频）
    command = [
        "ffmpeg",
        "-i", output_path,       # 输入文件
        "-c:v", "copy",          # 复制视频编码，避免重编码
        "-c:a", "aac",           # 音频编码格式（确保兼容）
        "-b:a", "192k",          # 音频码率
        "-strict", "experimental",
        new_path                 # 输出 MP4 文件
    ]
    
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"转换成功: {new_path}")
        
        # 删除原始文件
        os.remove(output_path)
        print(f"已删除原始文件: {output_path}")
        
        return new_path
    except subprocess.CalledProcessError as e:
        print(f"转换失败: {e}")
        return None
    
def download_video(video_id, output_dir):
    """使用 yt-dlp 下载视频"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    url = f"https://www.youtube.com/watch?v={video_id}"
    print("url: ", url)
    # ydl_opts = {
    #     'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    #     'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
    #     'cookies': 'cookies.txt',  # 指定 cookies 文件路径
    # }
    id_int = len(os.listdir(output_dir))
    id_str_format = f"{str(id_int).zfill(7)}"
    output_path = os.path.join(output_dir, id_str_format)

    try:
        command = f"yt-dlp --cookies ./cookies.txt -o {output_path} {url}"
        return_code = os.system(command)
        if return_code == 0:
            # 转换视频格式
            new_output_path = convert_to_mp4(output_path)
            if new_output_path is None:
                return False, url, output_path
            return True, url, new_output_path
        else:
            return False, url, output_path
        # with YoutubeDL(ydl_opts) as ydl:
        #     ydl.download([url])
        print(f"Downloaded: {video_id}")
        return True, url, output_path
    except Exception as e:
        print(f"Failed to download video {video_id}: {e}")
        return False, url, output_path

def batch_download_videos(query_str, total_videos=15000, max_results_per_page=50):
    """批量下载视频"""
    downloaded = 0
    next_page_token = None

    while downloaded < total_videos:
        videos, next_page_token = search_videos(query_str, max_results_per_page, next_page_token)

        for video in videos:
            video_id = video["video_id"]
            output_dir=f"videos/{query_str.replace(' ','_')}"
            is_downloaded, url, output_path = download_video(video_id, output_dir)
            if is_downloaded:
                downloaded += 1
                
                
                # 记录视频信息
                print(f"Downloaded {downloaded}/{total_videos} videos")
                if downloaded >= total_videos:
                    break

        if not next_page_token:
            print("No more videos found.")
            break

        time.sleep(1)  # 避免触发速率限制

if __name__ == "__main__":
    # 搜索关键词（双人交互视频）
    query_str = "two people talking"

    # 下载视频数量
    # total_videos = 15000
    total_videos = 15

    # 每页最大结果数（API 限制为 50）
    max_results_per_page = 50

    # 开始批量下载
    print(f"Starting to download {total_videos} videos for query_str: '{query_str}'")
    batch_download_videos(query_str, total_videos, max_results_per_page)
    print("Download completed.")