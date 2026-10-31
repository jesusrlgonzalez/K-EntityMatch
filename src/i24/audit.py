"""Evidence preserving auditor for fictional company identity datasets."""
import argparse,csv,json,hashlib,datetime,sqlite3
from collections import Counter
from pathlib import Path
from .identities import valid_lei,valid_country,norm_name
from .matching import candidates,review_bucket

def read(path):
    with Path(path).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def dump(path,header,records):
    with Path(path).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=header,extrasaction='ignore');w.writeheader();w.writerows(records)
def bad_date(x):
    try: datetime.date.fromisoformat(x);return False
    except (TypeError,ValueError):return True

def audit(root,out):
    root=Path(root);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    raw_client=read(root/'client_entities_dirty.csv');raw_ref=read(root/'registry_reference_synthetic.csv');raw_watch=read(root/'sanctions_reference_SYNTHETIC_ONLY.csv');raw_edges=read(root/'relationships_dirty.csv')
    decisions=[];issues=[];clean=[];quarantine=[];review=[];seen=set()
    for pos,r in enumerate(raw_client):
        rid=r['entity_id'];flags=[];warnings=[]
        if rid in seen: flags.append('DUPLICATE_CLIENT_ID')
        seen.add(rid)
        if not r['legal_name'].strip():flags.append('EMPTY_LEGAL_NAME')
        if not valid_country(r['country']):flags.append('INVALID_COUNTRY')
        if r['lei'] and not valid_lei(r['lei']):flags.append('INVALID_LEI')
        if bad_date(r['updated_at']):flags.append('INVALID_UPDATE_DATE')
        if not r['registration_id']:warnings.append('MISSING_REGISTRATION_ID')
        if r['legal_name'] and r['legal_name'].strip()!=r['legal_name']:warnings.append('WHITESPACE_NORMALIZATION_CANDIDATE')
        if flags: status='QUARANTINE';quarantine.append(r)
        elif warnings: status='REVIEW';review.append(r);clean.append(r)
        else: status='CANDIDATE';clean.append(r)
        decisions.append({'row_number':pos+1,'entity_id':rid,'disposition':status,'flags':'|'.join(flags+warnings),'raw_source':'client_entities_dirty.csv'})
        for issue in flags+warnings:issues.append({'row_number':pos+1,'entity_id':rid,'issue':issue,'severity':'BLOCK' if issue in flags else 'REVIEW'})
    refs=[]
    for r in raw_ref+raw_watch:
        # Never silently use invalid-reference entries for identity matches.
        if r['legal_name'] and valid_country(r['country']) and (not r['lei'] or valid_lei(r['lei'])):refs.append(r)
    matching,counts=candidates(clean,refs)
    matches=[]
    for m in matching:
        matches.append({**m,'priority':review_bucket(m),'disposition':'REVIEW_ONLY','legal_determination':'NONE'})
    # Synthetic potential sanctions list matches are leads, not automatic accusations.
    matched_watch={m['client_id'] for m in matches if m['reference_source']=='WATCHLIST_SYNTHETIC' and m['priority']=='HIGH_PRIORITY_REVIEW'}
    matches_gleif={m['client_id'] for m in matches if m['reference_source']=='REGISTRY_SYNTHETIC' and m['priority']=='HIGH_PRIORITY_REVIEW'}
    summary=[]
    for d in decisions:
        eid=d['entity_id']
        st='DATA_QUALITY_BLOCK' if d['disposition']=='QUARANTINE' else ('POTENTIAL_MATCH_REVIEW' if eid in matched_watch else ('IDENTITY_REVIEW' if eid in matches_gleif else 'NO_CANDIDATE_OBSERVED'))
        # NO_CANDIDATE_OBSERVED is *not* a clearance status.
        summary.append({'row_number':d['row_number'],'entity_id':eid,'quality_disposition':d['disposition'],'triage_status':st,'legal_clearance':'NOT_PERFORMED','automated_payment_action':'FORBIDDEN'})
    edge_issues=[];known=set(r['entity_id'] for r in raw_client)
    for edge in raw_edges:
        if edge['from_entity_id'] not in known or edge['to_entity_id'] not in known:
            edge_issues.append({'relation_id':edge['relation_id'],'reason':'ORPHAN_ENDPOINT','evidence_id':edge['evidence_id']})
    # GRAPH is exploratory. Edges with synthetic evidences don't imply legal ownership.
    dump(out/'row_decisions.csv',list(decisions[0]),decisions)
    dump(out/'quality_issues.csv',['row_number','entity_id','issue','severity'],issues)
    dump(out/'quarantine.csv',list(raw_client[0]),quarantine)
    dump(out/'review.csv',list(raw_client[0]),review)
    dump(out/'match_candidates.csv',['client_id','reference_id','reference_source','score','name_similarity','lei_match','registration_match','country_match','country_conflict','priority','disposition','legal_determination'],matches)
    dump(out/'entity_triage.csv',list(summary[0]),summary)
    dump(out/'edge_issues.csv',['relation_id','reason','evidence_id'],edge_issues)
    # typed SQL tables store disposition and match evidence, not raw sensitive source names.
    db=out/'i24_review.sqlite'
    if db.exists():db.unlink()
    with sqlite3.connect(db) as con:
        con.execute('CREATE TABLE triage(row_number INTEGER,entity_id TEXT,quality_disposition TEXT,triage_status TEXT,legal_clearance TEXT,automated_payment_action TEXT)')
        con.executemany('INSERT INTO triage VALUES (?,?,?,?,?,?)',[(int(r['row_number']),r['entity_id'],r['quality_disposition'],r['triage_status'],r['legal_clearance'],r['automated_payment_action']) for r in summary])
        con.execute('CREATE INDEX idx_triage_id ON triage(entity_id)')
        con.execute('CREATE TABLE matches(client_id TEXT,reference_id TEXT,reference_source TEXT,score REAL,priority TEXT,disposition TEXT)')
        con.executemany('INSERT INTO matches VALUES (?,?,?,?,?,?)',[(r['client_id'],r['reference_id'],r['reference_source'],r['score'],r['priority'],r['disposition']) for r in matches])
        con.commit()
    metrics={'dataset_type':'SYNTHETIC_ONLY','screened_against_real_OFAC':False,'matches_have_no_legal_effect':True,'clients_total':len(raw_client),'registry_total':len(raw_ref),'synthetic_watchlist_total':len(raw_watch),'relations_total':len(raw_edges),'quality_counts':dict(sorted(Counter(d['disposition'] for d in decisions).items())),'quality_issues':len(issues),'candidate_pairs':len(matches),'watchlist_high_priority_entities':len(matched_watch),'registry_high_priority_entities':len(matches_gleif),'broken_relation_rows':len(edge_issues),'balanced':len(raw_client)==len(decisions)==sum(1 for d in decisions if d['disposition'] in ('CANDIDATE','REVIEW','QUARANTINE')),'important_limitations':['synthetic labels only','blocking can miss aliases/transliterations','no jurisdiction or ownership determination','no sanctions certification','fuzzy scores not calibrated probabilities','no human reviewer approvals']}
    (out/'quality_report.json').write_text(json.dumps(metrics,indent=2,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf-8')
    return metrics
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',default='DATOS_FUENTES/04_SINTETICOS');p.add_argument('--out',default='outputs/demo');a=p.parse_args();print(json.dumps(audit(a.source,a.out),indent=2))
