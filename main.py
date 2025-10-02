import logging
import csv
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from telegram.request import HTTPXRequest

# ------------------------------------------------------------
# Timezone
# ------------------------------------------------------------
YANGON_TZ = ZoneInfo("Asia/Yangon")

# ------------------------------------------------------------
# Logging setup
# ------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

attendance = {}
group_chat_id = None   # auto detected group chat id

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def now_yangon():
    return datetime.now(YANGON_TZ)

def init_user(user_id, user_name="Unknown"):
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
    return f"{hours} hours {minutes:02d} minutes {seconds:02d} seconds"

def get_total_work_time(user_data):
    """Return total work time including current ongoing session if working."""
    total = user_data["total_time"]
    if user_data["status"] == "working" and user_data["last_start"]:
        total += now_yangon() - user_data["last_start"]
    return total

# ------------------------------------------------------------
# Core Logic
# ------------------------------------------------------------
def log_activity(user_id, action, user_name="Unknown"):
    now = now_yangon()
    user_data = init_user(user_id, user_name)

    # check 24h auto reset
    if user_data["total_time"] >= timedelta(hours=24):
        user_data["total_time"] = timedelta()
        user_data["status"] = "offwork"
        return (
            f"User: {user_name}\n"
            f"User ID: {user_id}\n"
            f"⚠️ You have worked 24 hours in one day!\n"
            f"System has reset your work time.\n"
            f"Please take a rest today."
        )

    # ---------------- Work In ----------------
    if action == "work_in":
        if user_data["status"] == "working":
            return (
                f"User: {user_name}\n"
                f"User ID: {user_id}\n"
                f"⚠️ You are already clocked in!"
            )
        user_data["status"] = "working"
        user_data["last_start"] = now
        user_data["records"].append(("Work In", now, None))
        return (
            f"User: {user_name}\n"
            f"User ID: {user_id}\n"
            f"✅ Clock-in Success: Work In - {now.strftime('%m/%d %H:%M:%S')}\n"
            f"Note: Have a nice day!"
        )

    # ---------------- Work Out ----------------
    elif action == "work_out":
        if user_data["status"] == "idle":
            return (
                f"User: {user_name}\n"
                f"User ID: {user_id}\n"
                f"⚠️ Cannot clock out!\n"
                f"Reason: You must clock-in with Work In first."
            )

        if user_data["last_start"]:
            duration = now - user_data["last_start"]
            user_data["total_time"] += duration
            user_data["records"].append(("Work Out", user_data["last_start"], now, duration))

        user_data["status"] = "offwork"
        user_data["last_start"] = None

        warning = ""
        if get_total_work_time(user_data) < timedelta(hours=8):
            warning = "\n⚠️ Warning: Less than 8 hours worked today!"

        return (
            f"User: {user_name}\n"
            f"User ID: {user_id}\n"
            f"✅ Clock-out Success: Work Out - {now.strftime('%m/%d %H:%M:%S')}\n"
            f"Note: Thank you for your hard work!\n"
            f"Today's total work: {format_duration(get_total_work_time(user_data))}\n"
            f"Pure work time: {format_duration(get_total_work_time(user_data))}\n"
            f"------------------------\n"
            f"Total break time today: {format_duration(user_data['break_time'])}\n"
            f"Break count today: {user_data['break_count']} times\n"
            f"Total smoking time today: {format_duration(user_data['smoking_time'])}\n"
            f"Smoking count today: {user_data['smoking_count']} times"
            f"{warning}"
        )

    # ---------------- Smoking ----------------
    elif action == "smoking":
        if user_data["status"] != "working":
            return (
                f"User: {user_name}\n"
                f"User ID: {user_id}\n"
                f"⚠️ You must be working before starting Smoking."
            )
        # add worked time before break
        if user_data["last_start"]:
            user_data["total_time"] += now - user_data["last_start"]

        user_data["smoking_count"] += 1
        user_data["status"] = "smoking"
        user_data["last_start"] = now
        user_data["records"].append(("Smoking", now, None))
        return (
            f"User: {user_name}\n"
            f"User ID: {user_id}\n"
            f"✅ Clock-in Success: Smoking - {now.strftime('%m/%d %H:%M:%S')}\n"
            f"Note: This is your {user_data['smoking_count']} smoking break\n"
            f"Reminder: Please clock-in 'Back' after finishing.\n"
            f"Back: /back"
        )

    # ---------------- Break ----------------
    elif action == "break":
        if user_data["status"] != "working":
            return (
                f"User: {user_name}\n"
                f"User ID: {user_id}\n"
                f"⚠️ You must be working before starting Break."
            )
        # add worked time before break
        if user_data["last_start"]:
            user_data["total_time"] += now - user_data["last_start"]

        user_data["break_count"] += 1
        user_data["status"] = "break"
        user_data["last_start"] = now
        user_data["records"].append(("Break", now, None))
        return (
            f"User: {user_name}\n"
            f"User ID: {user_id}\n"
            f"✅ Clock-in Success: Break - {now.strftime('%m/%d %H:%M:%S')}\n"
            f"Note: This is your {user_data['break_count']} break\n"
            f"Reminder: Please clock-in 'Back' after finishing.\n"
            f"Back: /back"
        )

    # ---------------- Back ----------------
    elif action == "back":
        if user_data["status"] == "idle":
            return (
                f"User: {user_name}\n"
                f"User ID: {user_id}\n"
                f"Status: ❌ Back clock-in failed!\n"
                f"Reason: You have not started working\n"
                f"Suggestion: Please clock-in with Work In first"
            )
        if user_data["status"] not in ["smoking", "break"]:
            return (
                f"User: {user_name}\n"
                f"User ID: {user_id}\n"
                f"Status: ❌ Back clock-in failed!\n"
                f"Reason: You have no ongoing activity\n"
                f"You can ————\n"
                f"Break\n"
                f"Smoking"
            )
        # valid back
        activity_type = user_data["status"]
        if user_data["last_start"]:
            duration = now - user_data["last_start"]
            if activity_type == "smoking":
                user_data["smoking_time"] += duration
                user_data["records"].append(("Smoking Ended", user_data["last_start"], now, duration))
                activity_label = "Smoking"
                total_today = user_data["smoking_time"]
                count_today = user_data["smoking_count"]
            elif activity_type == "break":
                user_data["break_time"] += duration
                user_data["records"].append(("Break Ended", user_data["last_start"], now, duration))
                activity_label = "Break"
                total_today = user_data["break_time"]
                count_today = user_data["break_count"]

            user_data["status"] = "working"
            user_data["last_start"] = now
            return (
                f"User: {user_name}\n"
                f"User ID: {user_id}\n"
                f"✅ {now.strftime('%m/%d %H:%M:%S')} Back clock-in success: {activity_label}\n"
                f"Note: This activity has been recorded\n"
                f"Duration this activity: {format_duration(duration)}\n"
                f"Total {activity_label.lower()} time today: {format_duration(total_today)}\n"
                f"Total activity time today: {format_duration(total_today)}\n"
                f"------------------------\n"
                f"Today's {activity_label.lower()}: {count_today} times"
            )

