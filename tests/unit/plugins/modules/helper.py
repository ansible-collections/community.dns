# (c) 2021 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

try:
    import lxml.etree
except ImportError:
    # should be handled in module importing this one
    pass


DEFAULT_ENTRIES = [
    (125, 42, 'A', '', '1.2.3.4', 3600, None, None),
    (126, 42, 'A', '*', '1.2.3.5', 3600, None, None),
    (127, 42, 'AAAA', '', '2001:1:2::3', 3600, None, None),
    (128, 42, 'AAAA', '*', '2001:1:2::4', 3600, None, None),
    (129, 42, 'MX', '', 'example.com', 3600, None, '10'),
    (130, 42, 'NS', '', 'ns3.hostserv.eu', 10800, None, None),
    (131, 42, 'NS', '', 'ns2.hostserv.eu', 10800, None, None),
    (132, 42, 'NS', '', 'ns1.hostserv.eu', 10800, None, None),
]


def validate_wsdl_call(conditions):
    def predicate(content):
        assert content.startswith(b"<?xml version='1.0' encoding='utf-8'?>\n")

        root = lxml.etree.fromstring(content)
        header = None
        body = None

        for header_ in root.iter(lxml.etree.QName('http://schemas.xmlsoap.org/soap/envelope/', 'Header').text):
            header = header_
        for body_ in root.iter(lxml.etree.QName('http://schemas.xmlsoap.org/soap/envelope/', 'Body').text):
            body = body_

        for condition in conditions:
            if not condition(content, header, body):
                return False
        return True

    return predicate


def get_value(root, name):
    for auth in root.iter(name):
        return auth
    raise Exception('Cannot find child "{0}" in node {1}: {2}'.format(name, root, lxml.etree.tostring(root)))


def expect_authentication(username, password):
    def predicate(content, header, body):
        auth = get_value(header, lxml.etree.QName('auth', 'authenticate').text)
        assert get_value(auth, 'UserName').text == username
        assert get_value(auth, 'Password').text == password
        return True

    return predicate


def check_nil(node):
    nil_flag = node.get(lxml.etree.QName('http://www.w3.org/2001/XMLSchema-instance', 'nil'))
    if nil_flag != 'true':
        print(nil_flag)
    assert nil_flag == 'true'


def check_value(node, value, type=None):
    if type is not None:
        type_text = node.get(lxml.etree.QName('http://www.w3.org/2001/XMLSchema-instance', 'type'))
        assert type_text is not None, 'Cannot find type in {0}: {1}'.format(node, lxml.etree.tostring(node))
        i = type_text.find(':')
        if i < 0:
            ns = None
        else:
            ns = node.nsmap.get(type_text[:i])
            type_text = type_text[i + 1:]
        if ns != type[0] or type_text != type[1]:
            print(ns, type[0], type_text, type[1])
        assert ns == type[0] and type_text == type[1]
    if node.text != value:
        print(node.text, value)
    assert node.text == value


def find_map_entry(map_root, key_name, allow_non_existing=False):
    for map_entry in map_root.iter('item'):
        key = get_value(map_entry, 'key')
        value = get_value(map_entry, 'value')
        if key.text == key_name:
            check_value(key, key_name, type=('http://www.w3.org/2001/XMLSchema', 'string'))
            return value
    if allow_non_existing:
        return None
    raise Exception('Cannot find map entry with key "{0}" in node {1}: {2}'.format(key_name, map_root, lxml.etree.tostring(map_root)))


def expect_value(path, value, type=None):
    def predicate(content, header, body):
        node = body
        for entry in path:
            node = get_value(node, entry)
        check_value(node, value, type=type)
        return True

    return predicate


def add_answer_start_lines(lines):
    lines.extend([
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"'
        ' xmlns:ns1="https://ns1.hosttech.eu/public/api"'
        ' xmlns:xsd="http://www.w3.org/2001/XMLSchema"'
        ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        ' xmlns:ns2="http://xml.apache.org/xml-soap"'
        ' xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/"'
        ' SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">',
        '<SOAP-ENV:Header>',
        '<ns1:authenticateResponse>',
        '<return xsi:type="xsd:boolean">true</return>',
        '</ns1:authenticateResponse>',
        '</SOAP-ENV:Header>',
        '<SOAP-ENV:Body>',
    ])


