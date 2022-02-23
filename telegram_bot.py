from http import HTTPStatus

import config
import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from bs4 import BeautifulSoup
import requests

logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot, storage=storage)

TITLE = 'title'
BRAND = 'brand'

MESSAGE_TEMPLATE = (
        'Я помогаю искать {field_name} товаров по артикулам на сайте '
        '<b><a href=\'https://www.wildberries.ru/\'>Wildberries</a></b>,'
        ' для получения информации отправте артикул.'
)


@dp.message_handler(commands=['get_brand'])
async def get_brand(message: types.message, state: FSMContext):
    async with state.proxy() as data:
        data['field_to_retrieve'] = BRAND
    await bot.send_message(
        message.chat.id,
        MESSAGE_TEMPLATE.format(field_name='Бренд'),
        parse_mode='html',
        disable_web_page_preview=True
    )


@dp.message_handler(commands=['get_title'])
async def get_title(message: types.message, state: FSMContext):
    async with state.proxy() as data:
        data['field_to_retrieve'] = TITLE
    await bot.send_message(
        message.chat.id,
        MESSAGE_TEMPLATE.format(field_name='Название'),
        parse_mode='html',
        disable_web_page_preview=True
    )


# получить информацию с html страницы

@dp.message_handler(content_types=['text'])
async def parser(message: types.message, state: FSMContext):
    async with state.proxy() as data:
        field_to_retrieve = data['field_to_retrieve']
    if message.text.isdigit():
        url = f'https://www.wildberries.ru/catalog/{message.text}/detail.aspx'
        # TODO: made async requests
        response = requests.get(url)
        if response.status_code == HTTPStatus.NOT_FOUND:
            await bot.send_message(message.chat.id, 'Вы ввели несуществующий артикул')
        elif not response.ok:
            await bot.send_message(message.chat.id, 'Что-то пошло не так')
        soup = BeautifulSoup(response.text, 'html.parser')
        if field_to_retrieve == TITLE:
            title = soup.find('div', class_='same-part-kt__header-wrap hide-mobile').find('h1').contents[2].text
            if title:
                await bot.send_message(message.chat.id, title)
            else:
                await bot.send_message(message.chat.id, 'описание не найдено')
        elif field_to_retrieve == BRAND:
            brand = soup.find('div', class_='same-part-kt__header-wrap hide-mobile').find('span').text
            await bot.send_message(message.chat.id, brand)
    else:
        await bot.send_message(message.chat.id, 'введите корректный артикул')


# получить информацию HTTP запросом который присылает данные в json
#
# @dp.message_handler(content_types=['text'])
# async def parser(message: types.message, state: FSMContext):
#     async with state.proxy() as data:
#         field_to_retrieve = data['field_to_retrieve']
#     if message.text.isdigit():
#         url = f'https://wbx-content-v2.wbstatic.net/ru/{message.text}.json'
#         # TODO: made async requests
#         response = requests.get(url).json()
#         if field_to_retrieve == TITLE:
#             if response['description']:
#                 await bot.send_message(message.chat.id, response['imt_name'])
#             else:
#                 await bot.send_message(message.chat.id, 'описание не найдено')
#         elif field_to_retrieve == BRAND:
#             await bot.send_message(message.chat.id, response['selling']['brand_name'])
#     else:
#         await bot.send_message(message.chat.id, 'введите корректный артикул')

# run long-polling
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
