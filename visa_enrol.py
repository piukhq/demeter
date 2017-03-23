#!/usr/bin/env python3
from sys import argv
import logging

from plumbum.cmd import lftp, rsync


logfile = '/var/log/demeter/visa-enrol.log'

_, file_path = argv

archive_server = {
    'host': 'txmatch@172.26.127.22',
    'port': '2020',
    'dir': '/data/demeter/archive/amex/',
}

logging.basicConfig(filename=logfile,
                    level=logging.DEBUG,
                    format='[%(asctime)s] %(levelname)s :: %(message)s')
logger = logging.getLogger('__name__')

logger.debug('Running visa enrolment file export process for file: {}.'.format(file_path))

logger.debug('Transferring file to visa...')
lftp('sftp://la.taqc:DUMMY_PASSWORD@198.241.159.22',
     '-e', '"set sftp:connect-program \'ssh -a -x -i /root/.ssh/id_rsa_visa\'; put {}; bye"'.format(file_path))

logger.debug('Archiving file...')
rsync('-e', 'ssh -p {}'.format(archive_server['port']),
      '-a',
      '--progress',
      '--remove-source-files',
      file_path,
      '{}:{}'.format(archive_server['host'],
                     archive_server['dir']))

logger.debug('Visa file transfer completed.')
