import calendar
import logging
from datetime import datetime
from typing import List, Tuple, Optional

import pandas as pd
from django.core.management.base import BaseCommand

from main.models import Topic, Item, ItemPage, Volume

logger = logging.getLogger(__name__)


class Importer:
    UTF_8 = 'utf-8'
    WINDOWS_1252 = 'windows-1252'

    @staticmethod
    def readCsvMultiEncoding(fileName: str, encodings: List[str]) -> \
            Tuple[pd.DataFrame, str]:
        """
        Try reading a CSV using several encodings until one works.
        TODO: Add support for TSV/Excel
        """

        df: Optional[pd.DataFrame] = None
        encoding: Optional[str] = None
        lastException: Optional[Exception] = None

        for encoding in encodings:
            lastException = None
            try:
                df = pd.read_csv(fileName, encoding=encoding)
            except UnicodeDecodeError as e:
                lastException = e
                continue

        if lastException:
            raise lastException

        return df, encoding

    @staticmethod
    def cleanUpData(df: pd.DataFrame) -> Optional[pd.DataFrame]:
        REQUIRED_COLUMNS = {'topic', 'item', 'page', 'year', 'month'}

        # dictionary of month name/abbr to number
        MONTHS = {month.lower(): index for index, month in
                  list(enumerate(calendar.month_name[1:], 1)) +
                  list(enumerate(calendar.month_abbr[1:], 1))}

        # drop rows of all null values and drop columns
        # with any null values, because all values are required
        # dropped required columns will trigger an error later
        df = df.dropna(axis='rows', how='all') \
            .dropna(axis='columns', how='any')

        # lower-case and strip column names,
        # rename "phrase" column for backwards compatibility
        # hopefully one `rename()` call is more efficient than two
        df = df.rename(
            mapper=lambda s: s.lower().strip().replace('phrase', 'topic'),
            axis='columns')

        if REQUIRED_COLUMNS & set(df.columns) < REQUIRED_COLUMNS:
            logger.error(
                'Some required columns are missing or empty: ' +
                ', '.join(f'"{c}"' for c in REQUIRED_COLUMNS))
            return None

        # lower case month names, convert to number
        df['month'] = df['month'].apply(str.lower).apply(MONTHS.get)

        # remove leading and trailing whitespace from topics and items
        df['topic'] = df['topic'].apply(str.strip)
        df['item'] = df['item'].apply(str.strip)

        # make columns integer: "year" for datetime compatibility,
        # "page" to remove ".0" from end
        df = df.astype({'page': int, 'year': int, 'month': int})

        return df

    @staticmethod
    def importIndex(df: pd.DataFrame):
        """
        Import index data from DataFrame
        """
        logger.info(f'Initial rows x columns: {df.shape[0]} x {df.shape[1]}')

        df = Importer.cleanUpData(df)
        if df is None:
            return

        logger.debug(df)
        logger.info(f'Remaining rows x columns: {df.shape[0]} x {df.shape[1]}')

        newTopics, newItems, newItemPages = 0, 0, 0
        for row in df.itertuples():
            logger.debug(row)

            itemDate = datetime(row.year, row.month, 1)

            try:
                volume = Volume.objects.get(
                    dateBegin__lte=itemDate,
                    dateEnd__gte=itemDate)
            except Volume.DoesNotExist as e:
                logger.error(f'No volume found for {itemDate:%Y-%b}.')
                return

            if row.page > volume.pages:
                logger.error(
                    f'Page ({row.page}) is greater than the '
                    f'number of pages in the volume ({volume.pages}).')
                return

            topic, new = Topic.objects.get_or_create(
                name=row.topic)
            # logger.debug(topic)
            newTopics += int(new)

            try:
                item, new = Item.objects.get_or_create(
                    name=row.item,
                    topic=topic)
                # logger.debug(item)
                newItems += int(new)
            except Item.MultipleObjectsReturned as e:
                logger.warning(
                    f'Multiple items found for "{row.item}" '
                    f'in topic "{topic}".')
                item = Item.objects.filter(
                    name=row.item,
                    topic=topic).first()
                logger.warning(
                    f'Using first item found, ID ({item.id}).')

            itemPage, new = ItemPage.objects.get_or_create(
                item=item, page=row.page, date=itemDate, volume=volume)
            # logger.debug(itemPage)
            newItemPages += int(new)

        logger.info(f'{newTopics} new topics, '
                    f'{newItems} new items, '
                    f'{newItemPages} new item pages')
        logger.info('The CSV file has been imported.')


class Command(BaseCommand):
    FILE_NAME = 'fileName'
    help = 'Imports index entries from a CSV file.'

    def add_arguments(self, parser):
        parser.add_argument(self.FILE_NAME, type=str,
                            help='Name of the CSV file to import.')

    def handle(self, *args, **options):
        # load the CSV file
        df, encoding = Importer.readCsvMultiEncoding(
            options[self.FILE_NAME],
            [Importer.UTF_8, Importer.WINDOWS_1252])
        # load the index
        Importer.importIndex(df)
        # self.stdout.write(
        #     self.style.ERROR('Success!')
        # )

    # for poll_id in options['poll_ids']:
    #     try:
    #         poll = Poll.objects.get(pk=poll_id)
    #     except Poll.DoesNotExist:
    #         raise CommandError('Poll "%s" does not exist' % poll_id)
    #
    #     poll.opened = False
    #     poll.save()
    #
    #     self.stdout.write(
    #         self.style.SUCCESS('Successfully closed poll "%s"' % poll_id)
    #     )
