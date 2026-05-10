import requests
from bs4 import BeautifulSoup
import smtplib
import os
from email.mime.text import MIMEText
from email.header import Header

# --- 1. 基础配置 ---
# 在这里添加你想精准追踪的战队名称（不区分大小写）
TEAMS_TO_TRACK = ["Spirit", "TYLOO","Vitality","BC.Game","Falcons"]

# 5EPlay 的目标 URL
URL_NEWS = "https://www.5eplay.com/article"
URL_MATCH = "https://www.5eplay.com/data/match"

def send_email(subject, body):
    """使用 Gmail 发送邮件"""
    # 从 GitHub Secrets 获取环境变量
    sender = os.environ.get('MAIL_USER')
    password = os.environ.get('MAIL_PASS')
    receiver = os.environ.get('MAIL_RECEIVER')
    
    if not all([sender, password, receiver]):
        print("错误：邮件配置变量缺失，请检查 GitHub Secrets 设置。")
        return

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = sender
    msg['To'] = receiver

    try:
        # Gmail 必须使用 587 端口并启用 TLS
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls() 
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        print("邮件通知已发送！")
    except Exception as e:
        print(f"邮件发送失败: {e}")

def scrape_5eplay():
    """抓取新闻和比赛结果并根据关键字过滤"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    found_content = []
    
    # --- 抓取新闻 ---
    try:
        print("正在抓取 5EPlay 新闻...")
        resp = requests.get(URL_NEWS, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 5EPlay 的新闻标题通常在 a 标签中
        articles = soup.find_all('a')
        for art in articles:
            title = art.get_text().strip()
            link = art.get('href', '')
            
            # 如果标题包含指定战队
            if any(team.lower() in title.lower() for team in TEAMS_TO_TRACK):
                if link.startswith('/article/'):
                    full_link = f"https://www.5eplay.com{link}"
                    info = f"【战队新闻】{title}\n直达链接: {full_link}"
                    if info not in found_content:
                        found_content.append(info)
    except Exception as e:
        print(f"新闻抓取出错: {e}")

    # --- 抓取比赛结果 ---
    try:
        print("正在抓取 5EPlay 比赛结果...")
        resp = requests.get(URL_MATCH, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 寻找包含战队名的比赛列表项
        matches = soup.find_all('div', class_='match-item') # 5E 常用类名
        if not matches:
             # 如果 class 没对上，尝试通用的 div 查找
             matches = soup.find_all('div')

        for match in matches:
            text = match.get_text()
            if any(team.lower() in text.lower() for team in TEAMS_TO_TRACK):
                # 简单清洗文本
                clean_text = " ".join(text.split())
                if clean_text and clean_text not in found_content:
                    found_content.append(f"【比赛结果/预告】{clean_text}")
    except Exception as e:
        print(f"比赛抓取出错: {e}")

    return found_content

if __name__ == "__main__":
    results = scrape_5eplay()
    
    if results:
        # 将列表转为字符串
        email_body = "\n\n" + "\n\n---\n\n".join(results)
        send_email("CS 战队情报更新 - 5EPlay 提醒", email_body)
    else:
        print("未发现匹配战队的新动态。")
