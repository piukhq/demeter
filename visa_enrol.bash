#!/bin/bash
# this script is invoked with a single argument; the path of the file to be sent to visa.
set -eu

logfile=/var/log/demeter/visa_enrol.log

function log() {
    echo "$1" >> "$logfile"
}

file_path="$1"
file_name=$(basename "$file_path")

# archive server details
archive_dir="/data/demeter/archive/visa"
archive_host="txmatch@172.26.127.22"
archive_port="2020"

log "[$(date)] Archiving $file_name"
log $(/usr/bin/rsync -e "ssh -p $archive_port" -a --progress "$file_path" "$archive_host:$archive_dir")

log "[$(date)] Transferring $file_name to Visa"
log $(/usr/bin/lftp 'sftp://user:pass@visa.sftp.server' -e "put $file_path; bye")

log "[$(date)] $file_name transfer successful"
