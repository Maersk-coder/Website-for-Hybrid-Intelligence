"""
Loads the research publications into the database:   python manage.py import_research

It reads front_page/files/research.json (not on GitHub: see front_page/files/README.md).
Running it again REPLACES all publications with the ones in the file, so after the first import,
add and edit publications in the admin site instead (http://127.0.0.1:8001/admin/ -> Publications).
"""

import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from front_page.models import Publication

DATA_FILE = settings.BASE_DIR / 'front_page' / 'files' / 'research.json'


class Command(BaseCommand):
    help = "Load the research publications from front_page/files/research.json (replaces the current ones)"

    def handle(self, *args, **options):
        if not DATA_FILE.exists():
            raise CommandError("research.json is missing. See front_page/files/README.md.")
        items = json.loads(DATA_FILE.read_text(encoding='utf-8'))
        with transaction.atomic():                     # all or nothing
            Publication.objects.all().delete()
            for item in items:
                Publication.objects.create(order=item['order'], date=item['date'], title=item['title'],
                                           url=item['url'], excerpt=item['excerpt'], authors=item['authors'])
        self.stdout.write(f"Loaded {Publication.objects.count()} publications.")
