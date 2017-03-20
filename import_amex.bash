#!/bin/bash
set -eu

import_dir="/tmp/demeter/amex"

recovery_dir="/data/demeter/recovery/amex/"

# archive server details
archive_dir="/data/demeter/archive/amex"
archive_host="txmatch@172.26.126.22"
archive_port="2020"

# txmatching server details
db_import_dir="/tmp/import/payment/amex"
db_host="txmatch@172.26.127.21"
db_port="2020"

# create the folders we're going to need
mkdir -p $import_dir

echo "[$(date)] Importing Amex files..."
/usr/bin/lftp 'sftp://CHINGSPRD:taua@13@fsgateway.aexp.com' -e "mirror --include-glob=AXP_CHINGS_TLOG_* outbox $import_dir; bye"

echo "[$(date)] Importing Amex recovery files..."
/usr/bin/rsync -a --progress "$recovery_dir" "$import_dir"

echo "[$(date)] Archiving files..."
/usr/bin/rsync -e "ssh -p $archive_port" -a --progress "$import_dir" "$archive_host:$archive_dir"

echo "[$(date)] Transferring to aphrodite..."
/usr/bin/rsync -r -e "ssh -p $db_port" -a --progress --remove-source-files "$import_dir/*" "$db_host:$db_import_dir"

echo "[$(date)] Amex files transferred."
echo ''
