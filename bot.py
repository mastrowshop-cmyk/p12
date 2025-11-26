import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN, ADMIN_GROUP_ID, CHANNEL_ID

bot = Bot(TOKEN)
dp = Dispatcher()

admin_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Ответить", callback_data="reply"),
            InlineKeyboardButton(text="Отклонить", callback_data="reject"),
            InlineKeyboardButton(text="Принять", callback_data="approve"),
        ]
    ]
)

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("Подслушано АК")

@dp.message()
async def forward_to_admins(message: types.Message):
    user = message.from_user
    username = f"@{user.username}" if user.username else user.full_name
    text = message.text or message.caption or ""

    sent_msg = None

    if message.photo:
        sent_msg = await bot.send_photo(
            ADMIN_GROUP_ID,
            message.photo[-1].file_id,
            caption=text if message.caption else None,
            reply_markup=admin_keyboard
        )
    elif message.video:
        sent_msg = await bot.send_video(
            ADMIN_GROUP_ID,
            message.video.file_id,
            caption=text if message.caption else None,
            reply_markup=admin_keyboard
        )
    elif message.document:
        sent_msg = await bot.send_document(
            ADMIN_GROUP_ID,
            message.document.file_id,
            caption=text if message.caption else None,
            reply_markup=admin_keyboard
        )
    elif message.voice:
        sent_msg = await bot.send_voice(
            ADMIN_GROUP_ID,
            message.voice.file_id,
            reply_markup=admin_keyboard
        )
        if text:
            sent_msg = await bot.send_message(
                ADMIN_GROUP_ID, text, reply_markup=admin_keyboard
            )
    else:
        sent_msg = await bot.send_message(
            ADMIN_GROUP_ID,
            text,
            reply_markup=admin_keyboard
        )

    info = (
        "👤 От: " + username + "\n"
        "🆔 ID: `" + str(user.id) + "`"
    )

    await bot.send_message(
        ADMIN_GROUP_ID,
        info,
        parse_mode="Markdown",
        reply_to_message_id=sent_msg.message_id
    )

    await message.answer("Отправлено 👌")

@dp.callback_query(lambda c: c.data in ["reply", "reject", "approve"])
async def process_buttons(callback: types.CallbackQuery):
    action = callback.data
    msg = callback.message

    if action == "approve":
        if msg.photo:
            await bot.send_photo(CHANNEL_ID, msg.photo[-1].file_id, caption=msg.caption)
        elif msg.video:
            await bot.send_video(CHANNEL_ID, msg.video.file_id, caption=msg.caption)
        elif msg.document:
            await bot.send_document(CHANNEL_ID, msg.document.file_id, caption=msg.caption)
        elif msg.voice:
            await bot.send_voice(CHANNEL_ID, msg.voice.file_id)
        else:
            await bot.send_message(CHANNEL_ID, msg.text)

        await msg.answer("✅ Сообщение опубликовано в канале.")
        await callback.answer()

    elif action == "reject":
        await msg.answer("❌ Сообщение отклонено.")
        await callback.answer()

    elif action == "reply":
        await msg.answer("Напишите ответ пользователю реплаем на сообщение с его ID.")
        await callback.answer("Режим ответа включён")

@dp.message(lambda msg: msg.chat.id == ADMIN_GROUP_ID and msg.reply_to_message)
async def admin_reply(message: types.Message):
    try:
        reply_msg = message.reply_to_message
        content = reply_msg.text or reply_msg.caption or ""
        user_id = None

        for line in content.split("\n"):
            if "ID:" in line:
                try:
                    user_id = int(
                        line.replace("🆔 ID:", "")
                        .replace("ID:", "")
                        .replace("`", "")
                        .strip()
                    )
                except:
                    pass

        if not user_id:
            await message.answer("❌ Не могу определить ID пользователя.")
            return

        await bot.send_message(user_id, "Ответ администрации:\n\n" + message.text)
        await message.answer("Ответ отправлен 👍")

    except Exception as e:
        await message.answer(f"Ошибка: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
