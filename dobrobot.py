import os
from datetime import datetime, timedelta
from random import randint

from peewee import fn, DoesNotExist
from vkbottle import Bot, Message
from vkbottle.api.keyboard import Keyboard, Text, OpenLink
from vkbottle.user import User
from conf import BOT_TOKEN, USER_TOKEN, PREDICTOR_URL, GROUP_ID, ALBOM_ID
from models import Offer, Category, Report
from vkbottle.api.uploader.photo import PhotoUploader
import requests
import json

if not os.path.exists('tmp'):
    os.makedirs('tmp')

bot = Bot(BOT_TOKEN, debug='DEBUG')
user = User(USER_TOKEN)

photo_uploader = PhotoUploader(user.api, generate_attachment_strings=True)

NEXT_AND_BACK_KEY_DICT = {
    'Следующий': 'primary',
    'Назад': 'primary',
}
LITTLE_BIT_SUM = 20000  # Сумма для раздела "чуть-чуть не хватает"
URGENT_DAY = 10  # Количество дней для раздела "Срочные"


def get_pay_link(project_url):
    """
    Ссылка на оплату
    :param project_url: url
    :return: url
    """
    return project_url + '/donate/settings/?eventCategory=Project'


async def get_message_photo_from_url(photo_link):  # первая загрузка в альбом, дальше уже из альбома брать
    """
    Получение ссылки фото для ВК из ссылки интернета
    :param photo_link: url
    :return: photo_id
    """
    group_id = GROUP_ID
    albom_id = ALBOM_ID
    photo = requests.get(photo_link)
    file_name = f'tmp/{randint(0, 100)}.jpg'
    with open(file_name, 'wb') as file:
        file.write(photo.content)
    pathlike = file_name
    photo = await photo_uploader.upload_photo_to_album(album_id=albom_id, group_id=group_id, pathlike=pathlike)
    os.remove(file_name)

    return photo[0]


# async def get_message_photo_from_url(photo_link):     # каждый раз грузит по ссылке
#     """
#     Получение ссылки фото для ВК из ссылки интернета
#     :param photo_link: url
#     :return: photo_id
#     """
#     data = await photo_uploader.get_data_from_link(photo_link)
#     photo = await photo_uploader.upload_message_photo(data)
#     return photo


@bot.on.event.photo_comment_new()
# @bot.on.event.photo_comment_edit()
@bot.on.event.wall_reply_new()
# @bot.on.event.wall_reply_edit()
async def a(event):
    text = event.text
    response = requests.post(PREDICTOR_URL + 'msg_score', {'text': text})
    msg_score = float(json.loads(response.text)['score'])
    if msg_score > 0.8:
        await user.api.wall.delete_comment(comment_id=event.id, owner_id=event.owner_id)
        print(f'SCORE = {msg_score}\ntext = {event}', file=open('delete_comment.log', 'a', encoding='utf-8'))


@bot.on.message(text='Проект <project_id>', lower=True)
async def send_offer_info(ans: Message, project_id):
    """
    Отправляет сообщение о проекте по его id
    :param available: bool
    :param ans: Message
    :param project_id: integer
    :return: send message
    """
    try:
        offer = Offer.select().where(Offer.offer_id == project_id).get()
    except Exception as e:
        print(e)
    else:
        if offer.article_quote == '':
            photo = await get_message_photo_from_url(offer.picture)
            offer.article_quote = photo
            offer.save()
        else:
            photo = offer.article_quote

        keyboard = Keyboard(inline=True)
        keyboard.add_row()
        if offer.available:
            # user = await bot.api.users.get(ans.from_id)
            # user_id = user[0].id
            keyboard.add_button(OpenLink("Хочу помочь", link=get_pay_link(offer.url)))
        try:
            Report.select().where(Report.offer == offer).get()
        except DoesNotExist:
            pass
        else:
            keyboard.add_button(OpenLink("Посмотреть отчет", link=f'{offer.url}reports/'))
        keyboard.add_button(OpenLink("Сделать репост", link=f'https://vk.com/share.php?url={offer.url}'))
        await ans(f'{offer.short_description} \n\n '
                  f'Собрано {offer.collected_many} руб. из {offer.total_many} руб. \n\n Подробнее {offer.url}',
                  attachment=photo,
                  keyboard=keyboard.generate())


