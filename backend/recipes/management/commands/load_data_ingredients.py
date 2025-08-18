import csv
import logging
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand
from recipes.models import Ingredient

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Команда для загрузки ингредиентов в базу данных."""

    help = 'Загружает ингредиенты в БД'

    def handle(self, *args, **options):
        """Выполняет загрузку ингредиентов из CSV-файла."""
        file_path = Path(settings.BASE_DIR) / 'data' / 'ingredients.csv'

        Ingredient.objects.all().delete()

        ingredients_to_create = []

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                ingredients_to_create.append(
                    Ingredient(
                        name=row[0],
                        measurement_unit=row[1]
                    )
                )

        Ingredient.objects.bulk_create(ingredients_to_create)

        logger.info(f'Загружено {len(ingredients_to_create)} ингредиентов')
        self.stdout.write(self.style.SUCCESS(
            f'Загружено {len(ingredients_to_create)} ингредиентов'
        ))
