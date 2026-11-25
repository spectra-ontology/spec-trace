"""Preserve reviewed source editions when a TS writer replaces Section nodes.

Spec: docs/common/process/internal_ontology_guide.md
Ontology: EvidenceAssertion, FeatureAssertion and source-reviewed SourceUnit.
Cycle: read-only preflight before source replacement and structural deletion.
LLM calls: zero. A new edition requires explicit source reassessment.
"""
from __future__ import annotations


def require_unbound_sections(session, spec=None, release=None):
    """Reject automatic repointing of assertions bound to an existing edition.

    Legacy release migration and Phase-11 replacement have no atomic grounding
    refresh contract. A matching clause number alone cannot transfer reviewed
    meaning, even within a release. Restrict the guard to the writer's scope.
    """
    rows = session.run("""
        MATCH (s:Section)
        WHERE ($spec IS NULL OR EXISTS {
            MATCH (s)-[:BELONGS_TO_SPEC]->(sp:Spec {specNumber:$spec})
            WHERE $release IS NULL OR sp.specRelease=$release
        })
        MATCH (s)-[r]-(a)
        WHERE a:EvidenceAssertion OR a:FeatureAssertion OR a:TRImpact
           OR a.evidenceStatus='source_verified'
           OR a.sourceUnitAssessmentSha256 IS NOT NULL
           OR r.evidenceStatus='source_verified'
           OR EXISTS {
               MATCH (claim:FeatureAssertion {evidenceStatus:'source_verified'})
                     -[:assertionObject|assertionSubject]->(a)
           }
        RETURN DISTINCT s.sectionId AS sectionId,
               coalesce(a.assertionId,a.trImpactId,a.procedureName,
                        a.sourceUnitTitle,a.id,elementId(a)) AS sourceIdentity
        LIMIT 20
        """, spec=spec, release=release).data()
    if rows:
        examples = ', '.join(f"{r['sectionId']} ({r['sourceIdentity']})" for r in rows)
        raise ValueError(
            'Source-bound Section replacement requires source reassessment; '
            'automatic release/number repointing would change reviewed evidence: ' + examples)
