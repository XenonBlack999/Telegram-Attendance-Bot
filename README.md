# 🕒 Telegram Attendance Bot

一个用于 **打卡上班、下班、抽烟、休息** 的 Telegram 机器人。  
支持自动生成日报表（CSV 格式），并在群组中自动推送。  

---

## 🌏 语言 (Languages)

### 🇲🇲 မြန်မာဘာသာ (Myanmar)
ဒီ Bot က Telegram မှာ **အလုပ်ဝင်၊ အလုပ်ထွက်၊ စားသောက်နား၊ ဆေးလိပ်time** စတဲ့ အချိန်စာရင်းသိမ်းဆည်းပေးမယ်။  
နောက်ပြီး CSV report ကို generate လုပ်ပေးပြီး၊ အချိန်ကြိုတင်ပြီး Group ထဲကို စာတိုက်ပေးနိုင်တယ်။  

### 🇬🇧 English
This bot helps you **track work attendance** (Work In / Work Out / Break / Smoking) inside Telegram.  
It automatically generates **CSV reports** and can send **daily summaries** to a group.  

### 🇷🇺 Русский (Russian)
Этот бот помогает **отслеживать рабочее время** (Начало работы / Конец работы / Перерыв / Курение) в Telegram.  
Он автоматически создаёт **отчёты CSV** и может отправлять **ежедневные отчёты** в группу.  

### 🇨🇳 中文 (Chinese)
这个机器人可以在 Telegram 中进行 **上班 / 下班 / 休息 / 抽烟** 打卡。  
它会自动生成 **CSV 报表**，并每天向群组发送 **日报告**。  

---

## 🚀 功能 (Features)
- ✅ 上班 / 下班 打卡  
- ✅ 休息 / 抽烟 计时（45分钟限制）  
- ✅ 自动统计每天工作时长  
- ✅ CSV 报表导出  
- ✅ 自动群组推送日报  

---

## ⚙️ 安装步骤 (Installation)

### 1️⃣ 克隆项目 (Clone project)
```bash
https://github.com/XenonBlack999/Telegram-Attendance-Bot
cd attendance-bot
```

### 2️⃣ 安装依赖 (Install dependencies)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3️⃣ 配置 Token (Set Telegram Bot Token)
在 `main.py` 里替换：
```python
token = "YOUR_BOT_TOKEN"
```

### 4️⃣ 启动 Bot (Run the bot)
```bash
python main.py
```

---

## 📊 使用方法 (Usage)

- `/start` → 打开菜单按钮  
- 点击按钮：  
  - 🟢 上班  
  - 🔴 下班  
  - ☕ 休息  
  - 🚬 抽烟  
  - 🔙 返回工作  
- `/report` → 生成 CSV 报表  

---

## 📝 报表示例 (CSV Report Example)
| 姓名 | 用户ID | 总工作时间 | 休息次数 | 休息时间 | 抽烟次数 | 抽烟时间 |
|------|--------|------------|----------|----------|----------|----------|
| 张三 | 123456 | 07小时30分 | 2 | 00小时40分 | 1 | 00小时10分 |

---

## 📌 注意事项 (Notes)
- 如果工作不足 **8小时** → ⚠️ 会自动警告  
- 连续工作超过 **24小时** → ⏰ 系统会自动重置并提醒休息  
- 抽烟/休息默认时长 **45分钟**  

---

## 👨‍💻 作者 (Author)
- 你可以自由修改和二次开发  
- 如果好用，请给个 ⭐ Star 支持  