@bot.on.message(text='Узнать о проектах', lower=True)
async def projects_menu(ans: Message):
    key_dict = {
        'Текущие': 'primary',
        'Системные': 'primary',
        'Завершенные': 'positive',
    }
    keyboard = get_keyboard_button(key_dict)
    await ans('О каких проектах Вы хотите узнать?', keyboard=keyboard.generate())


@bot.on.message(text='Текущие', lower=True)
async def project_submenu(ans: Message):
    key_dict = {
        'Категории': 'primary',
        'Чуть-чуть не хватает': 'positive',
        'Срочные': 'negative',
        'В начало': 'primary',
    }
    keyboard = get_keyboard_button(key_dict)
    await ans('Показать категории, проекты, которые можем закрыть уже сегодня или до конца сборов которых осталось меньше 10 дней?',
              keyboard=keyboard.generate())


@bot.on.message(text='Категории', lower=True)
async def show_category(ans: Message, personified: bool = True):
    """
    Отправляет сообщением список не пустых категорий
    :param ans: Message
    :param personified: bool
    :return: Message
    """
    categories = Category.select()
    not_empty_categories = []
    keyboard = Keyboard(inline=False)
    for category in categories:
        if category.offer_set.select().where(Offer.personified == personified).count() > 0:
            not_empty_categories.append(category)

    for category in not_empty_categories:
        keyboard.add_row()
        keyboard.add_button(Text(label=f'= {category.name} ='), color='primary')
    keyboard.add_row()
    keyboard.add_button(Text(label='В начало'), color='primary')

    await ans('Я рад, что Вас заинтересовали наши проекты. Мы не ограничиваемся помощью только людям. Мы живем в окружении '
              'природы и животных и им тоже нужна наша помощь. Поэтому все проекты у нас разделены на пять категорий. \n\n '
              'Какая категория Вас интересует?', keyboard=keyboard.generate())


@bot.on.message(text="= <category_name> =", lower=True)
async def wrapper(ans: Message, category_name):
    def get_project(category_name):
        c = Category.select().where(Category.name == category_name)
        projects = Offer.select().where(Offer.available == True).where(Offer.category_id == c). \
            where(Offer.personified == True).order_by(fn.Random())
        for project in projects:
            yield project

    p = get_project(category_name)

    await bot.branch.add(ans.peer_id, "show_project_from_category", category_name=category_name, p=p)
    await send_offer_info(ans, next(p).offer_id)

    key_dict = {
        'Следующий': 'primary',
        'Сменить категорию': 'primary',
        'В начало': 'primary',
    }
    keyboard = get_keyboard_button(key_dict)
    await ans('Далее?', keyboard=keyboard.generate())


@bot.branch.simple_branch("show_project_from_category")
async def branch(ans: Message, *args, **kwargs):
    if ans.text.lower() == 'сменить категорию':
        await bot.branch.exit(ans.peer_id)
        await show_category(ans)
    elif ans.text.lower() == 'в начало':
        await bot.branch.exit(ans.peer_id)
        await start_menu(ans)
    else:
        keyboard = Keyboard(one_time=True)
        keyboard.add_row()
        keyboard.add_button(Text(label='Следующий'), color='primary')
        keyboard.add_row()
        keyboard.add_button(Text(label='Сменить категорию'), color='primary')
        keyboard.add_row()
        keyboard.add_button(Text(label='В начало'), color='primary')

        try:
            await send_offer_info(ans, next(kwargs['p']).offer_id)
        except StopIteration:
            await ans('В данной категории больше нет сборов')
            await bot.branch.exit(ans.peer_id)
            await show_category(ans)
        else:
            await ans('Далее?', keyboard=keyboard.generate())


@bot.on.message(text="Системные", lower=True)
async def wrapper(ans: Message):
    def get_project():
        projects = Offer.select().where(Offer.available == True).where(Offer.personified == False).order_by(fn.Random())
        for project in projects:
            if project.collected_many and project.total_many:
                yield project

    p = get_project()

    await bot.branch.add(ans.peer_id, "system", p=p)

    key_dict = NEXT_AND_BACK_KEY_DICT
    keyboard = get_keyboard_button(key_dict)
    await branch_send_msg(ans, keyboard, p=p, error_text='Мне пока нечего показать здесь')


