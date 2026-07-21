#!/bin/sh

for f in /var/www/html/index.php /var/www/html/login.php /var/www/html/search.php; do
  if [ -n "$FLAG" ] && [ -f "$f" ]; then
    sed -i "s/flag{testflag}/$FLAG/g" "$f"
  fi
done

exit 0
