import sys
from pymarc import marcxml, record

data = sys.stdin
#record = record.Record(data)
#print record.title()
#print marcxml.record_to_xml(data)
record = marcxml.parse_xml_to_array(data)[0]
#record = marcxml.parse_xml_to_array(data)[0]
print marcxml.record_to_xml(record)