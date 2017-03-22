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

# lftp requires that you provide a password even if it's not going to be used.
# it checks password first, ssh agent second.
log "[$(date)] Transferring $file_name to Visa"
log $(/usr/bin/lftp 'sftp://la.taqc:DUMMY_PASSWORD@198.241.159.22' -e "set sftp:connect-program 'ssh -a -x -i /root/.ssh/id_rsa_visa'; put $file_path; bye")

log "[$(date)] $file_name transfer successful"
