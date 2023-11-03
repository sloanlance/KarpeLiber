import logging
from itertools import groupby

from django.db.models import F
from django.db.models.query import QuerySet

from main.models import Volume, ItemPage

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

        # until `ItemPage.page` string is changed to an integer, it must
        # be converted for ordering; `int()` doesn't work here, so using `* 1`
        self.itemPages: QuerySet = (
            ItemPage.objects.filter(volume__id=volumeId)
            .order_by('item__topic__name', F('page') * 1, 'item__name'))

    def format(self) -> str:
        """
        Format the index for printing.
        """
        previousLetter: str = ''
        indexText: str = ''

        topic: str
        topicLetter: str
        itemPages: QuerySet

        for (topic, topicLetter), itemPages in groupby(
                self.itemPages, lambda ip: (
                        (n := ip.item.topic.name), n[0].upper())):
            indexText += (
                    (f'\n{(previousLetter := topicLetter)}\n\n'
                     if previousLetter != topicLetter else '')
                    + f'{topic}: '
                    + '; '.join([f'{itemPage.item.name}, {itemPage.page}'
                                 for itemPage in itemPages])
                    + '\n')

        return indexText


