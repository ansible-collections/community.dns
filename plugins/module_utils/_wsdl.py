# Copyright (c) 2017-2020 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations

from ansible.module_utils.common.text.converters import to_native

try:
    import lxml.etree

    HAS_LXML_ETREE = True
except ImportError:
    HAS_LXML_ETREE = False

from ansible_collections.community.dns.plugins.module_utils._http import NetworkError


class WSDLException(Exception):
    pass


class WSDLNetworkError(WSDLException):
    pass


class WSDLError(WSDLException):
    def __init__(self, origin, error_code, message):
        super().__init__(f"{origin} ({error_code}): {message}")
        self.error_origin = origin
        self.error_code = error_code
        self.error_message = message


class WSDLCodingException(WSDLException):
    pass


def _split_text_namespace(node, text):
    i = text.find(":")
    if i < 0:
        return text, None
    ns = node.nsmap.get(text[:i])
    text = text[i + 1 :]
    return text, ns


_NAMESPACE_ENVELOPE = "http://schemas.xmlsoap.org/soap/envelope/"
_NAMESPACE_XSI = "http://www.w3.org/2001/XMLSchema-instance"
_NAMESPACE_XSD = "http://www.w3.org/2001/XMLSchema"
_NAMESPACE_XML_SOAP = "http://xml.apache.org/xml-soap"
_NAMESPACE_XML_SOAP_ENCODING = "http://schemas.xmlsoap.org/soap/encoding/"


def _set_type(node, type_value, namespace=None):
    if namespace is not None:
        type_value = lxml.etree.QName(namespace, type_value)
    node.set(lxml.etree.QName(_NAMESPACE_XSI, "type").text, type_value)


def encode_wsdl(node, value):
    if value is None:
        node.set(lxml.etree.QName(_NAMESPACE_XSI, "nil").text, "true")
    elif isinstance(value, str):
        _set_type(node, "xsd:string")
        node.text = value
    elif isinstance(value, int):
        _set_type(node, "xsd:int")
        node.text = str(value)
    elif isinstance(value, bool):
        _set_type(node, "xsd:boolean")
        node.text = "true" if value else "false"
    elif isinstance(value, dict):
        _set_type(node, "Map", _NAMESPACE_XML_SOAP)
        for key, val in sorted(value.items()):
            child = lxml.etree.Element("item")
            ke = lxml.etree.Element("key")
            encode_wsdl(ke, key)
            child.append(ke)
            ve = lxml.etree.Element("value")
            encode_wsdl(ve, val)
            child.append(ve)
            node.append(child)
    elif isinstance(value, list):
        _set_type(node, "SOAP-ENC:Array")
        for elt in value:
            child = lxml.etree.Element("item")
            encode_wsdl(child, elt)
            node.append(child)
    else:
        raise WSDLCodingException(f"Do not know how to encode {type(value)}!")


def _decode_wsdl_array(result, node, root_ns, ids):
    for item in node:
        if item.tag != "item":
            raise WSDLCodingException(f'Invalid child tag "{item.tag}" in map!')
        result.append(decode_wsdl(item, root_ns, ids))


def decode_wsdl(node, root_ns, ids):
    href = node.get("href")
    nil = node.get(lxml.etree.QName(_NAMESPACE_XSI, "nil"))
    nid = node.get("id")
    if href is not None:
        if not href.startswith("#"):
            raise WSDLCodingException(f'Global reference "{href}" not supported!')
        href = href[1:]
        if href not in ids:
            raise WSDLCodingException(f'ID "{href}" not yet defined!')
        result = ids[href]
    elif nil == "true":
        result = None
    else:
        type_with_ns = node.get(lxml.etree.QName(_NAMESPACE_XSI, "type"))
        if type_with_ns is None:
            raise WSDLCodingException(f'Element "{node}" has no "xsi:type" tag!')
        ntype, ns = _split_text_namespace(node, type_with_ns)
        if ns is None:
            raise WSDLCodingException(f'Cannot find namespace for "{type_with_ns}"!')
        if ns == _NAMESPACE_XSD:
            if ntype == "boolean":
                if node.text == "true":
                    result = True
                elif node.text == "false":
                    result = False
                else:
                    raise WSDLCodingException(
                        f'Invalid value for boolean: "{node.text}"'
                    )
            elif ntype == "int":
                result = int(node.text)
            elif ntype == "string":
                result = node.text
            else:
                raise WSDLCodingException(f'Unknown XSD type "{ntype}"!')
        elif ns == _NAMESPACE_XML_SOAP:
            if ntype == "Map":
                result = {}
                if nid is not None:
                    ids[nid] = result
                for item in node:
                    if item.tag != "item":
                        raise WSDLCodingException(
                            f'Invalid child tag "{item.tag}" in map!'
                        )
                    key = item.find("key")
                    if key is None:
                        raise WSDLCodingException(f'Cannot find key for "{item}"!')
                    key = decode_wsdl(key, root_ns, ids)
                    value = item.find("value")
                    if value is None:
                        raise WSDLCodingException(f'Cannot find value for "{item}"!')
                    value = decode_wsdl(value, root_ns, ids)
                    result[key] = value
                return result
            raise WSDLCodingException(f'Unknown XSD type "{ntype}"!')
        elif ns == _NAMESPACE_XML_SOAP_ENCODING:
            if ntype == "Array":
                result = []
                if nid is not None:
                    ids[nid] = result
                _decode_wsdl_array(result, node, root_ns, ids)
            else:
                raise WSDLCodingException(f'Unknown XSD type "{ntype}"!')
        elif ns == root_ns:
            array_type = node.get(
                lxml.etree.QName(_NAMESPACE_XML_SOAP_ENCODING, "arrayType")
            )
            if array_type is not None:
                result = []
                if nid is not None:
                    ids[nid] = result
                _decode_wsdl_array(result, node, root_ns, ids)
            else:
                result = {}
                if nid is not None:
                    ids[nid] = result
                for item in node:
                    result[item.tag] = decode_wsdl(item, root_ns, ids)
        else:
            raise WSDLCodingException(
                f'Unknown type namespace "{ns}" (with type "{ntype}")!'
            )
    if nid is not None:
        ids[nid] = result
    return result


