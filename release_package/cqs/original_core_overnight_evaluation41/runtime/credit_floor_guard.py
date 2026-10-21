"""Operational credit admission only; no prompt, parser or scoring changes."""
import json
import math
import threading
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

class CreditFloorGuard:
    def __init__(self, api_key, run_dir, floor_usd=5.0):
        self.api_key = api_key
        self.run_dir = Path(run_dir)
        self.floor = float(floor_usd)
        self.lock = threading.Lock()
        self.initial_remaining = None
        self.charged_upper = 0.0

    def _get(self, suffix):
        req = urllib.request.Request('https://openrouter.ai/api/v1/' + suffix,
            headers={'Authorization': 'Bearer ' + self.api_key})
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)['data']

    def _record(self, value):
        self.run_dir.mkdir(parents=True, exist_ok=True)
        value['observed_utc'] = datetime.now(timezone.utc).isoformat()
        with (self.run_dir / 'credit_floor_guard.jsonl').open('a') as out:
            out.write(json.dumps(value, ensure_ascii=False) + '\n')

    def run(self, request_id, messages, max_tokens, callback):
        # Serialize admission, transport and settlement. Another worker cannot
        # admit against a stale balance while this request is in flight.
        with self.lock:
            account, key = self._get('credits'), self._get('key')
            account_remaining = float(account['total_credits']) - float(account['total_usage'])
            key_remaining = key.get('limit_remaining')
            if key_remaining is None and key.get('limit') is not None:
                key_remaining = float(key['limit']) - float(key['usage'])
            observed = min(account_remaining, float(key_remaining)) if key_remaining is not None else account_remaining
            if not math.isfinite(observed):
                raise RuntimeError('Nonfinite credit balance; no paid dispatch')
            if self.initial_remaining is None:
                self.initial_remaining = observed
            usable = min(observed, self.initial_remaining - self.charged_upper)
            # UTF-8 bytes plus 4096 framing tokens is deliberately more
            # conservative than chars/3. Use the largest verified input/cache
            # price (10 USD/M) and completion price25 USD/M, two possible
            # identical transport attempts, and an additional25% margin.
            prompt_bound = sum(len(json.dumps(m, ensure_ascii=False).encode('utf-8')) for m in messages) + 4096
            attempt_bound = prompt_bound * .000010 + int(max_tokens) * .000025
            reservation = 2 * attempt_bound * 1.25
            record = {'request_id': str(request_id), 'account_remaining_usd': account_remaining,
                'key_remaining_usd': key_remaining, 'floor_usd': self.floor,
                'effective_remaining_usd': usable, 'two_attempt_reservation_usd': reservation,
                'prompt_byte_plus_framing_bound': prompt_bound,
                'max_completion_tokens': int(max_tokens), 'headers_saved': False}
            if usable - reservation < self.floor:
                record['decision'] = 'STOP_BEFORE_PAID_CALL'
                self._record(record)
                return {'ok': False, 'error': 'USD5_credit_floor_guard', 'content': None,
                    'usage': {}, 'provider': None, 'finish_reason': None}
            record['decision'] = 'ADMIT'
            self._record(record)
            try:
                outcome = callback()
            except BaseException:
                self.charged_upper += reservation
                self._record({'request_id': str(request_id), 'decision': 'UNKNOWN_CHARGE_RESERVED',
                    'charged_upper_usd': self.charged_upper})
                raise
            known = outcome.get('known_actual_cost_usd', 0)
            unknown = outcome.get('unknown_cost_attempts', 0)
            # A failed HTTP transport may have no usage field even when its
            # upstream cost is unknown; preserve a full two-attempt reserve.
            failed_transports = sum(a.get('http_status') != 200 for a in outcome.get('attempts', []))
            unknown = max(unknown, failed_transports)
            charge = float(known) if not unknown else max(float(known), reservation)
            self.charged_upper += charge
            self._record({'request_id': str(request_id), 'decision': 'SETTLED',
                'known_actual_cost_usd': known, 'unknown_cost_attempts': unknown,
                'charged_upper_usd': self.charged_upper})
            return outcome
