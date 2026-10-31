import csv,json,sqlite3,hashlib
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from i24.identities import valid_lei,make_lei,norm_name,valid_country,token_key
from i24.matching import score_pair,candidates,review_bucket
from i24.fixture import generate
from i24.audit import audit,read
from i24.gates import assess,GATES
from i24.graph import build_graph,evidence_neighborhood
from i24.adapters import gleif_record_to_candidate,ofac_requires_official_schema_mapping
import i24.api as api

@pytest.fixture(scope='module')
def work(tmp_path_factory):
    base=tmp_path_factory.mktemp('i24fixture')
    src=base/'source';out=base/'out'
    gen=generate(src);rep=audit(src,out)
    return src,out,gen,rep

@pytest.mark.parametrize('name,expected',[
    ('München GmbH','munchen'),('  Aurora   Systems  LLC','aurora systems'),
    ('ÉXITO, S.A.','exito s a'),('',''),('A\tB','a b')])
def test_normalization_non_destructive(name,expected):
    assert norm_name(name)==expected

@pytest.mark.parametrize('seed',[1,5,25,100,9981,435101,900000])
def test_lei_generation_valid(seed):assert valid_lei(make_lei(seed))
@pytest.mark.parametrize('lei',['','A'*19,'!'+ '0'*19,'52990000000000000000','1234XX',None])
def test_bad_lei_rejected(lei):assert not valid_lei(lei)
@pytest.mark.parametrize('country,expected',[('MX',True),('US',True),('DE',True),('ZZZ',False),('',False),('mx',False)])
def test_country_shape(country,expected):assert valid_country(country)==expected

def test_fixture_sizes_and_provenance(work):
    src,_,gen,_=work
    assert (gen['clients'],gen['registry'],gen['watchlist'],gen['relations'],gen['injections'])==(640,620,180,190,72)
    meta=json.loads((src/'SOURCE_PROVENANCE.json').read_text())
    assert meta['real_ofac_data'] is False and meta['real_gleif_data'] is False

def test_conservation(work):
    src,out,gen,report=work
    assert report['balanced'] is True
    assert sum(report['quality_counts'].values())==gen['clients']==len(read(out/'row_decisions.csv'))

def test_all_dispositions_fail_open_prevented(work):
    _,out,_,_=work
    assert {'CANDIDATE','QUARANTINE','REVIEW'}=={r['disposition'] for r in read(out/'row_decisions.csv')}
    assert all(r['legal_clearance']=='NOT_PERFORMED' and r['automated_payment_action']=='FORBIDDEN' for r in read(out/'entity_triage.csv'))

def test_raw_file_immutability(work):
    src,out,_,_=work
    f=src/'client_entities_dirty.csv';before=hashlib.sha256(f.read_bytes()).digest()
    audit(src,out)
    assert hashlib.sha256(f.read_bytes()).digest()==before

def test_nonempty_quarantine_and_issues(work):
    _,out,_,_=work
    assert len(read(out/'quarantine.csv'))>=30
    issues={r['issue'] for r in read(out/'quality_issues.csv')}
    assert {'INVALID_LEI','EMPTY_LEGAL_NAME','INVALID_COUNTRY','DUPLICATE_CLIENT_ID','INVALID_UPDATE_DATE'}<=issues

def test_scripted_sanctions_hits_are_only_simulated(work):
    src,out,_,rep=work
    assert rep['watchlist_high_priority_entities']==12
    assert all(r['source']=='WATCHLIST_SYNTHETIC' and r['status']=='TEST_ONLY' for r in read(src/'sanctions_reference_SYNTHETIC_ONLY.csv'))
    assert all(r['disposition']=='REVIEW_ONLY' and r['legal_determination']=='NONE' for r in read(out/'match_candidates.csv'))

def test_match_strong_key_not_legal_match():
    a={'legal_name':'Test Example SA','country':'DE','lei':'','registration_id':'A2'}
    b={'legal_name':'Different Entity','country':'DE','lei':'','registration_id':'A2'}
    s=score_pair(a,b)
    assert s['registration_match'] and review_bucket(s)=='HIGH_PRIORITY_REVIEW'

def test_different_legal_name_will_not_be_exonerated():
    a={'legal_name':'A','country':'MX','lei':'','registration_id':'A'}
    b={'legal_name':'Unrelated','country':'US','lei':'','registration_id':'B'}
    assert score_pair(a,b)['score']<.7

def test_country_conflict_preserved():
    a={'legal_name':'Aurora Holdings','country':'MX','lei':'','registration_id':''}
    b={'legal_name':'Aurora Holdings','country':'DE','lei':'','registration_id':''}
    assert score_pair(a,b)['country_conflict'] is True

def test_candidate_no_proof_of_absence(work):
    _,out,_,_=work
    for r in read(out/'entity_triage.csv'):
        assert r['triage_status'] !='CLEAR'

