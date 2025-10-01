import logging
import csv
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo   # ✅ Import timezone support
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from telegram.request import HTTPXRequest

# ------------------------------------------------------------
# Timezone (set to Asia/Yangon)
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

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def now_yangon():
    """Return current time in Asia/Yangon timezone"""
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


def log_activity(user_id, action, user_name="Unknown"):
    now = now_yangon()   # ✅ Use Yangon time
    user_data = init_user(user_id, user_name)

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

        return (
            f"User: {user_name}\n"
            f"User ID: {user_id}\n"
            f"✅ Clock-out Success: Work Out - {now.strftime('%m/%d %H:%M:%S')}\n"
            f"Note: Thank you for your hard work!\n"
            f"Today's total work: {format_duration(user_data['total_time'])}\n"
            f"Pure work time: {format_duration(user_data['total_time'])}\n"
            f"------------------------\n"
            f"Total break time today: {format_duration(user_data['break_time'])}\n"
            f"Break count today: {user_data['break_count']} times\n"
            f"Total smoking time today: {format_duration(user_data['smoking_time'])}\n"
            f"Smoking count today: {user_data['smoking_count']} times"
        )

    # ---------------- Smoking ----------------
    elif action == "smoking":
        if user_data["status"] != "working":
            return (
                f"User: {user_name}\n"
                f"User ID: {user_id}\n"
                f"⚠️ You must be working before starting Smoking."
            )

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

        # valid back after smoking/break
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

            # Reset to working
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
    user_name = user.full_name
    user_id = user.id

    response_text = log_activity(user_id, query.data, user_name)
    await query.message.reply_text(response_text)


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    filename = f"attendance_{now_yangon().strftime('%Y%m%d')}.csv"  # ✅ Yangon date
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "User ID", "Total Work Hours", "Break Count", "Break Time", "Smoking Count", "Smoking Time"])
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
    await update.message.reply_text("📊 Attendance report generated.")


# ------------------------------------------------------------
# Global Error Handler
# ------------------------------------------------------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling an update:", exc_info=context.error)
    try:
        if update and hasattr(update, "message") and update.message:
            await update.message.reply_text("⚠️ A network error occurred. Please try again later.")
    except Exception:
        pass


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    token = "7830166364:AAHy9AJT_ysJaM5OCWph4zF2NuroqJyXTEw"

    # Use custom HTTPX request with longer timeout
    request = HTTPXRequest(connect_timeout=30, read_timeout=30)

    app = Application.builder().token(token).request(request).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CommandHandler("report", report))
    app.add_error_handler(error_handler)

    logger.info("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
