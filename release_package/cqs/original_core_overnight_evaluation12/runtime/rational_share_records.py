"""Exact, gold-blind share decoding. No source, answer, file or API lookup.

Raw answer and SQL JSON text must enter through the Decimal parser before any
binary float conversion. Native driver float values have only their actual
shortest JSON decimal encoding available; no lost precision is reconstructed.
Invalid candidate cells remain distinct unmatched rows; valid rows survive.
"""
from decimal import Decimal
from fractions import Fraction
import json
import math

PAIR_SCHEMA = {'type':'object','properties':{'numerator':{'type':'integer'},
    'denominator':{'type':'integer'}},'required':['numerator','denominator'],
    'additionalProperties':False}


def exact_json_loads(content):
    def reject(value):
        raise ValueError('Non-finite JSON number: '+value)
    return json.loads(content, parse_float=Decimal, parse_constant=reject)


def _fraction(value):
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError('nonfinite native share number')
        value=Decimal(str(value))
    if type(value) not in (int,Decimal):
        raise ValueError('share needs a typed finite number')
    if type(value) is Decimal and not value.is_finite():
        raise ValueError('nonfinite share number')
    if type(value) is Decimal:
        parts=value.as_tuple()
        if len(parts.digits)+abs(parts.exponent)>4096:
            raise ValueError('expanded decimal precision exceeds public 4096-digit resource bound')
    return Fraction(value)


def rational(value):
    if type(value) in (int,float,Decimal):
        result=_fraction(value)
    elif type(value) is dict and set(value)=={'numerator','denominator'}:
        n,d=value['numerator'],value['denominator']
        if type(n) is not int or type(d) is not int or d==0:
            raise ValueError('share pair needs integer numerator/nonzero integer denominator')
        result=Fraction(n,d)
    elif type(value) is dict and set(value)=={'percent'}:
        result=_fraction(value['percent'])/100
    else:
        raise ValueError('unsupported exact share encoding')
    if not 0<=result<=1:
        raise ValueError('share outside unit interval')
    return {'numerator':result.numerator,'denominator':result.denominator}


def encoding(contract):
    value=contract.get('collection',{}).get('rational_share_representation')
    if value is None:
        return None
    if (type(value) is not dict or value.get('kind')!='exact_rational_share'
            or value.get('unit')!='one' or type(value.get('field')) is not str):
        raise ValueError('unsupported exact share contract')
    return value


def _tagged(value):
    """JSON-safe candidate identity for an invalid value; never a gold lookup."""
    if type(value) is Decimal:
        return ['decimal',str(value)]
    if type(value) is float and not math.isfinite(value):
        return ['nonfinite_float',repr(value)]
    if type(value) is dict:
        return ['object',[[str(k),_tagged(v)] for k,v in sorted(value.items(),key=lambda x:str(x[0]))]]
    if type(value) is list:
        return ['array',[_tagged(v) for v in value]]
    return [type(value).__name__,value]


def invalid(value):
    # This reserved shape cannot satisfy PAIR_SCHEMA or rational().
    return {'__invalid_exact_share__':_tagged(value)}


def normalize_records(contract,records,*,gold=False):
    spec=encoding(contract)
    if spec is None:
        return records
    if type(records) is not list:
        raise ValueError('answer records must be a list')
    field=spec['field']; result=[]
    for row in records:
        if type(row) is not dict:
            if gold:
                raise ValueError('nonobject gold share row')
            result.append({field:invalid(row)})
            continue
        converted=dict(row)
        if field in row:
            try:
                converted[field]=rational(row[field])
            except (ValueError,TypeError,ArithmeticError) as error:
                if gold:
                    raise ValueError('invalid gold share') from error
                # Preserve our own marker rather than recursively retagging it.
                converted[field]=(row[field] if type(row[field]) is dict
                    and set(row[field])=={'__invalid_exact_share__'} else invalid(row[field]))
        elif gold:
            raise ValueError('missing gold share field')
        result.append(converted)
    return result


def parse_retrieval_answer(contract,content,legacy_parser):
    spec=encoding(contract)
    if spec is None:
        return legacy_parser(content)
    exact=exact_json_loads(content)
    if (type(exact) is not dict or type(exact.get('records')) is not list
            or type(exact.get('abstain')) is not bool or type(exact.get('complete')) is not bool):
        raise ValueError('answer needs records array and abstain/complete booleans')
    if exact['abstain'] and exact['records']:
        raise ValueError('abstain true conflicts with nonempty records')
    # Preserve ordinary JSON decoding of all auxiliaries. Only the declared
    # share field is read from the lossless Decimal parse.
    ordinary=json.loads(content)
    field=spec['field']; rows=[]
    for raw,shown in zip(exact['records'],ordinary['records']):
        if type(raw) is not dict:
            rows.append({field:invalid(raw)})
            continue
        row=dict(shown)
        if field in raw:
            row[field]=normalize_records(contract,[{field:raw[field]}])[0][field]
        rows.append(row)
    ordinary['records']=rows
    return ordinary


def normalize_sql_records(contract,rows):
    spec=encoding(contract)
    if spec is None:
        return rows
    field=spec['field']; result=[]
    for raw in rows:
        row=dict(raw) if type(raw) is dict else raw
        if type(row) is dict and field in row and type(row[field]) is str:
            try:
                row[field]=exact_json_loads(row[field])
            except (ValueError,TypeError):
                row[field]=invalid(raw[field])
        result.extend(normalize_records(contract,[row]))
    return result


def public_representation(contract):
    spec=encoding(contract)
    if spec is None:
        return None
    return {'field':spec['field'],'kind':'exact_rational_share','unit':'one',
        'canonical_json_schema':PAIR_SCHEMA,
        'equivalent_input_forms':['integer numerator/denominator object',
            'finite exact JSON number in units of one','object with one percent numeric property'],
        'integer_pair_keys':['numerator','denominator'],'percent_object_key':'percent',
        'integer_pair_denominator':'nonzero; sign normalized',
        'decimal_resource_bound':'coefficient digits plus absolute base-10 exponent at most 4096; no huge exponent expansion',
        'range':'zero through one inclusive (zero through one hundred for explicit percent)',
        'exactness':'Decimals mean their exact written value. No rounding tolerance. Use an integer pair for a nonterminating share.',
        'partial_rows':'Each malformed candidate value remains one unmatched row; valid rows retain matching credit.'}
