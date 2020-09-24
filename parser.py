import json
import locale

from lxml import etree
import requests
from bs4 import BeautifulSoup
from models import *
from peewee import IntegrityError
from requests.exceptions import ConnectionError
from conf import PREDICTOR_URL, URL_RSS

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
        try:
            create_offer(
                name=el.typeprefix.text,
                category_id=el.categoryid.text,
                url=el.url.text,
                picture=el.picture.text,
                offer_id=el['id'],
            )
        except IntegrityError as e:
            print(e)


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


def inactive_all_offers():
    offers = Offer.select().where(Offer.available == True)
    for offer in offers:
        offer.available = False
        offer.save()


def update_offer(offer_id, online_ml_server=False):
    available = True
    offer = Offer.select().where(Offer.offer_id == offer_id).get()
    r = requests.get(offer.url)
    if r.status_code != 200:
        print(f'Ошибка проекта {offer_id} {offer.url} - код {r.status_code}')
        return
    soup = BeautifulSoup(r.text, 'lxml')
    name = soup.find(class_='hdr__inner').text
    short_description = soup.find(class_='p-project__lead').text
    article_text = soup.find(class_='article__text').text
    city = soup.find('span', class_='breadcrumbs__item').text
    dom = etree.HTML(str(soup))
    try:
        collected_many = soup.find(class_='p-money__money').text.replace('р.', '').replace(' ', '')
        percent = dom.xpath(
            '/html/body/div[3]/div/div[1]/div[4]/div[4]/div/div/div/div/div/div/div/div/div[2]/div[1]/div[1]/div[1]/div/div[2]/div[2]')[
            0].attrib['style'].replace('width: ', '').replace('%', '')
    except (AttributeError, IndexError):
        collected_many = 0
    try:
        total_many = soup.find(class_='p-money__money p-money__money_goal').text.replace('р.', '').replace(' ', '')
    except AttributeError:
        total_many = '999999999'
    if percent == '100':
        available = False
        if collected_many:
            total_many = collected_many
        else:
            collected_many = total_many
    elif percent == '0' and collected_many == total_many:
        collected_many = 0
    final_date = soup.find(class_='note__text breadcrumbs__text').text

    try:
        create_city(city)
    except IntegrityError:
        pass

    city_id = get_city_id(city)

    text = article_text + short_description
    personified = True
    if online_ml_server:
        response = requests.post(PREDICTOR_URL + 'project_type', {'text': text})
        offer_type = json.loads(response.text)['type']
        if offer_type == 'common':
            personified = False

    Offer.update(
        name=name,
        short_description=short_description,
        article_text=article_text,
        city_id=city_id,
        collected_many=collected_many,
        total_many=total_many,
        final_date=refactor_date_format(final_date),
        available=available,
        personified=personified,
    ).where(Offer.offer_id == offer_id).execute()

    print(f'{datetime.datetime.now()} Выполнено: {offer_id} - {name}')


def update_all_offers(online_ml_server):
    offers = Offer.select()
    for offer in offers:
        update_offer(offer.offer_id, online_ml_server)


if __name__ == '__main__':
    inactive_all_offers()
    parse_rss()
    try:
        update_all_offers(online_ml_server=True)
    except ConnectionError:
        print('Сервер ML недоступен, все проекты будут считаться персонифицированными')
        update_all_offers(online_ml_server=False)
    update_offer(3144)