class Parser:
    def _parse(self, result, node, where):
        for child in node:
            tag = lxml.etree.QName(child.tag)
            if tag.namespace != self._api:
                raise WSDLCodingException(
                    f'Cannot interpret {where} item of type "{tag}"!'
                )
            for res in child.iter("return"):
                result[tag.localname] = decode_wsdl(res, self._api, {})

    def __init__(self, api, root):
        self._main_ns = _NAMESPACE_ENVELOPE
        self._api = api
        self._root = root
        for fault in self._root.iter(lxml.etree.QName(self._main_ns, "Fault").text):
            fault_code = fault.find("faultcode")
            fault_code_val = None
            fault_string = fault.find("faultstring")
            origin = "server"
            if fault_code is not None and fault_code.text:
                code, code_ns = _split_text_namespace(fault, fault_code.text)
                fault_code_val = code
                if code_ns == self._main_ns:
                    origin = code.lower()
            if fault_string is not None and fault_string.text:
                raise WSDLError(origin, fault_code_val, fault_string.text)
            raise WSDLError(
                origin, fault_code_val, lxml.etree.tostring(fault).decode("utf-8")
            )
        self._header = {}
        self._body = {}
        for header in self._root.iter(lxml.etree.QName(self._main_ns, "Header").text):
            self._parse(self._header, header, "header")
        for body in self._root.iter(lxml.etree.QName(self._main_ns, "Body").text):
            self._parse(self._body, body, "body")

    def get_header(self, header):
        return self._header[header]

    def get_result(self, body):
        return self._body[body]

    def __str__(self):
        return f"header={self._header}, body={self._body}"

    def __repr__(self):
        return (
            """<?xml version='1.0' encoding='utf-8'?>"""
            + "\n"
            + lxml.etree.tostring(self._root, pretty_print=True).decode("utf-8")
        )


class Composer:
    @staticmethod
    def _create(tag, namespace=None, **kwarg):
        if namespace:
            return lxml.etree.Element(lxml.etree.QName(namespace, tag), **kwarg)
        return lxml.etree.Element(tag, **kwarg)

    def __str__(self):
        return (
            """<?xml version='1.0' encoding='utf-8'?>"""
            + "\n"
            + lxml.etree.tostring(self._root, pretty_print=True).decode("utf-8")
        )

    def _create_envelope(self, tag, **kwarg):
        return self._create(tag, self._main_ns, **kwarg)

    def __init__(self, http_helper, api, namespaces=None):
        self._http_helper = http_helper
        self._main_ns = _NAMESPACE_ENVELOPE
        self._api = api
        # Compose basic document
        all_namespaces = {
            "SOAP-ENV": _NAMESPACE_ENVELOPE,
            "xsd": _NAMESPACE_XSD,
            "xsi": _NAMESPACE_XSI,
            "ns2": "auth",
            "SOAP-ENC": _NAMESPACE_XML_SOAP_ENCODING,
        }
        if namespaces is not None:
            all_namespaces.update(namespaces)
        self._root = self._create_envelope("Envelope", nsmap=all_namespaces)
        self._root.set(
            lxml.etree.QName(self._main_ns, "encodingStyle").text,
            _NAMESPACE_XML_SOAP_ENCODING,
        )
        self._header = self._create_envelope("Header")
        self._root.append(self._header)
        self._body = self._create_envelope("Body")
        self._root.append(self._body)
        self._command = None

    def add_auth(self, username, password):
        auth = self._create("authenticate", "auth")
        user = self._create("UserName")
        user.text = username
        auth.append(user)
        pw = self._create("Password")
        pw.text = password
        auth.append(pw)
        self._header.append(auth)

    def add_simple_command(self, command, **args):
        self._command = command
        command = self._create(command, self._api)
        for arg, value in args.items():
            arg = self._create(arg)
            encode_wsdl(arg, value)
            command.append(arg)
        self._body.append(command)

    def execute(self, debug=False):
        payload = (
            b"""<?xml version='1.0' encoding='utf-8'?>"""
            + b"\n"
            + lxml.etree.tostring(self._root)
            + b"\n"
        )
        try:
            headers = {
                "Content-Type": "text/xml; charset=utf-8",
                "Content-Length": str(len(payload)),
            }
            if self._command:
                headers["SOAPAction"] = f'"{self._api}#{self._command}"'
            result, info = self._http_helper.fetch_url(
                self._api, data=payload, method="POST", timeout=300, headers=headers
            )
            code = info["status"]
        except NetworkError as e:
            raise WSDLNetworkError(to_native(e))
        # if debug:
        #     q.q('Result: {0}, content: {1}'.format(code, result.decode('utf-8')))
        if code < 200 or code >= 300:
            Parser(self._api, lxml.etree.fromstring(result))
            raise WSDLError(
                "server",
                "",
                f"Error {code} while executing WSDL command:\n{result.decode('utf-8')}",
            )
        return Parser(self._api, lxml.etree.fromstring(result))