@bot.on.message(text="Завершенные", lower=True)
@bot.on.message(text="Узнать о успехах", lower=True)
async def wrapper(ans: Message):
    def get_project():
        projects = Offer.select().where(Offer.available == False).order_by(fn.Random())
        for project in projects:
            yield project

    p = get_project()

    await bot.branch.add(ans.peer_id, "canceled", p=p)

    key_dict = NEXT_AND_BACK_KEY_DICT
    keyboard = get_keyboard_button(key_dict)
    await branch_send_msg(ans, keyboard, p=p, error_text='Мне пока нечего показать здесь')


@bot.on.message(text="Чуть-чуть<_>", lower=True)
async def wrapper(ans: Message, _):
    def get_project(diff_many):
        projects = Offer.select().where(Offer.available == True).where((Offer.total_many - Offer.collected_many) <= diff_many). \
            where(Offer.personified == True).order_by(fn.Random())
        for project in projects:
            if project.collected_many and project.total_many:
                yield project

    p = get_project(LITTLE_BIT_SUM)

    await bot.branch.add(ans.peer_id, "little_bit", p=p)

    key_dict = NEXT_AND_BACK_KEY_DICT
    keyboard = get_keyboard_button(key_dict)
    await branch_send_msg(ans, keyboard, p=p, error_text='Мне пока нечего показать здесь')


@bot.on.message(text="Срочные<_>", lower=True)
async def wrapper(ans: Message, _):
    def get_project(diff_date):
        date_delta = (datetime.today() + timedelta(days=diff_date)).strftime('%Y-%m-%d')
        projects = Offer.select().where(Offer.available == True).where(Offer.final_date <= date_delta).where(
            Offer.final_date >= datetime.today()). \
            where(Offer.personified == True).order_by(fn.Random())
        for project in projects:
            yield project

    p = get_project(URGENT_DAY)

    await bot.branch.add(ans.peer_id, "urgent", p=p)

    key_dict = NEXT_AND_BACK_KEY_DICT
    keyboard = get_keyboard_button(key_dict)
    await branch_send_msg(ans, keyboard, p=p, error_text='Мне пока нечего показать здесь')


def get_keyboard_button(key_dict: dict, one_time: bool = True, inline: bool = False):
    """
    Генерация клавиатуры
    :param key_dict: dict
    :param one_time: bool
    :param inline: bool
    :return:
    """
    keyboard = Keyboard(one_time=one_time, inline=inline)
    for label, color in key_dict.items():
        keyboard.add_row()
        keyboard.add_button(Text(label=label), color=color)
    return keyboard


async def branch_send_msg(ans: Message, keyboard, error_text='На данный момент это все.', *args, **kwargs):
    try:
        await send_offer_info(ans, next(kwargs['p']).offer_id)
    except StopIteration:
        await ans(error_text)
        await bot.branch.exit(ans.peer_id)
        await project_submenu(ans)
    else:
        await ans('Далее?', keyboard=keyboard.generate())


@bot.branch.simple_branch("little_bit")
@bot.branch.simple_branch("canceled")
@bot.branch.simple_branch("system")
@bot.branch.simple_branch("urgent")
async def branch(ans: Message, *args, **kwargs):
    if ans.text.lower() == 'назад':
        await bot.branch.exit(ans.peer_id)
        await project_submenu(ans)
    else:
        key_dict = NEXT_AND_BACK_KEY_DICT
        keyboard = get_keyboard_button(key_dict)

        await branch_send_msg(ans, keyboard, *args, **kwargs)


@bot.on.message()
async def start_menu(ans: Message):
    keyboard = Keyboard(inline=False)
    keyboard.add_row()
    keyboard.add_button(Text(label='Узнать о проектах'), color='primary')
    keyboard.add_row()
    keyboard.add_button(Text(label='Узнать о успехах'), color='positive')

    await ans(
        'Здравствуйте! Я - Добрыня, чат-бот благотворительного проекта Добро mail.ru (https://dobro.mail.ru/). '
        'Расскажу все о проекте и людях, которые помогают и которым мы помогаем.',
        keyboard=keyboard.generate())


bot.run_polling(skip_updates=False)
