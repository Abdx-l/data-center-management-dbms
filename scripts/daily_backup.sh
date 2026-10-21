#!/bin/sh
set -eu
database=${1:?Usage: daily_backup.sh DATABASE BACKUP_DIRECTORY}
directory=${2:?Usage: daily_backup.sh DATABASE BACKUP_DIRECTORY}
mkdir -p "$directory"
day=$(date +%Y%m%d)
python3 "$(dirname "$0")/../dc.py" backup "$database" "$directory/datacenter-$day.db"
python3 "$(dirname "$0")/../dc.py" check "$directory/datacenter-$day.db"

