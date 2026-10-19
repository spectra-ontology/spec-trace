"""OLE 복합 파일(Compound File Binary, MS-CFB) 읽기 — 개체 안 스트림 하나를 이름으로 꺼낸다.

헤더 · FAT(DIFAT 사슬 포함) · 디렉터리 · 미니 FAT · 미니 스트림만 읽는다. 쓰기 · 트리 순회는 하지 않는다 —
디렉터리 항목을 차례로 훑어 이름이 같은 스트림을 찾는다."""
import struct

SIG = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
END, FREE = 0xFFFFFFFE, 0xFFFFFFFF


class CFBError(ValueError):
    pass


def streams(data: bytes) -> dict[str, bytes]:
    """복합 파일 `data` 의 스트림 이름 → 내용. 형식이 어긋나면 `CFBError`."""
    if data[:8] != SIG or len(data) < 512:
        raise CFBError("not a compound file")
    major, = struct.unpack_from("<H", data, 0x1A)
    shift, mini_shift = struct.unpack_from("<HH", data, 0x1E)
    n_fat, dir_start = struct.unpack_from("<II", data, 0x2C)
    cutoff, minifat_start, n_minifat, difat_start, n_difat = struct.unpack_from("<IIIII", data, 0x38)
    ssz, msz = 1 << shift, 1 << mini_shift

    def sector(n: int) -> bytes:
        off = (n + 1) * ssz
        if off + ssz > len(data) + ssz:  # 끝 섹터는 파일 끝에서 잘릴 수 있다
            raise CFBError(f"sector {n} out of range")
        return data[off:off + ssz]

    fat_secs = [s for s in struct.unpack_from("<109I", data, 0x4C) if s not in (END, FREE)]
    d, seen = difat_start, 0
    while d not in (END, FREE) and seen < n_difat:
        ints = struct.unpack(f"<{ssz // 4}I", sector(d).ljust(ssz, b"\0"))
        fat_secs.extend(s for s in ints[:-1] if s not in (END, FREE))
        d, seen = ints[-1], seen + 1
    fat_secs = fat_secs[:n_fat]
    fat = []
    for s in fat_secs:
        fat.extend(struct.unpack(f"<{ssz // 4}I", sector(s).ljust(ssz, b"\0")))

    def chain(start: int, table: list, limit: int) -> list:
        out, n = [], start
        while n not in (END, FREE):
            if n >= len(table) or len(out) > limit:
                raise CFBError("broken chain")
            out.append(n)
            n = table[n]
        return out

    big_limit = len(data) // ssz + 1
    dir_bytes = b"".join(sector(s) for s in chain(dir_start, fat, big_limit))
    entries = []
    for off in range(0, len(dir_bytes) - 127, 128):
        e = dir_bytes[off:off + 128]
        nlen, = struct.unpack_from("<H", e, 0x40)
        kind = e[0x42]
        if kind == 0 or nlen < 2:
            continue
        name = e[:min(nlen, 64) - 2].decode("utf-16-le", "replace")
        start, = struct.unpack_from("<I", e, 0x74)
        size, = struct.unpack_from("<Q", e, 0x78)
        if major == 3:
            size &= 0xFFFFFFFF
        entries.append((name, kind, start, size))
    root = next((e for e in entries if e[1] == 5), None)
    if root is None:
        raise CFBError("no root entry")
    ministream = b"".join(sector(s) for s in chain(root[2], fat, big_limit)) if root[3] else b""
    minifat = []
    if n_minifat:
        for s in chain(minifat_start, fat, big_limit):
            minifat.extend(struct.unpack(f"<{ssz // 4}I", sector(s).ljust(ssz, b"\0")))
    out = {}
    for name, kind, start, size in entries:
        if kind != 2:
            continue
        if size < cutoff:
            body = b"".join(ministream[m * msz:(m + 1) * msz] for m in chain(start, minifat, len(ministream) // msz + 1))
        else:
            body = b"".join(sector(s) for s in chain(start, fat, big_limit))
        out[name] = body[:size]
    return out
