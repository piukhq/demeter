#!/bin/bash

set -eu

# intermediate directories
import_dir="/tmp/demeter/import"
archive_dir="/var/lib/demeter/archive"

# db server details
db_conn="txmatch@172.26.127.21"
db_port="2020"
db_import_dir="/tmp/import/payment"

# create the folders we're going to need
mkdir -p $import_dir

# if veft2016aP is logged in, we want to skip the visa files this time around.
set +e
username='veft2016aP'
ps ax | grep -v grep | grep "sshd: $username"
if [ $? != 0 ]; then
    # pull visa files
    echo "[`date`] Importing Visa files..."
    mkdir -p $import_dir/visa

    # this can fail if the glob doesn't match anything, so ignore failures (dangerous...) and move on
    /usr/bin/rsync --progress -a --remove-source-files /home/veft2016aP/*.C2.pgp /tmp/demeter/import/visa/
else
    echo "[`date`] $username is logged in, skipping Visa files..."
fi
set -e

# pull visa plaintext files
echo "[`date`] Importing Visa plaintext files..."
/usr/bin/rsync --remove-source-files --progress -a /var/lib/demeter/recovery/visa/ /tmp/demeter/import/visa/

# pull mastercard files
echo "[`date`] Importing Mastercard files..."
/usr/bin/rsync --remove-source-files --progress -a --exclude='.*' /home/mfesftp/ /tmp/demeter/import/mastercard/

# pull amex files
echo "[`date`] Importing Amex files..."
/usr/bin/lftp 'sftp://CHINGSPRD:taua@13@fsgateway.aexp.com' -e "mirror outbox $import_dir/amex; bye"

# pull amex recovery files
echo "[`date`] Importing Amex recovery files..."
/usr/bin/rsync --remove-source-files --progress -a /var/lib/demeter/recovery/amex/ /tmp/demeter/import/amex/

# push everything across to the DB server
echo "[`date`] Copying to Aphrodite..."
/usr/bin/rsync -r -e "ssh -p $db_port" --progress $import_dir/* $db_conn:$db_import_dir

# move everything into the archive directory
echo "[`date`] Archiving files..."
/usr/bin/rsync -a --progress --remove-source-files $import_dir $archive_dir

echo "[`date`] All done."
echo ''
