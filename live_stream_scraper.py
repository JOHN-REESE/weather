#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直播流地址抓取器和M3U8生成器
支持抓取多种直播网站的直播流地址，并生成标准的M3U8播放列表文件
兼容PotPlayer、APTV等主流播放器
"""

import requests
import re
import json
import os
import time
from urllib.parse import urljoin, urlparse, parse_qs
from typing import List, Dict, Optional
import argparse
import logging

class LiveStreamScraper:
    def __init__(self, config_file: str = 'live_config.json'):
        self.config_file = config_file
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://live.bilibili.com/',
            'Origin': 'https://live.bilibili.com'
        }
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # 常见直播流正则表达式
        self.stream_patterns = [
            r'https?://[^"\']*\.m3u8[^"\']*',  # M3U8流
            r'https?://[^"\']*\.flv[^"\']*',   # FLV流
            r'https?://[^"\']*\.mp4[^"\']*',   # MP4流
            r'rtmp://[^"\']*',                 # RTMP流
            r'rtsp://[^"\']*',                 # RTSP流
        ]

    def load_config(self) -> Dict:
        """加载配置文件"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"sources": []}

    def save_config(self, config: Dict):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def extract_bilibili_room_id(self, url: str) -> Optional[str]:
        """从B站直播URL中提取房间ID"""
        try:
            # 匹配 https://live.bilibili.com/30931147 格式
            match = re.search(r'live\.bilibili\.com/(\d+)', url)
            if match:
                return match.group(1)
            return None
        except:
            return None

    def get_bilibili_stream_url(self, room_id: str) -> List[str]:
        """获取B站直播流地址"""
        try:
            self.logger.info(f"正在获取B站房间 {room_id} 的直播流地址")
            
            # B站直播流获取API
            api_url = f"https://api.live.bilibili.com/room/v1/Room/playUrl"
            params = {
                'cid': room_id,
                'qn': 80,  # 画质参数，80为原画
                'platform': 'web'
            }
            
            response = requests.get(api_url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') == 0 and data.get('data'):
                # 解析直播流地址
                stream_urls = []
                durl_list = data['data'].get('durl', [])
                
                for durl in durl_list:
                    url = durl.get('url')
                    if url:
                        stream_urls.append(url)
                
                if stream_urls:
                    self.logger.info(f"成功获取到 {len(stream_urls)} 个B站直播流地址")
                    return stream_urls
                else:
                    self.logger.warning("B站API返回数据中未找到直播流地址")
            else:
                self.logger.warning(f"B站API返回错误: {data}")
                
        except Exception as e:
            self.logger.error(f"获取B站直播流地址失败: {e}")
        
        return []

    def extract_stream_urls(self, url: str) -> List[str]:
        """从网页中提取直播流地址"""
        try:
            # 特殊处理B站直播
            if 'live.bilibili.com' in url:
                room_id = self.extract_bilibili_room_id(url)
                if room_id:
                    return self.get_bilibili_stream_url(room_id)
                else:
                    self.logger.error("无法从B站URL中提取房间ID")
                    return []
            
            # 其他网站的通用处理
            self.logger.info(f"正在访问: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            content = response.text
            stream_urls = []
            
            # 使用正则表达式匹配流地址
            for pattern in self.stream_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                stream_urls.extend(matches)
            
            # 去重并过滤
            unique_urls = list(set(stream_urls))
            valid_urls = [url for url in unique_urls if self.is_valid_stream_url(url)]
            
            self.logger.info(f"找到 {len(valid_urls)} 个有效流地址")
            return valid_urls
            
        except Exception as e:
            self.logger.error(f"提取流地址失败: {e}")
            return []

    def is_valid_stream_url(self, url: str) -> bool:
        """检查流地址是否有效"""
        try:
            parsed = urlparse(url)
            return parsed.scheme in ['http', 'https', 'rtmp', 'rtsp'] and parsed.netloc
        except:
            return False

    def test_stream_url(self, url: str) -> bool:
        """测试流地址是否可访问"""
        try:
            if url.startswith(('rtmp://', 'rtsp://')):
                return True  # RTMP/RTSP流无法直接测试，返回True
            
            response = requests.head(url, headers=self.headers, timeout=10)
            return response.status_code == 200
        except:
            return False

    def generate_m3u8(self, sources: List[Dict], output_file: str = 'live_channels.m3u8'):
        """生成M3U8播放列表文件"""
        m3u8_content = "#EXTM3U\n"
        
        for source in sources:
            name = source.get('name', '未知频道')
            url = source.get('url', '')
            group = source.get('group', '直播')
            logo = source.get('logo', '')
            
            if url:
                # 添加频道信息
                extinf_line = f"#EXTINF:-1"
                
                # 添加频道名称
                extinf_line += f' tvg-name="{name}"'
                
                # 添加分组
                extinf_line += f' group-title="{group}"'
                
                # 添加logo
                if logo:
                    extinf_line += f' tvg-logo="{logo}"'
                
                extinf_line += f",{name}\n"
                
                m3u8_content += extinf_line
                m3u8_content += f"{url}\n"
        
        # 使用当前工作目录而不是硬编码路径
        output_path = os.path.abspath(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(m3u8_content)
        
        self.logger.info(f"M3U8文件已生成: {output_path}")
        return output_path

    def add_source(self, name: str, url: str, group: str = "直播", logo: str = ""):
        """添加直播源"""
        config = self.load_config()
        
        # 检查是否已存在
        for source in config["sources"]:
            if source["name"] == name:
                source["url"] = url
                source["group"] = group
                source["logo"] = logo
                self.save_config(config)
                self.logger.info(f"已更新直播源: {name}")
                return
        
        # 添加新源
        new_source = {
            "name": name,
            "url": url,
            "group": group,
            "logo": logo,
            "added_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        config["sources"].append(new_source)
        self.save_config(config)
        self.logger.info(f"已添加直播源: {name}")

    def scrape_and_add(self, webpage_url: str, channel_name: str = None, group: str = "直播"):
        """抓取网页并添加直播源"""
        stream_urls = self.extract_stream_urls(webpage_url)
        
        if not stream_urls:
            self.logger.warning("未找到有效的直播流地址")
            return
        
        # 如果找到多个流，选择第一个有效的
        for stream_url in stream_urls:
            if self.test_stream_url(stream_url):
                name = channel_name or f"频道_{int(time.time())}"
                self.add_source(name, stream_url, group)
                self.logger.info(f"成功添加直播源: {name} -> {stream_url}")
                break
        else:
            # 如果没有可测试的流，添加第一个
            name = channel_name or f"频道_{int(time.time())}"
            self.add_source(name, stream_urls[0], group)
            self.logger.info(f"添加直播源(未测试): {name} -> {stream_urls[0]}")

    def list_sources(self):
        """列出所有直播源"""
        config = self.load_config()
        sources = config.get("sources", [])
        
        if not sources:
            self.logger.info("暂无直播源")
            return
        
        print(f"\n共有 {len(sources)} 个直播源:")
        print("-" * 80)
        for i, source in enumerate(sources, 1):
            print(f"{i:2d}. {source['name']}")
            print(f"    地址: {source['url']}")
            print(f"    分组: {source['group']}")
            if source.get('logo'):
                print(f"    Logo: {source['logo']}")
            if source.get('added_time'):
                print(f"    添加时间: {source['added_time']}")
            print()

    def remove_source(self, name: str):
        """删除直播源"""
        config = self.load_config()
        sources = config.get("sources", [])
        
        for i, source in enumerate(sources):
            if source["name"] == name:
                del sources[i]
                self.save_config(config)
                self.logger.info(f"已删除直播源: {name}")
                return
        
        self.logger.warning(f"未找到直播源: {name}")

def main():
    parser = argparse.ArgumentParser(description='直播流抓取器和M3U8生成器')
    parser.add_argument('--scrape', help='抓取网页地址')
    parser.add_argument('--name', help='频道名称')
    parser.add_argument('--group', default='直播', help='分组名称')
    parser.add_argument('--add', nargs=2, metavar=('NAME', 'URL'), help='直接添加直播源')
    parser.add_argument('--list', action='store_true', help='列出所有直播源')
    parser.add_argument('--remove', help='删除直播源')
    parser.add_argument('--generate', help='生成M3U8文件')
    parser.add_argument('--config', default='live_config.json', help='配置文件路径')
    
    args = parser.parse_args()
    
    scraper = LiveStreamScraper(args.config)
    
    if args.scrape:
        scraper.scrape_and_add(args.scrape, args.name, args.group)
    elif args.add:
        scraper.add_source(args.add[0], args.add[1], args.group)
    elif args.list:
        scraper.list_sources()
    elif args.remove:
        scraper.remove_source(args.remove)
    elif args.generate:
        config = scraper.load_config()
        scraper.generate_m3u8(config.get("sources", []), args.generate)
    else:
        # 交互模式
        print("直播流抓取器和M3U8生成器")
        print("1. 抓取网页并添加直播源")
        print("2. 手动添加直播源")
        print("3. 列出所有直播源")
        print("4. 删除直播源")
        print("5. 生成M3U8文件")
        print("0. 退出")
        
        while True:
            try:
                choice = input("\n请选择操作 (0-5): ").strip()
                
                if choice == '0':
                    break
                elif choice == '1':
                    url = input("请输入要抓取的网页地址: ").strip()
                    name = input("请输入频道名称 (可选): ").strip() or None
                    group = input("请输入分组名称 (默认: 直播): ").strip() or "直播"
                    scraper.scrape_and_add(url, name, group)
                elif choice == '2':
                    name = input("请输入频道名称: ").strip()
                    url = input("请输入直播流地址: ").strip()
                    group = input("请输入分组名称 (默认: 直播): ").strip() or "直播"
                    logo = input("请输入Logo地址 (可选): ").strip()
                    scraper.add_source(name, url, group, logo)
                elif choice == '3':
                    scraper.list_sources()
                elif choice == '4':
                    name = input("请输入要删除的频道名称: ").strip()
                    scraper.remove_source(name)
                elif choice == '5':
                    filename = input("请输入M3U8文件名 (默认: live_channels.m3u8): ").strip()
                    filename = filename or "live_channels.m3u8"
                    config = scraper.load_config()
                    scraper.generate_m3u8(config.get("sources", []), filename)
                else:
                    print("无效选择，请重新输入")
            except KeyboardInterrupt:
                print("\n\n再见!")
                break
            except Exception as e:
                print(f"操作失败: {e}")

if __name__ == "__main__":
    main()