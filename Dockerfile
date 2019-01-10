FROM httpd:alpine
ENTRYPOINT ["/entrypoint.sh"]
CMD ["httpd-foreground"]

COPY entrypoint.sh /

RUN apk add -U --no-cache python2 py2-pip \
&& apk add --no-cache --virtual .build-deps build-base python2-dev \
&& sh -c 'pip install cx_Oracle pymarc' \
&& apk --no-cache del .build-deps \
&& rm -rf /tmp/* /var/tmp/*