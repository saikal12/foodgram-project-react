import csv

from django.core.management.base import BaseCommand

from recipes.models import Tag

# python3 manage.py load_tags - команда для загрузки тегов


class Command(BaseCommand):
    """Команда для загрузки тегов в базу данных """

    help = 'Загрузка тегов в базу данных'

    def handle(self, *args, **kwargs):
        csv_path = "recipes/management/commands/tags.csv"
        with open(
                csv_path, encoding='utf-8'
        ) as file:
            reader = csv.reader(file)
            next(reader)
            tags = [
                Tag(
                    name=row[0],
                    slug=row[1],
                    color=row[2]
                )
                for row in reader
            ]
            Tag.objects.bulk_create(tags)
        print('Теги в базу данных загружены')
        print('ADD', Tag.objects.count(), 'Tags')
