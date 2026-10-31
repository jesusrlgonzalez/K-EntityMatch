"""Exploratory ML ranker; gold is synthetic, never from real-world labels."""
import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .audit import read

def run(source,out):
    source=Path(source);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    clients=read(source/'client_entities_dirty.csv');refs=read(source/'registry_reference_synthetic.csv')
    clean=[r for r in clients if r['legal_name'].strip() and r['entity_id'] in {f'CUS-{i:05}' for i in range(440)}]
    registry=[r for r in refs if r['entity_id'] in {f'REF-{i:05}' for i in range(440)}]
    train=clean[:300];test=clean[300:440]
    # Deterministic TF-IDF character ngram. Only public synthetic names.
    v=TfidfVectorizer(analyzer='char',ngram_range=(2,4),min_df=1)
    matrix=v.fit_transform([r['legal_name'] for r in train]+[r['legal_name'] for r in registry])
    refs_m=matrix[len(train):]
    scores=cosine_similarity(v.transform([r['legal_name'] for r in test]),refs_m)
    correct=0
    for idx,r in enumerate(test):
        best=registry[int(scores[idx].argmax())]
        correct+=int(best['entity_id']=='REF-'+r['entity_id'][4:])
    report={'experiment':'TFIDF_CHAR_NGRAM_RETRIEVAL','data':'SYNTHETIC_ONLY','train_clients':len(train),'test_clients':len(test),'reference_entities':len(registry),'test_top1_exact_scripted_match_rate':round(correct/len(test),6),'statistical_limits':['designed positive pairs only; lacks hard negative generalization','no OFAC labels','not production-calibrated','name overlap can inflate apparent quality']}
    (out/'ml_baseline.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return report
if __name__=='__main__':
    import sys
    print(run(sys.argv[1] if len(sys.argv)>1 else 'DATOS_FUENTES/04_SINTETICOS',sys.argv[2] if len(sys.argv)>2 else 'outputs/demo'))
