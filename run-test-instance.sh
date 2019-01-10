#!/bin/sh
docker run \
  --rm \
  -v $PWD/conf.json:/usr/local/apache2/cgi-bin/voyager-crud-api-conf.json:ro \
  -v $PWD/index.cgi:/usr/local/apache2/cgi-bin/voyager-crud-api.cgi:ro \
  -p 8080:80 \
  --name vger-test \
  voyager-crud-api-test