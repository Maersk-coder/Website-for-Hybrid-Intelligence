"""
Copies the pictures for the three Manifesto pages:   python manage.py import_manifesto_images

It takes the pictures in front_page/files/manifesto_images/ (not on GitHub: see front_page/files/README.md)
and copies them into media/manifesto/, where the Manifesto pages show them.
The pages are written in their templates (templates/buttons/manifesto/), so there is nothing to put in the database.
Running it again simply copies the pictures again.
"""

import shutil

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

SOURCE = settings.BASE_DIR / 'front_page' / 'files' / 'manifesto_images'   # where the pictures are kept
TARGET = settings.MEDIA_ROOT / 'manifesto'                                 # where the website shows them from


class Command(BaseCommand):
    help = "Copy the Manifesto pictures from front_page/files/manifesto_images/ into media/manifesto/"

    def handle(self, *args, **options):
        if not SOURCE.exists():
            raise CommandError("The folder manifesto_images is missing. See front_page/files/README.md.")
        TARGET.mkdir(parents=True, exist_ok=True)      # make media/manifesto/ if it isn't there yet
        copied = 0
        for picture in SOURCE.iterdir():
            if picture.is_file():
                shutil.copy2(picture, TARGET / picture.name)
                copied += 1
        self.stdout.write(f"Copied {copied} pictures into media/manifesto/.")
