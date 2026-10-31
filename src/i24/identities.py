"""Normalization is for candidate generation only: never overwrites original legal names."""
import re,unicodedata
from decimal import Decimal
SUFFIXES={'SA','S A','SA DE CV','S DE RL','LLC','LTD','LIMITED','GMBH','INC','INCORPORATED','CORP','CORPORATION','AG','BV','SAS','PLC'}
ALPH='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
def norm_name(value):
    if not isinstance(value,str): return ''
    norm=unicodedata.normalize('NFKD',value).casefold()
    norm=''.join(c for c in norm if not unicodedata.combining(c))
    norm=re.sub(r'[^a-z0-9 ]+',' ',norm)
    norm=re.sub(r'\s+',' ',norm).strip()
    # Suffix removal only for comparison view, not matching authority
    tokens=norm.upper().split()
    while tokens and tokens[-1] in {'SA','LLC','LTD','GMBH','INC','AG','SAS','PLC','BV','CORP'}: tokens.pop()
    return ' '.join(tokens).lower()
def token_key(value):
    parts=norm_name(value).split()
    return parts[0] if parts else ''
def valid_lei(lei):
    if not isinstance(lei,str) or len(lei)!=20 or any(c not in ALPH for c in lei): return False
    if not lei[:18].isalnum():return False
    ds=''.join(str(int(c,36)) if c.isalpha() else c for c in lei)
    return int(ds)%97==1
def make_lei(seed):
    base='529900'+format(seed,'012d') # 18 chars
    assert len(base)==18
    expanded=''.join(str(int(c,36)) if c.isalpha() else c for c in base)
    check=98-(int(expanded+'00')%97)
    result=base+f'{check:02d}'
    assert valid_lei(result)
    return result
def valid_country(code): return isinstance(code,str) and bool(re.fullmatch(r'[A-Z]{2}',code))