# ------------------------------------------------------------
# Bot Handlers
# ------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global group_chat_id
    # auto detect group chat id
    if update.message.chat.type in ["group", "supergroup"]:
        group_chat_id = update.message.chat_id
        logger.info(f"Auto-detected group chat id: {group_chat_id}")

    keyboard = [
        [InlineKeyboardButton("Work In", callback_data="work_in"),
         InlineKeyboardButton("Work Out", callback_data="work_out")],
        [InlineKeyboardButton("Break", callback_data="break"),
         InlineKeyboardButton("Smoking", callback_data="smoking")],
        [InlineKeyboardButton("Back", callback_data="back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose an action:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    response_text = log_activity(user.id, query.data, user.full_name)
    await query.message.reply_text(response_text)

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filename = f"attendance_{now_yangon().strftime('%Y%m%d')}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "User ID", "Total Work Hours", "Break Count", "Break Time", "Smoking Count", "Smoking Time"])
        for uid, data in attendance.items():
            writer.writerow([
                data["name"], uid,
                format_duration(get_total_work_time(data)),
                data["break_count"], format_duration(data["break_time"]),
                data["smoking_count"], format_duration(data["smoking_time"]),
            ])
    await update.message.reply_document(open(filename, "rb"))
    await update.message.reply_text("📊 Attendance report generated.")

# ------------------------------------------------------------
# Scheduled Reports
# ------------------------------------------------------------
async def send_daily_report(app):
    if not group_chat_id:
        return
    if not attendance:
        return
    lines = ["📊 Daily Report:"]
    for uid, data in attendance.items():
        work_time = get_total_work_time(data)
        lines.append(
            f"{data['name']} ({uid}) - Work: {format_duration(work_time)}, "
            f"Breaks: {data['break_count']}, Smoking: {data['smoking_count']}"
        )
    await app.bot.send_message(group_chat_id, "\n".join(lines))

async def send_monthly_report(app):
    if not group_chat_id:
        return
    lines = ["📊 Monthly Report:"]
    for uid, data in attendance.items():
        work_time = get_total_work_time(data)
        lines.append(
            f"{data['name']} ({uid}) - Work: {format_duration(work_time)}, "
            f"Breaks: {data['break_count']}, Smoking: {data['smoking_count']}"
        )
    await app.bot.send_message(group_chat_id, "\n".join(lines))

async def daily_scheduler(app):
    global attendance
    while True:
        now = now_yangon()
        if now.hour == 2 and now.minute == 0:  # 2AM daily report
            await send_daily_report(app)
        if now.hour == 3 and now.minute == 0:  # 3AM reset
            await send_daily_report(app)
            attendance.clear()
            if group_chat_id:
                await app.bot.send_message(group_chat_id, "✅ Daily reset done.")
        if now.day == 3 and now.hour == 3 and now.minute == 0:  # 15th monthly
            await send_monthly_report(app)
        await asyncio.sleep(60)

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    token = "7830166364:AAHy9AJT_ysJaM5OCWph4zF2NuroqJyXTEw"
    request = HTTPXRequest(connect_timeout=30, read_timeout=30)
    app = Application.builder().token(token).request(request).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CommandHandler("report", report))

    loop = asyncio.get_event_loop()
    loop.create_task(daily_scheduler(app))

    logger.info("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
