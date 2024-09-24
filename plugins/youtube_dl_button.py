#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K | Modified By > @DC4_WARRIOR

import logging
import asyncio
import json
import os
import shutil
from pyrogram import Client, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
from translation import Translation
from helper_funcs.display_progress import progress_for_pyrogram, humanbytes

# Logging setup
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def youtube_dl_call_back(bot, update):
    cb_data = update.data
    tg_send_type, youtube_dl_format, youtube_dl_ext = cb_data.split("|")
    save_ytdl_json_path = os.path.join(Config.DOWNLOAD_LOCATION, f"{update.from_user.id}.json")

    try:
        with open(save_ytdl_json_path, "r", encoding="utf8") as f:
            response_json = json.load(f)
    except FileNotFoundError:
        if update.message:
            await update.message.delete(True)
        return False

    chat_id = update.message.chat.id if update.message else update.callback_query.message.chat.id
    reply_to_message_id = (update.message.message_id if update.message else 
                            update.callback_query.message.reply_to_message.message_id)

    # Check if the message is a reply and has the required data.
    if not (update.message and update.message.reply_to_message):
        await bot.send_message(
            chat_id=chat_id,
            text="Please reply to a message containing a valid URL.",
            parse_mode=enums.ParseMode.HTML,
            reply_to_message_id=reply_to_message_id,
        )
        return
    
    youtube_dl_url = (update.message.reply_to_message.text if update.message else 
                      update.callback_query.message.reply_to_message.text).strip()

    custom_file_name = str(response_json.get("title"))[:50] + "_" + youtube_dl_format + "." + youtube_dl_ext

    await bot.edit_message_text(
        text=Translation.DOWNLOAD_START,
        chat_id=chat_id,
        message_id=reply_to_message_id)

    description = response_json.get("fulltitle", "Downloading...")[:1021]

    tmp_directory_for_each_user = os.path.join(Config.DOWNLOAD_LOCATION, str(update.from_user.id))
    
    if not os.path.isdir(tmp_directory_for_each_user):
        os.makedirs(tmp_directory_for_each_user)

    file_name = custom_file_name.replace('/', ' ')
    download_directory = os.path.join(tmp_directory_for_each_user, file_name)

    command_to_exec = []
    
    # Prepare command based on type of media being downloaded.
    if tg_send_type == "audio":
        command_to_exec = ["yt-dlp", "-c",
             "--max-filesize", str(Config.TG_MAX_FILE_SIZE),
             "--prefer-ffmpeg", "--extract-audio",
             "--audio-format", youtube_dl_ext,
             "--audio-quality", youtube_dl_format,
             youtube_dl_url, "-o", download_directory]
    else:
        minus_f_format = youtube_dl_format + "+bestaudio" if "youtu" in youtube_dl_url else youtube_dl_format
        
        command_to_exec = ["yt-dlp", "-c",
            "--max-filesize", str(Config.TG_MAX_FILE_SIZE),
            "--embed-subs", "-f", minus_f_format,
            "--hls-prefer-ffmpeg", youtube_dl_url,
            "-o", download_directory]

    # Add proxy and authentication details if provided.
    if Config.HTTP_PROXY != "":
        command_to_exec.append("--proxy")
        command_to_exec.append(Config.HTTP_PROXY)

    start = datetime.now()
    
    process = await asyncio.create_subprocess_exec(*command_to_exec,
                                                   stdout=asyncio.subprocess.PIPE, 
                                                   stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await process.communicate()
    
    e_response = stderr.decode().strip()
    
    if e_response:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=reply_to_message_id,
            text=e_response)
        
        return False
    
    file_size = os.path.getsize(download_directory) if os.path.exists(download_directory) else 0

    if file_size == 0:
         await bot.edit_message_text(text="File Not found 🤒",
                                      chat_id=chat_id,
                                      message_id=reply_to_message_id)
         return
        
    if file_size > Config.TG_MAX_FILE_SIZE:
        await bot.edit_message_text(
            chat_id=chat_id,
            text=Translation.RCHD_TG_API_LIMIT.format(time_taken_for_download, humanbytes(file_size)),
            message_id=reply_to_message_id)
            
    else:
        await bot.edit_message_text(
            text=Translation.UPLOAD_START,
            chat_id=chat_id,
            message_id=reply_to_message_id)

        # Upload logic here...
        
async def clendir(directory):
    try:
        shutil.rmtree(directory)
    except Exception as e:
        logger.error(f"Error removing directory {directory}: {e}")

# Main function to start the bot (example)
app = Client("my_bot")

@app.on_message(filters.text & filters.private)
async def message_handler(client, message):
    url = message.text.strip()
    
    # Here you would typically run yt-dlp to get available formats/qualities.
    
    # For demonstration purposes, let's assume we have some dummy data for qualities.
    qualities = [
        "audio|192k|mp3",
        "video|720p|mp4",
        "video|480p|mp4"
    ]
    
    # Create inline buttons for each quality option.
    buttons = [
        [InlineKeyboardButton(text=f"{q.split('|')[1]} {q.split('|')[2]}", callback_data=q) for q in qualities]
    ]
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await bot.send_message(
        chat_id=message.chat.id,
        text="Choose a quality:",
        reply_markup=reply_markup,
        reply_to_message_id=message.message_id
    )

@app.on_callback_query()
async def callback_handler(client, callback_query):
   await youtube_dl_call_back(client, callback_query)

if __name__ == "__main__":
   app.run()
