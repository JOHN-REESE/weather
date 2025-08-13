# 直播流抓取器 - B站支持增强版

## 新增功能

✅ **B站直播流专用支持**
- 自动识别B站直播URL
- 使用B站官方API获取真实流地址
- 自动获取直播间标题和封面
- 支持多种画质选择

## 修复的问题

原版代码在抓取B站直播时提示"找不到有效地址"的原因：
1. B站使用JavaScript动态加载流地址，静态HTML中没有直播流URL
2. 需要通过专用API接口获取真实流地址
3. 流地址包含认证参数和时间戳

## 使用方法

### 命令行模式

```bash
# 抓取B站直播并自动添加
python3 live_stream_scraper_enhanced.py --scrape "https://live.bilibili.com/30912748" --group "B站"

# 抓取并指定自定义名称
python3 live_stream_scraper_enhanced.py --scrape "https://live.bilibili.com/30912748" --name "我的直播间" --group "B站"

# 生成M3U8播放列表
python3 live_stream_scraper_enhanced.py --generate "my_channels.m3u8"

# 查看所有直播源
python3 live_stream_scraper_enhanced.py --list
```

### 交互模式

```bash
python3 live_stream_scraper_enhanced.py
```

选择选项1，输入B站直播URL，程序会：
1. 自动识别房间号
2. 检查直播状态
3. 获取直播间信息（标题、封面等）
4. 抓取真实流地址
5. 自动添加到配置中

## 支持的B站URL格式

- `https://live.bilibili.com/123456`
- `https://live.bilibili.com/h5/123456`
- `https://live.bilibili.com/blanc/123456`

## 技术实现

### B站API接口

1. **获取直播间信息**
   ```
   GET https://api.live.bilibili.com/room/v1/Room/get_info?room_id={房间号}
   ```

2. **获取播放地址**
   ```
   GET https://api.live.bilibili.com/room/v1/Room/playUrl?cid={房间号}&qn=10000&platform=web
   ```

### 画质参数说明
- `qn=10000`: 原画
- `qn=400`: 蓝光
- `qn=250`: 超清
- `qn=150`: 高清

## 生成的M3U8格式

```m3u8
#EXTM3U
#EXTINF:-1 tvg-name="直播间标题" group-title="B站",直播间标题
https://直播流地址...
```

## 兼容性

- ✅ PotPlayer
- ✅ VLC Media Player  
- ✅ APTV
- ✅ IPTV播放器
- ✅ 其他支持M3U8的播放器

## 注意事项

1. **直播状态检查**: 程序会自动检查直播间是否开播
2. **流地址时效性**: B站流地址包含时间戳，有一定时效性
3. **网络要求**: 需要能够访问B站API接口
4. **频率限制**: 建议不要频繁请求，避免被限制

## 错误处理

- 如果直播间未开播，会显示警告信息
- 如果网络请求失败，会显示错误详情
- 如果API返回错误，会显示具体错误信息

## 测试结果

✅ 成功抓取B站直播流地址
✅ 自动获取直播间信息
✅ 生成标准M3U8播放列表
✅ 兼容主流播放器

使用示例中的B站直播间(30912748)测试成功！