"""Resolve documented source-template identity errors without changing source bytes.

Spec: operations rulebook §3–4; tr_source_identity_resolutions.json.
Cycle: exact source SHA + official archive/registry + document body → metadata.
No network, model or database calls. A changed document requires a new assessment.
"""
import hashlib
import json
from pathlib import Path
import re

CONFIG='ontology/config/tr_source_identity_resolutions.json'

def evidence_sha256(proof):
    """Digest the authored observation, independently of JSON whitespace."""
    return hashlib.sha256(json.dumps(proof,ensure_ascii=False,sort_keys=True,
                                     separators=(',',':')).encode('utf-8')).hexdigest()


def _sha(value):
    return isinstance(value,str) and re.fullmatch(r'[0-9a-f]{64}',value) is not None


def _check_archive_evidence(entry,source_bytes):
    """Validate retained observations; this does not re-fetch official archives."""
    proof=entry.get('officialArchiveEvidence')
    if not isinstance(proof,dict) or not _sha(entry.get('officialArchiveEvidenceSha256')) or \
            evidence_sha256(proof)!=entry['officialArchiveEvidenceSha256']:
        raise ValueError('Official archive identity evidence digest is missing or changed')
    if proof.get('localPath')!=entry['sourcePath'] or proof.get('localSha256')!=entry['sourceSha256']:
        raise ValueError('Official archive identity evidence no longer matches the retained source')
    sources=proof.get('officialSources')
    if not isinstance(sources,list) or len(sources)!=2:
        raise ValueError('Official archive identity evidence requires an unambiguous archive comparison')
    numbers=(entry['trNumber'],entry.get('sourceCoverNumber'))
    if numbers[0]==numbers[1] or not all(isinstance(n,str) and re.fullmatch(r'\d{2}\.\d{3}(?:-\d+)*',n)
                                        for n in numbers):
        raise ValueError('Official archive identity evidence has invalid document identities')
    seen=set()
    for observed in sources:
        if not isinstance(observed,dict) or type(observed.get('status')) is not int or observed['status']!=200 or \
                not _sha(observed.get('archiveSha256')):
            raise ValueError('Official archive identity evidence has invalid archive metadata')
        members=observed.get('members')
        if not isinstance(members,list) or len(members)!=1 or not isinstance(members[0],dict):
            raise ValueError('Official archive identity evidence has ambiguous members')
        member=members[0];name=member.get('name')
        if not isinstance(name,str) or Path(name).name!=name or not name.endswith('.docx') or \
                not _sha(member.get('sha256')) or type(member.get('bytes')) is not int or member['bytes']<=0 or \
                type(member.get('matchesLocal')) is not bool:
            raise ValueError('Official archive identity evidence has invalid member metadata')
        identities=[number for number in numbers if observed.get('url')==
                    f'https://www.3gpp.org/ftp/Specs/archive/{number[:2]}_series/{number}/{name[:-5]}.zip'
                    and name.startswith(number.replace('.','')+'-')]
        if len(identities)!=1 or identities[0] in seen:
            raise ValueError('Official archive identity evidence has an invalid or ambiguous official URL')
        number=identities[0];seen.add(number)
        same=number==entry['trNumber']
        if member['matchesLocal'] is not same or (member['sha256']==entry['sourceSha256']) is not same or \
                (same and (name!=Path(entry['sourcePath']).name or member['bytes']!=len(source_bytes))):
            raise ValueError('Official archive identity evidence no longer matches the retained source')
    if seen!=set(numbers):
        raise ValueError('Official archive identity evidence is missing its archive comparison')

def resolution_for(root,wg,tr_number,path):
    root=Path(root);path=Path(path)
    config_path=root/CONFIG
    if not config_path.exists():
        return None
    config=json.loads(config_path.read_text())
    if type(config.get('schema')) is not int or config['schema']!=1 or not isinstance(config.get('resolutions'),list):
        raise ValueError('Invalid TR source identity configuration')
    matches=[r for r in config['resolutions'] if r['wg']==wg and r['trNumber']==tr_number
             and r['sourcePath']==str(path.relative_to(root))]
    if not matches:return None
    if len(matches)!=1:raise ValueError('Ambiguous TR source identity resolution')
    entry=matches[0]
    source_bytes=path.read_bytes()
    if not _sha(entry.get('sourceSha256')) or hashlib.sha256(source_bytes).hexdigest()!=entry['sourceSha256']:
        raise ValueError('TR source identity resolution is bound to different source bytes')
    _check_archive_evidence(entry,source_bytes)
    from tr_impact_evidence import source_text
    text=source_text(path)
    quotes=entry.get('bodyIdentityQuotes')
    if not isinstance(quotes,list) or not quotes or not all(isinstance(quote,str) and quote.strip() and quote in text
                                                          for quote in quotes):
        raise ValueError('TR identity resolution body passages are missing')
    if path.read_bytes()!=source_bytes:
        raise ValueError('TR source identity changed while reading its body')
    return entry
