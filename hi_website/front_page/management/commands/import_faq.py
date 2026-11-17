"""
Loads the FAQ (categories, questions and answers) into the database:   python manage.py import_faq

It reads front_page/files/faq.json (not on GitHub: see front_page/files/README.md).
Run it once on a new computer or server. Running it again REPLACES all FAQ questions with the ones in
the file, so changes made in the admin site since then are lost. After the first import, it's
easier to edit the FAQ in the admin site (http://127.0.0.1:8001/admin/ -> FAQ categories).
"""

import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from front_page.models import FaqCategory, FaqQuestion

FAQ_FILE = settings.BASE_DIR / 'front_page' / 'files' / 'faq.json'


class Command(BaseCommand):
    help = "Load the FAQ from front_page/files/faq.json into the database (replaces the current FAQ)"

    def handle(self, *args, **options):
        if not FAQ_FILE.exists():
            raise CommandError(f"{FAQ_FILE.name} is missing. See front_page/files/README.md.")
        categories = json.loads(FAQ_FILE.read_text(encoding='utf-8'))

        # transaction.atomic: all or nothing. If something goes wrong halfway, the old FAQ stays.
        with transaction.atomic():
            FaqCategory.objects.all().delete()          # also deletes their questions (on_delete=CASCADE)
            for place, item in enumerate(categories, start=1):
                category = FaqCategory.objects.create(title=item['title'], anchor=item['anchor'], order=place)
                for q in item['questions']:
                    FaqQuestion.objects.create(category=category, number=q['number'],
                                               question=q['question'], answer=q['answer'])

        self.stdout.write(f"Loaded {FaqCategory.objects.count()} categories and {FaqQuestion.objects.count()} questions.")
