import logging

from django.core.management.base import BaseCommand

from main.indexformatter import IndexFormatter

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    VOLUME_ID = 'volumeId'
    help = ('Produce a printable index for entries '
            'associated with a specific volume.')

    def add_arguments(self, parser):
        parser.add_argument(
            self.VOLUME_ID, type=int,
            help='ID number of the volume for which the index is to '
                 'be printed.  The ID number can be found in the admin '
                 'pages and is often the same as the year of the '
                 "volume's starting date.")

    def handle(self, *args, **options):
        print(IndexFormatter(options[self.VOLUME_ID]).format())

