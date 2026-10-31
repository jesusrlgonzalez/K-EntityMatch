"""Synthetic alias stress set. A deliberately failing retrieval diagnostic, not a production claim."""
import json
from pathlib import Path
from .matching import candidates
CASES=[
    ('München Alpha GmbH','Munchen Alpha GmbH','DE'),
    ('Muenchen Alpha GmbH','München Alpha GmbH','DE'),
    ('ООО Альфа','OOO Alfa','RU'),
    ('Global Steel Ltd','G. Steel Ltd','GB'),
    ('Aurora Test LLC','Aurora Test Inc','US'),
    ('Étoile Holdings','Etoile Holdings','FR'),
    ('Shenzhen Wei','Shen Zhen Wei','CN'),
    ('Délta Logistics','Delta Logistics','MX'),
    ('Naviera Sur','Sur Naviera','ES'),
]
def evaluate(output=None):
    cls=[{'entity_id':f'TEST-{i}','legal_name':a,'country':ct,'lei':'','registration_id':''} for i,(a,b,ct) in enumerate(CASES)]
    ref=[{'entity_id':f'ALIAS-{i}','legal_name':b,'country':ct,'lei':'','registration_id':'','source':'SYNTHETIC_ALIAS'} for i,(a,b,ct) in enumerate(CASES)]
    found,_=candidates(cls,ref)
    pairs={(r['client_id'],r['reference_id']) for r in found}
    retrieved=[{'case':i,'client_name':a,'reference_name':b,'retrieved':(f'TEST-{i}',f'ALIAS-{i}') in pairs} for i,(a,b,ct) in enumerate(CASES)]
    count=sum(r['retrieved'] for r in retrieved)
    result={'kind':'SYNTHETIC_STRESS_NOT_REAL_BENCHMARK','expected_true_alias_pairs':len(CASES),'retrieved_correct_alias_pairs':count,'alias_candidate_recall':round(count/len(CASES),4),'warning':'Blocking first token can miss transliterations, initials and word order. REQUIRE negative/hard positive real gold before G3.','cases':retrieved}
    if output:
        p=Path(output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf-8')
    return result
if __name__=='__main__':
    print(json.dumps(evaluate('outputs/demo/adversarial_alias_report.json'),indent=2,ensure_ascii=False))
