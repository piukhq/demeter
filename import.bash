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

# pull visa files
echo "Importing Visa files..."
mkdir -p $import_dir/visa
sudo /bin/bash -c '/usr/bin/rsync --progress -a --remove-source-files /home/veft2016aP/*.pgp /tmp/demeter/import/visa/'

# pull mastercard files
echo "Importing Mastercard files..."
/usr/bin/rsync --remove-source-files --progress -a --exclude='.*' /home/mfesftp/ /tmp/demeter/import/mastercard

# pull amex files
echo "Importing Amex files..."
/usr/bin/lftp 'sftp://CHINGSPRD:taua@13@fsgateway.aexp.com' -e "mirror outbox $import_dir/amex; bye"

# push everything across to the DB server
echo "Copying to Aphrodite..."
rsync -r -e "ssh -p $db_port" --progress $import_dir/* $db_conn:$db_import_dir

# move everything into the archive directory
echo "Archiving files..."
rsync -a --progress --remove-source-files $import_dir $archive_dir

echo "All done."
