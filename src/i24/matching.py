"""Candidate generation and evidence-based triage. NOT automated sanctions clearance."""
from collections import defaultdict
from rapidfuzz.fuzz import ratio,token_sort_ratio
from .identities import norm_name,token_key

def score_pair(a,b):
    name=ratio(norm_name(a.get('legal_name')),norm_name(b.get('legal_name')))/100
    token=token_sort_ratio(norm_name(a.get('legal_name')),norm_name(b.get('legal_name')))/100
    text=round(max(name,token),4)
    lei_match=bool(a.get('lei') and b.get('lei') and a['lei']==b['lei'])
    reg_match=bool(a.get('registration_id') and b.get('registration_id') and a['registration_id']==b['registration_id'])
    country_match=bool(a.get('country') and b.get('country') and a['country']==b['country'])
    country_conflict=bool(a.get('country') and b.get('country') and a['country']!=b['country'])
    # Strong identity is a *review lead*, not proof of OFAC match.
    score=max(.995 if lei_match else 0,.970 if reg_match else 0, .78*text+(.12 if country_match else 0))
    return {'score':round(min(score,1),4),'name_similarity':text,'lei_match':lei_match,'registration_match':reg_match,'country_match':country_match,'country_conflict':country_conflict}

def candidates(clients,reference,max_per_client=15):
    # Block on name-prefix token (avoid exhaustive cross join); supplement via strong identifiers.
    by_token=defaultdict(list);by_lei=defaultdict(list);by_reg=defaultdict(list)
    for r in reference:
        if token_key(r['legal_name']):by_token[token_key(r['legal_name'])].append(r)
        if r.get('lei'):by_lei[r['lei']].append(r)
        if r.get('registration_id'):by_reg[r['registration_id']].append(r)
    scored=[];counts={}
    for a in clients:
        selected={}
        for b in by_token.get(token_key(a['legal_name']),[]) + by_lei.get(a.get('lei',''),[]) + by_reg.get(a.get('registration_id',''),[]):
            selected[b['entity_id']]=b
        local=[]
        for b in selected.values():
            s=score_pair(a,b)
            if s['score']>=.52 or s['lei_match'] or s['registration_match']:
                local.append({'client_id':a['entity_id'],'reference_id':b['entity_id'],'reference_source':b['source'],**s})
        local.sort(key=lambda x:(-x['score'],x['reference_id']))
        counts[a['entity_id']]=len(local)
        scored.extend(local[:max_per_client])
    return scored,counts

def review_bucket(item):
    if item['lei_match'] or item['registration_match'] or item['score']>=.88: return 'HIGH_PRIORITY_REVIEW'
    if item['score']>=.67:return 'REVIEW'
    return 'WEAK_CANDIDATE'
