"""
Loads the press stories into the database:   python manage.py import_press

It reads front_page/files/press.json and the pictures in front_page/files/press_images/
(not on GitHub: see front_page/files/README.md). The pictures are copied into media/press/.
Running it again REPLACES all press stories with the ones in the file, so after the first import,
add and edit stories in the admin site instead (http://127.0.0.1:8001/admin/ -> Press articles).
"""

import json

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from front_page.models import PressArticle

FILES = settings.BASE_DIR / 'front_page' / 'files'


class Command(BaseCommand):
    help = "Load the press stories from front_page/files/press.json (replaces the current ones)"

    def handle(self, *args, **options):
        data_file = FILES / 'press.json'
        if not data_file.exists():
            raise CommandError("press.json is missing. See front_page/files/README.md.")
        stories = json.loads(data_file.read_text(encoding='utf-8'))

        with transaction.atomic():                     # all or nothing
            for old in PressArticle.objects.all():
                old.image.delete(save=False)           # remove the old copy of its picture from media/
                old.delete()
            missing = 0
            for item in stories:
                article = PressArticle(title=item['title'], outlet=item['outlet'], date=item['date'],
                                       excerpt=item['excerpt'], url=item['url'])
                picture = FILES / 'press_images' / item['image']
                if picture.exists():
                    with picture.open('rb') as f:
                        article.image.save(item['image'], File(f), save=False)   # copies it into media/press/
                else:
                    missing += 1
                article.save()

        self.stdout.write(f"Loaded {PressArticle.objects.count()} press stories ({missing} without a picture).")
