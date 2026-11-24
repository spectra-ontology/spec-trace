import collections
import json
import re
import sys


def graph(path):
    with open(path, encoding="utf-8") as stream:
        return json.load(stream)["@graph"]


def values(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def unique_rows(rows):
    return [list(row) for row in sorted(set(tuple(row) for row in rows))]


def build():
    with open("questions.jsonl", encoding="utf-8") as stream:
        questions = [json.loads(line) for line in stream if line.strip()]

    meetings = {r["@id"]: r for r in graph("records/phase-1/meetings.jsonld")}
    releases = {
        r["@id"]: r["tdoc:releaseName"]
        for r in graph("records/phase-1/releases.jsonld")
        if "tdoc:releaseName" in r
    }
    keep = {
        "@id", "tdoc:tdocNumber", "tdoc:type", "tdoc:status",
        "targetRelease", "modifies", "revisedTo", "isRevisionOf",
        "tdoc:crNumber", "tdoc:crRevision", "tdoc:clausesAffected",
        "tdoc:tsgCRPack", "presentedAt",
    }
    documents = {
        r["@id"]: {k: v for k, v in r.items() if k in keep}
        for r in graph("records/phase-1/tdocs.jsonld")
    }
    successors = collections.defaultdict(set)
    for document, r in documents.items():
        successors[document].update(values(r.get("revisedTo")))
        for predecessor in values(r.get("isRevisionOf")):
            successors[predecessor].add(document)

    def descendants(document):
        seen = {document}
        pending = list(successors[document])
        while pending:
            later = pending.pop()
            if later not in seen:
                seen.add(later)
                pending.extend(successors[later])
        return seen - {document}

    packs = {r["@id"]: r for r in graph("records/phase-4/crpacks.jsonld")}
    document_packs = collections.defaultdict(set)
    for pack, r in packs.items():
        for document in values(r.get("hasCR")):
            document_packs[document].add(pack)

    sections = {
        r["@id"]: r for r in graph("records/phase-4/section_extensions.jsonld")
    }
    section_documents = collections.defaultdict(set)
    document_sections = collections.defaultdict(set)
    for section, r in sections.items():
        for document in values(r.get("modifiedByCR")):
            section_documents[section].add(document)
            document_sections[document].add(section)

    # Both directions are assertions in the records; compare before using them.
    extensions = graph("records/phase-4/cr_extensions.jsonld")
    inverse_packs = {
        (r["@id"], pack)
        for r in extensions for pack in values(r.get("belongsToCRPack"))
    }
    forward_packs = {(d, p) for d, ps in document_packs.items() for p in ps}
    assert inverse_packs == forward_packs
    inverse_sections = {
        (r["@id"], section)
        for r in extensions for section in values(r.get("modifiesSection"))
    }
    forward_sections = {(d, s) for d, ss in document_sections.items() for s in ss}
    assert inverse_sections == forward_sections
    del extensions

    relevant = {"tdoc:" + n for q in questions for n in re.findall(r"R3-\d+", q["question"])}
    for q in questions:
        text = q["question"]
        if text.startswith("RAN3 recorded"):
            relevant.update(descendants("tdoc:" + re.search(r"R3-\d+", text).group()))
        elif text.startswith("TSG RAN CR pack"):
            pack = "tdoc:crpack/" + re.search(r"RP-\d+", text).group()
            relevant.update(values(packs[pack].get("hasCR")))
        elif text.startswith("Which Rel-"):
            release, clause, spec = re.search(
                r"Which (Rel-\d+) change requests that modify clause (\S+) of TS (\d+\.\d+)", text
            ).groups()
            # Retain subclause candidates for an ambiguity audit as well.
            section = "tdoc:section/" + spec + "-" + release + "-" + clause
            for s in sections:
                if s == section or s.startswith(section + "."):
                    relevant.update(section_documents[s])

    dispositions = collections.defaultdict(list)
    all_relevant_dispositions = collections.defaultdict(list)
    for r in graph("records/phase-2/decision_dispositions.jsonld"):
        document = r["dispositionTarget"]
        if document not in relevant:
            continue
        assessment = json.loads(r["assessmentMethod"])
        r["parsedAssessment"] = assessment
        all_relevant_dispositions[document].append(r)
        if r["evidenceStatus"] == "source_verified" and assessment.get("scope") == "whole_target":
            dispositions[document].append(r)

    event_ids = {r["dispositionOf"] for ds in all_relevant_dispositions.values() for r in ds}
    events = {}
    for filename in [
        "resolutions_document_dispositions.jsonld", "resolutions_agreements.jsonld",
        "resolutions_conclusions.jsonld", "resolutions_working_assumptions.jsonld",
    ]:
        for r in graph("records/phase-2/" + filename):
            if r["@id"] in event_ids:
                events[r["@id"]] = r

    def decisions(document):
        for r in dispositions[document]:
            event = events[r["dispositionOf"]]
            meeting = meetings[event["madeAt"]]
            if meeting["tdoc:workingGroup"] == "RAN3":
                yield r["dispositionCode"], meeting["tdoc:meetingNumber"]

    def memberships(document):
        for pack in sorted(document_packs[document]):
            r = packs[pack]
            yield r["tdoc:crPackId"], r["tdoc:tsgMeeting"]

    def section_parts(section):
        match = re.fullmatch(r"tdoc:section/(\d+\.\d+)-(Rel-\d+)-(.+)", section)
        assert match, section
        return match.groups()

    answers = []
    audit = {}
    for q in questions:
        text = q["question"]
        rows = []
        notes = []
        document_match = re.search(r"R3-\d+", text)
        document = "tdoc:" + document_match.group() if document_match else None
        if text.startswith("In which TSG RAN CR pack"):
            rows = list(memberships(document))
            if not rows:
                notes.append(
                    "No CR-pack membership is recorded for the exact named document. "
                    "An alternative reading follows the CR through later document revisions; "
                    "I did not expand the document identity."
                )
            audit[q["id"]] = {"kind": "pack_lookup", "document": document}
        elif text.startswith("RAN3 recorded"):
            later_documents = descendants(document)
            for later in later_documents:
                for code, meeting in decisions(later):
                    for pack, plenary in memberships(later):
                        rows.append([documents[later]["tdoc:tdocNumber"], code, pack])
            notes.append(
                "Interpreted every later version as all reachable revision descendants, "
                "including qualifying intermediate versions; an alternative includes only terminal revisions."
            )
            for r in dispositions[document]:
                if r["dispositionCode"] != "revised":
                    continue
                for target in re.findall(r"revised (?:to|in) (R3-\d+)", r["evidenceQuote"]):
                    if "tdoc:" + target not in successors[document]:
                        notes.append(
                            "A decision quote names " + target +
                            " as a revision target, whereas the document's revision links point to " +
                            ", ".join(sorted(s.removeprefix("tdoc:") for s in successors[document])) +
                            "; followed the revision links."
                        )
            audit[q["id"]] = {"kind": "revisions", "document": document, "descendants": sorted(later_documents)}
        elif text.startswith("TSG RAN CR pack"):
            pack = "tdoc:crpack/" + re.search(r"RP-\d+", text).group()
            for member in values(packs[pack].get("hasCR")):
                member_decisions = list(decisions(member))
                for code, meeting in member_decisions:
                    rows.append([documents[member]["tdoc:tdocNumber"], code, meeting])
                if not member_decisions:
                    notes.append(
                        member.removeprefix("tdoc:") +
                        " is a pack member but has no qualifying whole-document disposition record; excluded."
                    )
            audit[q["id"]] = {"kind": "pack_members", "pack": pack}
        elif text.startswith("Which Rel-"):
            release, clause, spec = re.search(
                r"Which (Rel-\d+) change requests that modify clause (\S+) of TS (\d+\.\d+)", text
            ).groups()
            section = "tdoc:section/" + spec + "-" + release + "-" + clause
            for member in section_documents[section]:
                r = documents.get(member)
                if r is None:
                    notes.append(
                        member.removeprefix("tdoc:") +
                        " has clause and pack links but no phase-1 document or disposition record; excluded."
                    )
                    assert not all_relevant_dispositions[member], member
                    continue
                if releases.get(r.get("targetRelease")) != release:
                    continue
                for code, meeting in decisions(member):
                    for pack, plenary in memberships(member):
                        rows.append([r["tdoc:tdocNumber"], code, meeting, pack])
            notes.append(
                "Interpreted the named clause as the exact numbered clause; "
                "an alternative includes its subclauses. Release means the CR's target release."
            )
            additional = set()
            for child in sections:
                if not child.startswith(section + "."):
                    continue
                for member in section_documents[child] - section_documents[section]:
                    r = documents.get(member, {})
                    if releases.get(r.get("targetRelease")) == release and list(decisions(member)) and list(memberships(member)):
                        additional.add(r["tdoc:tdocNumber"])
            if additional:
                notes.append("Including subclauses would additionally include " + ", ".join(sorted(additional)) + ".")
            audit[q["id"]] = {"kind": "release_clause", "section": section}
        elif text.startswith("Change request"):
            for code, meeting in decisions(document):
                for pack, plenary in memberships(document):
                    rows.append([code, meeting, pack, plenary])
            notes.append(
                "Joined the recorded whole-document decision and exact document's pack membership. "
                "The records provide no submission timestamp to independently verify 'then'."
            )
            audit[q["id"]] = {"kind": "decision_pack", "document": document}
        elif text.startswith("Trace change request"):
            spec = re.search(r"to TS (\d+\.\d+)", text).group(1)
            for code, meeting in decisions(document):
                for pack, plenary in memberships(document):
                    for section in document_sections[document]:
                        section_spec, release, clause = section_parts(section)
                        if section_spec == spec:
                            rows.append([code, meeting, pack, plenary, clause])
            audit[q["id"]] = {"kind": "trace", "document": document}
        else:
            raise ValueError(text)
        rows = unique_rows(rows)
        assert all(len(row) == len(q["fields"]) and all(isinstance(v, str) for v in row) for row in rows)
        answers.append({"id": q["id"], "rows": rows, "note": " ".join(notes)})

    assert len(answers) == len(questions)
    assert [a["id"] for a in answers] == [q["id"] for q in questions]
    assert len({a["id"] for a in answers}) == len(answers)

    return {
        "questions": questions, "answers": answers, "audit": audit,
        "documents": documents, "successors": successors,
        "descendants": descendants, "packs": packs, "document_packs": document_packs,
        "sections": sections, "section_documents": section_documents,
        "document_sections": document_sections, "dispositions": dispositions,
        "all_dispositions": all_relevant_dispositions, "events": events,
        "decisions": decisions, "memberships": memberships, "releases": releases,
    }


if __name__ == "__main__":
    result = build()
    with open("answers.jsonl", "w", encoding="utf-8") as stream:
        for answer in result["answers"]:
            stream.write(json.dumps(answer, ensure_ascii=False) + "\n")
    for answer in result["answers"]:
        kind = result["audit"][answer["id"]]["kind"]
        print(answer["id"], len(answer["rows"]), kind)
    print("TOTAL", len(result["answers"]), sum(len(a["rows"]) for a in result["answers"]))
    if "--notes" in sys.argv:
        for answer in result["answers"]:
            if answer["note"]:
                print(answer["id"], answer["note"])
    if "--audit" in sys.argv:
        print("SELECTED_ROWS")
        for answer in result["answers"]:
            entry = result["audit"][answer["id"]]
            if entry["kind"] in {"revisions", "decision_pack", "pack_lookup", "release_clause"}:
                print(json.dumps({"id": answer["id"], "rows": answer["rows"]}, ensure_ascii=False))
            if entry["kind"] == "revisions":
                print("REVISION_NODES", entry["document"], entry["descendants"])
                for later in entry["descendants"]:
                    print("REVISION_ARCS", later, sorted(result["successors"][later]))
            if entry["kind"] == "pack_members":
                pack = result["packs"][entry["pack"]]
                excluded = []
                for member in values(pack.get("hasCR")):
                    if not list(result["decisions"](member)):
                        excluded.append({
                            "document": member,
                            "dispositions": [
                                {"code": r["dispositionCode"], "status": r["evidenceStatus"],
                                 "scope": r["parsedAssessment"].get("scope"), "quote": r["evidenceQuote"]}
                                for r in result["all_dispositions"][member]
                            ],
                        })
                if excluded:
                    print("PACK_EXCLUDED", json.dumps(excluded, ensure_ascii=False))
        print("TDOC_PACK_CONFLICTS")
        relevant_documents = set(result["all_dispositions"])
        for document in sorted(relevant_documents):
            source = result["documents"].get(document, {}).get("tdoc:tsgCRPack")
            if source and "tdoc:crpack/" + source not in result["document_packs"][document]:
                print(document, source, sorted(result["document_packs"][document]))
