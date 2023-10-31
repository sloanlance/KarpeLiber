import logging

from django.core.management.base import BaseCommand
from django.db.models import F

from main.models import ItemPage, Volume

logger = logging.getLogger(__name__)


class IndexFormatter:
    """
    Format an index for printing.
    """

    def __init__(self, volumeId: int):
        try:
            Volume.objects.get(id=volumeId)
        except Volume.DoesNotExist as e:
            errorMessage = f'No volume found for ID ({volumeId}).'
            logger.error(errorMessage)
            e.args = e.args + (errorMessage,)
            raise e

        # until `ItemPage.page` is changed to an integer field, we need to
        # convert it to an integer for ordering
        self.itemPages = (ItemPage.objects.filter(volume__id=volumeId)
                          .order_by('item__topic__name', F('page') * 1,
                                    'item__name'))

    def format(self) -> str:
        """
        Format the index for printing.
        """
        previousLetter = None
        indexText = ''

        # unable to use `.distinct()` here for some reason
        # using `list(dict.fromkeys(…))` trick to mimic an ordered set
        topics = list(dict.fromkeys(self.itemPages.values_list(
            'item__topic__id', 'item__topic__name')))

        for topicId, topicName in topics:
            if topicName[0].upper() != previousLetter:
                previousLetter = topicName[0].upper()
                indexText += f'\n{previousLetter}\n\n'

            indexText += f'{topicName}: ' + '; '.join([
                f'{itemName}, {page}'
                for page, itemName in self.itemPages.filter(
                    item__topic=topicId).values_list(
                    'page', 'item__name')]) + '\n'
        return indexText


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
        indexFormatter = IndexFormatter(options[self.VOLUME_ID])
        print(indexFormatter.format())
        return
