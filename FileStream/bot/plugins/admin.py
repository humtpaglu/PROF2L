import os
import time
import string
import random
import asyncio
import aiofiles
import datetime

from FileStream.utils.broadcast_helper import send_msg
from FileStream.utils.database import Database
from FileStream.bot import FileStream
from FileStream.server.exceptions import FIleNotFound
from FileStream.config import Telegram, Server
from pyrogram import filters, Client
from pyrogram.types import Message
from pyrogram.enums.parse_mode import ParseMode

db = Database(Telegram.DATABASE_URL, Telegram.SESSION_NAME)
broadcast_ids = {}


@FileStream.on_message(filters.command("status") & filters.private & filters.user(Telegram.OWNER_ID))
async def sts(c: Client, m: Message):
    await m.reply_text(text=f"""**Total Users in DB:** `{await db.total_users_count()}`
**Banned Users in DB:** `{await db.total_banned_users_count()}`
**Total Links Generated: ** `{await db.total_files()}`"""
                       , parse_mode=ParseMode.MARKDOWN, quote=True)


@FileStream.on_message(filters.command("ban") & filters.private & filters.user(Telegram.OWNER_ID))
async def sts(b, m: Message):
    id = m.text.split("/ban ")[-1]
    if not await db.is_user_banned(int(id)):
        try:
            await db.ban_user(int(id))
            await db.delete_user(int(id))
            await m.reply_text(text=f"`{id}`** is Banned** ", parse_mode=ParseMode.MARKDOWN, quote=True)
            if not str(id).startswith('-100'):
                await b.send_message(
                    chat_id=id,
                    text="**Your Banned to Use The Bot**",
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
        except Exception as e:
            await m.reply_text(text=f"**something went wrong: {e}** ", parse_mode=ParseMode.MARKDOWN, quote=True)
    else:
        await m.reply_text(text=f"`{id}`** is Already Banned** ", parse_mode=ParseMode.MARKDOWN, quote=True)


@FileStream.on_message(filters.command("unban") & filters.private & filters.user(Telegram.OWNER_ID))
async def sts(b, m: Message):
    id = m.text.split("/unban ")[-1]
    if await db.is_user_banned(int(id)):
        try:
            await db.unban_user(int(id))
            await m.reply_text(text=f"`{id}`** is Unbanned** ", parse_mode=ParseMode.MARKDOWN, quote=True)
            if not str(id).startswith('-100'):
                await b.send_message(
                    chat_id=id,
                    text="**Your Unbanned now Use can use The Bot**",
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
        except Exception as e:
            await m.reply_text(text=f"** something went wrong: {e}**", parse_mode=ParseMode.MARKDOWN, quote=True)
    else:
        await m.reply_text(text=f"`{id}`** is not Banned** ", parse_mode=ParseMode.MARKDOWN, quote=True)


@FileStream.on_message(filters.command("broadcast") & filters.private & filters.user(Telegram.OWNER_ID) & filters.reply)
async def broadcast_(c, m):
    all_users = await db.get_all_users()
    broadcast_msg = m.reply_to_message
    while True:
        broadcast_id = ''.join([random.choice(string.ascii_letters) for i in range(3)])
        if not broadcast_ids.get(broadcast_id):
            break
    out = await m.reply_text(
        text=f"Broadcast initiated! You will be notified with log file when all the users are notified."
    )
    start_time = time.time()
    total_users = await db.total_users_count()
    done = 0
    failed = 0
    success = 0
    broadcast_ids[broadcast_id] = dict(
        total=total_users,
        current=done,
        failed=failed,
        success=success
    )
    async with aiofiles.open('broadcast.txt', 'w') as broadcast_log_file:
        async for user in all_users:
            sts, msg = await send_msg(
                user_id=int(user['id']),
                message=broadcast_msg
            )
            if msg is not None:
                await broadcast_log_file.write(msg)
            if sts == 200:
                success += 1
            else:
                failed += 1
            if sts == 400:
                await db.delete_user(user['id'])
            done += 1
            if broadcast_ids.get(broadcast_id) is None:
                break
            else:
                broadcast_ids[broadcast_id].update(
                    dict(
                        current=done,
                        failed=failed,
                        success=success
                    )
                )
                try:
                    await out.edit_text(f"Broadcast Status\n\ncurrent: {done}\nfailed:{failed}\nsuccess: {success}")
                except:
                    pass
    if broadcast_ids.get(broadcast_id):
        broadcast_ids.pop(broadcast_id)
    completed_in = datetime.timedelta(seconds=int(time.time() - start_time))
    await asyncio.sleep(3)
    await out.delete()
    if failed == 0:
        await m.reply_text(
            text=f"broadcast completed in `{completed_in}`\n\nTotal users {total_users}.\nTotal done {done}, {success} success and {failed} failed.",
            quote=True
        )
    else:
        await m.reply_document(
            document='broadcast.txt',
            caption=f"broadcast completed in `{completed_in}`\n\nTotal users {total_users}.\nTotal done {done}, {success} success and {failed} failed.",
            quote=True
        )
    os.remove('broadcast.txt')


@FileStream.on_message(filters.command("del") & filters.private & filters.user(Telegram.OWNER_ID))
async def sts(c: Client, m: Message):
    file_id = m.text.split(" ")[-1]
    try:
        file_info = await db.get_file(file_id)
    except FIleNotFound:
        await m.reply_text(
            text=f"**File Already Deleted**",
            quote=True
        )
        return
    await db.delete_one_file(file_info['_id'])
    await db.count_links(file_info['user_id'], "-")
    await m.reply_text(
        text=f"**Fɪʟᴇ Dᴇʟᴇᴛᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ !** ",
        quote=True
    )

@FileStream.on_message(filters.command("status") & filters.private & filters.user(list(Var.OWNER_ID)))
async def show_status(client: StreamBot, message: Message):
    """Display the current status of the bot, including workloads per connected bot."""
    try:
        uptime = get_readable_time(time.time() - StartTime)
        
        # Generate a string representation of workload distribution
        workloads_text = "📊 **Workloads per Bot:**\n\n"
        workloads = dict(
            ("🤖 Bot" + str(c + 1), l) 
            for c, (_, l) in enumerate(
                sorted(work_loads.items(), key=lambda x: x[1], reverse=True)
            )
        )
        for bot_name, load in workloads.items():
            workloads_text += f"   {bot_name}: {load}\n"
        
        # Combine all parts into status text
        stats_text = (
            f"⚙️ **Server Status:** Running\n\n"
            f"🕒 **Uptime:** {uptime}\n\n"
            f"🤖 **Connected Bots:** {len(multi_clients)}\n\n"
            f"{workloads_text}\n"
            f"♻️ **Version:** {__version__}\n"
        )
        
        # Send status as a reply
        await message.reply_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    
    except Exception as e:
        logging.error(f"Error displaying status: {e}")
        await message.reply_text(
            "🚨 An error occurred while retrieving the status.",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )

@FileStream.on_message(filters.command("stats") & filters.private & filters.user(list(Var.OWNER_ID)))
async def show_stats(client: StreamBot, message: Message):
    """Display server statistics where the bot is hosted."""
    try:
        current_time = get_readable_time(time.time() - StartTime)
        total, used, free = shutil.disk_usage('.')

        stats_text = (
            f"📊 **𝘽𝙤𝙩 𝙎𝙩𝙖𝙩𝙞𝙨𝙩𝙞𝙘𝙨** 📊\n\n"
            f"⏳ **Uptime:** {current_time}\n\n"
            f"💾 **Disk Space:**\n\n"
            f"   📀 **Total:** {get_readable_file_size(total)}\n\n"
            f"   📝 **Used:** {get_readable_file_size(used)}\n\n"
            f"   📭 **Free:** {get_readable_file_size(free)}\n\n\n"
            f"📶 **Data Usage:**\n\n"
            f"   🔺 **Upload:** {get_readable_file_size(psutil.net_io_counters().bytes_sent)}\n\n"
            f"   🔻 **Download:** {get_readable_file_size(psutil.net_io_counters().bytes_recv)}\n\n\n"
            f"🖥️ **CPU Usage:** {psutil.cpu_percent(interval=0.5)}%\n\n"
            f"🧠 **RAM Usage:** {psutil.virtual_memory().percent}%\n\n"
            f"📦 **Disk Usage:** {psutil.disk_usage('/').percent}%\n"
        )
        await message.reply_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    except Exception as e:
        logging.error(f"Error retrieving bot statistics: {e}")
        await message.reply_text(
            "🚨 An error occurred while retrieving the statistics.",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )



