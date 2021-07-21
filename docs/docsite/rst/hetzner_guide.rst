.. _ansible_collections.community.dns.docsite.hetzner_guide:

Hetzner DNS Guide
=================

.. contents:: Contents
   :local:
   :depth: 2

The :ref:`community.dns collection <plugins_in_community.dns>` offers several modules for working with the `Hetzner DNS service <https://docs.hetzner.com/dns-console/dns/>`_.
The modules use the `JSON REST based API <https://dns.hetzner.com/api-docs/>`_.

The collection provides five modules for working with Hetzner DNS:

- :ref:`community.dns.hetzner_dns_record_info <ansible_collections.community.dns.hetzner_dns_record_info_module>`: retrieve information on DNS records
- :ref:`community.dns.hetzner_dns_record <ansible_collections.community.dns.hetzner_dns_record_module>`: create/update/delete single DNS records
- :ref:`community.dns.hetzner_dns_record_set <ansible_collections.community.dns.hetzner_dns_record_set_module>`: create/update/delete DNS record sets
- :ref:`community.dns.hetzner_dns_record_sets <ansible_collections.community.dns.hetzner_dns_record_sets_module>`: bulk synchronize DNS record sets
- :ref:`community.dns.hetzner_dns_zone_info <ansible_collections.community.dns.hetzner_dns_zone_info_module>`: retrieve zone information

Authentication
--------------

To use Hetzner's API, you need to create a API token. You can manage API tokens in the "API tokens" menu entry in your user menu in the `DNS Console <https://dns.hetzner.com/>`_. You must provide the token to the ``hetzner_token`` option of the modules, its alias ``api_token``, or pass it on in the ``HETZNER_DNS_TOKEN`` environment variable:

.. code-block:: yaml+jinja

  - community.dns.hetzner_dns_record:
      hetzner_token: '{{ token }}'
      ...

In the examples in this guide, we will leave the authentication options away. Please note that you can set them globally with ``module_defaults`` (see :ref:`module_defaults`) or with an environment variable for the user and machine where the modules are run on.

Working with DNS zones
----------------------

The :ref:`community.dns.hetzner_dns_zone_info module <ansible_collections.community.dns.hetzner_dns_zone_info_module>` allows to query information on a zone. The zone can be identified both by its name and by its ID (which is an integer):

.. code-block:: yaml+jinja

    - name: Query zone information by name
      community.dns.hetzner_dns_zone_info:
        zone_name: example.com
      register: result

    - name: Query zone information by ID
      community.dns.hetzner_dns_zone_info:
        zone_id: aBcDeFgHiJlMnOpQrStUvW
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

The :ref:`community.dns.hetzner_dns_record_info module <ansible_collections.community.dns.hetzner_dns_record_info_module>` allows to query DNS records from the API. It can be used to query a single record:

.. code-block:: yaml+jinja

    - name: Query single record
      community.dns.hetzner_dns_record_info:
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
      when: result.set

    - name: Show that record is not set
      ansible.builtin.debug:
        msg: There is no A record for www.example.com
      when: not result.set

In all examples in this section, you can replace ``zone_name=example.com`` by ``zone_id=aBcDeFgHiJlMnOpQrStUvW`` with the zone's ID string.

You can also query a list of all records for a record name or prefix:

.. code-block:: yaml+jinja

    - name: Query all records for www.example.com
      community.dns.hetzner_dns_record_info:
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

Finally you can query all records for a zone:

.. code-block:: yaml+jinja

    - name: Query all records for a zone
      community.dns.hetzner_dns_record_info:
        zone_name: example.com
        what: all_records
      register: result

    - name: Show all records for the example.com zone
      ansible.builtin.debug:
        msg: >
          {{ item.type }} record for {{ item.record }} with
          TTL {{ item.ttl }} has values {{ item.value | join(', ') }}
      loop: result.sets

Creating and updating DNS single records
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :ref:`community.dns.hetzner_dns_record module <ansible_collections.community.dns.hetzner_dns_record_module>` allows to set, update and remove single DNS records. Setting and updating can be done as follows. Records will be matched by record name and type, and the TTL value will be updated if necessary:

.. code-block:: yaml+jinja

    - name: Add an A record with value 1.1.1.1 for www.example.com, resp. make sure the TTL is 300
      community.dns.hetzner_dns_record:
        state: present
        zone_name: example.com
        type: A  # IPv4 addresses
        # Either specify a record name:
        record: www.example.com
        # Or a record prefix ('' is the zone itself):
        prefix: www
        value: 1.1.1.1
        ttl: 300

To delete records, simply use ``state=absent``. Records will be matched by record name and type, and the TTL will be ignored:

.. code-block:: yaml+jinja

    - name: Remove A values for www.example.com
      community.dns.hetzner_dns_record:
        state: absent
        zone_name: example.com
        type: A  # IPv4 addresses
        record: www.example.com
        value: 1.1.1.1

Records of the same type for the same record name with other values are ignored.

Creating and updating DNS record sets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :ref:`community.dns.hetzner_dns_record_set module <ansible_collections.community.dns.hetzner_dns_record_set_module>` allows to set, update and remove DNS record sets. Setting and updating can be done as follows:

.. code-block:: yaml+jinja

    - name: Make sure record is set to the given value
      community.dns.hetzner_dns_record_set:
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

If you want to assert that a record has a certain value, set ``on_existing=keep``. Using ``keep_and_warn`` instead will emit a warning if this happens, and ``keep_and_fail`` will make the module fail.

To delete values, you can either overwrite the values with value ``[]``, or use ``state=absent``:

.. code-block:: yaml+jinja

    - name: Remove A values for www.example.com
      community.dns.hetzner_dns_record_set:
        state: present
        zone_name: example.com
        type: A  # IPv4 addresses
        record: www.example.com
        value: []

    - name: Remove TXT values for www.example.com
      community.dns.hetzner_dns_record_set:
        zone_name: example.com
        type: TXT
        prefix: www
        state: absent

    - name: Remove specific AAAA values for www.example.com
      community.dns.hetzner_dns_record:
        zone_name: example.com
        type: AAAA  # IPv6 addresses
        prefix: www
        state: absent
        on_existing: keep_and_fail
        ttl: 300
        value:
          - '::1'

In the third example, ``on_existing=keep_and_fail`` is present and an explicit value and TTL are given. This makes the module remove the current value only if there's a AAAA record for ``www.example.com`` whose current value is ``::1`` and whose TTL is 300. If another value is set, the module will not make any change, but fail. This can be useful to not accidentally remove values you do not want to change. To issue a warning instead of failing, use ``on_existing=keep_and_warn``, and to simply not do a change without any indication of this situation, use ``on_existing=keep``.

Bulk synchronization of DNS record sets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to set/update multiple records at once, or even make sure that the precise set of records you are providing are present and nothing else, you can use the :ref:`community.dns.hetzner_dns_record_sets module <ansible_collections.community.dns.hetzner_dns_record_sets_module>`.

The following example shows up to set/update multiple records at once:

.. code-block:: yaml+jinja

    - name: Make sure that multiple records are present
      community.dns.hetzner_dns_record_sets:
        zone_name: example.com
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

The next example shows how to make sure that only the given records are available and all other records are deleted. Note that for the ``type=NS`` record we used ``ignore=true``, which allows us to skip the value. It tells the module that it should not touch the ``NS`` record for ``example.com``.

.. code-block:: yaml+jinja

    - name: Make sure that multiple records are present
      community.dns.hetzner_dns_record_sets:
        zone_name: example.com
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
