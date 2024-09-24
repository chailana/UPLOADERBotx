#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K | Modified By > @DC4_WARRIOR

# The logging setup
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import asyncio
import json
import math
import os
import shutil
import time
from pyrogram.enums import ParseMode
from datetime import datetime
# The secret configuration specific things
from config import Config
# The Strings used for this "thing"
from translation import Translation
from plugins.custom_thumbnail import *
logging.getLogger("pyrogram").setLevel(logging.WARNING)
from pyrogram.types import InputMediaPhoto
from helper_funcs.display_progress import progress_for_pyrogram, humanbytes
# Database access
from database.access import clinton
from PIL import Image

async def youtube_dl_call_back(bot, update):
    cb_data = update.data
    tg_send_type, youtube_dl_format, youtube_dl_ext = cb_data.split("|")
    save_ytdl_json_path = Config.DOWNLOAD_LOCATION + "/" + str(update.from_user.id) + ".json"
    
    try:
        with open(save_ytdl_json_path, "r", encoding="utf8") as f:
            response_json = json.load(f)
    except FileNotFoundError:
        await update.message.delete(True)
        return False

    # Check if the message is a reply and has the required data.
    if not update.message.reply_to_message:
     await bot.send_message(
        chat_id=update.message.chat.id,
        text="Please reply to a message containing a valid URL.",
        parse_mode=ParseMode.HTML,
        reply_to_message_id=update.id if update.message is None else update.message.id,
    )
    return
    
    youtube_dl_url = update.message.reply_to_message.text  # Safely access text now that we've checked

    custom_file_name = str(response_json.get("title"))[:50] + "_" + youtube_dl_format + "." + youtube_dl_ext
    youtube_dl_username = None
    youtube_dl_password = None
    
    # Parsing URL and additional parameters if present
    if "|" in youtube_dl_url:
        url_parts = youtube_dl_url.split("|")
        if len(url_parts) == 2:
            youtube_dl_url = url_parts[0]
            custom_file_name = url_parts[1]
        elif len(url_parts) == 4:
            youtube_dl_url = url_parts[0]
            custom_file_name = url_parts[1]
            youtube_dl_username = url_parts[2]
            youtube_dl_password = url_parts[3]
    
    # Clean up URLs and filenames
    if youtube_dl_url is not None:
        youtube_dl_url = youtube_dl_url.strip()
    
    if custom_file_name is not None:
        custom_file_name = custom_file_name.strip()
    
    if youtube_dl_username is not None:
        youtube_dl_username = youtube_dl_username.strip()
    
    if youtube_dl_password is not None:
        youtube_dl_password = youtube_dl_password.strip()

    await bot.edit_message_text(
        text=Translation.DOWNLOAD_START,
        chat_id=update.message.chat.id,
        message_id=update.message.message_id)

    description = Translation.CUSTOM_CAPTION_UL_FILE
    
    if "fulltitle" in response_json:
        description = response_json["fulltitle"][0:1021]

    tmp_directory_for_each_user = Config.DOWNLOAD_LOCATION + "/" + str(update.from_user.id)
    
    if not os.path.isdir(tmp_directory_for_each_user):
        os.makedirs(tmp_directory_for_each_user)

    file_name = custom_file_name.replace('/', ' ')  # Replace slashes with spaces for filenames.
    
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
        
    if youtube_dl_username is not None:
        command_to_exec.append("--username")
        command_to_exec.append(youtube_dl_username)
        
    if youtube_dl_password is not None:
        command_to_exec.append("--password")
        command_to_exec.append(youtube_dl_password)

    command_to_exec.append("--no-warnings")
    command_to_exec.append("--quiet")

    start = datetime.now()
    
    process = await asyncio.create_subprocess_exec(*command_to_exec,
                                                   stdout=asyncio.subprocess.PIPE, 
                                                   stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await process.communicate()
    
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()

    ad_string_to_replace = "please report this issue on https://yt-dl.org/bug . Make sure you are using the latest version; see  https://yt-dl.org/update  on how to update. Be sure to call youtube-dl with the --verbose flag and include its complete output."
    
    if e_response and ad_string_to_replace in e_response:
        error_message = e_response.replace(ad_string_to_replace, "")
        
        await bot.edit_message_text(
            chat_id=update.message.chat.id,
            message_id=update.message.message_id,
            text=error_message)
        
        return False
    
    if t_response:
        os.remove(save_ytdl_json_path)
        asyncio.create_task(clendir(save_ytdl_json_path))
        
        try:
            file_size = os.stat(download_directory).st_size
        except FileNotFoundError:
            try:
                directory = os.path.splitext(download_directory)[0] + "." + "mp4"
                file_size = os.stat(directory).st_size
            except FileNotFoundError:
                try:
                    directory = os.path.splitext(download_directory)[0] + "." + "mkv"
                    file_size = os.stat(directory).st_size
                except FileNotFoundError:
                    file_size = 0

        if file_size == 0:
             await update.message.edit(text="File Not found 🤒")
             asyncio.create_task(clendir(tmp_directory_for_each_user))
             return
        
        if file_size > Config.TG_MAX_FILE_SIZE:
            await bot.edit_message_text(
                chat_id=update.message.chat.id,
                text=Translation.RCHD_TG_API_LIMIT.format(time_taken_for_download, humanbytes(file_size)),
                message_id=update.message.message_id)
                
        else:
            await bot.edit_message_text(
                text=Translation.UPLOAD_START,
                chat_id=update.message.chat.id,
                message_id=update.message.message_id)
                
            start_time = time.time()
            
            # Handle different media types for upload.
            if tg_send_type == "audio":
                duration = await Mdata03(download_directory)
                thumbnail = await Gthumb01(bot, update)
                
                await bot.send_audio(
                    chat_id=update.message.chat.id,
                    audio=download_directory,
                    caption=description,
                    parse_mode=ParseMode.HTML,
                    duration=duration,
                    thumb=thumbnail,
                    reply_to_message_id=update.message.reply_to_message.message_id,
                    progress=progress_for_pyrogram,
                    progress_args=(Translation.UPLOAD_START, update.message, start_time))

            elif tg_send_type == "file":
                thumbnail = await Gthumb01(bot, update)
                
                await bot.send_document(
                    chat_id=update.message.chat.id,
                    document=download_directory,
                    thumb=thumbnail,
                    caption=description,
                    parse_mode=ParseMode.HTML,
                    reply_to_message_id=update.message.reply_to_message.message_id,
                    progress=progress_for_pyrogram,
                    progress_args=(Translation.UPLOAD_START, update.message, start_time))

            elif tg_send_type == "vm":
                width, duration = await Mdata02(download_directory)
                thumbnail = await Gthumb02(bot, update, duration, download_directory)

                await bot.send_video_note(
                    chat_id=update.message.chat.id,
                    video_note=download_directory,
                    duration=duration,
                    length=width,
                    thumb=thumbnail,  # Ensure this variable is defined correctly.
                    reply_to_message_id=update.message.reply_to_message.message_id,
                    progress=progress_for_pyrogram,
                    progress_args=(Translation.UPLOAD_START, update.message, start_time))

            elif tg_send_type == "video":
                 width, height, duration = await Mdata01(download_directory)
                 thumbnail = await Gthumb02(bot, update, duration, download_directory)

                 await bot.send_video(
                     chat_id=update.message.chat.id,
                     video=download_directory,
                     caption=description,
                     parse_mode=ParseMode.HTML,
                     duration=duration,
                     width=width,
                     height=height,
                     thumb=thumbnail,
                     supports_streaming=True,
                     reply_to_message_id=update.message.reply_to_message.message_id,
                     progress=progress_for_pyrogram,
                     progress_args=(Translation.UPLOAD_START, update.message, start_time))

            asyncio.create_task(clendir(tmp_directory_for_each_user))
            asyncio.create_task(clendir(thumbnail))
            
            await bot.edit_message_text(
                text="Uploaded successfully ✓\n\nJOIN : @TeleRoidGroup",
                chat_id=update.message.chat.id,
                message_id=update.message.message_id,
                disable_web_page_preview=True)

#=================================

async def clendir(directory):
    try:
        shutil.rmtree(directory)
    except Exception as e:  # Catch specific exceptions for better debugging.
        logger.error(f"Error removing directory {directory}: {e}")
        
    try:
        os.remove(directory)
    except Exception as e:  # Catch specific exceptions for better debugging.
        logger.error(f"Error removing file {directory}: {e}")

#=================================
