import datetime
from conf import DB_IP, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
from peewee import *

db = PostgresqlDatabase(DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_IP, port=DB_PORT,
                        autocommit=True, autorollback=True)


class BaseModel(Model):
    class Meta:
        database = db


class Category(BaseModel):
    name = CharField(null=False, unique=True)

    class Meta:
        db_table = 'Category'


class City(BaseModel):
    name = CharField(null=False, unique=True)

    class Meta:
        db_table = 'City'


class Offer(BaseModel):
    name = CharField(null=False)
    offer_id = IntegerField(unique=True)
    url = TextField(null=False)
    category_id = ForeignKeyField(Category)
    picture = TextField(null=True)
    city_id = ForeignKeyField(City, default=0)
    start_date = DateField(default=datetime.datetime.now)
    final_date = DateField(default='2999-12-31')
    collected_many = IntegerField(default=0)
    total_many = IntegerField(default=0)
    short_description = TextField(default='')
    article_text = TextField(default='')
    article_quote = CharField(default='')
    personified = BooleanField(default=True)
    available = BooleanField(default=True)

    class Meta:
        db_table = 'Offer'


class Report(BaseModel):
    offer = ForeignKeyField(Offer, unique=True)
    date = DateField(default=datetime.datetime.now)

    class Meta:
        db_table = 'Report'


if __name__ == '__main__':
    db.connect()
    Category.create_table()
    City.create_table()
    Offer.create_table()
    Report.create_table()

    try:
        City.create(id=0, name='')
        Category.create(id=1, name='Дети')
        Category.create(id=2, name='Взрослые')
        Category.create(id=3, name='Пожилые')
        Category.create(id=4, name='Животные')
        Category.create(id=5, name='Природа')
        Category.create(id=32, name='Другое')
    except IntegrityError:
        pass
