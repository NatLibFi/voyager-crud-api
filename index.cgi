#!/usr/bin/env python
# -*- coding: utf8 -*-
'''
Copyright 2018 University Of Helsinki (The National Library Of Finland)
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import cgi
import os
import sys
import json
import re
import subprocess
import cx_Oracle
from pymarc import marcxml
from pymarc.record import Record
from datetime import date
from uuid import uuid4
from base64 import b64decode

CONF_FILE = 'voyager-crud-api-conf.json'

def main():
  conf = parse_conf()
  params = parse_query_params()

  validate_api_key(conf, params)
  validate_resource(params)

  if os.getenv('REQUEST_METHOD') == 'POST':
    validate_content_type()    
    process_write(conf, params)
  elif os.getenv('REQUEST_METHOD') == 'GET':
    validate_accept()
    process_read(conf, params)
  else:
    error(405)

def parse_conf():
  data = open(CONF_FILE).read()
  return json.loads(data)

def parse_query_params():
  params = {}

  if os.getenv('QUERY_STRING'):
    str = os.getenv('QUERY_STRING').split('?')[0]

    for param in str.split('&'):
      [key, value] = param.split('=')
      params[key] = value

  return params

def validate_api_key(conf, params):
  if ('apiKey' not in params or params['apiKey'] not in conf['apiKeys']):
    error(401)

def validate_resource(params):
  if 'resource' not in params:
    error(400, 'Parameter \'resource\' is missing')
  elif params['resource'] != 'bib' and params['resource'] != 'auth':
    error(404)

def validate_content_type():
  if 'CONTENT_TYPE' not in os.environ or os.getenv('CONTENT_TYPE') != 'application/xml':
    error(415)

def validate_accept():
  if 'HTTP_ACCEPT' in os.environ:
    accept = os.getenv('HTTP_ACCEPT')
    if accept != 'application/xml' and accept != '*/*':
      error(406)

def process_read(conf, params):
  if 'id' not in params:
    error(400, 'Parameter \'id\' missing')

  resource = params['resource'].upper()
  dsn = cx_Oracle.makedsn(conf['db']['host'], conf['db']['port'], sid=conf['db']['sid'])
  db = cx_Oracle.connect(user=conf['db']['user'], password=conf['db']['password'], dsn=dsn)

  cursor = db.cursor()
  cursor.execute('SELECT utl_raw.CAST_TO_RAW(RECORD_SEGMENT) as SEG FROM {0}_DATA WHERE {0}_ID = {1} ORDER BY SEQNUM'.format(resource, params['id']))

  data = reduce(lambda memo, v: memo+v[0], cursor.fetchall(), '')

  if len(data) is 0:
    error(404)

  record = Record(data)
  xml_str = marcxml.record_to_xml(record, namespace=True)
  
  print 'Status: 200'
  print 'Content-Type: application/xml'
  print
  print '<?xml version="1.0" encoding="UTF-8"?>{}'.format(xml_str)

def process_write(conf, params):
  record = marcxml.parse_xml_to_array(sys.stdin)[0]
  import_codes = conf['importCodes'][params['resource']]

  try:
    if 'update' in params and params['update'] == '1':
      output = run_bulkimport(conf['instance'], import_codes['update'], conf['operator'], record.as_marc21())
      parse_bulkimport_log(conf, output)
      
      print 'Status: 204'
      print
    else:
      output = run_bulkimport(conf['instance'], import_codes['create'], conf['operator'], record.as_marc21())
      id = parse_bulkimport_log(conf, output)
    
      print 'Status: 201'
      print 'Record-ID: {}'.format(id)
      print
  except Exception as e:
    write_log('Failed running bulkimport: {}'.format(e))
    error(500)

def write_log(msg):
  sys.stderr.write(msg+'\n')

def error(code, msg=None):
  print 'Status: {}'.format(str(code))

  if msg:
    print 'Content-Type: application/xml'
    print
    print '<?xml version="1.0" encoding="UTF-8"?><error>{}</error>'.format(msg)
  else:
    print

  sys.exit()

def run_bulkimport(db, import_code, operator, payload):
  input_file = '/tmp/{}'.format(str(uuid4()).replace('-', ''))
  args = [
    '/m1/voyager/{}/sbin/Pbulkimport3'.format(db),
    '-reportsdir',
    '/m1/voyager/{}/rpt'.format(db),
    '-envfile',
    '/m1/voyager/{}/ini/voyager.env'.format(db),
    '-f', input_file,
    '-i{}'.format(import_code),
    '-o{}'.format(operator),
    '-K', 'ADDKEY',
    '-M']

  f = open(input_file, 'w')
  f.write(payload)
  f.close()

  p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

  (stdout, stderr) = p.communicate()

  os.unlink(input_file)

  if p.returncode is not 0:
    raise Exception(stderr)

  return stdout

def parse_bulkimport_log(conf, data):
  dir = '/m1/voyager/{}/rpt'.format(conf['instance'])
  pid = re.search('Bulkimport Process id: ([0-9]+)', data, re.M).group(1)
  date_str = date.today().strftime('%Y%m%d')
  pattern = re.compile('log.imp.{}.[0-9]{{4}}.{}$'.format(date_str, pid))

  for filename in os.listdir(dir):   
    if pattern.match(filename):
      f = open(os.path.join(dir, filename))
      log = f.read()      
      f.close()

      if re.search('Added:         1', log):
        m = re.search('Adding Bib record ([0-9]+)', log)
	if m:
          return m.group(1)
        else:
          raise Exception(log)
      elif re.search('Replaced:      1', log):
        return
      else:
        raise Exception(log)

if __name__ == '__main__':
  main()

