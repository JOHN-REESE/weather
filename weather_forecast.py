#!/usr/bin/env python3
"""
天气预报查询脚本
输入城市名称或经纬度查询未来一周的天气预报
使用 Open-Meteo 免费 API（无需 API Key）
使用 geocode.maps.co 免费地理编码 API
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import argparse
import re


def get_coordinates_from_city(city_name):
    """
    根据城市名称获取经纬度
    使用 Nominatim OpenStreetMap 免费地理编码 API
    
    Args:
        city_name (str): 城市名称
        
    Returns:
        tuple: (latitude, longitude, display_name) 或 None
    """
    # 使用 Nominatim OSM 免费地理编码 API（无需API密钥）
    url = "https://nominatim.openstreetmap.org/search"
    
    params = {
        "q": city_name,
        "format": "json",
        "limit": 1,
        "addressdetails": 1
    }
    
    headers = {
        "User-Agent": "WeatherForecastScript/1.0"  # OSM要求设置User-Agent
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if data and len(data) > 0:
            result = data[0]
            lat = float(result['lat'])
            lng = float(result['lon'])
            display_name = result.get('display_name', city_name)
            return lat, lng, display_name
        else:
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"地理编码API请求失败: {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f"解析地理编码数据失败: {e}")
        return None


def get_weather_forecast(latitude, longitude):
    """
    根据经纬度获取7天天气预报
    
    Args:
        latitude (float): 纬度
        longitude (float): 经度
        
    Returns:
        dict: 天气预报数据
    """
    # Open-Meteo API 端点
    url = "https://api.open-meteo.com/v1/forecast"
    
    # API 参数
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode,windspeed_10m_max,sunrise,sunset",
        "timezone": "auto",
        "forecast_days": 7
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API 请求失败: {e}")
        return None


def weather_code_to_description(code):
    """将天气代码转换为中文描述"""
    weather_codes = {
        0: "晴朗",
        1: "主要晴朗",
        2: "部分多云",
        3: "阴天",
        45: "雾",
        48: "雾凇",
        51: "小毛毛雨",
        53: "中等毛毛雨",
        55: "密集毛毛雨",
        56: "轻度冻毛毛雨",
        57: "密集冻毛毛雨",
        61: "小雨",
        63: "中雨",
        65: "大雨",
        66: "轻度冻雨",
        67: "重度冻雨",
        71: "小雪",
        73: "中雪",
        75: "大雪",
        77: "雪粒",
        80: "轻度阵雨",
        81: "中等阵雨",
        82: "猛烈阵雨",
        85: "轻度阵雪",
        86: "重度阵雪",
        95: "雷暴",
        96: "雷暴伴小冰雹",
        99: "雷暴伴大冰雹"
    }
    return weather_codes.get(code, f"未知天气 (代码: {code})")


def format_forecast(weather_data, location_info=None):
    """格式化天气预报输出"""
    if not weather_data or 'daily' not in weather_data:
        return "无法获取天气数据"
    
    daily = weather_data['daily']
    
    if location_info:
        print(f"\n🏙️  城市: {location_info}")
        print(f"📍 坐标: {weather_data.get('latitude', 'N/A')}°N, {weather_data.get('longitude', 'N/A')}°E")
    else:
        print(f"\n📍 位置: {weather_data.get('latitude', 'N/A')}°N, {weather_data.get('longitude', 'N/A')}°E")
    print(f"🌐 时区: {weather_data.get('timezone', 'N/A')}")
    print(f"📅 预报时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "="*60)
    print("📅 未来7天天气预报")
    print("="*60)
    
    for i in range(len(daily['time'])):
        date = datetime.fromisoformat(daily['time'][i])
        temp_max = daily['temperature_2m_max'][i]
        temp_min = daily['temperature_2m_min'][i]
        precipitation = daily['precipitation_sum'][i]
        weather_code = daily['weathercode'][i]
        wind_speed = daily['windspeed_10m_max'][i]
        
        weather_desc = weather_code_to_description(weather_code)
        
        print(f"\n📅 {date.strftime('%Y-%m-%d')} ({date.strftime('%A')})")
        print(f"🌡️  温度: {temp_min}°C - {temp_max}°C")
        print(f"☁️  天气: {weather_desc}")
        print(f"🌧️  降水量: {precipitation}mm")
        print(f"💨 最大风速: {wind_speed}km/h")
        
        if 'sunrise' in daily and 'sunset' in daily:
            if daily['sunrise'][i] and daily['sunset'][i]:
                sunrise = datetime.fromisoformat(daily['sunrise'][i]).strftime('%H:%M')
                sunset = datetime.fromisoformat(daily['sunset'][i]).strftime('%H:%M')
                print(f"🌅 日出: {sunrise}  🌇 日落: {sunset}")


def is_coordinates(input_str):
    """
    判断输入是否为坐标格式
    支持格式: "lat,lng" 或 "lat lng" 或两个独立参数
    """
    # 检查是否包含逗号或空格分隔的两个数字
    coord_pattern = r'^\s*-?\d+\.?\d*\s*[,\s]\s*-?\d+\.?\d*\s*$'
    return bool(re.match(coord_pattern, input_str.strip()))


def parse_coordinates(coord_str):
    """
    解析坐标字符串
    """
    # 移除多余空格并分割
    coord_str = coord_str.strip()
    if ',' in coord_str:
        parts = coord_str.split(',')
    else:
        parts = coord_str.split()
    
    if len(parts) == 2:
        try:
            lat = float(parts[0].strip())
            lng = float(parts[1].strip())
            return lat, lng
        except ValueError:
            return None
    return None


def validate_coordinates(lat, lng):
    """验证经纬度是否有效"""
    try:
        lat = float(lat)
        lng = float(lng)
        
        if not (-90 <= lat <= 90):
            print("❌ 纬度必须在 -90 到 90 度之间")
            return False
            
        if not (-180 <= lng <= 180):
            print("❌ 经度必须在 -180 到 180 度之间")
            return False
            
        return True, lat, lng
        
    except ValueError:
        print("❌ 请输入有效的数字格式")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="查询城市或坐标未来7天天气预报")
    parser.add_argument("location", nargs='*', help="城市名称 (例如: 北京 或 Beijing) 或坐标 (例如: 39.9042,116.4074)")
    
    args = parser.parse_args()
    
    # 处理命令行参数
    if args.location:
        location_input = ' '.join(args.location).strip()
        # 如果有命令行参数，执行一次查询后退出
        query_weather(location_input)
        return
    
    # 交互模式 - 循环查询
    print("🌤️  天气预报查询工具")
    print("=" * 40)
    print("💡 支持输入:")
    print("   • 城市名称: 北京, Shanghai, New York")
    print("   • 坐标格式: 39.9042,116.4074")
    print("   • 输入 'quit' 或 'exit' 退出程序")
    print("-" * 40)
    
    while True:
        try:
            location_input = input("\n🏙️  请输入城市名称或坐标: ").strip()
            
            # 检查退出命令
            if location_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 再见!")
                break
                
            if not location_input:
                print("❌ 输入不能为空，请重新输入")
                continue
                
            # 执行查询
            query_weather(location_input)
            
            # 询问是否继续
            print("\n" + "-" * 40)
            print("💡 按回车键继续查询，或输入 'quit' 退出")
            
        except KeyboardInterrupt:
            print("\n\n👋 再见!")
            break


def query_weather(location_input):
    """执行天气查询"""
    location_info = None
    
    # 判断输入类型并获取坐标
    if is_coordinates(location_input):
        # 输入是坐标格式
        coords = parse_coordinates(location_input)
        if coords:
            latitude, longitude = coords
            validation_result = validate_coordinates(latitude, longitude)
            if validation_result is False:
                return
            _, latitude, longitude = validation_result
            print(f"\n🔍 正在查询坐标 ({latitude}, {longitude}) 的天气预报...")
        else:
            print("❌ 坐标格式不正确，请使用格式: 纬度,经度 (例如: 39.9042,116.4074)")
            return
    else:
        # 输入是城市名称
        print(f"\n🔍 正在查询 '{location_input}' 的坐标...")
        coords_result = get_coordinates_from_city(location_input)
        
        if coords_result:
            latitude, longitude, location_info = coords_result
            print(f"✅ 找到位置: {location_info}")
            print(f"📍 坐标: {latitude}, {longitude}")
            print(f"\n🔍 正在获取天气预报...")
        else:
            print(f"❌ 无法找到城市 '{location_input}' 的地理位置")
            print("💡 请尝试:")
            print("   • 使用更具体的地名 (如: 北京市 而不是 北京)")
            print("   • 使用英文地名 (如: Beijing, China)")
            print("   • 直接输入坐标 (如: 39.9042,116.4074)")
            return
    
    # 获取天气数据
    weather_data = get_weather_forecast(latitude, longitude)
    
    if weather_data:
        format_forecast(weather_data, location_info)
        print(f"\n📊 数据来源: Open-Meteo API (天气) + OpenStreetMap Nominatim (地理编码)")
        print(f"🔗 了解更多: https://open-meteo.com")
    else:
        print("❌ 获取天气数据失败，请检查网络连接或稍后重试")


if __name__ == "__main__":
    main()