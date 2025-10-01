# 🕒 Telegram Attendance Bot | 出勤管理机器人

A simple **Telegram Bot** for managing staff attendance with buttons for **Work In, Work Out, Break, Smoking, and Back**.  
一个简易的 **Telegram 出勤管理机器人**，通过按钮实现 **上班、下班、休息、抽烟、返回** 等考勤操作。  

---

## ✨ Features 功能特点
- ✅ Inline buttons for easy staff usage  
  内嵌按钮，员工使用更方便  
- ✅ Track work time, breaks, and smoking time  
  记录上班时长、休息时间、抽烟时间  
- ✅ Auto-generate daily attendance report (CSV)  
  自动生成每日考勤报表 (CSV)  
- ✅ User-friendly messages with timestamps  
  提供详细的时间戳提示信息  

---

## 📦 Installation 安装步骤

1. Clone this repository  
   克隆本仓库  
   ```bash
   git clone https://github.com/yourusername/telegram-attendance-bot.git
   cd telegram-attendance-bot
   ```

2. Create a virtual environment and install dependencies  
   创建虚拟环境并安装依赖  
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Create a bot using [BotFather](https://t.me/botfather) and get your **API Token**  
   在 [BotFather](https://t.me/botfather) 创建机器人并获取 **API Token**  

4. Edit the `bot.py` file and replace with your token  
   修改 `bot.py` 文件，将 `token` 替换为你的机器人 Token  

---

## ▶️ Usage 使用方法

Run the bot 启动机器人:
```bash
python3 bot.py
```

In your Telegram group or chat:  
在你的 Telegram 群组或私聊中：

- `/start` → Show the menu (Work In, Work Out, Break, Smoking, Back)  
  显示菜单（上班、下班、休息、抽烟、返回）  
- `/report` → Generate and send today’s attendance report (CSV file)  
  生成并发送今日的考勤报表（CSV 文件）  

---

## 📂 Example 按钮示例

When you type `/start`, you will see:  
输入 `/start` 后，你会看到：

```
[ Work In ]   [ Work Out ]
[ Break ]     [ Smoking ]
[ Back ]
```

---

## 📊 Attendance Report 报表示例

CSV file example 输出报表示例：
```csv
Name,User ID,Total Work Hours,Break Count,Break Time,Smoking Count,Smoking Time
Alice,123456,8 hours 15 minutes,2,30 minutes,1,10 minutes
Bob,789012,7 hours 45 minutes,1,15 minutes,2,20 minutes
```

---

## ⚠️ Notes 注意事项
- Bot must be added as **Admin** in the group  
  机器人必须设置为群组 **管理员**  
- Reports are stored locally as CSV files  
  报表以 CSV 文件形式保存在本地  
- Tested on `python-telegram-bot v20+`  
  已在 `python-telegram-bot v20+` 环境下测试  

---

## 📜 License 许可证
MIT License. Free to use and modify.  
MIT 协议，自由使用与修改。  
