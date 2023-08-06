#!/usr/bin/env python
import random
from dotenv import dotenv_values
from nanoid import generate
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging

TELEGRAM_TOKEN = dotenv_values(".env")["TELEGRAM_TOKEN"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


def error_handler(update, context):
    """Custom error handler to log exceptions."""
    logging.error(f"Exception occurred: {context.error}")
    # You can add additional error handling logic here if needed


class Reminder:
    def __init__(self, text):
        self.text = text
        self.id = generate(size=10)

    def get_text(self):
        return self.text


# List of reminders
reminders = [
    Reminder("Drink water"),
    Reminder("Take a walk"),
    Reminder("Do some pushups"),
]
# cron job id
cronID = "reminder"


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def add_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) == 0:
        await update.message.reply_text("Please provide a reminder!")
        return
    reminder = Reminder(" ".join(context.args))
    reminders.append(reminder)
    await update.message.reply_text("Reminder added successfully!")


async def rm_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    id = context.args[0]
    for reminder in reminders:
        if reminder.id == id:
            reminders.remove(reminder)
            break

    await update.message.reply_text("Reminder removed successfully!")


async def show_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(reminders) == 0:
        await update.message.reply_text("No reminders found!")
        return

    message = "Reminders:\n\n"
    for reminder in reminders:
        message += f"{reminder.id} - {reminder.text}\n"

    await update.message.reply_text(message)


async def push_random(context: ContextTypes.DEFAULT_TYPE):
    reminder = random.choice(reminders)
    job = context.job
    await context.bot.send_message(job.chat_id, text=reminder.get_text())


# start cron job to send a random reminder every 5 seconds
async def cron_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_message.chat_id
    if len(reminders) == 0:
        return
    # if current job is running, cancel it
    current_jobs = context.job_queue.get_jobs_by_name(cronID)
    if current_jobs:
        for job in current_jobs:
            job.schedule_removal()

    # create new job
    context.job_queue.run_repeating(
        push_random, interval=5, name=cronID, chat_id=chat_id
    )

    await update.message.reply_text("Cron job started!")


# kill cron job
async def kill_cron_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    job_removed = remove_job_if_exists(cronID, context)
    await update.message.reply_text(
        ("Cron job successfully canceled!", "You have no active cron job.")[job_removed]
    )


def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("add", add_reminder))  # Add Reminder command
    application.add_handler(
        CommandHandler("remove", rm_reminder)
    )  # Remove Reminder command By ID
    application.add_handler(
        CommandHandler("showall", show_all)
    )  # Show all Reminders command
    application.add_handler(CommandHandler("cron", cron_job))  # Start cron job
    application.add_handler(CommandHandler("kill", kill_cron_job))  # Kill cron job

    application.add_error_handler(error_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
