from vkbottle import Bot, Message, carousel_gen, CarouselEl
from vkbottle.api.keyboard import Keyboard, Text, Location, OpenLink
from conf import TOKEN, API_APP, API_KEY
from models import Offer, Category
from vkbottle.api.uploader.photo import PhotoUploader
from vkbottle.branch import ClsBranch, rule_disposal
from vkbottle.rule import VBMLRule

bot = Bot(TOKEN, debug='DEBUG')
photo_uploader = PhotoUploader(bot.api, generate_attachment_strings=True)


def get_pay_link(project_url):
    return project_url + '/donate/settings/?eventCategory=Project'


async def get_carousel_category(category_id=1, start=0, quantity=9):
    offers = Offer.select().where(Offer.category_id == category_id)[start:start + quantity]
    elements = []
    for offer in offers:
        elements.append(CarouselEl(
            title=offer.name,
            description=f"Собрано {offer.collected_many} руб. из {offer.total_many} руб.",
            # photo_id=(await get_message_photo_from_url(offer.picture)).replace('photo', ''),
            photo_id='-109837093_457242811',
            action={
                "type": "open_link",
                "link": offer.url,
            },
            buttons=[{
                "action": {
                    "type": "open_link",
                    "label": "Хочу помочь",
                    "payload": "{}",
                    "link": offer.url,
                }
            }],

        ))

    return elements


async def get_message_photo_from_url(photo_link):
    data = await photo_uploader.get_data_from_link(photo_link)
    photo = await photo_uploader.upload_message_photo(data)
    return photo


@bot.on.message(text='Карусель <category_id>')
async def send_carousel(ans: Message, category_id):
    carousel = await get_carousel_category(category_id)
    await ans('1', template=carousel_gen(*carousel))


@bot.on.message(text='Проект <project_id>', lower=True)
async def send_offer_info(ans: Message, project_id):
    separator = '' * 25
    try:
        offer = Offer.select().where(Offer.offer_id == project_id).get()
    except Exception as e:
        print(e)
    else:
        photo = await get_message_photo_from_url(offer.picture)
        keyboard = Keyboard(inline=True)
        keyboard.add_row()
        user = await bot.api.users.get(ans.from_id)
        user_id = user[0].id
        keyboard.add_button(OpenLink("Хочу помочь", link=get_pay_link(offer.url)))
        await ans(f'{separator}\n\n{offer.short_description} \n\n '
                  f'Собрано {offer.collected_many} руб. из {offer.total_many} руб. \n\n Подробнее {offer.url}',
                  attachment=photo,
                  keyboard=keyboard.generate())


@bot.on.message(text='Узнать о проектах', lower=True)
async def projects_menu(ans: Message):
    keyboard = Keyboard(inline=False)
    keyboard.add_row()
    keyboard.add_button(Text(label='Текущие'), color='primary')
    # keyboard.add_button(Text(label='Завершенные'), color='primary')

    await ans('Какие показать проекты?', keyboard=keyboard.generate())


@bot.on.message(text='Текущие', lower=True)
async def project_submenu(ans: Message):
    keyboard = Keyboard(inline=False)
    keyboard.add_row()
    keyboard.add_button(Text(label='По категории'), color='primary')

    await ans('.', keyboard=keyboard.generate())


@bot.on.message(text='По категории', lower=True)
async def show_category(ans: Message):
    categories = Category.select()
    keyboard = Keyboard(inline=False)

    for category in categories:
        keyboard.add_row()
        keyboard.add_button(Text(label=f'Категория: {category.name}'), color='primary')

    await ans('Выберите категорию', keyboard=keyboard.generate())


@bot.on.message(text="Категория: <category_name>", lower=True)
async def wrapper(ans: Message, category_name):
    def get_project(category_name):
        c = Category.select().where(Category.name == category_name)
        projects = Offer.select().where(Offer.category_id == c)
        for project in projects:
            yield project

    p = get_project(category_name)

    await bot.branch.add(ans.peer_id, "show_project_from_category", category_name=category_name, p=p)


@bot.branch.cls_branch("show_project_from_category")
class Branch(ClsBranch):
    @rule_disposal(VBMLRule(["Сменить категорию"], lower=True))
    async def exit_branch(self, ans: Message):
        await bot.branch.exit(ans.peer_id)
        await show_category(ans)

    @bot.on.message(text="Категория: <category_name>", lower=True)
    async def branch(self, ans: Message, *args):

        # for project in p:
        keyboard = Keyboard(one_time=True)
        keyboard.add_row()
        keyboard.add_button(Text(label='Следующий'), color='primary')
        keyboard.add_row()
        keyboard.add_button(Text(label='Сменить категорию'), color='primary')

        try:
            await send_offer_info(ans, next(self.context['p']).offer_id)
        except StopIteration:
            await ans('В данной категории больше нет сборов')
            await bot.branch.exit(ans.peer_id)
            await show_category(ans)
        else:
            await ans('Далее?', keyboard=keyboard.generate())


@bot.on.message()
async def start_menu(ans: Message):
    keyboard = Keyboard(inline=False)
    keyboard.add_row()
    keyboard.add_button(Text(label='Узнать о проектах'), color='primary')
    # keyboard.add_button(Text(label='Узнать о успехах'), color='primary')

    await ans('Меню', keyboard=keyboard.generate())


bot.run_polling(skip_updates=False)
