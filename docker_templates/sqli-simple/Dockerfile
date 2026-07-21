FROM ctftraining/base_image_nginx_mysql_php_56

COPY setup.sh /setup.sh
COPY start.sh /start.sh
COPY init.sql /init.sql
COPY index.php /var/www/html/index.php
COPY login.php /var/www/html/login.php
COPY search.php /var/www/html/search.php
COPY flag.sh /var/www/html/flag.sh

RUN mv /var/www/html/flag.sh /flag.sh \
    && sed -i 's/\r$//' /flag.sh /setup.sh /start.sh \
    && chmod +x /flag.sh /setup.sh /start.sh

EXPOSE 80

ENTRYPOINT ["/start.sh"]