def add_answer_end_lines(lines):
    lines.extend([
        '</SOAP-ENV:Body>',
        '</SOAP-ENV:Envelope>'
    ])


def add_dns_record_lines(lines, entry, tag_name):
    lines.extend([
        '<{tag_name} xsi:type="ns2:Map">'.format(tag_name=tag_name),
        '<item><key xsi:type="xsd:string">id</key><value xsi:type="xsd:int">{value}</value></item>'.format(value=entry[0]),
        '<item><key xsi:type="xsd:string">zone</key><value xsi:type="xsd:int">{value}</value></item>'.format(value=entry[1]),
        '<item><key xsi:type="xsd:string">type</key><value xsi:type="xsd:string">{value}</value></item>'.format(value=entry[2]),
        '<item><key xsi:type="xsd:string">prefix</key><value xsi:type="xsd:string">{value}</value></item>'.format(value=entry[3]),
        '<item><key xsi:type="xsd:string">target</key><value xsi:type="xsd:string">{value}</value></item>'.format(value=entry[4]),
        '<item><key xsi:type="xsd:string">ttl</key><value xsi:type="xsd:int">{value}</value></item>'.format(value=entry[5]),
    ])
    if entry[6] is None:
        lines.append('<item><key xsi:type="xsd:string">comment</key><value xsi:nil="true"/></item>')
    else:
        lines.append('<item><key xsi:type="xsd:string">comment</key><value xsi:type="xsd:string">{value}</value></item>'.format(value=entry[6]))
    if entry[7] is None:
        lines.append('<item><key xsi:type="xsd:string">priority</key><value xsi:nil="true"/></item>')
    else:
        lines.append('<item><key xsi:type="xsd:string">priority</key><value xsi:type="xsd:int">{value}</value></item>'.format(value=entry[7]))
    lines.append('</{tag_name}>'.format(tag_name=tag_name))


def create_zones_answer(zone_id, zone_name, entries):
    lines = []
    add_answer_start_lines(lines)
    lines.extend([
        '<ns1:getZoneResponse>',
        '<return xsi:type="ns2:Map">',
        '<item><key xsi:type="xsd:string">id</key><value xsi:type="xsd:int">{zone_id}</value></item>'.format(zone_id=zone_id),
        '<item><key xsi:type="xsd:string">user</key><value xsi:type="xsd:int">23</value></item>',
        '<item><key xsi:type="xsd:string">name</key><value xsi:type="xsd:string">{zone_name}</value></item>'.format(zone_name=zone_name),
        '<item><key xsi:type="xsd:string">email</key><value xsi:type="xsd:string">dns@hosttech.eu</value></item>',
        '<item><key xsi:type="xsd:string">ttl</key><value xsi:type="xsd:int">10800</value></item>',
        '<item><key xsi:type="xsd:string">nameserver</key><value xsi:type="xsd:string">ns1.hostserv.eu</value></item>',
        '<item><key xsi:type="xsd:string">serial</key><value xsi:type="xsd:string">12345</value></item>',
        '<item><key xsi:type="xsd:string">serialLastUpdate</key><value xsi:type="xsd:int">0</value></item>',
        '<item><key xsi:type="xsd:string">refresh</key><value xsi:type="xsd:int">7200</value></item>',
        '<item><key xsi:type="xsd:string">retry</key><value xsi:type="xsd:int">120</value></item>',
        '<item><key xsi:type="xsd:string">expire</key><value xsi:type="xsd:int">1234567</value></item>',
        '<item><key xsi:type="xsd:string">template</key><value xsi:nil="true"/></item>',
        '<item><key xsi:type="xsd:string">ns3</key><value xsi:type="xsd:int">1</value></item>',
    ])
    lines.append(
        '<item><key xsi:type="xsd:string">records</key><value SOAP-ENC:arrayType="ns2:Map[{count}]" xsi:type="SOAP-ENC:Array">'.format(
            count=len(entries)))
    for entry in entries:
        add_dns_record_lines(lines, entry, 'item')
    lines.extend([
        '</value>',
        '</item>',
        '</return>',
        '</ns1:getZoneResponse>',
    ])
    add_answer_end_lines(lines)
    return ''.join(lines)


DEFAULT_ZONE_RESULT = create_zones_answer(42, 'example.com', DEFAULT_ENTRIES)
