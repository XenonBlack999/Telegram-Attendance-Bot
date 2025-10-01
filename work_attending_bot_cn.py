import logging
import csv
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from telegram.request import HTTPXRequest

# ------------------------------------------------------------
# 日志记录
# ------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

attendance = {}

# ------------------------------------------------------------
# 工具函数
# ------------------------------------------------------------
def init_user(user_id, user_name="未知"):
    if user_id not in attendance:
        attendance[user_id] = {
            "name": user_name,
            "records": [],
            "status": "idle",
            "total_time": timedelta(),
            "last_start": None,
            "smoking_count": 0,
            "smoking_time": timedelta(),
            "break_count": 0,
            "break_time": timedelta(),
        }
    return attendance[user_id]


def format_duration(td: timedelta):
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours} 小时 {minutes:02d} 分钟 {seconds:02d} 秒"


def log_activity(user_id, action, user_name="未知"):
    now = datetime.now()
    user_data = init_user(user_id, user_name)

    # ---------------- 上班 ----------------
    if action == "work_in":
        if user_data["status"] == "working":
            return (
                f"用户：{user_name}\n"
                f"用户标识：{user_id}\n"
                f"⚠️ 您已经打过上班卡了！"
            )

        user_data["status"] = "working"
        user_data["last_start"] = now
        user_data["records"].append(("上班", now, None))

        return (
            f"用户：{user_name}\n"
            f"用户标识：{user_id}\n"
            f"✅ 上班打卡成功 - {now.strftime('%m/%d %H:%M:%S')}\n"
            f"提示：祝您工作愉快！"
        )

    # ---------------- 下班 ----------------
    elif action == "work_out":
        if user_data["status"] == "idle":
            return (
                f"用户：{user_name}\n"
                f"用户标识：{user_id}\n"
                f"⚠️ 无法打下班卡！\n"
                f"原因：请先打上班卡。"
            )

        if user_data["last_start"]:
            duration = now - user_data["last_start"]
            user_data["total_time"] += duration
            user_data["records"].append(("下班", user_data["last_start"], now, duration))

        user_data["status"] = "offwork"
        user_data["last_start"] = None

        return (
            f"用户：{user_name}\n"
            f"用户标识：{user_id}\n"
            f"✅ 下班打卡成功 - {now.strftime('%m/%d %H:%M:%S')}\n"
            f"提示：辛苦了！\n"
            f"今日总工作时长：{format_duration(user_data['total_time'])}\n"
            f"纯工作时长：{format_duration(user_data['total_time'])}\n"
            f"------------------------\n"
            f"今日累计休息时长：{format_duration(user_data['break_time'])}\n"
            f"今日休息次数：{user_data['break_count']} 次\n"
            f"今日累计抽烟时长：{format_duration(user_data['smoking_time'])}\n"
            f"今日抽烟次数：{user_data['smoking_count']} 次"
        )

    # ---------------- 抽烟 ----------------
    elif action == "smoking":
        if user_data["status"] != "working":
            return (
                f"用户：{user_name}\n"
                f"用户标识：{user_id}\n"
                f"⚠️ 请先打上班卡后再进行抽烟打卡。"
            )

        user_data["smoking_count"] += 1
        user_data["status"] = "smoking"
        user_data["last_start"] = now
        user_data["records"].append(("抽烟", now, None))

        return (
            f"用户：{user_name}\n"
            f"用户标识：{user_id}\n"
            f"✅ 抽烟打卡成功 - {now.strftime('%m/%d %H:%M:%S')}\n"
            f"提示：今天这是您的第 {user_data['smoking_count']} 次抽烟。\n"
            f"记得回来后点击“回座”哦。\n"
        )

    # ---------------- 休息 ----------------
    elif action == "break":
        if user_data["status"] != "working":
            return (
                f"用户：{user_name}\n"
                f"用户标识：{user_id}\n"
                f"⚠️ 请先打上班卡后再进行休息打卡。"
            )

        user_data["break_count"] += 1
        user_data["status"] = "break"
        user_data["last_start"] = now
        user_data["records"].append(("休息", now, None))

        return (
            f"用户：{user_name}\n"
            f"用户标识：{user_id}\n"
            f"✅ 休息打卡成功 - {now.strftime('%m/%d %H:%M:%S')}\n"
            f"提示：今天这是您的第 {user_data['break_count']} 次休息。\n"
            f"记得回来后点击“回座”哦。\n"
        )

    # ---------------- 回座 ----------------
    elif action == "back":
        if user_data["status"] == "idle":
            return (
                f"用户：{user_name}\n"
                f"用户标识：{user_id}\n"
                f"状态：❌ 回座打卡失败！\n"
                f"原因：您还没有开始工作。\n"
                f"建议：请先点击上班打卡。"
            )

        if user_data["status"] not in ["smoking", "break"]:
            return (
                f"用户：{user_name}\n"
                f"用户标识：{user_id}\n"
                f"状态：❌ 回座打卡失败！\n"
                f"原因：您没有进行中的活动。\n"
                f"您可以————\n"
                f"👉 抽烟\n"
                f"👉 休息"
            )

        # 结束活动
        activity_type = user_data["status"]
        if user_data["last_start"]:
            duration = now - user_data["last_start"]

            if activity_type == "smoking":
                user_data["smoking_time"] += duration
                user_data["records"].append(("抽烟结束", user_data["last_start"], now, duration))
                activity_label = "抽烟"
                total_today = user_data["smoking_time"]
                count_today = user_data["smoking_count"]

            elif activity_type == "break":
                user_data["break_time"] += duration
                user_data["records"].append(("休息结束", user_data["last_start"], now, duration))
                activity_label = "休息"
                total_today = user_data["break_time"]
                count_today = user_data["break_count"]

            # 状态重置为工作中
            user_data["status"] = "working"
            user_data["last_start"] = now

            return (
                f"用户：{user_name}\n"
                f"用户标识：{user_id}\n"
                f"✅ {now.strftime('%m/%d %H:%M:%S')} 回座打卡成功：{activity_label}\n"
                f"提示：本次活动已结算。\n"
                f"本次活动耗时：{format_duration(duration)}\n"
                f"今日累计{activity_label}时间：{format_duration(total_today)}\n"
                f"------------------------\n"
                f"今日{activity_label}：{count_today} 次"
            )

