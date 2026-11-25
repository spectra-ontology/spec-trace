#!/usr/bin/env python3
"""Assemble a metadata-only receipt after all bounded gate checks pass."""
import argparse
from pathlib import Path
import census_tree_gate as gate


def assemble(directory):
    certification = gate.read(directory/'certification_rp180200.json')
    frontier = gate.read(directory/'complete_original_frontier_receipt.json')
    controls = gate.read(directory/'negative_controls_receipt.json')
    projection_controls = gate.read(directory/'projection_negative_controls_receipt.json')
    replay = gate.read(directory/'full_audit_comparison/replay_receipt.json')
    condition = gate.read(directory/'full_audit_comparison/audit_condition.json')
    fixture = gate.read(directory/'expected_rp180200.json')
    proof = gate.read(directory/'conversion_proof_rp180200.json')
    if not (certification['selectedReconstructionWithFullAuditPassed'] and frontier['passed'] and controls['passed'] and projection_controls['passed']):
        raise ValueError('All executed bounded checks are required')
    events = directory/'full_audit_comparison/replacement_reads.jsonl'
    if condition['readEventsSha256'] != gate.digest(events):
        raise ValueError('Read-event ledger changed')
    allowed = ['census_tree_gate.py','negative_controls.py','complete_frontier_coverage.py','assemble_public_receipt.py',
        'projected_audit_gate.py','projection_negative_controls.py','projection_negative_controls_receipt.json',
        'expected_rp180200.json','conversion_proof_rp180200.json','input_gate_rp180200.json',
        'certification_rp180200.json','negative_controls_receipt.json',
        'original_full_frontier_receipt.json','complete_original_frontier_receipt.json','README.md',
        'full_audit_comparison/audit_condition.json','full_audit_comparison/replay_receipt.json','full_audit_comparison/replacement_reads.jsonl']
    result = {'schema':gate.SCHEMA, 'verifiedOriginalPublicCommit':fixture['publicCommit'],
        'condition':'Complete historical original derived base plus explicit RP-180200 reconstructed scientific reads',
        'originalBase':{'files':frontier['expectedCounts']['file'],'directories':frontier['expectedCounts']['directory'],
            'allHistoricalBytesExact':frontier['allOriginalHistoricalBytesMatched'], 'completePathSetMatched':frontier['completePathSetMatched']},
        'selectedArchive':{'archiveSha256':fixture['archives'][0]['sha256'],'files':len(fixture['files']),
            'exactNativeFiles':certification['counts']['exactUnconvertedFiles'], 'byteDifferentConvertedFiles':certification['counts']['historicalConvertedBytesDiffer'],
            'applicableReconstructedCrForms':sum('clause' in row['requiredFullAuditReaders'] for row in fixture['files']),
            'applicableReconstructedCovers':sum('pack' in row['requiredFullAuditReaders'] for row in fixture['files']),
            'directStrictXmlExports':sum(not row['acceptedFullTextCompared'] for row in proof['conversions']),
            'acceptedFullTextRecoveryReceipts':sum(row['acceptedFullTextCompared'] for row in proof['conversions'])},
        'originalAudits':{kind:{key:row[key] for key in ('auditorSha256','outputSha256','referenceSha256','elapsedSeconds','allComparedFieldsMatch','originalUnprojectedReferenceSha256','originalUnprojectedComparisonPassed','projectionVerification') if key in row} for kind,row in replay['audits'].items()},
        'actualReconstructedSha1Retained':condition['actualReconstructedSha1Retained'],
        'originalDeduplicationUnchanged':condition['originalDeduplicationUnchanged'],
        'negativeControlsPassed':len(controls['controls'])+len(projection_controls['controls']),
        'inputAndSha1ControlsPassed':len(controls['controls']), 'projectionControlsPassed':len(projection_controls['controls']),
        'selectedReconstructionWithFullAuditPassed':True,
        'wholeCorpusFreshlyReconstructed':False, 'fullCorpusReconstructionCertified':False,
        'newConversionExecutionPerformedInThisGateTask':False,
        'conversionEvidence':'Existing pinned constructor outputs verified; fresh original full-audit comparisons executed by this helper',
        'sourceTextIncluded':False,
        'publicationWhitelist':{name:{'sha256':gate.digest(directory/name),'bytes':(directory/name).stat().st_size} for name in allowed}}
    gate.write(directory/'public_receipt.json', result)
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,required=True)
    result=assemble(parser.parse_args().directory)
    print({'selectedReconstructionWithFullAuditPassed':result['selectedReconstructionWithFullAuditPassed'],'negativeControlsPassed':result['negativeControlsPassed']})
