import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


# python3 manage.py load_ingredients - команда для загрузки ингредиентов

class Command(BaseCommand):
    """Команда для загрузки ингредиентов в базу данных """

    help = 'Загрузка ингредиентов в базу данных'

    def handle(self, *args, **kwargs):
        csv_path = "recipes/management/commands/ingredients.csv"
        with open(
                csv_path, encoding='utf-8'
        ) as file:
            reader = csv.reader(file)
            ingredients = [
                Ingredient(
                    name=row[0],
                    measurement_unit=row[1],
                )
                for row in reader
            ]
            Ingredient.objects.bulk_create(ingredients)
        print('Ингредиенты в базу данных загружены')
        print('ADD', Ingredient.objects.count(), 'Ingredient')
