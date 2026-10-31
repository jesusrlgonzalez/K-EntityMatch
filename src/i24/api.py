"""Read-only API. The absence of a candidate NEVER equals sanctions clearance."""
import sqlite3
from pathlib import Path
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
app=FastAPI(title='I24 synthetic entity-resolution evidence API',version='1.0.0')
DB=Path('outputs/demo/i24_review.sqlite')
class Triage(BaseModel):
    entity_id:str
    quality_disposition:str
    triage_status:str
    legal_clearance:str
    automated_payment_action:str

def get_db():
    if not DB.exists():raise HTTPException(503,'Local demo DB missing; execute the auditor first')
    return sqlite3.connect(f'file:{DB.resolve()}?mode=ro',uri=True)
@app.get('/health')
def health():return {'ok':DB.exists(),'kind':'synthetic-demo','is_sanctions_certification':False}
@app.get('/entities/{entity_id}',response_model=Triage)
def entity(entity_id:str):
    if len(entity_id)>64:raise HTTPException(400,'id too long')
    with get_db() as c:
        row=c.execute('SELECT entity_id,quality_disposition,triage_status,legal_clearance,automated_payment_action FROM triage WHERE entity_id=? ORDER BY row_number LIMIT 1',(entity_id,)).fetchone()
    if not row:raise HTTPException(404,'Entity not found')
    return Triage(**dict(zip(Triage.model_fields,row)))
@app.get('/matches/{entity_id}')
def matches(entity_id:str):
    if len(entity_id)>64:raise HTTPException(400,'id too long')
    with get_db() as c:
        rs=c.execute('SELECT reference_id,reference_source,score,priority,disposition FROM matches WHERE client_id=? ORDER BY score DESC LIMIT 20',(entity_id,)).fetchall()
    return {'entity_id':entity_id,'dataset_type':'SYNTHETIC_ONLY','results':[dict(zip(['reference_id','reference_source','score','priority','disposition'],x)) for x in rs],'legal_clearance':'NOT_PERFORMED'}
