"""
Loads the use cases into the database:   python manage.py import_use_cases

It reads front_page/files/use_cases.json and the pictures in front_page/files/use_case_images/
(not on GitHub: see front_page/files/README.md). The pictures are copied into media/use_cases/.
Running it again REPLACES all use cases, so after the first import, add and edit them in the admin site.
"""

import json

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from front_page.models import UseCase

FILES = settings.BASE_DIR / 'front_page' / 'files'


class Command(BaseCommand):
    help = "Load the use cases from front_page/files/use_cases.json (replaces the current ones)"

    def handle(self, *args, **options):
        data_file = FILES / 'use_cases.json'
        if not data_file.exists():
            raise CommandError("use_cases.json is missing. See front_page/files/README.md.")
        items = json.loads(data_file.read_text(encoding='utf-8'))

        with transaction.atomic():                     # all or nothing
            for old in UseCase.objects.all():
                old.image.delete(save=False)           # remove the old copy of its picture from media/
                old.delete()
            missing = 0
            for item in items:
                case = UseCase(order=item['order'], organisation=item['organisation'], title=item['title'],
                               kind=item['kind'], url=item['url'])
                picture = FILES / 'use_case_images' / item['image']
                if picture.exists():
                    with picture.open('rb') as f:
                        case.image.save(item['image'], File(f), save=False)   # copies it into media/use_cases/
                else:
                    missing += 1
                case.save()

        self.stdout.write(f"Loaded {UseCase.objects.count()} use cases ({missing} without a picture).")
