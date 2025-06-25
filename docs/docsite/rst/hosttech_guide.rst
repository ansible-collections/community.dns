..
  Copyright (c) Ansible Project
  GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
  SPDX-License-Identifier: GPL-3.0-or-later

.. _ansible_collections.community.dns.docsite.hosttech_guide:

HostTech DNS Guide
==================

.. contents:: Contents
   :local:
   :depth: 2

The :anscollection:`community.dns collection <community.dns>` offers several modules for working with the `HostTech DNS service <https://www.hosttech.ch/>`_.
The modules support both the old `WSDL-based API <https://ns1.hosttech.eu/public/api?wsdl>`_ and the new `JSON REST based API <https://api.ns1.hosttech.eu/api/documentation/>`_.

The collection provides six modules for working with HostTech DNS:

- :ansplugin:`community.dns.hosttech_dns_record#module`: create/update/delete single DNS records
- :ansplugin:`community.dns.hosttech_dns_record_info#module`: retrieve information on DNS records
- :ansplugin:`community.dns.hosttech_dns_record_set#module`: create/update/delete DNS record sets
- :ansplugin:`community.dns.hosttech_dns_record_set_info#module`: retrieve information on DNS record sets
- :ansplugin:`community.dns.hosttech_dns_record_sets#module`: bulk synchronize DNS record sets
- :ansplugin:`community.dns.hosttech_dns_zone_info#module`: retrieve zone information

It also provides an inventory plugin:

- :ansplugin:`community.dns.hosttech_dns_records#inventory`: create inventory from DNS records

To find out which record types are supported and how to use them, look at :ref:`ansible_collections.community.dns.docsite.hosttech_guide.records`.

Authentication, Requirements and APIs
-------------------------------------

HostTech currently has two APIs for working with DNS records: the old WSDL-based API, and the new JSON-based REST API. We recommend using the new JSON REST API if possible.

JSON REST API
~~~~~~~~~~~~~

To use the JSON REST API, you need to create a API token. You can manage API tokens in the "DNS Editor" in the "API" section. You must provide the token to the :ansopt:`hosttech_token` option of the modules:

.. code-block:: yaml+jinja

  - community.dns.hosttech_dns_record:
      hosttech_token: '{{ token }}'
      # ...

In the examples in this guide, we will leave the authentication options away. Please note that you can set them globally with ``module_defaults`` (see :ref:`module_defaults`).

WSDL API
~~~~~~~~

To use the WSDL API, you need to set API credentials. These can be found and changed in the "Servercenter" and there in the "Solutions" section under settings for the "DNS Tool". The username is fixed, but the password can be changed. The credentials must be provided to the :ansopt:`hosttech_username` and :ansopt:`hosttech_password` options of the modules.

You also need to install the `lxml Python module <https://pypi.org/project/lxml/>`_ to work with the WSDL API. This can be done before using the modules:

.. code-block:: yaml+jinja

  - name: Make sure lxml is installed
    pip:
      name: lxml

  - community.dns.hosttech_dns_record:
      hosttech_username: '{{ username }}'
      hosttech_password: '{{ password }}'
      # ...

In the examples in this guide, we will leave the authentication options away. Please note that you can set them globally with ``module_defaults`` (see :ref:`module_defaults`).

Using the ``community.dns.hosttech`` module defaults group
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To avoid having to specify common parameters for all Hosttech DNS modules in every task, you can use the ``community.dns.hosttech`` module defaults group:

.. code-block:: yaml+jinja

    ---
    - name: Hosttech DNS
      hosts: localhost
      gather_facts: false
      module_defaults:
        group/community.dns.hosttech:
          hosttech_username: '{{ username }}'
          hosttech_password: '{{ password }}'
      tasks:
        - name: Query zone information
          community.dns.hosttech_dns_zone_info:
            zone_name: example.com
          register: result

        - name: Set A records for www.example.com
          community.dns.hosttech_dns_record_set:
            state: present
            zone_name: example.com
            type: A
            prefix: www
            value:
              - 192.168.0.1

Here all two tasks will use the options set for the module defaults group.

Working with DNS zones
----------------------

The :ansplugin:`community.dns.hosttech_dns_zone_info module <community.dns.hosttech_dns_zone_info#module>` allows to query information on a zone. The zone can be identified both by its name and by its ID (which is an integer):

.. code-block:: yaml+jinja

    - name: Query zone information by name
      community.dns.hosttech_dns_zone_info:
        zone_name: example.com
      register: result

    - name: Query zone information by ID
      community.dns.hosttech_dns_zone_info:
        zone_id: 42
      register: result

The module returns both the zone name and zone ID, so this module can be used to convert from zone ID to zone name and vice versa:

.. code-block:: yaml+jinja

    - ansible.builtin.debug:
        msg: |
            The zone ID: {{ result.zone_id }}
            The zone name: {{ result.zone_name }}

Working with DNS records
------------------------

