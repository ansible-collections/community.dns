.. _ansible_collections.community.dns.docsite.filter_guide:

Community.Dns Filter Guide
==========================

.. contents:: Contents
   :local:
   :depth: 1

The :ref:`community.dns collection <plugins_in_community.dns>` offers several filters for working with DNS names:

- ``community.dns.get_public_suffix``: given a domain name, returns the public suffix;
- ``community.dns.get_registrable_domain``: given a domain name, returns the registrable domain name;
- ``community.dns.remove_public_suffix``: given a domain name, returns the part before the public suffix;
- ``community.dns.remove_registrable_domain``: given a domain name, returns the part before the registrable domain name.

These filters allow to work with `public suffixes <https://en.wikipedia.org/wiki/Public_Suffix_List>`_; a *public suffix* is a DNS suffix under which users can (or could) directly register names. They use the `Public Suffix List <https://publicsuffix.org/>`_, a Mozilla initiative maintained as a community resource which tries to list all such public suffixes. Common examples for public suffixes are ``.com``, ``.net``, but also longer suffixes such as ``.co.uk`` or ``.github.io``.

The label directly before the public suffix together with the suffix is called the *registrable domain name* or *registered domain name*, since these are usually the names that people can register. Examples for registrable domain names are ``example.com`` and ``example.co.uk``, while ``www.example.com`` is not a registrable domain name. A public suffix itself is also not a registrable domain name, as for example ``github.io``.

Working with public suffixes
----------------------------

The ``community.dns.get_public_suffix`` and ``community.dns.remove_public_suffix`` filters allow to extract and remove public suffixes from DNS names:

.. code-block:: yaml+jinja

    - assert:
        that:
          - >-
            "www.ansible.com" | community.dns.get_public_suffix == ".com"
          - >-
            "some.random.prefixes.ansible.co.uk" | community.dns.get_public_suffix == ".co.uk"
          - >-
            "www.ansible.com" | community.dns.remove_public_suffix == "www.ansible"
          - >-
            "some.random.prefixes.ansible.co.uk" | community.dns.remove_public_suffix == "some.random.prefixes.ansible"

The filters also allow additional options (keyword arguments):

:keep_unknown_suffix:

  A boolean with default value ``true``. This treats unknown TLDs as valid public suffixes. So for example the public suffix of ``example.tlddoesnotexist`` is ``.tlddoesnotexist`` if this is ``true``. If set to ``false``, it will return an empty string in this case. This option corresponds to whether the global wildcard rule ``*`` in the Public Suffix List is used or not.

:icann_only:

  A boolean with default value ``false``. This controls whether only entries from the ICANN section of the Public Suffix List are used, or also entries from the Private section. For example, ``.co.uk`` is in the ICANN section, but ``github.io`` is in the Private section.

:normalize_result:

  (Only for ``community.dns.get_public_suffix``) A boolean with default value ``false``. This controls whether the result is reconstructed from the normalized name used during lookup. During normalization, ulabels are converted to alabels, and every label is converted to lowercase. For example, the ulabel ``ëçãmplê`` is converted to ``xn--mpl-llatwb`` (puny-code), and ``Example.COM`` is converted to ``example.com``.

:keep_leading_period:

  (Only for ``community.dns.get_public_suffix``) A boolean with default value ``true``. This controls whether the leading period of a public suffix is preserved or not.

:keep_trailing_period:

  (Only for ``community.dns.remove_public_suffix``) A boolean with default value ``false``. This controls whether the trailing period of the prefix (that is, the part before the public suffix) is preserved or not.

Working with registrable domain names
-------------------------------------

The ``community.dns.get_registrable_domain`` and ``community.dns.remove_registrable_domain`` filters allow to extract and remove registrable domain names from DNS names:

.. code-block:: yaml+jinja

    - assert:
        that:
          - >-
            "www.ansible.com" | community.dns.get_registrable_domain == "ansible.com"
          - >-
            "some.random.prefixes.ansible.co.uk" | community.dns.get_registrable_domain == "ansible.co.uk"
          - >-
            "www.ansible.com" | community.dns.remove_registrable_domain == "www"
          - >-
            "some.random.prefixes.ansible.co.uk" | community.dns.remove_registrable_domain == "some.random.prefixes"

The filters also allow additional options (keyword arguments):

:keep_unknown_suffix:

  A boolean with default value ``true``. This treats unknown TLDs as valid public suffixes. So for example the public suffix of ``example.tlddoesnotexist`` is ``.tlddoesnotexist`` if this is ``true``, and hence the registrable domain of ``www.example.tlddoesnotexist`` is ``example.tlddoesnotexist``. If set to ``false``, the registrable domain of ``www.example.tlddoesnotexist`` is ``tlddoesnotexist``. This option corresponds to whether the global wildcard rule ``*`` in the Public Suffix List is used or not.

:icann_only:

  A boolean with default value ``false``. This controls whether only entries from the ICANN section of the Public Suffix List are used, or also entries from the Private section. For example, ``.co.uk`` is in the ICANN section, but ``github.io`` is in the Private section.

:only_if_registerable:

  A boolean with default value ``true``. This controls the behavior in case there is no label in front of the public suffix. This is the case if the DNS name itself is a public suffix. If set to ``false``, in this case the public suffix is treated as a registrable domain. If set to ``true`` (default), the registrable domain of a public suffix is interpreted as an empty string.

:normalize_result:

  (Only for ``community.dns.get_registrable_domain``) A boolean with default value ``false``. This controls whether the result is reconstructed from the normalized name used during lookup. During normalization, ulabels are converted to alabels, and every label is converted to lowercase. For example, the ulabel ``ëçãmplê`` is converted to ``xn--mpl-llatwb`` (puny-code), and ``Example.COM`` is converted to ``example.com``.

:keep_trailing_period:

  (Only for ``community.dns.remove_registrable_domain``) A boolean with default value ``false``. This controls whether the trailing period of the prefix (that is, the part before the registrable domain) is preserved or not.
