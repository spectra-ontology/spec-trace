"""TS·TR 갱신의 사후 검증·완료 기록·이력 정리를 같은 정책으로 수행한다."""
from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path


def entity_section_link_counts(cypher, spec_number: str) -> tuple[int, int]:
    """대상 TS의 item 엔터티 수와 원문 절 연결 위반 수를 읽고 응답을 검증한다.

    스키마의 minCount에 따라 CapabilityItem·Procedure item의 정의 연결을
    요구하며 복수 절 연결을 허용한다. 나머지 세 클래스는 연결을 선택할 수 있다.
    존재하는 모든 정의 연결은 같은 TS의 Section을 가리켜야 한다. 엔터티 수는
    0일 수 있으므로 호출자는 원문 Section 존재 검사도 함께 실행한다. Feature의
    근거 assertion은 별도 적재·검증 계약을 사용하므로 이 조회에 포함하지 않는다.
    """
    rows = cypher(
        "MATCH (e) WHERE e.specNumber=$spec AND e.granularity='item' "
        "AND NOT e:Section AND (e:RRCParameter OR e:CapabilityItem "
        "OR e:Procedure OR e:PerformanceRequirement OR e:ConformanceTest) "
        "OPTIONAL MATCH (e)-[:definedInSection]->(s) "
        "WITH e, collect(s) AS sections "
        "RETURN count(e) AS entity_count, "
        "sum(CASE WHEN ((e:CapabilityItem OR e:Procedure) AND size(sections)=0) "
        "OR any(s IN sections WHERE "
        "NOT s:Section OR NOT (s)-[:BELONGS_TO_SPEC]->(:Spec {specNumber:$spec})) "
        "THEN 1 ELSE 0 END) AS invalid_count",
        spec=spec_number,
    )
    if (len(rows) != 1 or not isinstance(rows[0], dict)
            or any(type(rows[0].get(key)) is not int or rows[0][key] < 0
                   for key in ("entity_count", "invalid_count"))
            or rows[0]["invalid_count"] > rows[0]["entity_count"]):
        raise ValueError("엔터티 연결 조회의 건수 응답이 올바르지 않습니다")
    return rows[0]["entity_count"], rows[0]["invalid_count"]


