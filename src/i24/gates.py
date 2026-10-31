"""Independent approval is fail-closed, cannot be self-attested by owner."""
import json
GATES=['G0','G1','G2','G3','G4','G5_TECH','G5_BUSINESS']
def assess(gate,evidence):
    if gate not in GATES:raise ValueError('unknown gate')
    required={'approved_by_owner','independent_reviewer','reviewer_is_distinct','evidence_hash','source_authorized','scope_accepted','negative_findings_resolved'}
    if not isinstance(evidence,dict) or not required.issubset(evidence):return 'BLOCK'
    if any(not evidence[k] for k in required):return 'BLOCK'
    if evidence['approved_by_owner']==evidence['independent_reviewer']:return 'BLOCK'
    if evidence.get('synthetic_only',True):return 'BLOCK'
    if gate=='G5_BUSINESS' and not evidence.get('business_pilot_signed',False):return 'BLOCK'
    return 'ELIGIBLE_FOR_EXTERNAL_AUDIT_NOT_APPROVED'
