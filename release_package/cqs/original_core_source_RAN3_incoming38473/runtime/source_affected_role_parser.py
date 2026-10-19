#!/usr/bin/env python3
"""Read named specs only from an identified CR's own affected-role cells.

A proposed source-enrichment parser, kept outside the production pipeline.
Its only lexical repair inserts boundaries in explicit TS/TR + spec + CR
tokens in already identified own role values. It never searches arbitrary
CR text for an affected spec and never infers approval or normative changes.
"""
import re
from lxml import etree

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
SPEC_TEXT = re.compile(r'\b(\d{2})\.\s*(\d{3})((?:-\d{1,2}(?!\d|\.\s*\d{3}))*)\b')
JOINED_CR_SPEC = re.compile(r'(?<![\w.])(\d{2}\.\s*\d{3}(?:-\d{1,2}(?!\d|\.\s*\d{3}))*)(?=CR\s*\d)', re.I)


def normalize_own_role_value(value):
    value = re.sub(r'\b(TS|TR)(?=\d{2}\.)', r'\1 ', value, flags=re.I)
    return JOINED_CR_SPEC.sub(r'\1 ', value)


def named_specs(value):
    normalized = normalize_own_role_value(value)
    return sorted(set(f'{m.group(1)}.{m.group(2)}{m.group(3)}' for m in SPEC_TEXT.finditer(normalized)))


def compact(value):
    return re.sub(r'\s+', '', value).lower()


def text(node):
    if node.tag in {W + 'del', W + 'moveFrom'}:
        return ''
    if node.tag == W + 't':
        return node.text or ''
    if node.tag == W + 'tab':
        return '\t'
    if node.tag in {W + 'br', W + 'cr'}:
        return '\n'
    return ''.join(text(child) for child in node)


def style_chain(styles, ident):
    result, seen = [], set()
    while ident:
        if ident in seen or ident not in styles:
            raise ValueError('Unresolved or cyclic source style')
        seen.add(ident)
        element = styles[ident]
        result.append(element)
        parent = element.find(W + 'basedOn')
        ident = parent.get(W + 'val') if parent is not None else None
    return list(reversed(result))


def active_text(element, styles, defaults):
    chunks, excluded = [], []
    for paragraph in element.iter(W + 'p'):
        paragraph_style = paragraph.find('./' + W + 'pPr/' + W + 'pStyle')
        parents = style_chain(styles, paragraph_style.get(W + 'val')) if paragraph_style is not None else []
        paragraph_chunks = []
        for run in paragraph.iter(W + 'r'):
            run_style = run.find('./' + W + 'rPr/' + W + 'rStyle')
            chain = parents + (style_chain(styles, run_style.get(W + 'val')) if run_style is not None else [])
            effective = {'strike': False, 'dstrike': False}
            for props in [defaults] + [s.find(W + 'rPr') for s in chain] + [run.find(W + 'rPr')]:
                if props is None:
                    continue
                for name in effective:
                    prop = props.find(W + name)
                    if prop is not None:
                        effective[name] = prop.get(W + 'val', 'true') not in {'false', 'off', '0'}
            deleted = any(p.tag in {W + 'del', W + 'moveFrom'} for p in run.iterancestors())
            value = text(run)
            if deleted or any(effective.values()):
                excluded.append({'text': value, 'deleted': deleted, 'effective': effective,
                                 'xml': etree.tostring(run, encoding='unicode')})
            else:
                paragraph_chunks.append(value)
        chunks.append(''.join(paragraph_chunks))
    return '\n'.join(chunks), excluded


def parse_parts(document_xml, styles_xml, expected_tdoc=None):
    document = etree.fromstring(document_xml)
    body = document.find(W + 'body')
    style_root = etree.fromstring(styles_xml)
    styles = {s.get(W + 'styleId'): s for s in style_root.findall(W + 'style')}
    defaults = style_root.find('./' + W + 'docDefaults/' + W + 'rPrDefault/' + W + 'rPr')
    read = lambda element: active_text(element, styles, defaults)
    first_table = next(i for i, element in enumerate(body) if element.tag == W + 'tbl')
    header_text = '\n'.join(read(element)[0] for i, element in enumerate(body)
                            if i < first_table and element.tag == W + 'p')
    header_ids = sorted(set(re.findall(r'R3-\d{6}(?!\d)', header_text)))
    if expected_tdoc is not None and header_ids != [expected_tdoc]:
        raise ValueError('Own header identity does not uniquely match expected frozen CR')
    own_tables, fields = [], []
    role_names = {'othercorespecifications': 'core', 'corespecifications': 'core',
                  'testspecifications': 'test', 'o&mspecifications': 'om', 'oandmspecifications': 'om'}
    for table_index, table in enumerate(body.findall(W + 'tbl')):
        joined = compact(text(table))
        if not all(token in joined for token in ['reasonforchange:', 'summaryofchange:', 'otherspecs']):
            continue
        own_tables.append(table_index)
        for row_index, row in enumerate(table.findall(W + 'tr')):
            cells = row.findall(W + 'tc')
            values = [read(cell) for cell in cells]
            for column, (label, _) in enumerate(values):
                role = role_names.get(compact(label))
                if role is None:
                    continue
                if column < 2 or column + 1 >= len(cells):
                    raise ValueError('Affected-role row structure is incomplete')
                value, excluded = values[column + 1]
                yes = values[column - 2][0].strip()
                no = values[column - 1][0].strip()
                specs = named_specs(value)
                if specs and (yes.lower() != 'x' or no.lower() == 'x'):
                    raise ValueError('Explicit named specs conflict with own affected-role checkboxes')
                fields.append({'role': role, 'active_value': value, 'normalized_value': normalize_own_role_value(value),
                               'specs': specs, 'yes': yes, 'no': no, 'excluded_runs': excluded,
                               'table_index': table_index, 'row_index': row_index, 'label_column': column,
                               'row_xml': etree.tostring(row, encoding='unicode')})
    if len(own_tables) != 1 or sorted(field['role'] for field in fields) != ['core', 'om', 'test']:
        raise ValueError('Exactly one own cover and all three distinct affected-role rows are required')
    return {'header_text': header_text, 'header_ids': header_ids, 'own_cover_table_index': own_tables[0],
            'fields': fields, 'docDefaults_rPr_xml': etree.tostring(defaults, encoding='unicode') if defaults is not None else None}
