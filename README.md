# HTTP API for record CRUD operations in Voyager ILS
HTTP API for reading, creating and updating records in Voyager ILS. Use Oracle for reading records and bulkimport for writing.

## Installation
- The file index.cgi can be made available in `cgi-bin` directory with the configuration file, which must be named `voyager-crud-api-conf.json` (See `example-conf.json`)
- Copy bin/Pbulkimport3 to `/m1/voyager/<VOYAGER_INSTANCE>/sbin`
## Usage
### Read record
```sh
$ curl -H 'Accept: application/xml' 'https://foo.bar/voyager-crud-api?resource=bib&apiKey=foobar'
<?xml version="1.0" encoding="utf-8"?>
<record xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd">
    <leader>03357cam a22002894a 4500</leader>
    <controlfield tag="005">20110816200403.0</controlfield>
    <controlfield tag="008">071016s2007    fi ||||||m   |||||||fin||</controlfield>
    <datafield tag="245" ind1="1" ind2="0">
      <subfield code="a">FOOBAR</subfield>
    </datafield>
</record>
```
### Create a record
```sh
# The created record's id will be available in Record-ID response header
$ curl \
  -d@record.xml \
  -H 'Content-Type: application/xml' \
  'https://foo.bar/voyager-crud-api?resource=bib&apiKey=foobar'
```
### Update a record
```
$ curl \
  -d@record.xml \
  -H 'Content-Type: application/xml' \
  'https://foo.bar/voyager-crud-api?resource=bib&apiKey=foobar&id=12345'
```
## Development
Dockerfile is provided for basic testing (Bulkimport cannot be run outside of Voyager-servers of course):
```sh
$ docker build . -t voyager-crud-api-test
# This mounts index.cgi and conf.json in the testing image so that the code can be modified without restarting/building the the image
# HTTP server will be available in port 8080
$ ./run-test-instance.sh
```
## License and copyright

Copyright (c) 2019 **University Of Helsinki (The National Library Of Finland)**

This project's source code is licensed under the terms of **Apache License 2.0**.
