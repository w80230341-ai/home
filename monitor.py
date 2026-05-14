import requests
from bs4 import BeautifulSoup
import smtplib
import os
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime

# --- 1. 配置部分 ---
# 在这里填入你想追踪的战队名称（支持中文、英文，不区分大小写）
# 建议填入 5EPlay 页面上显示的常用简写
TEAMS_TO_TRACK = ["Spirit","Vitality", "TYLOO",]

# 5EPlay 的目标页面：比赛结果页与新闻页
URLS = [
    "https://www.5eplay.com/data/match",
    "https://www.5eplay.com/article"
]

def send_email(subject, body):
    """使用 QQ 邮箱发送邮件 (SSL 465端口)"""
    # 从 GitHub Secrets 获取环境变量
    sender = os.environ.get('MAIL_USER')
    password = os.environ.get('MAIL_PASS')
    receiver = os.environ.get('MAIL_RECEIVER')
    
    if not all([sender, password, receiver]):
        print("错误：GitHub Secrets 中的邮件配置变量 (USER/PASS/RECEIVER) 不完整。")
        return

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = f"CS战队监控助手 <{sender}>"
    msg['To'] = receiver

    try:
        # QQ 邮箱必须使用 SMTP_SSL 和 465 端口
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        print("邮件通知已成功发送至 QQ 邮箱！")
    except Exception as e:
        print(f"邮件发送失败，请检查授权码是否正确。错误信息: {e}")

def scrape_5eplay():
    """全页面扫描匹配战队信息"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    
    findings = []
    
    for url in URLS:
        try:
            print(f"正在扫描: {url}")
            resp = requests.get(url, headers=headers, timeout=20)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 策略：扫描所有可能包含信息的标签
            # 5EPlay 的比赛信息通常在 div 或 span 标签中
            tags = soup.find_all(['div', 'li', 'a', 'span'])
            
            for tag in tags:
                text = tag.get_text().strip()
                # 过滤掉太短或太长的干扰信息
                if 4 < len(text) < 200:
                    if any(team.lower() in text.lower() for team in TEAMS_TO_TRACK):
                        # 清洗换行符和多余空格
                        clean_info = " ".join(text.split())
                        if clean_info not in findings:
                            # 如果是 a 标签，尝试获取链接
                            if tag.name == 'a' and tag.get('href'):
                                link = tag.get('href')
                                if link.startswith('/'):
                                    clean_info += f" (链接: https://www.5eplay.com{link})"
                            findings.append(clean_info)
                            
        except Exception as e:
            print(f"抓取页面 {url} 时出错: {e}")

    return findings

if __name__ == "__main__":
    # 获取抓取结果
    results = scrape_5eplay()
    
    if results:
        # 生成邮件正文
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        content = f"你好！这是来自 5EPlay 的最新 CS 战队情报 ({time_str})：\n\n"
        content += "\n\n---\n\n".join(results)
        content += "\n\n💡 提示：该邮件由 GitHub Actions 自动发出，每天白天两次巡检。"
        
        send_email(f"CS战报提醒 - {time_str}", content)
    else:
        print("本次巡检未发现匹配战队的动态。")
