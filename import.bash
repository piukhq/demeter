#!/bin/bash
# this script is invoked with two arguments.
# the first argument is the provider name for the file being imported (usually 'visa' or 'mastercard')
# the second argument is the full path to the file to be imported
set -eu

# extract command line arguments
provider="$1"
file_path="$2"
file_name=$(basename "$file_path")

# archive server details
archive_dir="/data/demeter/archive/$provider"
archive_host="txmatch@172.26.126.22"
archive_port="2020"

# txmatching server details
db_host="txmatch@172.26.127.21"
db_port="2020"
db_import_dir="/tmp/import/payment/$provider"

echo "[$(date)] Archiving $file_name"
/usr/bin/rsync -e "ssh -p $archive_port" -a --progress "$file_path" "$archive_host:$archive_dir"

echo "[$(date)] Transferring $file_name to aphrodite"
/usr/bin/rsync -e "ssh -p $db_port" -a --progress --remove-source-files "$file_path" "$db_host:$db_import_dir"

echo "[$(date)] $1 file transferred."
echo ''
