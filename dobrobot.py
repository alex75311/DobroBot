from vkbottle import Bot, Message, carousel_gen, CarouselEl
from conf import TOKEN
from models import Offer
from vkbottle.api.uploader.photo import PhotoUploader

# url = 'https://dobro.mail.ru/projects/rss/target/'
#
# r = requests.get(url)
# response = BeautifulSoup(r.text, 'lxml')
# # response.is_xml = True
# x = response.find_all('offer')
# for el in x:
#     print(el.categoryid.text)
#     print(el.price.text)
#     print()

bot = Bot(TOKEN, debug='DEBUG')
photo_uploader = PhotoUploader(bot.api, generate_attachment_strings=True)


# @bot.on.message()
# async def wrapper(ans: Message):
#
#     user = await bot.api.users.get(ans.from_id, fields='sex, bdate, city, country')
#     data = await photo_uploader.get_data_from_link('https://dobro.mail.ru/media/images/thumbnails/gDw1D2pWD29COwD_XS3uP1BD5vOs0IxFcRRzk3Hv-Grl7A7XxreFRvIYqtDCPrOVNpS2WI_ZtQrDkNfaeoho-Kszg30VyXXIamsjw4Z2V6lHPI26IJP3DdzWa7PW9_5kPKGu4gxI-mgKwZHx4JV77Pzltm06Y3klynI3mq8yNv4EEIkmZsVz3w8935KmMVivWhCbVtbvBAD0uhP_XprU4OFvTWRYfl7QDFx7vIJBwN72YGdWZ6U_dL9d2PbZKPDTMcDMvtrHcqvlqCOGQ3ZXKPSRtSNNe908O5oSrwUL9cUkIJ7-_uHU8DGlytKuuDUsJE_kAzJ5BoZS6sGljxMaTg==.jpg')
#     photo = await photo_uploader.upload_message_photo(data)
#     await ans('Молодец', attachment=photo)


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


@bot.on.message()
async def send_offer_info(ans: Message):
    offer_id = ans.text
    try:
        offer = Offer.select().where(Offer.offer_id == offer_id).get()
    except Exception as e:
        print(e)
    else:
        photo = await get_message_photo_from_url(offer.picture)
        await ans(f'{offer.short_description} \n\n '
                  f'Собрано {offer.collected_many} руб. из {offer.total_many} руб. \n\n Подробнее {offer.url}', attachment=photo)
    # finally:
    #     photo = await get_message_photo_from_url(offer.picture)
    #     await ans(f'{offer.short_description} \n\n '
    #               f'Собрано {offer.collected_many} руб. из {offer.total_many} руб. \n\n Подробнее {offer.url}', attachment=photo)


bot.run_polling(skip_updates=False)
