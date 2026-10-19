"""Portable pure functions extracted from the independently authored source audit.
No local project paths, database, network, conversion or host fallback.
"""
import hashlib
import struct
import native_reader as native
R={k:getattr(native,k) for k in ("CFB","u16","u32","prls")}
u16,u32=R["u16"],R["u32"]
H=lambda b:hashlib.sha256(b).hexdigest()
WATCH = {2048: 'deleted_revision', 2050: 'hidden_field', 2103: 'strike', 2108: 'hidden', 10835: 'double_strike', 2072: 'style_separator', 2133: 'special_character', 2134: 'object', 2058: 'OLE_object', 10896: 'SDT_hidden', 27145: 'symbol', 51810: 'display_field_revision', 51849: 'property_revision', 51799: 'property_revision_old'}

def expand_ops(ops):
    """Recurse every table-style condition, irrespective of whether it applies."""
    out = []
    for op in ops:
        op = dict(op)
        out.append(op)
        if int(op['sprm'], 16) == 51845:
            operand = bytes.fromhex(op['operand_hex'])
            assert len(operand) >= 2
            for child in expand_ops(R['prls'](operand[2:])):
                out.append(dict(child, enclosing_condition=hex(u16(operand, 0))))
    return out

def stylesheet(raw):
    c = R['CFB'](raw)
    w = c.stream('WordDocument')
    table_name = '1Table' if u16(w, 10) & 512 else '0Table'
    t = c.stream(table_name)
    o = 32
    o += 2 + 2 * u16(w, o)
    o += 2 + 4 * u16(w, o)
    npairs = u16(w, o)
    o += 2
    (fc, n) = struct.unpack_from('<II', w, o + 8)
    s = t[fc:fc + n]
    assert len(s) == n
    cb = u16(s, 0)
    sh = s[2:2 + cb]
    (count, base_size) = (u16(sh, 0), u16(sh, 2))
    assert base_size in (10, 18)
    p = 2 + cb
    styles = []
    for i in range(count):
        l = u16(s, p)
        p += 2
        std = s[p:p + l]
        p += l
        assert len(std) == l
        if not l:
            continue
        bits = u16(std, 2)
        (stk, parent, cupx) = (bits & 15, bits >> 4, u16(std, 4) & 15)
        nn = u16(std, base_size)
        name = std[base_size + 2:base_size + 2 + 2 * nn].decode('utf-16-le')
        x = base_size + 2 + 2 * (nn + 1)
        assert u16(std, x - 2) == 0
        upx = []
        for j in range(cupx):
            ul = u16(std, x)
            x += 2
            body = std[x:x + ul]
            assert len(body) == ul
            x += ul + ul % 2
            upx.append(body)
        assert x == len(std), (i, name, x, len(std))
        char_index = {1: 1, 2: 0, 3: 2}.get(stk)
        char_ops = [] if char_index is None or char_index >= len(upx) else expand_ops(R['prls'](upx[char_index]))
        styles.append({'istd': i, 'name': name, 'stk': stk, 'istdBase': parent, 'cupx': cupx, 'std_sha256': H(std), 'character_UPX_PRLs': char_ops})
    assert p <= len(s)
    by_id = {x['istd']: x for x in styles}
    for st in styles:
        parent = st['istdBase']
        seen = {st['istd']}
        while parent != 4095:
            assert parent not in seen and parent in by_id
            seen.add(parent)
            parent = by_id[parent]['istdBase']
    watched = [dict(style=st['name'], istd=st['istd'], **op) for st in styles for op in st['character_UPX_PRLs'] if int(op['sprm'], 16) in WATCH]
    return {'table_stream': table_name, 'fcStshf': fc, 'lcbStshf': n, 'stylesheet_sha256': H(s), 'style_slots': count, 'nonempty_styles': len(styles), 'styles': styles, 'watched_style_operations': watched, 'trailing_stylesheet_bytes': len(s) - p, 'FIB_pair_count': npairs}

def source_fields(text):
    result = []
    for (field, label, next_label) in [('reasonForChange', 'Reason for change:', 'Summary of change:'), ('summaryOfChange', 'Summary of change:', 'Consequences if not approved:')]:
        assert text.count(label) == 1 and text.count(next_label) == 1
        a = text.index(label) + len(label)
        assert text[a] == '\x07', (field, repr(text[a:a + 10]))
        a += 1
        b = text.index('\x07', a)
        next_pos = text.index(next_label, b)
        assert not text[b:next_pos].strip('\x07\r\n\t ')
        value = text[a:b]
        assert not any((ch in value for ch in '\x01\x08\x13\x14\x15\x03\x04\x05'))
        literal = value.replace('\r', '\n').replace('\x0b', '\n')
        result.append({'field': field, 'label': label, 'cp_start': a, 'cp_end': b, 'raw_value': value, 'transcribed_value': literal, 'following_cell_boundary': {'cp': b, 'codepoint': 7}, 'next_label': next_label, 'next_label_cp': next_pos})
    return result
