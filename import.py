#!/usr/bin/env python3
from sys import argv
import logging
import re
import os

from plumbum.cmd import rsync


logfile = '/var/log/demeter/import.log'
_, provider, file_path = argv
file_name = os.path.basename(file_path)

archive_server = {
    'host': 'txmatch@172.26.127.22',
    'port': '2020',
    'dir': '/data/demeter/archive/{}'.format(provider),
}

db_server = {
    'host': 'txmatch@172.26.127.21',
    'port': '2020',
    'dir': '/tmp/import/payment/{}'.format(provider),
}

import_file_name_patterns = {
    'visa': re.compile(r'^.*\.C2\.pgp$'),
    'mastercard': re.compile(r'^TTS44T0\..*\.001$'),
}


logger = logging.getLogger('__name__')
logger.basicConfig(filename=logfile,
                   level=logging.DEBUG,
                   format='[%(asctime)s] %(levelname)s :: %(message)s')

logger.debug('Running import process for {} file: {}.'.format(provider, file_path))

pattern = import_file_name_patterns[provider].match(file_name)
if not pattern:
    logger.debug('Skipping file name {} as it does not match the regex {}'.format(file_name, repr(pattern)))
    exit(0)

logger.debug('Archiving file...')
rsync('-e', 'ssh -p {}'.format(archive_server['port']),
      '-a',
      '--progress',
      file_path,
      '{}:{}'.format(archive_server['host'],
                     archive_server['dir']))

logger.debug('Transferring file to aphrodite...')
rsync('-e', 'ssh -p {}'.format(db_server['port']),
      '-a',
      '--progress',
      '--remove-source-files',
      file_path,
      '{}:{}'.format(db_server['host'],
                     db_server['dir']))

logger.debug('{} file transfer completed.'.format(provider))