def test_no_missing_graph_edges_accepted(work):
    src,_,_,rep=work
    clients={r['entity_id'] for r in read(src/'client_entities_dirty.csv')}
    graph,bad=build_graph(src/'relationships_dirty.csv',clients)
    assert len(bad)==rep['broken_relation_rows']==8
    assert all(graph.has_node(x) for x in clients)
    assert evidence_neighborhood(graph,'CUS-00010')

def test_sql_integrity(work):
    _,out,gen,_=work
    with sqlite3.connect(out/'i24_review.sqlite') as c:
        assert c.execute('SELECT COUNT(*) FROM triage').fetchone()[0]==gen['clients']
        assert c.execute("SELECT COUNT(*) FROM triage WHERE legal_clearance != 'NOT_PERFORMED'").fetchone()[0]==0

def test_built_risk_report_has_no_real_ofac_screening(work):
    _,_,_,rep=work
    assert rep['screened_against_real_OFAC'] is False
    assert rep['matches_have_no_legal_effect'] is True

@pytest.mark.parametrize('gate',GATES)
def test_gates_fail_closed_without_evidence(gate):assert assess(gate,{})=='BLOCK'

def test_authority_cannot_self_approve():
    good={'approved_by_owner':'same','independent_reviewer':'same','reviewer_is_distinct':True,'evidence_hash':'sha256:abc','source_authorized':True,'scope_accepted':True,'negative_findings_resolved':True,'synthetic_only':False}
    assert assess('G1',good)=='BLOCK'

def test_synthetic_not_approved():
    ev={'approved_by_owner':'owner','independent_reviewer':'reviewer','reviewer_is_distinct':True,'evidence_hash':'sha256:abc','source_authorized':True,'scope_accepted':True,'negative_findings_resolved':True,'synthetic_only':True}
    assert assess('G1',ev)=='BLOCK'

def test_business_must_have_signed_pilot():
    ev={'approved_by_owner':'owner','independent_reviewer':'reviewer','reviewer_is_distinct':True,'evidence_hash':'sha256:abc','source_authorized':True,'scope_accepted':True,'negative_findings_resolved':True,'synthetic_only':False}
    assert assess('G5_BUSINESS',ev)=='BLOCK'
    ev['business_pilot_signed']=True
    assert assess('G5_BUSINESS',ev)=='ELIGIBLE_FOR_EXTERNAL_AUDIT_NOT_APPROVED'

def test_unsupported_ofac_adapter_fails_closed():
    with pytest.raises(RuntimeError):ofac_requires_official_schema_mapping()

def test_gleif_minimum_fields_and_no_ownership_invention():
    lei=make_lei(9999)
    v={'id':lei,'attributes':{'lei':lei,'entity':{'legalName':{'name':'Fictional Entity Ltd'},'legalAddress':{'country':'GB'}}}}
    ref=gleif_record_to_candidate(v)
    assert ref['entity_id']==lei and 'ownership' not in ref
    with pytest.raises(ValueError):gleif_record_to_candidate({'attributes':{}})

def test_api_readonly_and_no_clear(work,monkeypatch):
    _,out,_,_=work
    monkeypatch.setattr(api,'DB',out/'i24_review.sqlite')
    client=TestClient(api.app)
    health=client.get('/health');assert health.status_code==200 and health.json()['is_sanctions_certification'] is False
    r=client.get('/entities/CUS-00000')
    assert r.status_code==200 and r.json()['legal_clearance']=='NOT_PERFORMED'
    m=client.get('/matches/CUS-00470')
    assert m.status_code==200 and m.json()['legal_clearance']=='NOT_PERFORMED'
    assert client.post('/entities/CUS-00000').status_code==405
    assert client.get('/entities/DOES-NOT-EXIST').status_code==404

def test_zero_label_leakage(work):
    src,out,_,_=work
    raw_head=next(csv.reader((src/'client_entities_dirty.csv').open()))
    match_head=next(csv.reader((out/'match_candidates.csv').open()))
    assert not any('gold' in col or 'injection' in col or 'target' in col for col in raw_head+match_head)

def test_no_unauthorized_private_data_dir():
    assert not Path('DATOS_FUENTES/03_EMPRESARIALES_AUTORIZADOS/raw_local').exists()


def test_hard_alias_recall_not_perfect():
    from i24.adversarial import evaluate
    r=evaluate()
    assert r['expected_true_alias_pairs']==9
    assert r['retrieved_correct_alias_pairs']<9
    assert len([x for x in r['cases'] if not x['retrieved']])>=2


def test_adversarial_fixture_is_not_official():
    from i24.adversarial import evaluate
    assert evaluate()['kind']=='SYNTHETIC_STRESS_NOT_REAL_BENCHMARK'
