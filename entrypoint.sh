#!/bin/sh
echo 'LoadModule cgi_module modules/mod_cgi.so' >> conf/httpd.conf
echo 'LoadModule rewrite_module modules/mod_rewrite.so' >> conf/httpd.conf
exec "$@"