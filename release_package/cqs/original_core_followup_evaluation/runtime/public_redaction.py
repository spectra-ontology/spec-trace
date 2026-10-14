"""Public-copy privacy projection; immutable private originals remain untouched.

Mask provider account/key finance in ERROR messages/metadata and explicit private
account-query responses. Never mask experiment usage.cost/tokens, generation or
execution parameters, error status/code/limit_source/provider/choices, or general
timestamps. Return JSON pointers and reasons, never sensitive original values.
"""
import copy
import re

FINANCE_KEYS={'limit_usd','spend_usd','balance_usd','balance','credits','credits_remaining',
              'remaining_credits','total_credits','total_usage','limit_remaining',
              'remaining_usd','resets_at','reset_at','key_limit_usd','key_spend_usd',
              'account_balance_usd','account_usage_usd'}
ACCOUNT_ENDPOINT=re.compile(r'https?://(?:www\.)?openrouter\.ai/api/v1/(?:key|credits)(?:[/?#]|$)',re.I)
MONEY=re.compile(r'\$\s*[-+]?\d|\b(?:balance|spent|spend|remaining|limit|credits)\s*[:=]\s*[-+]?\d',re.I)
OPENROUTER_KEY=re.compile(r'sk-or-v1-[A-Za-z0-9_-]{20,}')
SENTINEL='[REDACTED_PRIVATE_ACCOUNT_FINANCE]'


def escape(key):return str(key).replace('~','~0').replace('/','~1')


def account_query_shape(value):
    if not isinstance(value,dict):return False
    if any(isinstance(value.get(k),str) and ACCOUNT_ENDPOINT.search(value[k])
           for k in ['url','endpoint','request_url','api_url']):return True
    data=value.get('data')
    return bool(isinstance(data,dict) and ('limit_remaining' in data
                 or {'total_credits','total_usage'}<=set(data)
                 or {'is_free_tier','usage','limit'}<=set(data)))


def redact_json(value):
    """Return a copied JSON value and [{json_pointer,reason}], preserving originals."""
    result=copy.deepcopy(value);redactions=[]
    def mask(obj,key,path,reason,replacement=SENTINEL):
        if obj[key]==replacement:return
        obj[key]=replacement;redactions.append({'json_pointer':path+'/'+escape(key),'reason':reason})
    def walk(obj,path=''):
        if isinstance(obj,list):
            for index,item in enumerate(obj):walk(item,path+'/'+str(index))
            return
        if not isinstance(obj,dict):return
        private_account=account_query_shape(obj)
        if private_account:
            # Account GET data is not model usage or a benchmark prediction.
            for key in ['data','response_data','account','key_info','credits_info']:
                if key in obj:mask(obj,key,path,'private_provider_account_query')
            response=obj.get('response')
            if isinstance(response,dict) and 'data' in response:
                mask(response,'data',path+'/response','private_provider_account_query')
        error=obj.get('error')
        if isinstance(error,dict):
            metadata=error.get('metadata')
            source=metadata.get('limit_source') if isinstance(metadata,dict) else None
            if isinstance(metadata,dict):
                for key in list(metadata):
                    if key in FINANCE_KEYS:
                        mask(metadata,key,path+'/error/metadata','provider_account_key_finance_error_metadata')
            message=error.get('message')
            if isinstance(message,str) and MONEY.search(message):
                neutral=('Provider rejected the request before generation because the API key spend limit was reached.'
                         if source=='openrouter_key_limit' else
                         'Provider rejected the request before generation because of an in-flight budget limit.'
                         if source=='openrouter_in_flight_budget' else
                         'Provider error message with private account financial details redacted.')
                mask(error,'message',path+'/error','provider_account_key_finance_error_message',neutral)
        for key,item in list(obj.items()):walk(item,path+'/'+escape(key))
    walk(result)
    return result,redactions


def scan_credentials(value,known_secrets=()):
    """Return pointer/kind only; no secret, prefix, hash or value is emitted.

Known exact secrets must be passed explicitly by the caller. This module never
loads environment variables, credential files or account state on its own.
"""
    secrets=[s for s in known_secrets if isinstance(s,str) and len(s)>=8];findings=[]
    def walk(obj,path='',key=None):
        if isinstance(obj,dict):
            for name,item in obj.items():walk(item,path+'/'+escape(name),str(name))
        elif isinstance(obj,list):
            for index,item in enumerate(obj):walk(item,path+'/'+str(index),key)
        elif isinstance(obj,str):
            kinds=[]
            if any(s in obj for s in secrets):kinds.append('exact_known_credential')
            if OPENROUTER_KEY.search(obj):kinds.append('openrouter_key_format')
            if key and key.lower()=='authorization' and obj.strip() and not obj.startswith('[REDACTED'):
                kinds.append('authorization_header')
            for kind in kinds:findings.append({'json_pointer':path,'kind':kind})
    walk(value)
    return findings
