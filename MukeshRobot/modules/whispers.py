# SOURCE https://github.com/Team-ProjectCodeX
# CREATED BY https://t.me/O_okarma
# PROVIDED BY https://t.me/ProjectCodeX
# ➥ @YaeMiko_Roxbot ʏᴏᴜʀ ᴍᴇssᴀɢᴇ @ᴜsᴇʀɴᴀᴍᴇ ᴏʀ ᴜsᴇʀɪᴅ
# ➥ @YaeMiko_Roxbot @ᴜsᴇʀɴᴀᴍᴇ ᴏʀ ᴜsᴇʀɪᴅ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ


import asyncio
import json
import logging
import os
import sys
import time

from pymongo import MongoClient
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from telegram.ext import CallbackQueryHandler, InlineQueryHandler

from MukeshRobot import MONGO_DB_URI, dispatcher

# Initialize MongoDB client
client = MongoClient(MONGO_DB_URI)
db = client["whisperdb"]
collection = db["whisper"]


# Whispers Class
class Whispers:
    @staticmethod
    def add_whisper(WhisperId, WhisperData):
        whisper = {"WhisperId": WhisperId, "whisperData": WhisperData}
        collection.insert_one(whisper)

    @staticmethod
    def del_whisper(WhisperId):
        collection.delete_one({"WhisperId": WhisperId})

    @staticmethod
    def get_whisper(WhisperId):
        whisper = collection.find_one({"WhisperId": WhisperId})
        return whisper["whisperData"] if whisper else None


# Inline query handler
def mainwhisper(update, context):
    query = update.inline_query
    if not query.query:
        return query.answer(
            [],
            switch_pm_text="Give me a username or ID!",
            switch_pm_parameter="ghelp_whisper",
        )

    user, message = parse_user_message(query.query)
    if len(message) > 200:
        return

    usertype = "username" if user.startswith("@") else "id"

    if user.isdigit():
        try:
            chat = context.bot.get_chat(int(user))
            user = f"@{chat.username}" if chat.username else chat.first_name
        except Exception:
            pass

    whisperData = {
        "user": query.from_user.id,
        "withuser": user,
        "usertype": usertype,
        "type": "inline",
        "message": message,
    }
    whisperId = shortuuid.uuid()

    # Add the whisper to the database
    Whispers.add_whisper(whisperId, whisperData)

    answers = [
        InlineQueryResultArticle(
            id=whisperId,
            title=f"👤 Send a whisper message to {user}!",
            description="Only they can see it!",
            input_message_content=InputTextMessageContent(
                f"🔐 A Whisper Message For {user}\nOnly they can see it!"
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "📩 𝗦𝗵𝗼𝘄 𝗪𝗵𝗶𝘀𝗽𝗲𝗿 📩",
                            callback_data=f"whisper_{whisperId}",
                        )
                    ]
                ]
            ),
        )
    ]

    context.bot.answer_inline_query(query.id, answers)


# Callback query handler
def showWhisper(update, context):
    callback_query = update.callback_query
    whisperId = callback_query.data.split("_")[-1]
    whisper = Whispers.get_whisper(whisperId)

    if not whisper:
        context.bot.answer_callback_query(
            callback_query.id, "This whisper is not valid anymore!"
        )
        return

    userType = whisper["usertype"]
    from_user_id = callback_query.from_user.id

    if from_user_id == whisper["user"]:
        context.bot.answer_callback_query(
            callback_query.id, whisper["message"], show_alert=True
        )
    elif (
        userType == "username"
        and callback_query.from_user.username
        and callback_query.from_user.username.lower()
        == whisper["withuser"].replace("@", "").lower()
    ):
        context.bot.answer_callback_query(
            callback_query.id, whisper["message"], show_alert=True
        )
    elif userType == "id" and from_user_id == int(whisper["withuser"]):
        context.bot.answer_callback_query(
            callback_query.id, whisper["message"], show_alert=True
        )
    else:
        context.bot.answer_callback_query(
            callback_query.id, "Not your Whisper!", show_alert=True
        )


# Function to parse user message
def parse_user_message(query_text):
    text = query_text.split(" ")
    user = text[0]
    first = True
    message = ""

    if not user.startswith("@") and not user.isdigit():
        user = text[-1]
        first = False

    if first:
        message = " ".join(text[1:])
    else:
        text.pop()
        message = " ".join(text)

    return user, message


# Add handlers
dispatcher.add_handler(InlineQueryHandler(mainwhisper))
dispatcher.add_handler(CallbackQueryHandler(showWhisper, pattern="^whisper_"))
