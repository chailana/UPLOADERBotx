from pyrogram import Client, filters
import asyncio
import json
import os
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ParseMode

# Initialize your bot client
app = Client("my_bot")

@app.on_message(filters.private & ~filters.via_bot & filters.regex(pattern=".*http.*"))
async def echo(client, message):
    await AddUser(client, message)

    # Check if message has message_id attribute
    if hasattr(message, 'message_id'):
        imog = await message.reply_text("Processing...⚡", reply_to_message_id=message.message_id)
    else:
        imog = await message.reply_text("Processing...⚡")

    youtube_dl_username = None
    youtube_dl_password = None
    file_name = None
    url = message.text

    if "|" in url:
        url_parts = url.split("|")
        if len(url_parts) == 2:
            url = url_parts[0].strip()
            file_name = url_parts[1].strip()
        elif len(url_parts) == 4:
            url = url_parts[0].strip()
            file_name = url_parts[1].strip()
            youtube_dl_username = url_parts[2].strip()
            youtube_dl_password = url_parts[3].strip()

    if message.entities:
        for entity in message.entities:
            if entity.type == "text_link":
                url = entity.url
            elif entity.type == "url":
                o = entity.offset
                l = entity.length
                url = url[o:o + l]

    if not url:
        await imog.edit("No valid URL found.")
        return

    command_to_exec = ["yt-dlp", "--no-warnings", "--youtube-skip-dash-manifest", "-j", url]

    if Config.HTTP_PROXY:
        command_to_exec += ["--proxy", Config.HTTP_PROXY]

    if youtube_dl_username:
        command_to_exec += ["--username", youtube_dl_username]

    if youtube_dl_password:
        command_to_exec += ["--password", youtube_dl_password]

    process = await asyncio.create_subprocess_exec(*command_to_exec,
                                                   stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()

    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()

    if e_response and "nonnumeric port" not in e_response:
        error_message = e_response.replace(Translation.ERROR_YTDLP, "")
        
        if "This video is only available for registered users." in error_message:
            error_message = Translation.SET_CUSTOM_USERNAME_PASSWORD
        else:
            error_message = "Invalid URL 🚸"
        
        await client.send_message(chat_id=message.chat.id,
                                  text=Translation.NO_VOID_FORMAT_FOUND.format(str(error_message)),
                                  disable_web_page_preview=True, parse_mode=ParseMode.HTML,
                                  reply_to_message_id=getattr(message, 'message_id', None))
        
        await imog.delete()
        return

    if t_response:
        response_json = json.loads(t_response.split("\n")[0])
        
        save_ytdl_json_path = os.path.join(Config.DOWNLOAD_LOCATION, f"{message.from_user.id}.json")
        os.makedirs(Config.DOWNLOAD_LOCATION, exist_ok=True)

        with open(save_ytdl_json_path, "w", encoding="utf8") as outfile:
            json.dump(response_json, outfile, ensure_ascii=False)

        inline_keyboard = []
        duration = response_json.get("duration")

        if "formats" in response_json:
            for formats in response_json["formats"]:
                format_id = formats.get("format_id")
                format_string = formats.get("format_note") or formats.get("format")
                format_ext = formats.get("ext")
                approx_file_size = humanbytes(formats.get("filesize", ""))

                cb_string_video = f"video|{format_id}|{format_ext}"
                cb_string_file = f"file|{format_id}|{format_ext}"

                ikeyboard = [
                    InlineKeyboardButton(f"🎬 {format_string} video {approx_file_size}", callback_data=cb_string_video.encode("UTF-8")),
                    InlineKeyboardButton(f"📂 {format_ext} {approx_file_size}", callback_data=cb_string_file.encode("UTF-8"))
                ]
                
                inline_keyboard.append(ikeyboard)

            if duration:
                inline_keyboard.append([
                    InlineKeyboardButton("🎵 MP3 (64 kbps)", callback_data="audio|64k|mp3".encode("UTF-8")),
                    InlineKeyboardButton("🎵 MP3 (128 kbps)", callback_data="audio|128k|mp3".encode("UTF-8")),
                    InlineKeyboardButton("🎵 MP3 (320 kbps)", callback_data="audio|320k|mp3".encode("UTF-8"))
                ])

        reply_markup = InlineKeyboardMarkup(inline_keyboard)
        
        await imog.delete()
        
        await client.send_message(chat_id=message.chat.id,
                                  text=Translation.FORMAT_SELECTION + "\n" + Translation.SET_CUSTOM_USERNAME_PASSWORD,
                                  reply_markup=reply_markup,
                                  parse_mode=ParseMode.HTML,
                                  reply_to_message_id=getattr(message, 'message_id', None))

# Start the bot using asyncio.run to handle the event loop correctly
if __name__ == "__main__":
    asyncio.run(app.run())
