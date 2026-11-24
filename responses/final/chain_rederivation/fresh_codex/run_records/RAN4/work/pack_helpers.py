"""Read the small CR pack and meeting record graphs, normalizing scalar links."""
import json
from collections import defaultdict


def as_list(value):
    return value if isinstance(value, list) else ([] if value is None else [value])


def load_pack_records():
    packs = json.load(open('records/phase-4/crpacks.jsonld'))['@graph']
    by_pack = {r['tdoc:crPackId']: r for r in packs}
    by_document = defaultdict(list)
    for pack in packs:
        for document in as_list(pack.get('hasCR')):
            by_document[document].append(pack)
    return by_pack, dict(by_document)


def load_meeting_names():
    meetings = json.load(open('records/phase-1/meetings.jsonld'))['@graph']
    return {r['@id']: r['tdoc:meetingNumber'] for r in meetings}
