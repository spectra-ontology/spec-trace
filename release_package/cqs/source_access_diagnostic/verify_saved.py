#!/usr/bin/env python3
"""Replay packaged original-source roles and saved context observations offline."""
import hashlib
import json
from pathlib import Path
import sys

import audit

HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    manifest = json.loads((HERE / 'manifest.json').read_text())
    aliases = manifest['original_path_aliases']
    file_checks = 0
    for entry in manifest['files']:
        p = HERE / entry['path']
        if not p.is_file() or sha(p) != entry['sha256'] or p.stat().st_size != entry['bytes']:
            raise ValueError('manifested saved evidence mismatch: ' + entry['path'])
        if entry['sha256'] != entry['original_sha256']:
            raise ValueError('copied evidence differs from recorded original bytes')
        file_checks += 1
    report = json.loads((HERE / 'report.json').read_text())
    if report['completed_n'] != 23 or report['selected_denominator'] != 23 or len(report['items']) != 23:
        raise ValueError('incomplete fixed diagnostic denominator')
    source_members = context_checks = role_checks = 0
    for item in report['items']:
        source_fragments = []
        for source in item['layer1_original_source'].get('archives', []):
            if source.get('content_decoded') is False:
                # These locators were observed, not decoded, by the original
                # audit and are not promoted to independently replayed support.
                continue
            archive = HERE / aliases[source['path']]
            observed = audit.read_docx(archive, item)
            if observed['sha256'] != source['sha256'] or observed['members'] != source['members']:
                raise ValueError('original DOCX extraction disagrees: ' + item['id'])
            source_members += len(observed['members'])
            role_checks += sum(len(m.get('requested_role_fragments', [])) for m in observed['members'])
            source_fragments.extend(f for m in observed['members'] for f in m.get('requested_role_fragments', []))
        if source_fragments != item['layer1_original_source']['named_role_fragments']:
            raise ValueError('reextracted source-role aggregation differs')
        for method, context in item['layer3_and4_actual_candidates_context_and_sufficiency'].items():
            if not isinstance(context, dict):
                continue
            rounds = context.get('rounds', [])
            final = context.get('final_context_artifact')
            if final:
                directory = (HERE / aliases[final]).parent
            elif rounds:
                directory = (HERE / aliases[rounds[0]['artifact']]).parent
            else:
                continue
            fresh = audit.scan_context(directory, item)
            role_values = {f.get('explicit_decision_text') or f.get('explicit_contact_text') for f in source_fragments}
            context_values = {f.get('explicit_decision_text') or f.get('explicit_contact_text') for f in fresh['final_requested_role_fragments']}
            fresh['same_explicit_role_value_as_located_original'] = bool(role_values and context_values and context_values <= role_values)
            if item['diagnostic_type'] == 'named_document_attribute' and fresh['same_explicit_role_value_as_located_original']:
                fresh['full_requested_population_sufficient'] = 'SUPPORTED_NAMED_SINGLE_FIELD_BY_MATCHED_ORIGINAL_TEXT'
                fresh['sufficiency_limit'] = 'The named source field is explicitly supplied and agrees with located original DOCX. This is source evidence support, not model correctness or graph-wide information equality.'
            # Recorded path strings become portable aliases, all remaining values
            # (including actual role fragments, SHA and counts) must stay exact.
            def normalized(value):
                if isinstance(value, dict):
                    return {k: normalized(v) for k, v in value.items() if k not in {'artifact_directory', 'artifact', 'final_context_artifact'}}
                if isinstance(value, list):
                    return [normalized(v) for v in value]
                return value
            if normalized(fresh) != normalized(context):
                raise ValueError('saved candidate/context replay disagrees: ' + item['id'] + '/' + method)
            context_checks += 1
    print(json.dumps({'status': 'PASS', 'denominator': 23, 'manifested_files': file_checks,
                      'reextracted_DOCX_members': source_members, 'explicit_original_role_fragments': role_checks,
                      'C_D_saved_context_replays': context_checks,
                      'corpus_FTS_probe_rerun': False, 'full_population_sufficiency_certified': 0,
                      'new_model_calls': 0, 'new_retrieval_calls': 0, 'human_expert_reviews': 0}))

if __name__ == '__main__':
    main()
