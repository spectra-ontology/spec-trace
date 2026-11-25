"""Measure one selected embedding workload and estimate remaining input work.

Spec: docs/common/process/internal_embedding_guide.md.
Cycle: selected nonempty input → measured batches → approximate remaining time.
LLM calls: 0. This module loads no model and connects to no database.
"""
from __future__ import annotations

import math
import time


class EmbeddingProgress:
    """Use observed characters and embedding time for a local, approximate ETA.

    Initialization, embedding, configured rest and uploads have separate timers.
    Character length is an input
    proxy; it does not represent tokenizer counts or a measured total-run ETA.
    """

    def __init__(self, chunks, *, existing_ids, point_id, text_of, clock=None):
        self.clock = time.monotonic if clock is None else clock
        self.total_chunks = self.pending_chunks = self.pending_characters = 0
        self.resumed_chunks = self.empty_chunks = 0
        for chunk in chunks:
            self.total_chunks += 1
            if point_id(chunk) in existing_ids:
                self.resumed_chunks += 1
                continue
            text = text_of(chunk).strip()
            if not text:
                self.empty_chunks += 1
                continue
            self.pending_chunks += 1
            self.pending_characters += len(text)
        self.attempted_chunks = self.input_characters = 0
        self.embedded_chunks = self.failed_chunks = self.uploaded_chunks = 0
        self.embedding_seconds = self.upload_seconds = self.rest_seconds = 0.0
        self.embedding_with_rest_seconds = 0.0
        self.initialization_seconds = None
        self.initialization_failed = self.upload_failed = False
        self.embedding_cycle_failed = False

    def embed(self, texts, call, *, initialize, around=None, rest_ratio=0.0):
        """Time initialization and encoding inside the original resting wrapper.

        Rest remains proportional to the whole first call, including its lazy
        initialization. ETA applies the configured rest ratio to measured
        embedding time; it excludes initialization and its first-call rest.
        """
        if not texts:
            return call()
        if not math.isfinite(rest_ratio) or rest_ratio < 0:
            raise ValueError("rest_ratio must be finite and nonnegative")

        def measured():
            if self.initialization_seconds is None:
                started = self.clock()
                try:
                    initialize()
                except BaseException:
                    self.initialization_failed = True
                    raise
                finally:
                    self.initialization_seconds = self.clock() - started
            started = self.clock()
            self.attempted_chunks += len(texts)
            self.input_characters += sum(len(text) for text in texts)
            try:
                vectors = call()
                if len(vectors) != len(texts):
                    self.failed_chunks += len(texts)
                else:
                    failed = sum(vector is None for vector in vectors)
                    self.failed_chunks += failed
                    self.embedded_chunks += len(texts) - failed
                return vectors
            except BaseException:
                self.failed_chunks += len(texts)
                raise
            finally:
                self.embedding_seconds += self.clock() - started

        initial_time = self.initialization_seconds or 0.0
        embedding_time = self.embedding_seconds
        started = self.clock()
        try:
            return measured() if around is None else around(measured)
        except BaseException:
            self.embedding_cycle_failed = True
            raise
        finally:
            embedding_time = self.embedding_seconds - embedding_time
            initialization_time = (self.initialization_seconds or 0.0) - initial_time
            self.rest_seconds += max(0.0, self.clock() - started - initialization_time - embedding_time)
            self.embedding_with_rest_seconds += embedding_time * (1 + rest_ratio)

    def upload(self, points, call):
        """Count uploaded points only after the original upload returns."""
        started = self.clock()
        try:
            result = call()
            self.uploaded_chunks += len(points)
            return result
        except BaseException:
            self.upload_failed = True
            raise
        finally:
            self.upload_seconds += self.clock() - started

    def snapshot(self):
        remaining = max(0, self.pending_characters - self.input_characters)
        failed = (self.failed_chunks or self.initialization_failed or self.upload_failed
                  or self.embedding_cycle_failed)
        if failed:
            eta, reason = None, "failure_requires_review"
        elif not remaining:
            eta, reason = 0.0, "selected_embedding_input_processed"
        elif not self.input_characters or self.embedding_seconds <= 0:
            eta, reason = None, "embedding_observation_pending"
        else:
            eta, reason = remaining * self.embedding_with_rest_seconds / self.input_characters, "character_length_proportional"
        return {"total_chunks": self.total_chunks, "pending_chunks": self.pending_chunks,
                "resumed_chunks": self.resumed_chunks, "empty_chunks": self.empty_chunks,
                "attempted_chunks": self.attempted_chunks, "embedded_chunks": self.embedded_chunks,
                "failed_chunks": self.failed_chunks, "uploaded_chunks": self.uploaded_chunks,
                "pending_characters": self.pending_characters, "input_characters": self.input_characters,
                "remaining_characters": remaining, "initialization_seconds": self.initialization_seconds,
                "embedding_seconds": self.embedding_seconds, "rest_seconds": self.rest_seconds,
                "embedding_with_rest_seconds": self.embedding_with_rest_seconds,
                "upload_seconds": self.upload_seconds,
                "initialization_failed": self.initialization_failed, "upload_failed": self.upload_failed,
                "embedding_cycle_failed": self.embedding_cycle_failed,
                "eta_embedding_seconds": eta, "eta_basis": reason,
                "eta_scope": "selected_remaining_embedding_including_configured_rest"}

    def format_line(self):
        row = self.snapshot()
        eta = row["eta_embedding_seconds"]
        estimate = "관측 대기" if eta is None else f"대략 {eta:.0f}초 (문자 길이 비례)"
        if row["eta_basis"] == "failure_requires_review":
            estimate = "실패 확인 후 재산정"
        initialization = ("관측 대기" if self.initialization_seconds is None else
                          f"{self.initialization_seconds:.1f}초")
        return (f"진행: 적재 {self.uploaded_chunks} · 재개 {self.resumed_chunks} · 빈 본문 {self.empty_chunks}"
                f" · 임베딩 실패 {self.failed_chunks} / 선택 {self.total_chunks}청크"
                f" | 임베딩 입력 {self.input_characters}/{self.pending_characters}자"
                f" · 모델 초기화 {initialization} · 임베딩 {self.embedding_seconds:.1f}초"
                f" · 휴식 {self.rest_seconds:.1f}초"
                f" · 업로드 {self.upload_seconds:.1f}초 | 남은 임베딩 {estimate}")
