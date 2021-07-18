#!/usr/bin/env python3

import importlib
import os
import re
import sys

import yaml


PROVIDERS = ['hetzner', 'hosttech']

TYPE_DEPENDENT_FRAGMENTS = [
    ('ZONE_CHOICES', 'options.type', [
        'module_record',
        'module_record_info',
        'module_record_set',
    ]),
    ('ZONE_CHOICES_RECORD_SETS_MODULE', 'options.record_sets.suboptions.type', [
        'module_record_sets',
    ]),
    ('ZONE_CHOICES_RECORDS_INVENTORY', 'options.filters.suboptions.type', [
        'inventory_records',
    ]),
]


def get_provider_informations(providers):
    files_to_remove = []

    def add_init_py(path):
        path = os.path.join(path, '__init__.py')
        if os.path.exists(path):
            return
        with open(path, 'wb') as f:
            f.write(b'')
        files_to_remove.append(path)

    try:
        sys.path.append(os.path.join('..', '..', '..'))

        add_init_py(os.path.join('..', '..'))
        add_init_py(os.path.join('..'))
        add_init_py(os.path.join('.'))
        add_init_py(os.path.join('plugins'))
        add_init_py(os.path.join('plugins', 'module_utils'))

        provider_infos = {}
        errors = []

        for provider in providers:
            add_init_py(os.path.join('plugins', 'module_utils', provider))
            full_py_path = 'ansible_collections.community.dns.plugins.module_utils.{0}.api'.format(provider)
            full_pathname = os.path.join('plugins', 'module_utils', provider, 'api.py')
            try:
                loader = importlib.machinery.SourceFileLoader(full_py_path, full_pathname)
                spec = importlib.util.spec_from_loader(full_py_path, loader)
                the_module = importlib.util.module_from_spec(spec)
                loader.exec_module(the_module)
            except Exception as e:
                errors.append('{0}: Error while importing module {1}: {2}'.format(full_pathname, full_py_path, e))
                continue

            create_provider_info_fn_name = 'create_{0}_provider_information'.format(provider)
            try:
                create_provider_info_fn = provider_information = the_module.__dict__[create_provider_info_fn_name]
                provider_infos[provider] = create_provider_info_fn()
            except KeyError as e:
                errors.append('{0}: Cannot find function {1}'.format(full_pathname, create_provider_info_fn))
            except Exception as e:
                errors.append('{0}: Error while invoking function {1}: {2}'.format(full_pathname, create_provider_info_fn, e))

        return provider_infos, errors
    finally:
        for path in files_to_remove:
            os.remove(path)


class DocFragmentParseError(Exception):
    def __init__(self, path, error_message):
        self.path = path
        self.error_message = error_message
        super(DocFragmentParseError, self).__init__('Error while parsing {0}: {1}'.format(path, error_message))


DOC_FRAGMENT_START_MATCHER = re.compile(r"^    ([A-Z_]+) = r'''$")


class Dumper(yaml.SafeDumper):
    def ignore_aliases(self, *args):
        return True

    def increase_indent(self, flow=False, *args, **kwargs):
        self.best_indent = kwargs.pop('ident_override', 4)
        return super().increase_indent(*args, **kwargs)

    def expect_block_sequence(self):
        self.increase_indent(flow=False, indentless=False, ident_override=2)
        self.state = self.expect_first_block_sequence_item


class DocFragment:
    def __init__(self, path, prefix_lines, name, lines):
        self.prefix_lines = prefix_lines
        self.name = name
        self.lines = lines

        try:
            self.data = yaml.safe_load('\n'.join(self.lines))
        except Exception as e:
            raise DocFragmentParseError(path, 'Error while parsing part {0}: {1}'.format(name, e))

    def recreate_lines(self):
        data = yaml.dump(self.data, default_flow_style=False, indent=4, Dumper=Dumper, sort_keys=False)
        self.lines = data.splitlines()

    def serialize_lines(self):
        return self.prefix_lines + ["    {0} = r'''".format(self.name)] + self.lines + ["'''"]


