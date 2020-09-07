import locale

import requests
from bs4 import BeautifulSoup
from models import *

URL_RSS = 'https://dobro.mail.ru/projects/rss/target/'
locale.setlocale(locale.LC_ALL, '')


def create_offer(name, category_id, url, picture, offer_id):
    row = Offer(
        name=name,
        category_id=category_id,
        url=url,
        picture=picture,
        offer_id=offer_id,
    )
    row.save()


def parse_rss():
    r = requests.get(URL_RSS)
    soup = BeautifulSoup(r.text, 'lxml')
    x = soup.find_all('offer')
    for el in x:
        create_offer(
            name=el.typeprefix.text,
            category_id=el.categoryid.text,
            url=el.url.text,
            picture=el.picture.text,
            offer_id=el['id'],
        )


def create_city(city_name):
    row = City(
        name=city_name,
    )
    row.save()


def get_city_id(city_name):
    try:
        id_ = City.select().where(City.name == city_name).get()
    except DoesNotExist:
        return False
    return id_


def refactor_date_format(date_str):
    month = {
      'января': 'январь',
      'февраля': 'февраль',
      'марта': 'март',
      'апреля': 'апрель',
      'мая': 'май',
      'июня': 'июнь',
      'июля': 'июль',
      'августа': 'август',
      'сентября': 'сентябрь',
      'октября': 'октябрь',
      'ноября': 'ноябрь',
      'декабря': 'декабрь',
    }

    date_str = date_str.split(' ')[1:]

    try:
        date_str[1] = month[date_str[1]]
    except IndexError:
        date_str = ['31', 'декабрь', '2099']

    date_str = ' '.join(date_str)
    date_str = datetime.datetime.strptime(date_str, '%d %B %Y').strftime('%Y-%m-%d')
    return date_str


def update_offer(offer_id):
    offer = Offer.select().where(Offer.offer_id == offer_id).get()
    r = requests.get(offer.url)
    soup = BeautifulSoup(r.text, 'lxml')
    name = soup.find(class_='hdr__inner').text
    short_description = soup.find(class_='p-project__lead').text
    article_text = soup.find(class_='article__text').text
    city = soup.find('span', class_='breadcrumbs__item').text
    collected_many = soup.find(class_='p-money__money').text.replace('р.', '').replace(' ', '')
    try:
        total_many = soup.find(class_='p-money__money p-money__money_goal').text.replace('р.', '').replace(' ', '')
    except AttributeError:
        total_many = ''
    final_date = soup.find(class_='note__text breadcrumbs__text').text

    try:
        create_city(city)
    except IntegrityError:
        pass

    city_id = get_city_id(city)

    Offer.update(
        name=name,
        short_description=short_description,
        article_text=article_text,
        city_id=city_id,
        collected_many=collected_many,
        total_many=total_many,
        final_date=refactor_date_format(final_date),
    ).where(Offer.offer_id == offer_id).execute()

    print(f'{datetime.datetime.now()} Выполнено: {offer_id} - {name}')


def update_all_offers():
    offers = Offer.select()
    for offer in offers:
        update_offer(offer.offer_id)


if __name__ == '__main__':
    parse_rss()
    update_all_offers()
