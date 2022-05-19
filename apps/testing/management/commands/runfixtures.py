from django.core.management.base import BaseCommand
from apps.testing.fixtures.all_data import create_fixtures


class Command(BaseCommand):
    help = 'Запускает скрипт загрузки фикстур'

    def handle(self, *args, **options):
        create_fixtures(levels=['banks', 'full_order', 'extra'])
