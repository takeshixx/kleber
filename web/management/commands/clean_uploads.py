import datetime
import logging

from django.core.management.base import BaseCommand

from web.models import KleberInput

LOGGER = logging.getLogger('management_commands')


class Command(BaseCommand):
    """Delete uploads that are older than x days
    and are bigger than 1MB. Should run as crontab:

    */10 * * * * sudo -u www /usr/local/www/env/bin/python \
    /srv/kleber/manage.py clean_uploads"""
    def add_arguments(self, parser):
        parser.add_argument('-q', action='store_true', dest='query',
                            help='Just query uploads, do not delete.')

    def handle(self, *args, **options):
        delta = datetime.datetime.now()-datetime.timedelta(days=10)
        uploads = KleberInput.objects.filter(created__lt=delta,
                                             size__gt=1048576)
        if options['query']:
            print('Found %d uploads for deletion' % len(uploads))
            for u in uploads:
                print('\t' + u.shortcut)
            return
        if uploads:
            for u in uploads:
                u.delete()
            print('Deleted %d uploads' % len(uploads))
            LOGGER.info('Deleted %d uploads' % len(uploads))
