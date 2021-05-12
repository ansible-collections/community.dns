.. _ansible_collections.community.dns.docsite.hosttech_guide:

HostTech DNS Guide
==================

The :ref:`community.dns collection <plugins_in_community.dns>` offers several modules for working with the `HostTech DNS service <https://www.hosttech.ch/>`_.
The modules support both the old `WSDL-based API <https://ns1.hosttech.eu/public/api?wsdl>`_ and the new `JSON REST based API <https://api.ns1.hosttech.eu/api/documentation/>`_.

The collection provides four modules for working with HostTech DNS:

- ``community.dns.hosttech_dns_record``: create/update/delete DNS records
- ``community.dns.hosttech_dns_record_info``: retrieve information on DNS records
- ``community.dns.hosttech_dns_records``: bulk synchronize DNS records
- ``community.dns.hosttech_dns_zone_info``: retrieve zone information

Authentication, Requirements and APIs
-------------------------------------

HostTech currently has two APIs for working with DNS records: the old WSDL-based API, and the new JSON-based REST API. We recommend using the new REST API if possible.

JSON REST API
~~~~~~~~~~~~~

To use the JSON REST API, you need to create a API token. You can manage API tokens in the "DNS Editor" in the "API" section. You must provide the token to the ``hosttech_token`` option of the modules:

.. code-block:: yaml+jinja

  - community.dns.hosttech_dns_record:
      hosttech_token: '{{ token }}'
      ...

In the examples in this guide, we will leave the authentication options away. Please note that you can set them globally with ``module_defaults`` (see :ref:`module_defaults`).

WSDL API
~~~~~~~~

To use the WSDL API, you need to set API credentials. These can be found and changed in the "Servercenter" and there in the "Solutions" section under settings for the "DNS Tool". The username is fixed, but the password can be changed. The credentials must be provided to the ``hosttech_username`` and ``hosttech_password`` options of the modules.

You also need to install the `lxml Python module <https://pypi.org/project/lxml/>`_ to work with the WSDL API. This can be done before using the modules:

.. code-block:: yaml+jinja

  - name: Make sure lxml is installed
    pip:
      name: lxml

  - community.dns.hosttech_dns_record:
      hosttech_username: '{{ username }}'
      hosttech_password: '{{ password }}'
      ...

In the examples in this guide, we will leave the authentication options away. Please note that you can set them globally with ``module_defaults`` (see :ref:`module_defaults`).

Working with DNS zones
----------------------

The ``community.dns.hosttech_dns_zone_info`` module allows to query information on a zone. The zone can be identified both by its name and by its ID (which is an integer):

.. code-block:: yaml+jinja

    - name: Query zone information by name
      community.dns.hosttech_dns_zone_info:
        zone: example.com
      register: result

    - name: Query zone information by name
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

Querying DNS records
~~~~~~~~~~~~~~~~~~~~

The ``community.dns.hosttech_dns_record_info`` module allows to query DNS records from the API. It can be used to query a single record:

.. code-block:: yaml+jinja

    - name: Query single record
      community.dns.hosttech_dns_record_info:
        zone: example.com
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
      when: result.set

    - name: Show that record is not set
      ansible.builtin.debug:
        msg: There is no A record for www.example.com
      when: not result.set

In all examples in this section, you can replace ``zone: example.com`` by ``zone_id: 42`` with the zone's integer ID.

You can also query a list of all records for a record name or prefix:

.. code-block:: yaml+jinja

    - name: Query all records for www.example.com
      community.dns.hosttech_dns_record_info:
        zone: example.com
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

Finally you can query all records for a zone:

.. code-block:: yaml+jinja

    - name: Query all records for a zone
      community.dns.hosttech_dns_record_info:
        zone: example.com
        what: all_records
      register: result

    - name: Show all records for the example.com zone
      ansible.builtin.debug:
        msg: >
          {{ item.type }} record for {{ item.record }} with
          TTL {{ item.ttl }} has values {{ item.value | join(', ') }}
      loop: result.sets

Creating and updating DNS records
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``community.dns.hosttech_dns_record`` module allows to set, update and remove DNS records. Setting and updating can be done as follows:

.. code-block:: yaml+jinja

    - name: Make sure record is set to the given value
      community.dns.hosttech_dns_record:
        zone: example.com
        type: A  # IPv4 addresses
        # Either specify a record name:
        record: www.example.com
        # Or a record prefix ('' is the zone itself):
        prefix: www
        # The following makes sure that existing values
        # (that differ form the one given) are updated:
        overwrite: true
        value:
          - 1.1.1.1
          - 8.8.8.8

If you want to assert that a record has a certain value (and fail if it has a different value), leave away the ``overwrite: true``.

To delete values, you can either overwrite the values with value ``[]``, or use ``state: absent``:

.. code-block:: yaml+jinja

    - name: Remove A values for www.example.com
      community.dns.hosttech_dns_record:
        zone: example.com
        type: A  # IPv4 addresses
        record: www.example.com
        overwrite: true
        value: []

    - name: Remove specific AAAA values for www.example.com
      community.dns.hosttech_dns_record:
        zone: example.com
        type: AAAA  # IPv6 addresses
        prefix: www
        state: absent
        ttl: 300
        value:
          - '::1'

In the second example, ``overwrite: true`` is not present, but an explicit value and TTL are given. This makes the module remove the current value only if there's a AAAA record for ``www.example.com`` whose current value is ``::1`` and whose TTL is 300. If another value is set, the module will not make any change. This can be useful to not accidentally remove values you do not want to change.

Bulk synchronization of DNS records
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to set/update multiple records at once, or even make sure that the precise set of records you are providing are present and nothing else, you can use the ``community.dns.hosttech_dns_records`` module.

The following example shows up to set/update multiple records at once:

.. code-block:: yaml+jinja

    - name: Make sure that multiple records are present
      community.dns.hosttech_dns_records:
        zone: example.com
        records:
          - prefix: www
            type: A
            value:
              - 1.1.1.1
              - 8.8.8.8
          - prefix: www
            type: AAAA
            value:
              - '::1'

The next example shows how to make sure that only the given records are available and all other records are deleted. Note that for the ``type: NS`` record we used ``ignore: true``, which allows us to skip the value. It tells the module that it should not touch the ``NS`` record for ``example.com``.

.. code-block:: yaml+jinja

    - name: Make sure that multiple records are present
      community.dns.hosttech_dns_records:
        zone: example.com
        prune: true
        records:
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
