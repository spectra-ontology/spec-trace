#!/usr/bin/env python3
"""Pinned OpenRouter transport. No gold data or benchmark scoring lives here."""
import hashlib
import json
import os
from pathlib import Path
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

MODEL = 'anthropic/claude-opus-4.8'
PROVIDER = 'Anthropic'
ENDPOINT = 'https://openrouter.ai/api/v1/chat/completions'
PROMPT_USD_PER_TOKEN = 0.000005
COMPLETION_USD_PER_TOKEN = 0.000025


def utc():
    return datetime.now(timezone.utc).isoformat()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


class OpenRouterCaller:
    """One identical transport retry only; never retry based on answer quality.

    Approximate reservation is a spending guard, not a reported actual cost.
    Raw responses retain authoritative usage/cost when supplied by OpenRouter.
    """
    def __init__(self, run_dir, api_key=None, budget_usd=250.0, timeout=180):
        self.run_dir = Path(run_dir)
        self.api_key = api_key or os.environ.get('OPENROUTER_API_KEY')
        if not self.api_key:
            raise RuntimeError('OPENROUTER_API_KEY is not configured')
        self.budget_usd, self.timeout = float(budget_usd), timeout
        self.lock = threading.Lock()
        self.reserved, self.actual_cost, self.calls = 0.0, 0.0, 0
        self.unknown_cost_attempts = 0

    def call(self, request_id, messages, max_tokens=8192):
        safe_id = str(request_id)
        if not safe_id or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.' for c in safe_id):
            raise ValueError('request ID must be a safe opaque filename')
        path = self.run_dir / 'calls' / safe_id
        request = {'model': MODEL, 'messages': messages, 'max_tokens': int(max_tokens),
                   'provider': {'only': [PROVIDER], 'allow_fallbacks': False,
                                'require_parameters': True},
                   'response_format': {'type': 'json_object'},
                   'reasoning': {'enabled': False}, 'stream': False}
        serialized = json.dumps(request, ensure_ascii=False).encode()
        estimated = (sum(len(m['content']) for m in messages) / 3.0 * PROMPT_USD_PER_TOKEN
                     + max_tokens * COMPLETION_USD_PER_TOKEN)
        with self.lock:
            if self.reserved + estimated > self.budget_usd:
                return {'ok': False, 'error': 'frozen_budget_guard', 'content': None,
                        'usage': {}, 'provider': None, 'finish_reason': None}
            self.reserved += estimated
        request_path = path.with_suffix('.request.json')
        if request_path.exists():
            raise ValueError('request ID already exists; result-based regeneration forbidden')
        dump(request_path, {'request_id': safe_id, 'created_utc': utc(), 'payload': request,
                            'payload_sha256': hashlib.sha256(serialized).hexdigest(),
                            'estimated_reservation_usd': estimated,
                            'authorization_header_omitted': True})
        started = time.monotonic()
        outcome = None
        known_cost = 0.0
        unknown = 0
        attempts = []
        for attempt in range(2):
            response_path = path.with_suffix('.attempt' + str(attempt) + '.response.json')
            began = time.monotonic()
            status = None
            retryable = False
            raw = None
            try:
                req = urllib.request.Request(ENDPOINT, serialized,
                    {'Authorization': 'Bearer ' + self.api_key, 'Content-Type': 'application/json'}, method='POST')
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    status = response.status
                    body = response.read().decode('utf-8')
                raw = json.loads(body)
                dump(response_path, {'request_id': safe_id, 'attempt': attempt, 'http_status': status,
                                     'elapsed_seconds': time.monotonic()-began, 'received_utc': utc(),
                                     'response': raw})
                usage = raw.get('usage') or {}
                if isinstance(usage.get('cost'), (int, float)):
                    known_cost += usage['cost']
                else:
                    unknown += 1
                with self.lock:
                    self.calls += 1
                if 'error' in raw or not raw.get('choices'):
                    outcome = {'ok': False, 'error': 'provider_error', 'content': None,
                               'usage': usage, 'provider': raw.get('provider'), 'finish_reason': None}
                else:
                    choice = raw['choices'][0]
                    provider = raw.get('provider')
                    valid = provider == PROVIDER and raw.get('model') == MODEL
                    outcome = {'ok': valid, 'error': None if valid else 'pinned_model_or_provider_mismatch',
                               'content': choice.get('message', {}).get('content'),
                               'usage': usage, 'provider': provider, 'model': raw.get('model'),
                               'finish_reason': choice.get('finish_reason'), 'generation_id': raw.get('id')}
            except urllib.error.HTTPError as exc:
                status = exc.code
                body = exc.read().decode('utf-8', errors='replace')
                try:
                    raw = json.loads(body)
                except ValueError:
                    raw = {'non_json_body': body}
                dump(response_path, {'request_id': safe_id, 'attempt': attempt, 'http_status': status,
                    'elapsed_seconds': time.monotonic()-began, 'response': raw})
                retryable = status == 429 or 500 <= status < 600
                outcome = {'ok': False, 'error': 'http_' + str(status), 'content': None,
                           'usage': {}, 'provider': None, 'finish_reason': None}
            except (OSError, TimeoutError, ValueError) as exc:
                retryable = not isinstance(exc, ValueError)
                unknown += 1
                dump(response_path, {'request_id': safe_id, 'attempt': attempt,
                    'elapsed_seconds': time.monotonic()-began, 'error_type': type(exc).__name__,
                    'error': str(exc).replace(self.api_key, '[redacted]')})
                outcome = {'ok': False, 'error': 'transport_or_response_error', 'content': None,
                           'usage': {}, 'provider': None, 'finish_reason': None}
            attempts.append({'attempt': attempt, 'http_status': status,
                             'response_path': str(response_path), 'retryable': retryable})
            if not retryable or attempt == 1:
                break
            time.sleep(2)
        outcome.update(request_path=str(request_path), response_path=str(response_path),
                       elapsed_seconds=time.monotonic()-started, attempts=attempts,
                       known_actual_cost_usd=known_cost, unknown_cost_attempts=unknown)
        dump(path.with_suffix('.outcome.json'), outcome)
        with self.lock:
            self.actual_cost += known_cost
            self.unknown_cost_attempts += unknown
            self.reserved -= estimated
            self.reserved += known_cost if not unknown else max(known_cost, estimated)
            dump(self.run_dir / 'usage.json', self.summary_unlocked())
        return outcome

    def summary_unlocked(self):
        return {'model': MODEL, 'provider': PROVIDER, 'received_response_calls': self.calls,
                'known_actual_cost_usd': self.actual_cost,
                'unknown_cost_attempts': self.unknown_cost_attempts,
                'guard_reserved_or_spent_usd': self.reserved, 'budget_guard_usd': self.budget_usd,
                'all_actual_costs_known': self.unknown_cost_attempts == 0}

