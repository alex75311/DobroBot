import json

from lxml import etree
import requests
from bs4 import BeautifulSoup
from models import *
from peewee import IntegrityError
from requests.exceptions import ConnectionError
from conf import PREDICTOR_URL, URL_RSS


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
            offer = Offer.select().where(Offer.offer_id == el['id']).get()
            if el.picture.text != offer.picture:
                offer.picture = el.picture.text
                offer.article_quote = ''
                offer.save()


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
        'января': 'January',
        'февраля': 'February',
        'марта': 'March',
        'апреля': 'April',
        'мая': 'May',
        'июня': 'June',
        'июля': 'July',
        'августа': 'August',
        'сентября': 'September',
        'октября': 'October',
        'ноября': 'November',
        'декабря': 'December',
    }

    date_str = date_str.split(' ')[1:]

    try:
        date_str[1] = month[date_str[1]]
    except IndexError:
        date_str = ['31', 'December', '2099']

    date_str = ' '.join(date_str)
    date_str = datetime.datetime.strptime(date_str, '%d %B %Y').strftime('%Y-%m-%d')
    return date_str


def inactive_all_offers():
    Offer.update(available=False).execute()


def update_offer(offer_id, online_ml_server=False):
    available = True
    offer = Offer.select().where(Offer.offer_id == offer_id).get()
    r = requests.get(offer.url)
    if r.status_code != 200:
        print(f'Ошибка проекта {offer_id} {offer.url} - код {r.status_code}')
        offer.delete_instance()
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


def check_report():
    offers = Offer.select().where(Offer.available == False)
    for offer in offers:
        try:
            Report.select().where(Report.offer == offer).get()
        except DoesNotExist:
            report_url = offer.url + 'reports/'
            r = requests.get(report_url)
            if r.status_code == 200:
                row = Report(
                    offer=offer.id,
                )
                row.save()


if __name__ == '__main__':
    inactive_all_offers()
    parse_rss()
    try:
        update_all_offers(online_ml_server=True)
    except ConnectionError:
        print('Сервер ML недоступен, все проекты будут считаться персонифицированными')
        update_all_offers(online_ml_server=False)
    check_report()
    # update_offer(3144)