# ------------------------------------------------------------
# Bot Handlers
# ------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("上班", callback_data="work_in"),
         InlineKeyboardButton("下班", callback_data="work_out")],
        [InlineKeyboardButton("休息", callback_data="break"),
         InlineKeyboardButton("抽烟", callback_data="smoking")],
        [InlineKeyboardButton("回座", callback_data="back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("请选择一个操作：", reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    user_name = user.full_name
    user_id = user.id

    response_text = log_activity(user_id, query.data, user_name)
    await query.message.reply_text(response_text)


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filename = f"attendance_{datetime.now().strftime('%Y%m%d')}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["姓名", "用户ID", "总工作时长", "休息次数", "休息时长", "抽烟次数", "抽烟时长"])
        for uid, data in attendance.items():
            writer.writerow([
                data["name"],
                uid,
                format_duration(data["total_time"]),
                data["break_count"],
                format_duration(data["break_time"]),
                data["smoking_count"],
                format_duration(data["smoking_time"]),
            ])
    await update.message.reply_document(open(filename, "rb"))
    await update.message.reply_text("📊 出勤报表已生成。")


# ------------------------------------------------------------
# 全局错误处理
# ------------------------------------------------------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("处理更新时发生异常：", exc_info=context.error)
    try:
        if update and hasattr(update, "message") and update.message:
            await update.message.reply_text("⚠️ 出现网络错误，请稍后再试。")
    except Exception:
        pass


# ------------------------------------------------------------
# 主程序入口
# ------------------------------------------------------------
def main():
    token = "YOUR_BOT_TOKEN"  # 替换成你的真实 Bot Token

    request = HTTPXRequest(connect_timeout=30, read_timeout=30)

    app = Application.builder().token(token).request(request).build()

    # 注册指令
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CommandHandler("report", report))
    app.add_error_handler(error_handler)

    logger.info("机器人已启动...")
    app.run_polling()

if __name__ == "__main__":
    main()