def finalize_pipeline(
    run_dir: Path,
    file_handler: logging.FileHandler,
    pipeline_start: datetime,
    task_results: dict,
    tasks_run: list[str],
    status: str,
    target_id: str,
    config=None,
    dry_run: bool = False,
    complete=None,
    no_changes: bool = False,
    *, pipeline, Phase11PostValidator, _resolve_cq_targets, summarize_cq,
    save_validation_report, _print_metrics, append_history, remove_file_handler, logger,
) -> str:
    """실제 평가한 CQ·보고서 저장·검증기 종료까지 마친 대상만 완료로 기록한다."""
    try:
        pipeline_end = datetime.now(timezone.utc)
        elapsed = int((pipeline_end - pipeline_start).total_seconds())

        # CQ 사후 검증 (Spec §5.3)
        # target_id "ALL"은 CQ에 그대로 넣으면 specNumber="ALL" 조회가 되어
        # 거짓 FAIL이 나므로, 처리된 개별 spec으로 풀어 검증한다.
        # 자동 수집이 성공했고 변경 대상이 없으면 평가할 작업도 없다.
        # 실제 작업의 빈 CQ·전체 SKIP 은 아래 검증 조건을 그대로 따른다.
        collection_task = f"{pipeline}-0"
        collection = task_results.get(collection_task, {})
        scanned = collection.get("total_scanned")
        skipped = collection.get("skipped")
        no_work = (
            no_changes and status == "SUCCESS" and target_id == "ALL"
            and complete is None and tasks_run == [collection_task]
            and set(task_results) == {collection_task}
            and collection.get("status") == "SUCCESS"
            and collection.get("collected") == []
            and collection.get("failed") == []
            and type(collection.get("failed_count")) is int and collection.get("failed_count") == 0
            and type(collection.get("collected_count")) is int and collection.get("collected_count") == 0
            and type(scanned) is int and scanned >= 0
            and type(collection.get("unchanged_count")) is int
            and collection.get("unchanged_count") == scanned
            and isinstance(skipped, list) and len(skipped) == scanned
        )
        # 빈 대상 범위와 실제 변경 점검을 구분해서 기록한다.
        cq_result_str = ("NO_TARGETS" if scanned == 0 else "NO_CHANGES") if no_work else "N/A"
        invalid_no_changes = no_changes and not no_work
        if invalid_no_changes and status == "SUCCESS":
            logger.warning("변경 없음 판정에 필요한 수집 점검 결과가 일치하지 않습니다")
            status = "FAILED"
        cq_results_list = []
        cq_targets: list[str] = []
        verified: set[str] = set()
        errors: list[str] = []
        if config and tasks_run and not dry_run and status != "CANCELLED" and not no_work:
            cq_targets = _resolve_cq_targets(target_id, task_results)
            try:
                with Phase11PostValidator(config) as validator:
                    vr = None
                    for cq_target in cq_targets:
                        # 한 대상의 검증 예외가 다른 대상의 검증을 막지 않게 대상마다 받는다.
                        try:
                            one = validator.run_all(pipeline, cq_target, tasks_run)
                        except Exception as e:
                            logger.warning("CQ 사후 검증 실패 (%s): %s", cq_target, e)
                            errors.append(f"{cq_target}: {e}")
                            continue
                        one_rows = one.to_list()
                        if any(row.get("status") != "SKIP" for row in one_rows) and not any(
                            not row.get("passed", False) and row.get("status") != "SKIP"
                            for row in one_rows
                        ):
                            verified.add(cq_target)
                        print(f"\n{one.summary()}")
                        if vr is None:
                            vr = one
                        else:
                            vr.results.extend(one.results)
                    cq_results_list = vr.to_list() if vr else []
                    if vr:
                        cq_result_str = summarize_cq(cq_results_list)
                    save_validation_report(
                        run_dir, pipeline, target_id, cq_results_list, task_results,
                    )
            except Exception as e:
                # 검증기를 열거나 닫지 못했거나 보고서를 남기지 못했다. 어느 대상도 검증을 마쳤다고 읽지 않는다.
                logger.warning("CQ 사후 검증 실패: %s", e)
                errors.append(str(e))
                verified.clear()
            if errors:
                cq_result_str = "ERROR: " + "; ".join(errors)

        # CQ FAIL 을 실행 상태에도 반영한다. 아래에서 통과한 대상의 완료만 기록하고,
        # 완료된 대상이 하나도 없으면 FAILED 로 낮춘다. SKIP 은 FAIL 로 세지 않는다.
        cq_failed = [str(r.get("cq_id")) for r in cq_results_list
                     if not r.get("passed", False) and r.get("status") != "SKIP"]
        if cq_failed and status == "SUCCESS":
            logger.warning("사후 CQ FAIL %d건: %s", len(cq_failed), ", ".join(cq_failed))
            status = "PARTIAL"

        if invalid_no_changes:
            verified.clear()

        # 완료 기록: 비어 있지 않은 사후 CQ 를 통과한 대상만 적는다. 나머지는 이번 실행이 내린 in_progress 로 남는다.
        held: list[str] = []
        recorded = 0
        if complete is not None:
            ready, record = complete
            # 대상 하나를 맡은 실행은 그 대상의 검증이 곧 맡은 전부의 검증이다.
            whole = target_id != "ALL" and target_id in verified
            for t in ready:
                if whole or t in verified:
                    record(t)
                    recorded += 1
                else:
                    held.append(t)
            if held:
                logger.warning("사후 CQ 완료 조건을 충족하지 못해 완료로 적지 않은 대상: %s", ", ".join(held))
        unverified = [t for t in cq_targets if t not in verified]
        if held or unverified:
            if complete is not None and complete[0]:
                done_any = recorded > 0
            else:
                done_any = bool(verified)
            if status == "SUCCESS":
                status = "PARTIAL" if done_any else "FAILED"
            elif status == "PARTIAL" and not done_any:
                status = "FAILED"

        # 결과 출력
        _print_metrics(pipeline_start, task_results, status)

        # 이력 기록 (Spec §4.2)
        scenario = "auto" if "--auto" in sys.argv else "manual"
        if not dry_run:
            append_history(
                pipeline=pipeline,
                target_id=target_id,
                duration_seconds=elapsed,
                scenario=scenario,
                tasks_run=tasks_run,
                status=status,
                cq_result=cq_result_str,
                metrics=task_results,
                wg=config.wg_name if config else None,
            )

        # 파일 핸들러 정리
        return status
    finally:
        if file_handler is not None:
            remove_file_handler(file_handler)
