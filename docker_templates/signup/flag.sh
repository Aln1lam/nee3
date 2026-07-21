#!/bin/sh

TARGET_HTML=/var/www/html/index.html
TARGET_PHP=/var/www/html/index.php

if [ -n "$FLAG" ]; then
  if [ -f "$TARGET_HTML" ]; then
    sed -i "s/flag{testflag}/$FLAG/g" "$TARGET_HTML"
  fi

  if [ -f "$TARGET_PHP" ]; then
    sed -i "s/flag{testflag}/$FLAG/g" "$TARGET_PHP"
  fi
fi

exit 0
