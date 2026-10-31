"""Conservative adapter for GLEIF public JSON. No OFAC parser is claimed implemented."""
from .identities import valid_lei

def gleif_record_to_candidate(record):
    """Extract identity reference candidate from GLEIF API record attributes.
    Reject missing core fields; ownership needs a separate Level-2 lineage adapter.
    """
    if not isinstance(record,dict):raise ValueError('expected GLEIF record object')
    attr=record.get('attributes',{})
    ent=attr.get('entity') or {}
    legal=ent.get('legalName') or {}
    address=ent.get('legalAddress') or {}
    value=legal.get('name') if isinstance(legal,dict) else str(legal)
    country=address.get('country') if isinstance(address,dict) else None
    lei=attr.get('lei') or record.get('id')
    if not value or not country or not valid_lei(lei):raise ValueError('incomplete or invalid identity snapshot; do not synthesize missing core fields')
    return {'entity_id':lei,'legal_name':value,'country':country,'lei':lei,'registration_id':'','source':'GLEIF_PUBLIC_EXTERNAL_CANDIDATE','updated_at':(attr.get('registration') or {}).get('lastUpdateDate','')}

def ofac_requires_official_schema_mapping():
    """Fail closed until separate SDN/non-SDN schemas, versions and list status are validated."""
    raise RuntimeError('OFAC official SDN/non-SDN adapters NOT IMPLEMENTED; legal and provenance review required')
