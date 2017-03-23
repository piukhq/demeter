#!/usr/bin/env python3
from sys import argv
import logging
import re
import os

from plumbum.cmd import lftp, rsync


logfile = '/var/log/demeter/enrolment.log'

_, file_path = argv
file_name = os.path.basename(file_path)

archive_server = {
    'host': 'txmatch@172.26.127.22',
    'port': '2020',
    'dir': '/data/demeter/archive/visa/',
}

enrolment_file_name_pattern = re.compile('LOYANG_REG_PAN_\d+\.gpg')

logging.basicConfig(filename=logfile,
                    level=logging.DEBUG,
                    format='[%(asctime)s] %(levelname)s :: %(message)s')
logger = logging.getLogger('__name__')

logger.debug('Running visa enrolment file export process for file: {}.'.format(file_path))

if not enrolment_file_name_pattern.match(file_name):
    logger.debug('Skipping file name {} as it does not match the regex {}'.format(
        file_name, enrolment_file_name_pattern.pattern))
    exit(0)

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