.. note::

  By default, TXT record values returned and accepted by the modules and plugins in this collection are unquoted. This means that  you do not have to add double quotes (``"``), and escape double quotes (as ``\"``) and backslashes (as ``\\``). All modules and plugins which work with DNS records support the :ansopt:`community.dns.hosttech_dns_record_set#module:txt_transformation` option which allows to configure this behavior.

Querying DNS records and record sets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :ansplugin:`community.dns.hosttech_dns_record_set_info module <community.dns.hosttech_dns_record_set_info#module>` allows to query DNS record sets from the API. It can be used to query a single record set:

.. code-block:: yaml+jinja

    - name: Query single record
      community.dns.hosttech_dns_record_set_info:
        zone_name: example.com
        type: A  # IPv4 addresses
        what: single_record  # default value
        # Either specify a record name:
        record: www.example.com
        # Or a record prefix ('' is the zone itself):
        prefix: www
      register: result

    - name: Show IPv4 addresses if record exists
      ansible.builtin.debug:
        msg: >
          IPv4s are {{ result.set.value | join(', ') }},
          TTL is {{ result.set.ttl }}
      when: result.set is truthy

    - name: Show that record is not set
      ansible.builtin.debug:
        msg: There is no A record for www.example.com
      when: result.set is falsy

In all examples in this section, you can replace :ansopt:`community.dns.hosttech_dns_record_set_info#module:zone_name=example.com` by :ansopt:`community.dns.hosttech_dns_record_set_info#module:zone_id=42` with the zone's integer ID.

You can also query a list of all record sets for a record name or prefix:

.. code-block:: yaml+jinja

    - name: Query all records for www.example.com
      community.dns.hosttech_dns_record_set_info:
        zone_name: example.com
        what: all_types_for_record
        # Either specify a record name:
        record: www.example.com
        # Or a record prefix ('' is the zone itself):
        prefix: www
      register: result

    - name: Show all records for www.example.com
      ansible.builtin.debug:
        msg: >
          {{ item.type }} record with TTL {{ item.ttl }} has
          values {{ item.value | join(', ') }}
      loop: result.sets

Finally you can query all record sets for a zone:

.. code-block:: yaml+jinja

    - name: Query all records for a zone
      community.dns.hosttech_dns_record_set_info:
        zone_name: example.com
        what: all_records
      register: result

    - name: Show all records for the example.com zone
      ansible.builtin.debug:
        msg: >
          {{ item.type }} record for {{ item.record }} with
          TTL {{ item.ttl }} has values {{ item.value | join(', ') }}
      loop: result.sets

If you are interested in individual DNS records, and not record sets, you should use the :ansplugin:`community.dns.hosttech_dns_record_info module <community.dns.hosttech_dns_record_info#module>`. It supports the same limiting options as the :ansplugin:`community.dns.hosttech_dns_record_set_info module <community.dns.hosttech_dns_record_set_info#module>`.

Creating and updating DNS single records
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you do not want to add/remove values, but replace values, you will be interested in modifying a **record set** and not a single record. This is in particular important when working with ``CNAME`` and ``SOA`` records.

The :ansplugin:`community.dns.hosttech_dns_record module <community.dns.hosttech_dns_record#module>` allows to set, update and remove single DNS records. Setting and updating can be done as follows. Records will be matched by record name and type, and the TTL value will be updated if necessary:

.. code-block:: yaml+jinja

    - name: Add an A record with value 1.1.1.1 for www.example.com, resp. make sure the TTL is 300
      community.dns.hosttech_dns_record:
        state: present
        zone_name: example.com
        type: A  # IPv4 addresses
        # Either specify a record name:
        record: www.example.com
        # Or a record prefix ('' is the zone itself):
        prefix: www
        value: 1.1.1.1
        ttl: 300

To delete records, simply use :ansopt:`community.dns.hosttech_dns_record#module:state=absent`. Records will be matched by record name and type, and the TTL will be ignored:

.. code-block:: yaml+jinja

    - name: Remove A values for www.example.com
      community.dns.hosttech_dns_record:
        state: absent
        zone_name: example.com
        type: A  # IPv4 addresses
        record: www.example.com
        value: 1.1.1.1

Records of the same type for the same record name with other values are ignored.

Creating and updating DNS record sets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :ansplugin:`community.dns.hosttech_dns_record_set module <community.dns.hosttech_dns_record_set#module>` allows to set, update and remove DNS record sets. Setting and updating can be done as follows:

.. code-block:: yaml+jinja

    - name: Make sure record is set to the given value
      community.dns.hosttech_dns_record_set:
        state: present
        zone_name: example.com
        type: A  # IPv4 addresses
        # Either specify a record name:
        record: www.example.com
        # Or a record prefix ('' is the zone itself):
        prefix: www
        value:
          - 1.1.1.1
          - 8.8.8.8

If you want to assert that a record has a certain value, set :ansopt:`community.dns.hosttech_dns_record_set#module:on_existing=keep`. Using :ansval:`keep_and_warn` instead will emit a warning if this happens, and :ansval:`keep_and_fail` will make the module fail.

To delete values, you can either overwrite the values with value :ansval:`[]`, or use :ansopt:`community.dns.hosttech_dns_record_set#module:state=absent`:

.. code-block:: yaml+jinja

    - name: Remove A values for www.example.com
      community.dns.hosttech_dns_record_set:
        state: present
        zone_name: example.com
        type: A  # IPv4 addresses
        record: www.example.com
        value: []

    - name: Remove TXT values for www.example.com
      community.dns.hosttech_dns_record_set:
        zone_name: example.com
        type: TXT
        prefix: www
        state: absent

    - name: Remove specific AAAA values for www.example.com
      community.dns.hosttech_dns_record_set:
        zone_name: example.com
        type: AAAA  # IPv6 addresses
        prefix: www
        state: absent
        on_existing: keep_and_fail
        ttl: 300
        value:
          - '::1'

In the third example, :ansopt:`community.dns.hosttech_dns_record_set#module:on_existing=keep_and_fail` is present and an explicit value and TTL are given. This makes the module remove the current value only if there's a AAAA record for ``www.example.com`` whose current value is ``::1`` and whose TTL is 300. If another value is set, the module will not make any change, but fail. This can be useful to not accidentally remove values you do not want to change. To issue a warning instead of failing, use :ansopt:`community.dns.hosttech_dns_record_set#module:on_existing=keep_and_warn`, and to simply not do a change without any indication of this situation, use :ansopt:`community.dns.hosttech_dns_record_set#module:on_existing=keep`.

Bulk synchronization of DNS record sets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to set/update multiple records at once, or even make sure that the precise set of records you are providing are present and nothing else, you can use the :ansplugin:`community.dns.hosttech_dns_record_sets module <community.dns.hosttech_dns_record_sets#module>`.

The following example shows up to set/update multiple records at once:

.. code-block:: yaml+jinja

    - name: Make sure that multiple records are present
      community.dns.hosttech_dns_record_sets:
        zone_name: example.com
        record_sets:
          - prefix: www
            type: A
            value:
              - 1.1.1.1
              - 8.8.8.8
          - prefix: www
            type: AAAA
            value:
              - '::1'

The next example shows how to make sure that only the given records are available and all other records are deleted. Note that for the :ansopt:`community.dns.hosttech_dns_record_sets#module:record_sets[].type=NS` record we used :ansopt:`community.dns.hosttech_dns_record_sets#module:record_sets[].ignore=true`, which allows us to skip the value. It tells the module that it should not touch the ``NS`` record for ``example.com``.

.. code-block:: yaml+jinja

    - name: Make sure that multiple records are present
      community.dns.hosttech_dns_record_sets:
        zone_name: example.com
        prune: true
        record_sets:
          - prefix: www
            type: A
            value:
              - 1.1.1.1
              - 8.8.8.8
          - prefix: www
            type: AAAA
            value:
              - '::1'
          - prefix: ''
            type: NS
            ignore: true

.. _ansible_collections.community.dns.docsite.hosttech_guide.records:

Supported DNS records
---------------------

Here you can find a list of supported DNS records together with their syntax for the :ansopt:`value` field:

- **A** records: IPv4 address.

  Simply provide the IPv4 address as :ansopt:`value`, such as ``127.0.0.1``.
- **AAAA** records: IPv6 address.

  Simply provide the IPv6 address as :ansopt:`value`, such as ``3fff::1:2``.
- **CAA** records: Certification Authority Authorization

  The record's :ansopt:`value` is of the form ``<flags> <tag> <value>``,
  where ``<flags>`` is an unsigned integer between 0 and 255;
  ``<tag>`` is a ASCII string such as ``issue``, ``issuewild``, or ``iodef``;
  and ``<value>`` is the value enclosed in double quotes.
  An example entry is ``0 issue "letsencrypt.org"``.
  The exact syntax is explained in L(Section 4.1.1 of RFC 8659, https://datatracker.ietf.org/doc/html/rfc8659#name-syntax).
- **CNAME** records: Canonical Name.
- **MX** records: Mail Exchange.

  The record's :ansopt:`value` is of the form ``<priority> <hostname>``,
  where ``<priority>`` is an unsigned integer and ``<hostname>`` a DNS hostname.
- **NS** records: Name Server record.

  The record's :ansopt:`value` is the list of DNS names of the authoritative nameservers for this zone.
- **PTR** records: Pointer to a canonical name.

  The record's :ansopt:`value` is of the form ``<origin> <ptr-name>``.
- **SPF** records: Sender Policy Framework.

  This kind of DNS record is deprecated, TXT records should be used instead for SPF policies.
- **SRV** records: Service locator.

  The record's :ansopt:`value` is of the form ``<priority> <weight> <port> <target>``.
- **TXT** records: Text record.

  The value is simply a free form text. Its use depends on its context.
