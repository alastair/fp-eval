#!/bin/bash

HOST=132.206.14.136
PASS=fsud987ydIHJf8K09fIDW2flfdJ
USER=fp
DATABASE=fpeval

DATE=`date "+%Y-%m-%d:%H:%M"`

/usr/local/bin/mysqldump -h$HOST -u$USER -p$PASS $DATABASE > backups/fpeval-backup-$DATE
