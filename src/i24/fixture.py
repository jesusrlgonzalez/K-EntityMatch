"""All names and watchlist claims below are FICTITIOUS synthetic test material."""
import csv,random,json
from pathlib import Path
from .identities import make_lei
NAMES=['Aurora','Solstice','Ginkgo','Cobalt','Arcadia','Birch','Sapphire','Dove','Ember','Helio','Primera','Delta','Marea','Comet','Umbral','Vega','Equinox','Monsoon','Celadon','Atlas','Brisa','Nebula','Lunar','Marisma','Orion','Nimbo','Mistral','Albatross','Ceiba','Zenith']
IND=['Analytics','Industries','Logistics','Systems','Materials','Trading','Capital','Consulting','Technology','Holdings']
COUNTRIES=['MX','DE','US','FR','CA','BR','NL','ES','GB','JP']
def dump(path,header,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=header);w.writeheader();w.writerows(data)
def generate(root):
    r=random.Random(20261015);root=Path(root);root.mkdir(parents=True,exist_ok=True)
    clients=[]; registry=[]; watch=[]; relations=[]; injections=[]; gold=[]
    for i in range(640):
        c={'entity_id':f'CUS-{i:05}', 'legal_name':f'{NAMES[i%30]} {IND[(i//30)%10]} {i:04} S.A.', 'country':COUNTRIES[i%10], 'lei':make_lei(10000+i) if i%5!=0 else '', 'registration_id':f'REG-{i:06}', 'updated_at':'2026-10-01','source':'CLIENT_SYNTHETIC'}
        clients.append(c)
        if i<460:
            registry.append({'entity_id':f'REF-{i:05}','legal_name':c['legal_name'],'country':c['country'],'lei':c['lei'],'registration_id':c['registration_id'],'updated_at':'2026-10-01','source':'REGISTRY_SYNTHETIC'})
            gold.append([c['entity_id'],f'REF-{i:05}','positive','same scripted identity'])
    # Non-registry reference identities and names not matching clients
    for i in range(460,620):
        registry.append({'entity_id':f'REF-{i:05}','legal_name':f'Nadir {IND[i%10]} Ref{i:05} Ltd','country':COUNTRIES[(i+3)%10],'lei':make_lei(31000+i),'registration_id':f'RFX-{i:06}','updated_at':'2026-10-02','source':'REGISTRY_SYNTHETIC'})
    for i in range(180):
        watch.append({'entity_id':f'WL-{i:04}','legal_name':f'Testwatch {NAMES[i%30]} Entity{i:04} LLC','country':COUNTRIES[(i+5)%10],'lei':'','registration_id':f'WLREG-{i:05}','listed_at':'2026-08-01','source':'WATCHLIST_SYNTHETIC','status':'TEST_ONLY'})
    # 12 planted real *within synthetic simulation* watchlist target positives
    for i in range(12):
        c=clients[470+i]
        watch[i]['legal_name']=c['legal_name'];watch[i]['country']=c['country'];watch[i]['registration_id']=c['registration_id']
        gold.append([c['entity_id'],watch[i]['entity_id'],'positive','scripted watchlist collision TEST ONLY'])
        # Rename subset to stress name matching, retaining strong ID
        if i%3==0: watch[i]['legal_name']=c['legal_name'].replace(' S.A.',' SA').replace('a','á',1)
    for i in range(190):
        relations.append({'relation_id':f'REL-{i:04}','from_entity_id':f'CUS-{i:05}','to_entity_id':f'CUS-{(i+7)%640:05}','relation_type':'SUPPLIER_TO','evidence_id':f'SYNTH-EDGE-{i:04}','as_of':'2026-10-01','source':'GRAPH_SYNTHETIC'})
    # Purposeful defects: 56 unique mutation rows on client records, separate from synthetic positives
    mutations={
      'bad_lei':lambda c: c.update(lei='1234XX'),
      'empty_name':lambda c:c.update(legal_name=''),
      'bad_country':lambda c:c.update(country='ZZZ'),
      'stale_time':lambda c:c.update(updated_at='not-a-date'),
      'duplicate_id':lambda c:c.update(entity_id='CUS-00025'),
      'missing_registration':lambda c:c.update(registration_id=''),
      'punctuation_alias':lambda c:c.update(legal_name='  '+c['legal_name'].replace(' ','  ')+'  '),
      'transposition':lambda c:c.update(legal_name=c['legal_name'].replace('Industries','Indsutries')),
    }
    keys=list(mutations)
    for k,i in enumerate(range(560,616)):
        c=clients[i];typ=keys[k%len(keys)];mutations[typ](c)
        injections.append([c['entity_id'],typ,'CLIENT_SYNTHETIC','scripted, not present in any real register'])
    # Inject 8 conflicting entries on synthetic registry rows (quality-only)
    for j,i in enumerate(range(605,613)):
        registry[i]['country']='' if j%2==0 else '??'
        injections.append([registry[i]['entity_id'],'bad_registry_country','REGISTRY_SYNTHETIC','scripted'])
    # 8 relation defects, not inferred ownership
    for j in range(8):
        relations[j]['to_entity_id']='CUS-99999' if j%2==0 else ''
        injections.append([relations[j]['relation_id'],'broken_graph_endpoint','GRAPH_SYNTHETIC','scripted'])
    dump(root/'client_entities_dirty.csv',list(clients[0]),clients)
    dump(root/'registry_reference_synthetic.csv',list(registry[0]),registry)
    dump(root/'sanctions_reference_SYNTHETIC_ONLY.csv',list(watch[0]),watch)
    dump(root/'relationships_dirty.csv',list(relations[0]),relations)
    dump(root/'INJECTION_TRUTH_NOT_FOR_TRAINING.csv',['source_row_id','injected_type','source_domain','note'],[dict(zip(['source_row_id','injected_type','source_domain','note'],x)) for x in injections])
    dump(root/'MATCH_GOLD_SYNTHETIC_DO_NOT_USE_AS_FEATURE.csv',['client_id','reference_id','label','explanation'],[dict(zip(['client_id','reference_id','label','explanation'],x)) for x in gold])
    (root/'SOURCE_PROVENANCE.json').write_text(json.dumps({'kind':'SYNTHETIC','generated_by':'python -m i24.fixture','seed':20261015,'real_ofac_data':False,'real_gleif_data':False,'subject_names':'fictional','no_claims_about_real_entities':True,'snapshot':'2026-10-15'},indent=2)+'\n',encoding='utf-8')
    return {'clients':len(clients),'registry':len(registry),'watchlist':len(watch),'relations':len(relations),'injections':len(injections),'gold':len(gold)}
if __name__=='__main__':
    import sys
    print(generate(sys.argv[1] if len(sys.argv)>1 else 'DATOS_FUENTES/04_SINTETICOS'))
