import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN, ADMIN_GROUP_ID, CHANNEL_ID

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)


# Клавиатура для админов
admin_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Ответить", callback_data="reply"),
            InlineKeyboardButton(text="Отклонить", callback_data="reject"),
            InlineKeyboardButton(text="Принять", callback_data="approve"),
        ]
    ]
)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Подслушано АК")


@dp.message_handler(content_types=types.ContentTypes.ANY)
async def forward_to_admins(message: types.Message):
    user = message.from_user
    username = f"@{user.username}" if user.username else user.full_name
    text = message.text or message.caption or ""

    sent_msg = None

    # Отправка сообщения в группу админов
    if message.photo:
        sent_msg = await bot.send_photo(
            ADMIN_GROUP_ID,
            message.photo[-1].file_id,
            caption=text,
            reply_markup=admin_keyboard
        )
    elif message.video:
        sent_msg = await bot.send_video(
            ADMIN_GROUP_ID,
            message.video.file_id,
            caption=text,
            reply_markup=admin_keyboard
        )
    elif message.document:
        sent_msg = await bot.send_document(
            ADMIN_GROUP_ID,
            message.document.file_id,
            caption=text,
            reply_markup=admin_keyboard
        )
    elif message.voice:
        sent_msg = await bot.send_voice(
            ADMIN_GROUP_ID,
            message.voice.file_id,
            reply_markup=admin_keyboard
        )
        if text:
            await bot.send_message(ADMIN_GROUP_ID, text)
    else:
        sent_msg = await bot.send_message(
            ADMIN_GROUP_ID,
            text,
            reply_markup=admin_keyboard
        )

    # Информация об авторе (reply)
    info = (
        f"👤 От: {username}\n"
        f"🆔 ID: <code>{user.id}</code>"
    )

    await bot.send_message(
        ADMIN_GROUP_ID,
        info,
        reply_to_message_id=sent_msg.message_id
    )

    await message.answer("Отправлено 👌")


# Обработка кнопок
@dp.callback_query_handler(lambda c: c.data in ["reply", "reject", "approve"])
async def process_buttons(callback: types.CallbackQuery):
    action = callback.data
    msg = callback.message

    # Публикация в канал
    if action == "approve":
        try:
            if msg.photo:
                await bot.send_photo(
                    CHANNEL_ID,
                    msg.photo[-1].file_id,
                    caption=msg.caption
                )
            elif msg.video:
                await bot.send_video(
                    CHANNEL_ID,
                    msg.video.file_id,
                    caption=msg.caption
                )
            elif msg.document:
                await bot.send_document(
                    CHANNEL_ID,
                    msg.document.file_id,
                    caption=msg.caption
                )
            elif msg.voice:
                await bot.send_voice(
                    CHANNEL_ID,
                    msg.voice.file_id
                )
            else:
                await bot.send_message(
                    CHANNEL_ID,
                    msg.text
                )

            await msg.answer("✅ Опубликовано в канале")
        except Exception as e:
            await msg.answer(f"Ошибка отправки: {e}")

        await callback.answer()

    # Отклонено
    elif action == "reject":
        await msg.answer("❌ Сообщение отклонено.")
        await callback.answer()

    # Режим ответа
    elif action == "reply":
        await msg.answer("Напишите ответ пользователю, приложив реплай к сообщению с его ID.")
        await callback.answer()


# Отправка ответа пользователю
@dp.message_handler(lambda m: m.chat.id == ADMIN_GROUP_ID, content_types=types.ContentTypes.TEXT)
async def admin_reply(message: types.Message):
    if not message.reply_to_message:
        return

    content = message.reply_to_message.text or message.reply_to_message.caption or ""
    user_id = None

    for line in content.split("\n"):
        if "ID:" in line:
            try:
                user_id = int(
                    line.replace("ID:", "")
                    .replace("🆔", "")
                    .replace("<code>", "")
                    .replace("</code>", "")
                    .strip()
                )
            except Exception:
                pass

    if not user_id:
        await message.answer("❌ Не удалось найти ID пользователя.")
        return

    await bot.send_message(
        user_id,
        f"Ответ администрации:\n\n{message.text}"
    )
    await message.answer("Ответ отправлен 👍")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
