FROM ctftraining/base_image_nginx_mysql_php_56

COPY index.html /var/www/html/index.html
COPY index.php /var/www/html/index.php
COPY flag.sh /var/www/html/flag.sh

RUN mv /var/www/html/flag.sh /flag.sh \
    && sed -i 's/\r$//' /flag.sh \
    && chmod +x /flag.sh

EXPOSE 80

ENTRYPOINT ["/bin/sh", "-c", "/flag.sh && php-fpm & exec nginx"]
