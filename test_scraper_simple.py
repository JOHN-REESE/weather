#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版直播流抓取器 - 使用内置urllib模块
"""

import urllib.request
import urllib.parse
import re
import json
import os
import time
from typing import List, Dict, Optional

class SimpleStreamScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://live.bilibili.com/',
        }

    def extract_bilibili_room_id(self, url: str) -> Optional[str]:
        """从B站直播URL中提取房间ID"""
        try:
            match = re.search(r'live\.bilibili\.com/(\d+)', url)
            return match.group(1) if match else None
        except:
            return None

    def get_bilibili_stream_url(self, room_id: str) -> List[str]:
        """获取B站直播流地址"""
        try:
            print(f"正在获取B站房间 {room_id} 的直播流地址...")
            
            # 构建API URL
            api_url = f"https://api.live.bilibili.com/room/v1/Room/playUrl?cid={room_id}&qn=80&platform=web"
            
            # 创建请求
            req = urllib.request.Request(api_url, headers=self.headers)
            
            # 发送请求
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            if data.get('code') == 0 and data.get('data'):
                stream_urls = []
                durl_list = data['data'].get('durl', [])
                
                for durl in durl_list:
                    url = durl.get('url')
                    if url:
                        stream_urls.append(url)
                
                if stream_urls:
                    print(f"✓ 成功获取到 {len(stream_urls)} 个B站直播流地址")
                    for i, url in enumerate(stream_urls):
                        print(f"  流地址 {i+1}: {url[:80]}...")
                    return stream_urls
                else:
                    print("✗ B站API返回数据中未找到直播流地址")
            else:
                print(f"✗ B站API返回错误: {data.get('message', 'Unknown error')}")
                
        except Exception as e:
            print(f"✗ 获取B站直播流地址失败: {e}")
        
        return []

    def save_to_m3u8(self, stream_urls: List[str], channel_name: str, group: str = "B站"):
        """保存流地址到M3U8文件"""
        if not stream_urls:
            print("没有流地址可保存")
            return
        
        filename = f"{channel_name}.m3u8"
        m3u8_content = "#EXTM3U\n"
        
        for i, url in enumerate(stream_urls):
            m3u8_content += f"#EXTINF:-1 tvg-name=\"{channel_name}\" group-title=\"{group}\",{channel_name}\n"
            m3u8_content += f"{url}\n"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(m3u8_content)
        
        print(f"✓ M3U8文件已保存: {os.path.abspath(filename)}")

def main():
    scraper = SimpleStreamScraper()
    
    # 测试B站直播流抓取
    test_url = "https://live.bilibili.com/30931147"
    print(f"测试URL: {test_url}")
    
    room_id = scraper.extract_bilibili_room_id(test_url)
    if room_id:
        print(f"提取到房间ID: {room_id}")
        stream_urls = scraper.get_bilibili_stream_url(room_id)
        
        if stream_urls:
            scraper.save_to_m3u8(stream_urls, "影视飓风", "B站")
        else:
            print("未获取到有效的直播流地址")
    else:
        print("无法从URL中提取房间ID")

if __name__ == "__main__":
    main()