class DocFragmentFile:
    def __init__(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()

        self.prefix = []
        self.fragments = []
        self.fragments_by_name = {}

        where = 'prefix'
        for line in lines:
            if where == 'prefix':
                self.prefix.append(line)
                if line == 'class ModuleDocFragment(object):':
                    where = 'body'
                    body_prefix = []
                    body_name = None
                    body_lines = []
            elif where == 'body':
                if body_name is None:
                    m = DOC_FRAGMENT_START_MATCHER.match(line)
                    if m:
                        body_name = m.group(1)
                    else:
                        body_prefix.append(line)
                elif line == "'''":
                    fragment = DocFragment(path, body_prefix, body_name, body_lines)
                    self.fragments.append(fragment)
                    self.fragments_by_name[body_name] = fragment
                    body_prefix = []
                    body_name = None
                    body_lines = []
                else:
                    body_lines.append(line)

        if where == 'prefix':
            raise DocFragmentParseError(path, 'Cannot find body')

    def serialize_to_string(self):
        lines = []
        lines.extend(self.prefix)
        for fragment in self.fragments:
            lines.extend(fragment.serialize_lines())
        lines.append('')
        return '\n'.join(lines)


def doc_fragment_fn(name):
    return os.path.join('plugins', 'doc_fragments', '{0}.py'.format(name))


def load_doc_fragment(name):
    fn = doc_fragment_fn(name)
    return DocFragmentFile(fn)


def load_single_doc_fragment(name):
    fragment = 'DOCUMENTATION'
    if '.' in name:
        name, fragment = name.split('.', 1)
        fragment = fragment.upper()
    doc_fragment = load_doc_fragment(name)
    return doc_fragment.fragments_by_name[fragment]


def write_doc_fragment(name, doc_fragment):
    fn = doc_fragment_fn(name)
    data = doc_fragment.serialize_to_string()
    with open(fn, 'w', encoding='utf-8') as f:
        f.write(data)


def compare_doc_fragment(name, doc_fragment):
    fn = doc_fragment_fn(name)
    data = doc_fragment.serialize_to_string()
    with open(fn, 'r', encoding='utf-8') as f:
        compare_data = f.read()
    return data == compare_data


def add_record_type_fragments(provider_fragment, provider_record_types):
    provider_record_types = sorted(provider_record_types)

    for fragment_name, insertion_point, doc_fragment_names in TYPE_DEPENDENT_FRAGMENTS:
        doc_fragments = [load_single_doc_fragment(doc_fragment) for doc_fragment in doc_fragment_names]
        insertion_point = insertion_point.split('.')
        insertion_fragment = provider_fragment.fragments_by_name.get(fragment_name)
        if insertion_fragment is None:
            insertion_fragment = DocFragment('', [], fragment_name, [])
            provider_fragment.fragments.append(insertion_fragment)
            provider_fragment.fragments_by_name[fragment_name] = insertion_fragment

        insertion_fragment.data = {}
        insertion_pos = insertion_fragment.data
        original_pos = doc_fragments[0].data  # FIXME
        for depth, part in enumerate(insertion_point):
            if part not in insertion_pos:
                insertion_pos[part] = {}
            insertion_pos = insertion_pos[part]
            original_pos = original_pos[part]
            if depth >= 2:
                insertion_pos.update(original_pos)
        insertion_pos['choices'] = provider_record_types

        insertion_fragment.prefix_lines = [
            '',
            '    # WARNING: This section is automatically generated by update-docs-fragments.py.',
            '    #          It is used to augment the docs fragment{0} {1}.'.format(
                's' if len(doc_fragment_names) != 1 else '',
                ', '.join(sorted(doc_fragment_names))),
            '    #          DO NOT EDIT MANUALLY!',
        ]
        insertion_fragment.recreate_lines()


def main(program, arguments):
    lint = '--lint' in arguments
    provider_infos, errors = get_provider_informations(PROVIDERS)
    try:
        for provider, provider_info in sorted(provider_infos.items()):
            try:
                doc_fragment = load_doc_fragment(provider)

                record_types = provider_info.get_supported_record_types()
                add_record_type_fragments(doc_fragment, record_types)

                if not compare_doc_fragment(provider, doc_fragment):
                    path = doc_fragment_fn(provider)
                    if lint:
                        errors.append('{0}: Needs to be updated by update-docs-fragments.py'.format(path))
                    else:
                        print('Writing {0}...'.format(path))
                        write_doc_fragment(provider, doc_fragment)

            except DocFragmentParseError as e:
                errors.append('{0}: Error while parsing docs fragment: {1}'.format(e.path, e.error_message))

    except Exception as e:
        errors.append('{0}: Unexpected error: {1}'.format(program, e))

    for error in errors:
        print(error)
    return 5 if errors else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[0], sys.argv[1:]))