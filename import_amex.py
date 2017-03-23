#!/usr/bin/env python3
import logging

from plumbum.cmd import lftp, rsync, mkdir


logfile = '/var/log/demeter/import.log'
import_dir = '/tmp/demeter/amex'
recovery_dir = '/data/demeter/recovery/'

archive_server = {
    'host': 'txmatch@172.26.127.22',
    'port': '2020',
    'dir': '/data/demeter/archive/',
}

db_server = {
    'host': 'txmatch@172.26.127.21',
    'port': '2020',
    'dir': '/tmp/import/payment/',
}


logging.basicConfig(filename=logfile,
                    level=logging.DEBUG,
                    format='[%(asctime)s] %(levelname)s :: %(message)s')
logger = logging.getLogger('__name__')

mkdir('-p', import_dir)

logger.debug('Running import process for amex files.')

logger.debug('Importing files...')
lftp('sftp://CHINGSPRD:taua@13@fsgateway.aexp.com',
     '-e', 'mirror --include-glob=AXP_CHINGS_TLOG_* outbox {}; bye'.format(import_dir))

logger.debug('Archiving files...')
rsync('-r',
      '-e', 'ssh -p {}'.format(archive_server['port']),
      '-a',
      '--progress',
      import_dir,
      '{}:{}'.format(archive_server['host'],
                     archive_server['dir']))

logger.debug('Transferring files to aphrodite...')
rsync('-r',
      '-e', 'ssh -p {}'.format(db_server['port']),
      '-a',
      '--progress',
      '--remove-source-files',
      import_dir,
      '{}:{}'.format(db_server['host'],
                     db_server['dir']))

logger.debug('Amex files transfer completed.')
