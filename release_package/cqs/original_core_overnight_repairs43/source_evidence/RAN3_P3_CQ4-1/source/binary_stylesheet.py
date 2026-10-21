import struct,hashlib,runpy
from pathlib import Path
R=runpy.run_path(str(Path(__file__).absolute().parent/'binary_reader.py'))
u16,u32=R['u16'],R['u32']
H=lambda b:hashlib.sha256(b).hexdigest()
WATCH={0x0800,0x0802,0x0837,0x083c,0x2a53,0x0818,0x0855,0x0856,0x080a,0x2a90,0x6a09,0xca62,0xca89,0xca57}
def expand_ops(ops):
    """Recurse every table-style condition, irrespective of whether it applies."""
    out = []
    for op in ops:
        op = dict(op)
        out.append(op)
        if int(op['sprm'], 16) == 0xca85:
            operand = bytes.fromhex(op['operand_hex'])
            assert len(operand) >= 2
            for child in expand_ops(R['prls'](operand[2:])):
                out.append(dict(child, enclosing_condition=hex(u16(operand, 0))))
    return out

def stylesheet(raw):
    c = R['CFB'](raw)
    w = c.stream('WordDocument')
    table_name = '1Table' if u16(w, 10) & 0x200 else '0Table'
    t = c.stream(table_name)
    o = 32
    o += 2 + 2 * u16(w, o)
    o += 2 + 4 * u16(w, o)
    npairs = u16(w, o)
    o += 2
    fc, n = struct.unpack_from('<II', w, o + 8)  # fcStshf/lcbStshf
    s = t[fc:fc+n]
    assert len(s) == n
    cb = u16(s, 0)
    sh = s[2:2+cb]
    count, base_size = u16(sh, 0), u16(sh, 2)
    assert base_size in (10, 18)
    p = 2 + cb
    styles = []
    for i in range(count):
        l = u16(s, p)
        p += 2
        std = s[p:p+l]
        p += l
        assert len(std) == l
        if not l:
            continue
        bits = u16(std, 2)
        stk, parent, cupx = bits & 15, bits >> 4, u16(std, 4) & 15
        nn = u16(std, base_size)
        name = std[base_size+2:base_size+2+2*nn].decode('utf-16-le')
        x = base_size + 2 + 2*(nn+1)
        assert u16(std, x-2) == 0
        upx = []
        for j in range(cupx):
            ul = u16(std, x)
            x += 2
            body = std[x:x+ul]
            assert len(body) == ul
            x += ul + ul % 2
            upx.append(body)
        assert x == len(std), (i, name, x, len(std))
        char_index = {1: 1, 2: 0, 3: 2}.get(stk)
        char_ops = [] if char_index is None or char_index >= len(upx) else expand_ops(R['prls'](upx[char_index]))
        styles.append({'istd': i, 'name': name, 'stk': stk, 'istdBase': parent,
                       'cupx': cupx, 'std_sha256': H(std), 'character_UPX_PRLs': char_ops})
    assert p <= len(s)
    by_id = {x['istd']: x for x in styles}
    for st in styles:
        parent = st['istdBase']
        seen = {st['istd']}
        while parent != 0xfff:
            assert parent not in seen and parent in by_id
            seen.add(parent)
            parent = by_id[parent]['istdBase']
    # All branches are checked; identifying the applied paragraph style is not
    # needed to establish that none can introduce the observed watched flags.
    watched = [dict(style=st['name'], istd=st['istd'], **op)
               for st in styles for op in st['character_UPX_PRLs'] if int(op['sprm'], 16) in WATCH]
    return {'table_stream': table_name, 'fcStshf': fc, 'lcbStshf': n,
            'stylesheet_sha256': H(s), 'style_slots': count,
            'nonempty_styles': len(styles), 'styles': styles,
            'watched_style_operations': watched,
            'trailing_stylesheet_bytes': len(s)-p,
            'FIB_pair_count': npairs}
