======================================
Community DNS Collection Release Notes
======================================

.. contents:: Topics

v1.2.3
======

Release Summary
---------------

End of Life release.

The 1.x.y release train of the community.dns collection is now End of Life.
There will be no more 1.x.y releases. Please upgrade to community.dns 2.x.y.
Thanks to all contributors to the 1.x.y releases!

v1.2.2
======

Release Summary
---------------

Bugfix release.

Bugfixes
--------

- Update Public Suffix List.
- wait_for_txt - do not fail if ``NXDOMAIN`` result is returned. Also do not succeed if no nameserver can be found (https://github.com/ansible-collections/community.dns/issues/81, https://github.com/ansible-collections/community.dns/pull/82).

v1.2.1
======

Release Summary
---------------

Bugfix maintenance release.

Bugfixes
--------

- Update Public Suffix List.
- wait_for_txt - fix handling of too long TXT values (https://github.com/ansible-collections/community.dns/pull/65).
- wait_for_txt - resolving nameservers sometimes resulted in an empty list, yielding wrong results (https://github.com/ansible-collections/community.dns/pull/64).

v1.2.0
======

Release Summary
---------------

Last minor 1.x.0 version. The 2.0.0 version will have some backwards incompatible changes to the ``hosttech_dns_record`` and ``hosttech_dns_records`` modules which will require user intervention. These changes should result in a better UX.

Minor Changes
-------------

- hosttech modules - add ``api_token`` alias for ``hosttech_token`` (https://github.com/ansible-collections/community.dns/pull/26).
- hosttech_dns_record - in ``diff`` mode, also return ``diff`` data structure when ``changed`` is ``false`` (https://github.com/ansible-collections/community.dns/pull/28).
- module utils - add default implementation for some zone/record API functions, and move common JSON API code to helper class (https://github.com/ansible-collections/community.dns/pull/26).

Bugfixes
--------

- Update Public Suffix List.
- hosttech_dns_record - correctly handle quoting in CAA records for JSON API (https://github.com/ansible-collections/community.dns/pull/30).

v1.1.0
======

Release Summary
---------------

Regular maintenance release.

Minor Changes
-------------

- Avoid internal ansible-core module_utils in favor of equivalent public API available since at least Ansible 2.9 (https://github.com/ansible-collections/community.dns/pull/24).

Bugfixes
--------

- Update Public Suffix List.

v1.0.1
======

Release Summary
---------------

Regular maintenance release.

Bugfixes
--------

- Update Public Suffix List.

v1.0.0
======

Release Summary
---------------

First stable release.

Bugfixes
--------

- Update Public Suffix List.

v0.3.0
======

Release Summary
---------------

Fixes bugs, adds rate limiting for Hosttech JSON API, and adds a new bulk synchronization module.

Minor Changes
-------------

- hosttech_dns_* - handle ``419 Too Many Requests`` with proper rate limiting for JSON API (https://github.com/ansible-collections/community.dns/pull/14).

Bugfixes
--------

- Avoid converting ASCII labels which contain underscores or other printable ASCII characters outside ``[a-zA-Z0-9-]`` to alabels during normalization (https://github.com/ansible-collections/community.dns/pull/13).
- Updated Public Suffix List.

New Modules
-----------

- community.dns.hosttech_dns_records - Bulk synchronize DNS records in Hosttech DNS service

v0.2.0
======

Release Summary
---------------

Major refactoring release, which adds a zone information module and supports HostTech's new REST API.

Major Changes
-------------

- hosttech_* modules - support the new JSON API at https://api.ns1.hosttech.eu/api/documentation/ (https://github.com/ansible-collections/community.dns/pull/4).

Minor Changes
-------------

- hosttech_dns_record* modules - allow to specify ``prefix`` instead of ``record`` (https://github.com/ansible-collections/community.dns/pull/8).
- hosttech_dns_record* modules - allow to specify zone by ID with the ``zone_id`` parameter, alternatively to the ``zone`` parameter (https://github.com/ansible-collections/community.dns/pull/7).
- hosttech_dns_record* modules - return ``zone_id`` on success (https://github.com/ansible-collections/community.dns/pull/7).
- hosttech_dns_record* modules - support IDN domain names and prefixes (https://github.com/ansible-collections/community.dns/pull/9).
- hosttech_dns_record_info - also return ``prefix`` for a record set (https://github.com/ansible-collections/community.dns/pull/8).
- hosttech_record - allow to delete records without querying their content first by specifying ``overwrite=true`` (https://github.com/ansible-collections/community.dns/pull/4).

Breaking Changes / Porting Guide
--------------------------------

- hosttech_* module_utils - completely rewrite and refactor to support new JSON API and allow to re-use provider-independent module logic (https://github.com/ansible-collections/community.dns/pull/4).

Bugfixes
--------

- Update Public Suffix List.
- hosttech_record - fix diff mode for ``state=absent`` (https://github.com/ansible-collections/community.dns/pull/4).
- hosttech_record_info - fix authentication error handling (https://github.com/ansible-collections/community.dns/pull/4).

New Modules
-----------

- community.dns.hosttech_dns_zone_info - Retrieve zone information in Hosttech DNS service

v0.1.0
======

Release Summary
---------------

Initial public release.

New Plugins
-----------

Filter
~~~~~~

- community.dns.get_public_suffix - Returns the public suffix of a DNS name
- community.dns.get_registrable_domain - Returns the registrable domain name of a DNS name
- community.dns.remove_public_suffix - Removes the public suffix from a DNS name
- community.dns.remove_registrable_domain - Removes the registrable domain name from a DNS name

New Modules
-----------

- community.dns.hosttech_dns_record - Add or delete entries in Hosttech DNS service
- community.dns.hosttech_dns_record_info - Retrieve entries in Hosttech DNS service
- community.dns.wait_for_txt - Wait for TXT entries to be available on all authoritative nameservers
