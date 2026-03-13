import asyncio
import qrcode
from PIL import Image
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile

TOKEN = "8756946436:AAF6-sJrPD9_tlHZ1k2Y0VLt1LM_NfFevc4"

bot = Bot(token=TOKEN)
dp = Dispatcher()

mode = {}
user_image = {}

keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="QR обычный")],
        [KeyboardButton(text="QR с картинкой в центре")],
        [KeyboardButton(text="QR на фоне картинки")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Выберите режим:", reply_markup=keyboard)


@dp.message(lambda m: m.text == "QR обычный")
async def simple_mode(message: types.Message):
    mode[message.from_user.id] = "simple"
    await message.answer("Отправьте текст или ссылку")


@dp.message(lambda m: m.text == "QR с картинкой в центре")
async def center_mode(message: types.Message):
    mode[message.from_user.id] = "center"
    await message.answer("Отправьте картинку для центра QR")


@dp.message(lambda m: m.text == "QR на фоне картинки")
async def background_mode(message: types.Message):
    mode[message.from_user.id] = "background"
    await message.answer("Отправьте картинку для фона QR")


@dp.message(lambda m: m.photo)
async def save_image(message: types.Message):

    user_mode = mode.get(message.from_user.id)

    if user_mode not in ["center", "background"]:
        return

    file = await bot.get_file(message.photo[-1].file_id)
    path = f"user_img_{message.from_user.id}.png"

    await bot.download_file(file.file_path, path)

    user_image[message.from_user.id] = path

    await message.answer("Теперь отправьте текст или ссылку для QR")


@dp.message()
async def generate_qr(message: types.Message):

    user_mode = mode.get(message.from_user.id)

    if not user_mode:
        await message.answer("Сначала выберите режим")
        return

    data = message.text

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(data)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    if user_mode == "simple":

        file = f"qr_{message.from_user.id}.png"
        qr_img.save(file)

        await message.answer_photo(FSInputFile(file))
        return


    img_path = user_image.get(message.from_user.id)

    if not img_path:
        await message.answer("Сначала отправьте картинку")
        return

    user_img = Image.open(img_path)

    qr_w, qr_h = qr_img.size

    if user_mode == "center":

        logo_size = qr_w // 4
        user_img = user_img.resize((logo_size, logo_size))

        pos = ((qr_w - logo_size) // 2, (qr_h - logo_size) // 2)

        qr_img.paste(user_img, pos)

        file = f"qr_center_{message.from_user.id}.png"
        qr_img.save(file)

        await message.answer_photo(FSInputFile(file))


    elif user_mode == "background":

        bg = user_img.resize((qr_w, qr_h))

        result = Image.blend(bg, qr_img, 0.6)

        file = f"qr_bg_{message.from_user.id}.png"
        result.save(file)

        await message.answer_photo(FSInputFile(file))


async def main():
    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())