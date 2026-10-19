"""Closed public contracts and deterministic integrity. Standard library only.

Schema construction is shared with the checked-in JSON Schemas. Validation
implements only the explicit vocabulary below; it never resolves external refs.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from datetime import datetime

SCHEMA_VERSION = 'creditpilot-public-golden.v1'
BUNDLE_VERSION = 'creditpilot-public-bundle.v1'
ARTIFACT_VERSION = '1.1.0'
EXPORTER_VERSION = 'public-exporter.v1'
BASELINE = '431a03e9656b79296c7e598a7fba27e0714b7abe'
MODEL_HASH = '3541a99a53b69764affbbe259d23ce326eb3b75e6e315951d53c647f5f9c7bb7'
MAX_BYTES = 1_000_000
SCENARIOS = {
    'CP-001': ('GOLDEN_SCENARIO_1', 'Golden Scenario 1 — Low-Risk Straight-Through'),
    'CP-002': ('GOLDEN_SCENARIO_2', 'Golden Scenario 2 — Verification + Review'),
    'CP-003': ('GOLDEN_SCENARIO_3', 'Golden Scenario 3 — Verification Failure + Escalation'),
}
FEATURES = ('age', 'monthly_income', 'debt_ratio', 'revolving_utilization',
            'number_of_open_credit_lines_and_loans', 'number_of_real_estate_loans_or_lines',
            'number_of_dependents', 'past_due_30_59_days', 'past_due_60_89_days', 'past_due_90_days_or_more')
MODEL_FEATURES = ('RevolvingUtilizationOfUnsecuredLines', 'age', 'NumberOfTime30-59DaysPastDueNotWorse',
                  'DebtRatio', 'MonthlyIncome', 'NumberOfOpenCreditLinesAndLoans', 'NumberOfTimes90DaysLate',
                  'NumberRealEstateLoansOrLines', 'NumberOfTime60-89DaysPastDueNotWorse', 'NumberOfDependents')
CONCEPTS = ('RevolvingUtilization', 'Age', 'Delinquency30To59Days', 'DebtRatio', 'MonthlyIncome',
            'OpenCreditLinesAndLoans', 'Delinquency90Days', 'RealEstateLoansOrLines',
            'Delinquency60To89Days', 'NumberOfDependents')
RECOMMENDATIONS = ('APPROVAL_RECOMMENDATION', 'REVIEW_RECOMMENDATION', 'DECLINE_RECOMMENDATION')
ROUTES = ('POLICY', 'VERIFY', 'RECOMPUTE', 'READY', 'UNRESOLVED')
STAGES = ('INPUT', 'RISK_SHAP', 'POLICY', 'ORCHESTRATOR', 'VERIFICATION', 'RECONCILIATION',
          'WORKFLOW_CONTROLLER', 'ADMISSION', 'DECISION_ENGINE', 'PHASE10', 'HUMAN_REVIEW', 'EXPLANATION')
KINDS = ('STAGE_RESULT', 'TRANSITION', 'ATTEMPT_STARTED', 'ATTEMPT_COMPLETED', 'RETRY_AUTHORIZED',
         'RETRY_EXHAUSTED', 'ADMISSION', 'DECISION', 'DISPOSITION', 'REVIEW_ENTRY', 'MOCK_ACTION', 'EXPLANATION')
LIMITATIONS = ('RECORDED_OFFLINE', 'SYNTHETIC_FIXTURES', 'DETERMINISTIC_ADAPTERS', 'PD_PROXY',
               'PARTIAL_SHAP', 'INITIAL_SNAPSHOTS_UNAVAILABLE', 'HISTORICAL_METRICS_MISSING', 'RAG_AGENT_UNSCORED')
ADAPTERS = dict(mode='SYNTHETIC_OFFLINE', policy_embeddings='DETERMINISTIC_HASH_DEMO',
                policy_generation='DETERMINISTIC_OFFLINE', explanation='OFFLINE_FACT_SELECTOR',
                verification='SYNTHETIC_FIXTURES', actions='MOCK')


class ArtifactError(ValueError):
    def __init__(self):
        super().__init__('PUBLIC_ARTIFACT_INVALID')


def require(condition):
    if not condition:
        raise ArtifactError()


def canonical(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                          allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise ArtifactError() from None


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(raw):
    return hashlib.sha256(raw).hexdigest()


def seal(payload):
    require(type(payload) is dict and 'integrity' not in payload)
    result = copy.deepcopy(payload)
    result['integrity'] = dict(algorithm='sha256', canonicalization='creditpilot-json-v1',
                               payload_sha256=digest(payload))
    return result


def verify_integrity(value):
    require(value['integrity']['payload_sha256'] == digest({k: v for k, v in value.items() if k != 'integrity'}))


def parse(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result)
            result[key] = value
        return result
    try:
        require(type(raw) is bytes and 0 < len(raw) <= MAX_BYTES)
        return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ArtifactError()))
    except Exception:
        raise ArtifactError() from None


def string(pattern=None, maximum=256):
    result = dict(type='string', minLength=1, maxLength=maximum)
    if pattern:
        result['pattern'] = pattern
    return result


def enum(*values):
    return {'enum': list(values)}


def obj(**properties):
    return dict(type='object', properties=properties, required=list(properties), additionalProperties=False)


def array(items, maximum=100, minimum=0):
    return dict(type='array', items=items, minItems=minimum, maxItems=maximum)


def nullable(schema):
    return {'anyOf': [schema, {'type': 'null'}]}


HASH = string(r'^[a-f0-9]{64}$', 64)
COMMIT = string(r'^[a-f0-9]{40}$', 40)
TIME = dict(string(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?\+00:00$', 40), format='date-time')
REF = string(r'^(?:(?:opaque|wfexec|evctx|vrq|evidence|p9admit|p9dec|p10route|p10esc|p10act|p10event|p11evt|reviewep|hrrec|case|msg|idxfp|retry_exhausted)_[a-f0-9]{16,64}|(?:finding|val|pq|claim)_[a-f0-9]{16}|record_[a-f0-9]{64}(?:_[a-z0-9_]+)?|attempt_(?:started_)?opaque_[a-f0-9]{64})$', 140)
SOURCE = string(r'^(?:application:(?:' + '|'.join(FEATURES) + r')|(?:verified|internal|external):opaque_[a-f0-9]{16,64}|opaque_[a-f0-9]{16,64})$', 150)
NUMBER = dict(type='number', minimum=-1e12, maximum=1e12)
INTEGER = dict(type='integer', minimum=0, maximum=10000)
BOOL = {'type': 'boolean'}
PROB = dict(type='number', minimum=0, maximum=1)
VERSION = string(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$', 80)
PROSE = string(maximum=12000)
INTEGRITY = obj(algorithm=enum('sha256'), canonicalization=enum('creditpilot-json-v1'), payload_sha256=HASH)
CONTRIBUTION = obj(concept=enum(*CONCEPTS), contribution=NUMBER,
                   direction=enum('risk_increasing', 'risk_reducing'))
SHAP = obj(target=enum('raw_model_score'), units=enum('log_odds'), coverage=enum('grouped_top_k'),
           base_score=NUMBER, top_risk_drivers=array(CONTRIBUTION, 3), top_risk_reducers=array(CONTRIBUTION, 3))
CONTEXT = string(r'^evctx_[a-f0-9]{64}$', 70)
POLICY_SOURCE = string(r'^policy://POL-[A-Z]{2,4}-\d{3}/\d+\.\d+/section-\d{3}/[A-Z]{2,4}-\d{3}\.\d{1,3}$', 120)
GROUNDED = obj(evidence_id=REF, document_id=string(r'^POL-[A-Z]{2,4}-\d{3}$'), document_version=enum('1.0'),
               section_id=string(r'^section-\d{3}$'), clause_id=string(r'^[A-Z]{2,4}-\d{3}\.\d{1,3}$'),
               source_reference=POLICY_SOURCE, text=PROSE,
               chunk_id=string(r'^POL-[A-Z]{2,4}-\d{3}:1\.0:[A-Z]{2,4}-\d{3}\.\d{1,3}:policy-chunking\.v1:chunk-\d{3}$'),
               text_hash=HASH, retrieval_query_id=REF, retrieval_version=enum('policy-retrieval.v1'),
               index_fingerprint=REF, grounding_version=enum('policy-grounding.v1'))
FINDING = obj(finding_ref=REF, status=enum('SUPPORTED', 'UNRESOLVED'),
              question=enum('What policy requirements apply to the current data-quality and evidence context?',
                            'Evaluate the applicable synthetic portfolio policy for these current case facts.'),
              claims=array(enum('The cited policy passage is relevant to this policy question.'), 20),
              evidence_refs=array(REF, 20, 1))
ADMISSION = obj(status=enum('ADMITTED'), admission_ref=REF, validator_version=enum('phase8.9-structural-admission.v1'),
                evidence_context_version=CONTEXT, finding_refs=array(REF, 20, 1))
VERIFY_EVIDENCE = obj(evidence_ref=REF, field=enum(*FEATURES), value=NUMBER, source_reference=SOURCE,
                      contradicts=array(string(r'^(?:application:(?:'+'|'.join(FEATURES)+r')|opaque_[a-f0-9]{16,64})$'), 10))
VERIFICATION = obj(request_ref=REF, attempt_ref=REF, attempt_number=dict(type='integer', minimum=1, maximum=3),
                   tool=enum('verify_income', 'verify_employment', 'get_credit_report'),
                   outcome=enum('SUCCEEDED', 'FAILED', 'UNAVAILABLE'),
                   retry_policy_version=nullable(enum('verification-retry.v1')), retry_proof_ref=nullable(REF),
                   evidence=array(VERIFY_EVIDENCE, 10))
SELECTED = obj(feature=enum(*FEATURES), selected_value=nullable(NUMBER),
               selected_source=enum('application', 'verified', 'internal', 'external', 'derived'),
               source_reference=SOURCE, rule_version=enum('feature-source.v2'),
               original_reported_value=nullable(NUMBER), verification_evidence_refs=array(REF, 10))
EVENT = obj(sequence=INTEGER, event_ref=REF, kind=enum(*KINDS), stage=enum(*STAGES),
            route=nullable(enum(*ROUTES)), authorized=nullable(BOOL), source_revision=nullable(INTEGER),
            attempt_ref=nullable(REF), evidence_refs=array(REF, 30))
DECISION = obj(engine_reached=BOOL, admission_ref=nullable(REF), decision_ref=nullable(REF),
               system_recommendation=nullable(enum(*RECOMMENDATIONS)),
               decision_rule=nullable(enum('DPV1_PD_LOW', 'DPV1_PD_INTERMEDIATE', 'DPV1_PD_HIGH')),
               decision_reason=nullable(enum('PD_BELOW_LOW_THRESHOLD', 'PD_IN_INTERMEDIATE_ZONE', 'PD_AT_OR_ABOVE_HIGH_THRESHOLD')))
HUMAN = obj(disposition=enum('NO_PHASE10_ACTION', 'HUMAN_CREDIT_REVIEW', 'HUMAN_INVESTIGATION', 'OPERATIONAL_HANDLING'),
            route_ref=REF, authorized=BOOL, review_required=BOOL, review_status=nullable(enum('PENDING')),
            review_trigger=nullable(enum('REVIEW_RECOMMENDATION', 'VERIFICATION_FAILED')),
            system_recommendation=nullable(enum(*RECOMMENDATIONS)), final_outcome={'type': 'null'})
ACTION = obj(action=enum('REVIEW_CASE', 'SLACK', 'EMAIL'),
             status=enum('INTENT', 'STARTED', 'UNCERTAIN', 'FAILED', 'SUCCEEDED'), provider=enum('MOCK'),
             action_ref=REF, case_ref=nullable(REF), receipt_ref=nullable(REF),
             effect_count=dict(type='integer', minimum=0, maximum=1),
             failure_code=nullable(enum('PROVIDER_FAILED', 'PROVIDER_UNAVAILABLE', 'REJECTED')))
PROVENANCE = obj(source_release_tag=enum('creditpilot-v1.0.0'), source_release_commit=enum(BASELINE),
                 execution_code_commit=COMMIT, exporter_code_commit=COMMIT, exporter_version=enum(EXPORTER_VERSION),
                 generated_at_utc=TIME, executed_at_utc=TIME, source_execution_id=REF,
                 source_runtime_sha256=HASH, source_evidence_sha256=HASH, model_artifact_sha256=enum(MODEL_HASH),
                 policy_corpus_sha256=HASH, decision_policy_sha256=HASH, execution_environment_sha256=HASH,
                 adapter_profile=obj(**{k: enum(v) for k, v in ADAPTERS.items()}))
GOLDEN_SCHEMA = obj(schema_version=enum(SCHEMA_VERSION), artifact_version=enum(ARTIFACT_VERSION),
    provenance=PROVENANCE,
    scenario=obj(id=enum(*SCENARIOS), source_scenario=enum(*(x[0] for x in SCENARIOS.values())),
                 title=enum(*(x[1] for x in SCENARIOS.values())), synthetic=enum(True)),
    risk=obj(status=enum('SUCCESS', 'INPUT_VALIDATION_FAILED', 'MODEL_EXECUTION_FAILED'),
             model_version=enum('phase1a-risk-model-v1'), calibration_version=enum('P1A_CALIBRATION_FREEZE_V1'),
             explanation_version=enum('phase1b-shap-v1'), calibrated_pd=nullable(PROB), raw_probability=nullable(PROB),
             raw_model_score=nullable(NUMBER), risk_band=nullable(enum('LOW', 'GRAY', 'HIGH')),
             model_timestamp=nullable(TIME), data_quality=obj(**{k: array(enum(*MODEL_FEATURES), 10) for k in
             ('missing_features', 'imputed_features', 'special_code_features')}), shap=nullable(SHAP)),
    policy=obj(evidence_context_version=CONTEXT, policy_as_of=TIME, findings=array(FINDING, 20, 1),
               grounded_evidence=array(GROUNDED, 30, 1), admission=nullable(ADMISSION)),
    verification=array(VERIFICATION, 3),
    lineage=obj(feature_source_policy_version=enum('feature-source.v2'), evidence_context_version=CONTEXT,
                selected_features=array(SELECTED, 10, 10), vector_changed=nullable(BOOL),
                relevance_rule_version=nullable(VERSION), policy_relevant=nullable(BOOL)),
    workflow=obj(terminal=enum('READY_FOR_PHASE9', 'UNRESOLVED', 'RUNTIME_FAILURE'), terminal_proof_ref=REF,
                 evidence_context_version=CONTEXT, events=array(EVENT, 150, 1)),
    decision=DECISION, human_route=HUMAN,
    explanation=nullable(obj(status=enum('SUCCEEDED', 'FAILED'), text=nullable(PROSE), source_ref=REF)),
    mock_actions=array(ACTION, 3), limitations=array(enum(*LIMITATIONS), 8, 1), integrity=INTEGRITY)
BUNDLE_SCHEMA = obj(schema_version=enum(BUNDLE_VERSION), artifact_version=enum(ARTIFACT_VERSION),
    exporter_version=enum(EXPORTER_VERSION), generated_at_utc=TIME,
    artifacts=array(obj(scenario_id=enum(*SCENARIOS), filename=enum('cp-001.json', 'cp-002.json', 'cp-003.json'),
                        schema_version=enum(SCHEMA_VERSION), payload_sha256=HASH, file_sha256=HASH), 3, 3), integrity=INTEGRITY)


def typed_ref(prefix, digits=64):
    return string(r'^(?:'+prefix+r')_[a-f0-9]{'+str(digits)+r'}$', 140)


# Historical locators retain their source types; no executable capability is exported.
PROVENANCE['properties']['source_execution_id']=typed_ref('wfexec')
GROUNDED['properties']['evidence_id']=typed_ref('evidence')
GROUNDED['properties']['retrieval_query_id']=typed_ref('pq',16)
GROUNDED['properties']['index_fingerprint']=typed_ref('idxfp')
FINDING['properties']['finding_ref']=typed_ref('finding',16)
FINDING['properties']['evidence_refs']=array(typed_ref('evidence'),20,1)
ADMISSION['properties']['admission_ref']=typed_ref('p9admit')
ADMISSION['properties']['finding_refs']=array(typed_ref('finding',16),20,1)
VERIFICATION['properties']['request_ref']=typed_ref('vrq')
VERIFICATION['properties']['attempt_ref']=typed_ref('opaque')
VERIFICATION['properties']['retry_proof_ref']=nullable(typed_ref('opaque'))
VERIFY_EVIDENCE['properties']['evidence_ref']=typed_ref('opaque')
SELECTED['properties']['verification_evidence_refs']=array(typed_ref('opaque'),10)
DECISION['properties']['admission_ref']=nullable(typed_ref('p9admit'))
DECISION['properties']['decision_ref']=nullable(typed_ref('p9dec'))
HUMAN['properties']['route_ref']=typed_ref('p10route')
ACTION['properties']['action_ref']=typed_ref('p10act')
ACTION['properties']['case_ref']=nullable(typed_ref('case'))
ACTION['properties']['receipt_ref']=nullable(typed_ref('case|msg'))
GOLDEN_SCHEMA['properties']['workflow']['properties']['terminal_proof_ref']=typed_ref('opaque')
GOLDEN_SCHEMA['properties']['explanation']['anyOf'][0]['properties']['source_ref']=typed_ref('p11evt')
# Approved presentation-only cases; absence never means irrelevant evidence.
_lineage = GOLDEN_SCHEMA['properties']['lineage']['properties']
GOLDEN_SCHEMA['properties']['lineage'] = {'anyOf': [
    obj(**{**_lineage, 'vector_changed': enum(changed),
           'relevance_rule_version': enum(rule), 'policy_relevant': relevance})
    for changed, rule, relevance in (
        (None, None, enum(None)),
        (True, None, enum(None)),
        (False, 'evidence-relevance.v2', BOOL))
]}


def validate_shape(value, schema, depth=0):
    require(depth <= 24)
    if 'anyOf' in schema:
        for option in schema['anyOf']:
            try:
                validate_shape(value, option, depth+1)
                return
            except ArtifactError:
                pass
        raise ArtifactError()
    if 'enum' in schema:
        require(any(type(value) is type(x) and value == x for x in schema['enum']))
        return
    kind = schema['type']
    if kind == 'object':
        require(type(value) is dict and set(value) == set(schema['properties']))
        for key, child in schema['properties'].items():
            validate_shape(value[key], child, depth+1)
    elif kind == 'array':
        require(type(value) is list and schema['minItems'] <= len(value) <= schema['maxItems'])
        for child in value:
            validate_shape(child, schema['items'], depth+1)
    elif kind == 'string':
        require(type(value) is str and schema['minLength'] <= len(value) <= schema['maxLength'])
        require(not any(ord(x) < 32 and x not in '\n\t' for x in value))
        if 'pattern' in schema:
            require(re.fullmatch(schema['pattern'], value) is not None)
        if schema.get('format') == 'date-time':
            try:
                datetime.fromisoformat(value)
            except ValueError:
                raise ArtifactError() from None
        screen(value, schema)
    elif kind in ('number', 'integer'):
        require(type(value) in ((int, float) if kind == 'number' else (int,)))
        require(math.isfinite(value) and schema['minimum'] <= value <= schema['maximum'])
    elif kind == 'boolean':
        require(type(value) is bool)
    else:
        require(kind == 'null' and value is None)


UNSAFE = re.compile(r'(?i)(?:[\w.+%-]+@[\w.-]+\.[a-z]{2,}|\b\d{3}[- ]\d{2}[- ]\d{4}\b|'
                    r'(?<![\w])(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}(?!\w)|'
                    r'\b\d{1,6}\s+[a-z0-9 .-]{1,50}\s(?:street|road|avenue|drive|lane|st|rd|ave)\b|'
                    r'https?://|file://|/Users/|/home/|/private/|[A-Z]:\\|\.\./|\\|'
                    r'bearer\s|xox[baprs]-|sk-[a-z0-9]|-----BEGIN|password\s*[:=]|secret\s*[:=]|'
                    r'customer_token|reviewer_id|api[_ -]?key\s*[:=])')


def screen(value, schema):
    # Exempt only fully validated structural hex IDs/hashes, never arbitrary prose.
    if schema in (HASH, COMMIT, REF, CONTEXT) or re.fullmatch(REF['pattern'], value):
        return
    require(not UNSAFE.search(value))


def _unique(rows, key):
    values = [row[key] for row in rows]
    require(len(set(values)) == len(values))
    return set(values)


def validate_artifact(value):
    try:
        validate_shape(value, GOLDEN_SCHEMA)
        verify_integrity(value)
        _bindings(value)
        return value
    except Exception:
        raise ArtifactError() from None


def _bindings(a):
    scenario = a['scenario']; sid = scenario['id']
    require((scenario['source_scenario'], scenario['title']) == SCENARIOS[sid])
    context = a['workflow']['evidence_context_version']
    require(context == a['policy']['evidence_context_version'] == a['lineage']['evidence_context_version'])
    risk = a['risk']
    fields = ('calibrated_pd', 'raw_probability', 'raw_model_score', 'model_timestamp', 'shap')
    require(all(risk[x] is not None for x in fields) if risk['status'] == 'SUCCESS' else all(risk[x] is None for x in fields))
    if risk['shap']:
        seen = set()
        for key, sign in [('top_risk_drivers', 1), ('top_risk_reducers', -1)]:
            rows = risk['shap'][key]
            require([abs(x['contribution']) for x in rows] == sorted([abs(x['contribution']) for x in rows], reverse=True))
            for x in rows:
                require(x['concept'] not in seen and x['contribution']*sign > 0)
                require(x['direction'] == ('risk_increasing' if sign == 1 else 'risk_reducing'))
                seen.add(x['concept'])
    evidence = a['policy']['grounded_evidence']
    ids = _unique(evidence, 'evidence_id')
    for x in evidence:
        require((x['text_hash'], x['source_reference'], x['section_id'], x['clause_id']) ==
                APPROVED_POLICY_CHUNKS.get(x['chunk_id']))
        require(x['source_reference'] == 'policy://{document_id}/{document_version}/{section_id}/{clause_id}'.format(**x))
        require(x['chunk_id'].startswith(x['document_id']+':'+x['document_version']+':'+x['clause_id']+':'))
        require(x['text_hash'] == file_digest(x['text'].encode()))
        identity = dict(chunk_id=x['chunk_id'], chunk_text_hash=x['text_hash'], retrieval_query_id=x['retrieval_query_id'],
                        retrieval_version=x['retrieval_version'], index_fingerprint=x['index_fingerprint'], grounding_version=x['grounding_version'])
        require(x['evidence_id'] == 'evidence_'+hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',', ':'),ensure_ascii=True).encode()).hexdigest())
    findings = _unique(a['policy']['findings'], 'finding_ref')
    for f in a['policy']['findings']:
        require(set(f['evidence_refs']) <= ids)
    admission = a['policy']['admission']; decision = a['decision']; human = a['human_route']
    require(decision['engine_reached'] == (admission is not None))
    if admission:
        require(admission['evidence_context_version'] == context and set(admission['finding_refs']) == findings)
        require(all(f['status'] == 'SUPPORTED' for f in a['policy']['findings']))
        require(decision['admission_ref'] == admission['admission_ref'])
        require(all(decision[k] is not None for k in ('decision_ref','system_recommendation','decision_rule','decision_reason')))
    else:
        require(all(v is None for k,v in decision.items() if k != 'engine_reached'))
    require(human['authorized'] is True and human['system_recommendation'] == decision['system_recommendation'])
    events = a['workflow']['events']; event_ids = _unique(events, 'event_ref')
    require([x['sequence'] for x in events] == list(range(len(events))))
    require(a['workflow']['terminal_proof_ref'] in event_ids)
    transitions=[e for e in events if e['kind']=='TRANSITION']
    require(bool(transitions) and a['workflow']['terminal_proof_ref']==transitions[-1]['event_ref'])
    revisions=[e['source_revision'] for e in transitions]
    require(revisions==sorted(set(revisions)))
    for x in events:
        if x['kind'] == 'TRANSITION':
            require(x['authorized'] is True and x['route'] is not None and x['source_revision'] is not None)
    attempts = _unique(a['verification'], 'attempt_ref')
    verify_ids = _unique([e for x in a['verification'] for e in x['evidence']], 'evidence_ref')
    for v in a['verification']:
        for e in v['evidence']:
            require(all(ref=='application:'+e['field'] or ref in verify_ids for ref in e['contradicts']))
    for x in events:
        require(x['attempt_ref'] is None or x['attempt_ref'] in attempts)
    references=ids|findings|verify_ids|attempts|event_ids|{v['request_ref'] for v in a['verification']}
    for x in events:
        require(set(x['evidence_refs'])<=references)
    counts={}
    for v in a['verification']:
        counts[v['tool']]=counts.get(v['tool'],0)+1
        require(v['attempt_number']==counts[v['tool']])
        start=next(i for i,e in enumerate(events) if e['kind']=='ATTEMPT_STARTED' and e['attempt_ref']==v['attempt_ref'])
        end=next(i for i,e in enumerate(events) if e['kind']=='ATTEMPT_COMPLETED' and e['attempt_ref']==v['attempt_ref'])
        require(start<end)
    selected = a['lineage']['selected_features']
    require(_unique(selected, 'feature') == set(FEATURES))
    for f in selected:
        require(set(f['verification_evidence_refs']) <= verify_ids)
        require(f['selected_source'] in ('application','verified'))
        if f['selected_source']=='application':
            require(f['source_reference']=='application:'+f['feature'])
            require(f['selected_value']==f['original_reported_value'] and not f['verification_evidence_refs'])
        if f['selected_source'] == 'verified':
            matches = [e for x in a['verification'] if x['outcome']=='SUCCEEDED' for e in x['evidence']
                       if e['evidence_ref'] in f['verification_evidence_refs'] and e['field']==f['feature']
                       and e['value']==f['selected_value'] and f['source_reference']=='verified:'+e['evidence_ref']]
            require(bool(matches))
    if a['lineage']['vector_changed'] is True:
        recompute = [i for i,e in enumerate(events) if e['kind']=='TRANSITION' and e['route']=='RECOMPUTE']
        require(len(recompute)==2)
        risk_at = [i for i,e in enumerate(events) if e['kind']=='TRANSITION' and e['stage']=='RISK_SHAP']
        require(any(i>recompute[-1] for i in risk_at))
        last_risk = max(risk_at)
        require(any(i>last_risk and e['kind']=='TRANSITION' and e['stage']=='POLICY' for i,e in enumerate(events)))
    expected = {
      'CP-001': ('APPROVAL_RECOMMENDATION', 'DPV1_PD_LOW', 'NO_PHASE10_ACTION', ['POLICY']*3+['READY']),
      'CP-002': ('REVIEW_RECOMMENDATION', 'DPV1_PD_INTERMEDIATE', 'HUMAN_CREDIT_REVIEW', ['POLICY']*3+['VERIFY','RECOMPUTE','RECOMPUTE']+['POLICY']*3+['READY']),
      'CP-003': (None,None,'HUMAN_INVESTIGATION',['POLICY']*3+['VERIFY','VERIFY','RECOMPUTE','RECOMPUTE']+['POLICY']*3+['UNRESOLVED'])}[sid]
    require((decision['system_recommendation'],decision['decision_rule'],human['disposition']) == expected[:3])
    require([x['route'] for x in events if x['kind']=='TRANSITION'] == expected[3])
    require(a['workflow']['terminal'] == ('UNRESOLVED' if sid=='CP-003' else 'READY_FOR_PHASE9'))
    require(human['review_required'] == (sid != 'CP-001'))
    require(human['review_status'] == (None if sid=='CP-001' else 'PENDING'))
    require(human['review_trigger'] == (None if sid=='CP-001' else 'REVIEW_RECOMMENDATION' if sid=='CP-002' else 'VERIFICATION_FAILED'))
    require(decision['decision_reason'] == (None if sid=='CP-003' else 'PD_BELOW_LOW_THRESHOLD' if sid=='CP-001' else 'PD_IN_INTERMEDIATE_ZONE'))
    require(a['explanation'] is None if sid=='CP-003' else a['explanation'] is not None and a['explanation']['status']=='SUCCEEDED')
    require(a['policy']['policy_as_of']=='2026-09-24T00:00:00+00:00')
    require([(e['event_ref'],e['kind']) for e in events if e['kind']=='DISPOSITION']==[(human['route_ref'],'DISPOSITION')])
    require([(e['event_ref'],e['kind']) for e in events if e['kind']=='DECISION']==
            ([(decision['decision_ref'],'DECISION')] if decision['engine_reached'] else []))
    require([(e['event_ref'],e['kind']) for e in events if e['kind']=='ADMISSION']==
            ([(decision['admission_ref'],'ADMISSION')] if admission else []))
    require(sum(e['kind']=='REVIEW_ENTRY' for e in events)==(1 if human['review_required'] else 0))
    require([e['event_ref'] for e in events if e['kind']=='MOCK_ACTION']==[x['action_ref'] for x in a['mock_actions']])
    require(sum(e['kind']=='EXPLANATION' for e in events)==(1 if a['explanation'] else 0))
    positions={e['event_ref']:i for i,e in enumerate(events)}
    terminal_at=positions[a['workflow']['terminal_proof_ref']]
    disposition_at=positions[human['route_ref']]
    if admission:
        require(terminal_at<positions[decision['admission_ref']]<positions[decision['decision_ref']]<disposition_at)
    else:
        require(terminal_at<disposition_at)
    require(all(positions[e['event_ref']]>disposition_at for e in events
                if e['kind'] in ('REVIEW_ENTRY','MOCK_ACTION','EXPLANATION')))
    for v in a['verification']:
        for kind in ('ATTEMPT_STARTED','ATTEMPT_COMPLETED'):
            require(sum(e['kind']==kind and e['attempt_ref']==v['attempt_ref'] for e in events)==1)
    if sid=='CP-001':
        require(not a['verification'] and not a['mock_actions'] and a['lineage']['vector_changed'] is None)
    if sid=='CP-002':
        require(len(a['verification'])==1 and a['verification'][0]['outcome']=='SUCCEEDED')
        require(a['verification'][0]['tool']=='verify_income')
        f = next(x for x in selected if x['feature']=='monthly_income')
        require((f['original_reported_value'],f['selected_value'],f['selected_source'])==(5000,3000,'verified'))
        require(not a['mock_actions'] and a['lineage']['vector_changed'] is True)
    if sid=='CP-003':
        require(a['lineage']['vector_changed'] is True)
        require([x['tool'] for x in a['verification']]==['verify_income','verify_income','get_credit_report'])
        first,second,credit = a['verification']
        require(first['outcome']==second['outcome']=='FAILED' and not first['evidence'] and not second['evidence'])
        require(first['request_ref']==second['request_ref'] and first['attempt_ref']!=second['attempt_ref'])
        require(credit['request_ref']!=first['request_ref'])
        require(second['retry_policy_version']=='verification-retry.v1' and second['retry_proof_ref'] is not None)
        require(credit['outcome']=='SUCCEEDED' and any(e['contradicts'] for e in credit['evidence']))
        require(sum(e['kind']=='RETRY_AUTHORIZED' for e in events)==1 and sum(e['kind']=='RETRY_EXHAUSTED' for e in events)==1)
        require(_unique(a['mock_actions'],'action')=={'REVIEW_CASE','SLACK','EMAIL'})
        require(a['mock_actions'][0]['action']=='REVIEW_CASE')
        case = a['mock_actions'][0]['case_ref']
        require(case==a['mock_actions'][0]['receipt_ref'])
        require(case is not None and all(x['case_ref']==case and x['status']=='SUCCEEDED' and x['effect_count']==1 and x['receipt_ref'] and x['failure_code'] is None for x in a['mock_actions']))
        ordered=[(e['kind'],e['attempt_ref']) for e in events]
        first_done=ordered.index(('ATTEMPT_COMPLETED',first['attempt_ref']))
        retry=ordered.index(('RETRY_AUTHORIZED',second['attempt_ref']))
        second_start=ordered.index(('ATTEMPT_STARTED',second['attempt_ref']))
        second_done=ordered.index(('ATTEMPT_COMPLETED',second['attempt_ref']))
        exhausted=next(i for i,e in enumerate(events) if e['kind']=='RETRY_EXHAUSTED')
        credit_start=ordered.index(('ATTEMPT_STARTED',credit['attempt_ref']))
        require(first_done<retry<second_start<second_done<exhausted<credit_start)
    if a['explanation'] is not None:
        require([e['event_ref'] for e in events if e['kind']=='EXPLANATION']==[a['explanation']['source_ref']])
        require(a['explanation']['text'] == expected_offline_explanation(a))


def expected_offline_explanation(a):
    """Validate frozen offline fact wording; no free-form names/secrets accepted.

    This checks presentation evidence, without executing an Agent or authoring
    an Explanation artifact. Only the persisted text is ever exported.
    """
    risk=a['risk']; decision=a['decision']; shap=risk['shap']
    lines=[f"Calibrated PD: {risk['calibrated_pd']:.4%} (rounded for display)."]
    for x in shap['top_risk_drivers']+shap['top_risk_reducers']:
        verb='increased' if x['contribution']>0 else 'reduced'
        lines.append(f"{x['concept']} {verb} the raw model score; SHAP contribution "
                     f"{x['contribution']:+.4f}. SHAP does not directly decompose calibrated PD.")
    selected={f['feature']:f for f in a['lineage']['selected_features']}
    for v in a['verification']:
        if not v['evidence']:
            lines.append(f"{v['tool']} returned {v['outcome'].lower()}; no verified value replaced reported application data.")
        for e in v['evidence']:
            relation='differs from' if selected[e['field']]['original_reported_value']!=e['value'] else 'matches'
            lines.append(f"Verified {e['field']} {relation} the separately retained reported value; "
                         'the source resolver controls which value enters the model.')
    evidence={e['evidence_id']:e for e in a['policy']['grounded_evidence']}
    findings={f['finding_ref']:f for f in a['policy']['findings']}
    for fid in a['policy']['admission']['finding_refs']:
        e=evidence[sorted(findings[fid]['evidence_refs'])[0]]
        excerpt=e['text'][:240].strip()+('…' if len(e['text'])>240 else '')
        lines.append(f"Validated synthetic policy evidence, section {e['section_id']}; source excerpt: {excerpt}")
    lines.extend((f"Phase 9 decision rule: {decision['decision_rule']}.",
                  f"Phase 9 decision reason: {decision['decision_reason']}.",
                  f"System recommendation: {decision['system_recommendation']}."))
    return '\n'.join(lines)


def validate_manifest(value):
    try:
        validate_shape(value, BUNDLE_SCHEMA)
        verify_integrity(value)
        require([x['scenario_id'] for x in value['artifacts']] == list(SCENARIOS))
        require([x['filename'] for x in value['artifacts']] == [x.lower()+'.json' for x in SCENARIOS])
        return value
    except Exception:
        raise ArtifactError() from None


# Frozen active synthetic policy chunk identities; no corpus/RAG imports at read time.
APPROVED_POLICY_CHUNKS = {'POL-AI-001:1.0:AI-001.001:policy-chunking.v1:chunk-001': ('3f2f0fd39ab7b6680aad94480b259b6da83de4d9fd401b4456a21e1a3b9d2329',
                                                            'policy://POL-AI-001/1.0/section-001/AI-001.001',
                                                            'section-001',
                                                            'AI-001.001'),
 'POL-AI-001:1.0:AI-001.002:policy-chunking.v1:chunk-001': ('1204ef406b6bc80f350cadd6e1861431c748035542843408fcefd59e836faa6b',
                                                            'policy://POL-AI-001/1.0/section-001/AI-001.002',
                                                            'section-001',
                                                            'AI-001.002'),
 'POL-AI-001:1.0:AI-001.1:policy-chunking.v1:chunk-001': ('2913c0b1af99395648092c8bdc5fadd81c99d261551e1c9880d5376f4eed838c',
                                                          'policy://POL-AI-001/1.0/section-004/AI-001.1',
                                                          'section-004',
                                                          'AI-001.1'),
 'POL-AI-001:1.0:AI-001.2:policy-chunking.v1:chunk-001': ('22b07d11d39cdc0dd0406b6dbb033452faecbc1763644658ef970e12760e3bae',
                                                          'policy://POL-AI-001/1.0/section-004/AI-001.2',
                                                          'section-004',
                                                          'AI-001.2'),
 'POL-AI-001:1.0:AI-001.3:policy-chunking.v1:chunk-001': ('0e5716724539aba08b8f4a6c690c91ede4260636327cb0fa0d34ba9c35a2c219',
                                                          'policy://POL-AI-001/1.0/section-004/AI-001.3',
                                                          'section-004',
                                                          'AI-001.3'),
 'POL-AI-001:1.0:AI-001.4:policy-chunking.v1:chunk-001': ('4f5c2d85c36c527bbd2fa99351d1c85ac0d7c3b766f25b478290341ba800a27f',
                                                          'policy://POL-AI-001/1.0/section-004/AI-001.4',
                                                          'section-004',
                                                          'AI-001.4'),
 'POL-AI-001:1.0:AI-001.5:policy-chunking.v1:chunk-001': ('14bf63b3c6456807447f8bdfad82b690d7ea1ace5745e2e037feb70e7f9c8ef3',
                                                          'policy://POL-AI-001/1.0/section-004/AI-001.5',
                                                          'section-004',
                                                          'AI-001.5'),
 'POL-AI-001:1.0:AI-001.6:policy-chunking.v1:chunk-001': ('e1e3c50fb44968831096667d7019d68837217dd4f448a1ece7f7c068dfa939fe',
                                                          'policy://POL-AI-001/1.0/section-004/AI-001.6',
                                                          'section-004',
                                                          'AI-001.6'),
 'POL-AI-001:1.0:AI-002.001:policy-chunking.v1:chunk-001': ('787757f79b91006e48501c8a6aab2d56a6b3c089343340a1ec826fd149f4e873',
                                                            'policy://POL-AI-001/1.0/section-002/AI-002.001',
                                                            'section-002',
                                                            'AI-002.001'),
 'POL-AI-001:1.0:AI-002.002:policy-chunking.v1:chunk-001': ('68c84085a8de9ec516bb2449654f5e4698aff835749eff6325f6643a70a888f3',
                                                            'policy://POL-AI-001/1.0/section-002/AI-002.002',
                                                            'section-002',
                                                            'AI-002.002'),
 'POL-AI-001:1.0:AI-003.001:policy-chunking.v1:chunk-001': ('ee57fd045dfb6e24348d9f3c35c9c01dd9ebb33683c12fe30b8d01030ae54a5c',
                                                            'policy://POL-AI-001/1.0/section-003/AI-003.001',
                                                            'section-003',
                                                            'AI-003.001'),
 'POL-AI-001:1.0:AI-003.002:policy-chunking.v1:chunk-001': ('84b0dc2297acc14a172c93eec99f4d87fffc5edd026476a19104847ff962f826',
                                                            'policy://POL-AI-001/1.0/section-003/AI-003.002',
                                                            'section-003',
                                                            'AI-003.002'),
 'POL-AI-001:1.0:AI-003.003:policy-chunking.v1:chunk-001': ('41c58afdcc2586f82a542ce642a5e545ab4b5b3ef16aabe1ff8cd33847d95f53',
                                                            'policy://POL-AI-001/1.0/section-003/AI-003.003',
                                                            'section-003',
                                                            'AI-003.003'),
 'POL-AI-001:1.0:AI-005.001:policy-chunking.v1:chunk-001': ('b262c4ed2fcbb32df747582aca06635ef1700ff42b55b6ef77e290619a42e51e',
                                                            'policy://POL-AI-001/1.0/section-005/AI-005.001',
                                                            'section-005',
                                                            'AI-005.001'),
 'POL-AI-001:1.0:AI-005.002:policy-chunking.v1:chunk-001': ('016fed2c85344d0a5961978fe44bb85250eb2e02d43037126d4a640aa2d2479e',
                                                            'policy://POL-AI-001/1.0/section-005/AI-005.002',
                                                            'section-005',
                                                            'AI-005.002'),
 'POL-AI-001:1.0:AI-006.001:policy-chunking.v1:chunk-001': ('8888a68952824a487220a821c1411eb5d97cc223130aa1afe9e6725a1fc52bc9',
                                                            'policy://POL-AI-001/1.0/section-006/AI-006.001',
                                                            'section-006',
                                                            'AI-006.001'),
 'POL-AI-001:1.0:AI-006.002:policy-chunking.v1:chunk-001': ('21910ebf17f6b304757072a78d8eb5b9fc8815cc70e7d91c9e45b924da02bd19',
                                                            'policy://POL-AI-001/1.0/section-006/AI-006.002',
                                                            'section-006',
                                                            'AI-006.002'),
 'POL-AI-001:1.0:AI-007.001:policy-chunking.v1:chunk-001': ('23d6308d51298eaf93cd9d7224c1e045a8dfe631cd6e037132e9366a9690674c',
                                                            'policy://POL-AI-001/1.0/section-007/AI-007.001',
                                                            'section-007',
                                                            'AI-007.001'),
 'POL-AI-001:1.0:AI-007.002:policy-chunking.v1:chunk-001': ('37af0b2143cd468d3ed85fc4d0393d016acf9e0f949ad866c29a3456c9050e79',
                                                            'policy://POL-AI-001/1.0/section-007/AI-007.002',
                                                            'section-007',
                                                            'AI-007.002'),
 'POL-DQ-001:1.0:DQ-001.001:policy-chunking.v1:chunk-001': ('dc934a324105262deb375ee40a4675d4d942300ae3123dcf2912f767765c2558',
                                                            'policy://POL-DQ-001/1.0/section-001/DQ-001.001',
                                                            'section-001',
                                                            'DQ-001.001'),
 'POL-DQ-001:1.0:DQ-001.002:policy-chunking.v1:chunk-001': ('d7da9e9f0634dd58c2f15088dfbb38d231a9619ad8f61125ce51839469bda565',
                                                            'policy://POL-DQ-001/1.0/section-001/DQ-001.002',
                                                            'section-001',
                                                            'DQ-001.002'),
 'POL-DQ-001:1.0:DQ-001.1:policy-chunking.v1:chunk-001': ('e511b26fd2a937b9084785a7703bda70f70fe448b4c8cbe13001a506aef338f7',
                                                          'policy://POL-DQ-001/1.0/section-004/DQ-001.1',
                                                          'section-004',
                                                          'DQ-001.1'),
 'POL-DQ-001:1.0:DQ-001.2:policy-chunking.v1:chunk-001': ('61ff3a355858f75cd6f0e63b7aaa177be35c27018bdd34280a60a8025ee00ce5',
                                                          'policy://POL-DQ-001/1.0/section-004/DQ-001.2',
                                                          'section-004',
                                                          'DQ-001.2'),
 'POL-DQ-001:1.0:DQ-001.3:policy-chunking.v1:chunk-001': ('9e7cc4343f274e8ca48b49029b05697f2162a79319d4714ad878778f5e2a20f0',
                                                          'policy://POL-DQ-001/1.0/section-004/DQ-001.3',
                                                          'section-004',
                                                          'DQ-001.3'),
 'POL-DQ-001:1.0:DQ-001.4:policy-chunking.v1:chunk-001': ('77c98c342efdc3a4bec52a59c67c1d40f9db8e4a34836d3ee0196a9b672fd13c',
                                                          'policy://POL-DQ-001/1.0/section-004/DQ-001.4',
                                                          'section-004',
                                                          'DQ-001.4'),
 'POL-DQ-001:1.0:DQ-001.5:policy-chunking.v1:chunk-001': ('fb7b1197875876a5b1681075140f25fa316e8e273cea8bd042869838c952c2d8',
                                                          'policy://POL-DQ-001/1.0/section-004/DQ-001.5',
                                                          'section-004',
                                                          'DQ-001.5'),
 'POL-DQ-001:1.0:DQ-001.6:policy-chunking.v1:chunk-001': ('76c686d3c562f9054990b43d4ef6916bf701c30552e57795ebed0ff2903bbc2b',
                                                          'policy://POL-DQ-001/1.0/section-004/DQ-001.6',
                                                          'section-004',
                                                          'DQ-001.6'),
 'POL-DQ-001:1.0:DQ-001.7:policy-chunking.v1:chunk-001': ('d5bf4764d947340aea37091004a2c5d717c3ddd4a70fd0d214010a9c0f39dd8f',
                                                          'policy://POL-DQ-001/1.0/section-004/DQ-001.7',
                                                          'section-004',
                                                          'DQ-001.7'),
 'POL-DQ-001:1.0:DQ-002.001:policy-chunking.v1:chunk-001': ('96c3a737145abc8bd9aeb36a8fb494419109e2c4e181975e9aba5cd65fcc1ebf',
                                                            'policy://POL-DQ-001/1.0/section-002/DQ-002.001',
                                                            'section-002',
                                                            'DQ-002.001'),
 'POL-DQ-001:1.0:DQ-002.002:policy-chunking.v1:chunk-001': ('a8112cc050bb0e963944bbb6f99b2f6fffca47680e88f88a618cbac53e234ab1',
                                                            'policy://POL-DQ-001/1.0/section-002/DQ-002.002',
                                                            'section-002',
                                                            'DQ-002.002'),
 'POL-DQ-001:1.0:DQ-003.001:policy-chunking.v1:chunk-001': ('4bea9e5a82da9ec7ed43775b1b17eee938a6c53af1fe7c21b3138b73e78d5057',
                                                            'policy://POL-DQ-001/1.0/section-003/DQ-003.001',
                                                            'section-003',
                                                            'DQ-003.001'),
 'POL-DQ-001:1.0:DQ-003.002:policy-chunking.v1:chunk-001': ('2fda22e209eb28c8fb5d4ca37e6ce3b1c27e16141b4e34e4af15946931852d08',
                                                            'policy://POL-DQ-001/1.0/section-003/DQ-003.002',
                                                            'section-003',
                                                            'DQ-003.002'),
 'POL-DQ-001:1.0:DQ-003.003:policy-chunking.v1:chunk-001': ('c7b28108461b5213fa350eba7b863ea6b034fe35a09603f357992a7d0f713686',
                                                            'policy://POL-DQ-001/1.0/section-003/DQ-003.003',
                                                            'section-003',
                                                            'DQ-003.003'),
 'POL-DQ-001:1.0:DQ-005.001:policy-chunking.v1:chunk-001': ('b2df16df42092e0f80b0e547ae9b6e77b9217e624b331523f9b6a8b1da872bff',
                                                            'policy://POL-DQ-001/1.0/section-005/DQ-005.001',
                                                            'section-005',
                                                            'DQ-005.001'),
 'POL-DQ-001:1.0:DQ-005.002:policy-chunking.v1:chunk-001': ('4e8a82a3bece7e2e4823128856219171e2cfc897244f611e83942f039398cb91',
                                                            'policy://POL-DQ-001/1.0/section-005/DQ-005.002',
                                                            'section-005',
                                                            'DQ-005.002'),
 'POL-DQ-001:1.0:DQ-006.001:policy-chunking.v1:chunk-001': ('c105be50dcf17f520b915f53a71ccda6bc60502fa39cbf0dca90c9f0dbfd7b3a',
                                                            'policy://POL-DQ-001/1.0/section-006/DQ-006.001',
                                                            'section-006',
                                                            'DQ-006.001'),
 'POL-DQ-001:1.0:DQ-006.002:policy-chunking.v1:chunk-001': ('2b6458eb2a2bdb2147df35a1483793220597c60385e9c0305fceed4588b43ba9',
                                                            'policy://POL-DQ-001/1.0/section-006/DQ-006.002',
                                                            'section-006',
                                                            'DQ-006.002'),
 'POL-DQ-001:1.0:DQ-007.001:policy-chunking.v1:chunk-001': ('4944cc65c9f541479df821a568763b90f8835950ffff97ea052a6a38529f61bb',
                                                            'policy://POL-DQ-001/1.0/section-007/DQ-007.001',
                                                            'section-007',
                                                            'DQ-007.001'),
 'POL-DQ-001:1.0:DQ-007.002:policy-chunking.v1:chunk-001': ('b1e49be63689bfef6ee001f8c26922dbb18b144ab3628dd339284967cd0f9f2b',
                                                            'policy://POL-DQ-001/1.0/section-007/DQ-007.002',
                                                            'section-007',
                                                            'DQ-007.002'),
 'POL-EV-001:1.0:EV-001.001:policy-chunking.v1:chunk-001': ('344a982a70f4e0fbeb0964eee96395a4c6bc1b58c24cbdec88cceac5f3ba6671',
                                                            'policy://POL-EV-001/1.0/section-001/EV-001.001',
                                                            'section-001',
                                                            'EV-001.001'),
 'POL-EV-001:1.0:EV-001.002:policy-chunking.v1:chunk-001': ('4f7eab989655a69ac58edc205ecf9f7be2446d66125725db1eced63a8cdd4b2c',
                                                            'policy://POL-EV-001/1.0/section-001/EV-001.002',
                                                            'section-001',
                                                            'EV-001.002'),
 'POL-EV-001:1.0:EV-001.1:policy-chunking.v1:chunk-001': ('83bd294c193c4088af545d5e67ff603b357087e10b62078fd2b480a7b92a6c45',
                                                          'policy://POL-EV-001/1.0/section-004/EV-001.1',
                                                          'section-004',
                                                          'EV-001.1'),
 'POL-EV-001:1.0:EV-001.2:policy-chunking.v1:chunk-001': ('7eeed9f21c9cd429b804b37eb1e1498c24fb43ef840b440a7acd65fec23a120e',
                                                          'policy://POL-EV-001/1.0/section-004/EV-001.2',
                                                          'section-004',
                                                          'EV-001.2'),
 'POL-EV-001:1.0:EV-001.3:policy-chunking.v1:chunk-001': ('7fdf18e7e8762a9c335ebfaee5b91499cfea8f4336632f4a39c0ef62bb3f7c30',
                                                          'policy://POL-EV-001/1.0/section-004/EV-001.3',
                                                          'section-004',
                                                          'EV-001.3'),
 'POL-EV-001:1.0:EV-001.4:policy-chunking.v1:chunk-001': ('d576ed592187a03b2b4c833c9e7da48ad664acee9e44c462204aa7b705ced5df',
                                                          'policy://POL-EV-001/1.0/section-004/EV-001.4',
                                                          'section-004',
                                                          'EV-001.4'),
 'POL-EV-001:1.0:EV-001.5:policy-chunking.v1:chunk-001': ('f975c22ac2b96e4e6e32c15da59b1d9182712d7b33eaad50b01c58732d5cb2ad',
                                                          'policy://POL-EV-001/1.0/section-004/EV-001.5',
                                                          'section-004',
                                                          'EV-001.5'),
 'POL-EV-001:1.0:EV-001.6:policy-chunking.v1:chunk-001': ('52126afeb893a6f742a21142fd35b2acc55089aedd81653e9e88dfa4abfdda78',
                                                          'policy://POL-EV-001/1.0/section-004/EV-001.6',
                                                          'section-004',
                                                          'EV-001.6'),
 'POL-EV-001:1.0:EV-002.001:policy-chunking.v1:chunk-001': ('7efb1c6483ffab0d6fd63fdaa096469fb6ac9f0ffde0f0cfa824ae7e9b46b74a',
                                                            'policy://POL-EV-001/1.0/section-002/EV-002.001',
                                                            'section-002',
                                                            'EV-002.001'),
 'POL-EV-001:1.0:EV-002.002:policy-chunking.v1:chunk-001': ('4f13c2781e2dc4900e9c261b085d5ebd2a3e400f7aba857da3aae4ce423acc4d',
                                                            'policy://POL-EV-001/1.0/section-002/EV-002.002',
                                                            'section-002',
                                                            'EV-002.002'),
 'POL-EV-001:1.0:EV-003.001:policy-chunking.v1:chunk-001': ('cdedd84a89868c2f85ba19c596de721d5f37e047b443e8765b0a114ef925a282',
                                                            'policy://POL-EV-001/1.0/section-003/EV-003.001',
                                                            'section-003',
                                                            'EV-003.001'),
 'POL-EV-001:1.0:EV-003.002:policy-chunking.v1:chunk-001': ('d1b070bb0d93d164550aa3ac3ffd25765a59241c60e3692330e6c8a6480f9025',
                                                            'policy://POL-EV-001/1.0/section-003/EV-003.002',
                                                            'section-003',
                                                            'EV-003.002'),
 'POL-EV-001:1.0:EV-003.003:policy-chunking.v1:chunk-001': ('58eecea9304df5056bec36effbaeaf1eae1ff203b9dbc3f8bdd38d5c58bf6835',
                                                            'policy://POL-EV-001/1.0/section-003/EV-003.003',
                                                            'section-003',
                                                            'EV-003.003'),
 'POL-EV-001:1.0:EV-005.001:policy-chunking.v1:chunk-001': ('511df5c33e6b9b8886f1371c7a09712250e04c4ad99e04cac46c363254e6960c',
                                                            'policy://POL-EV-001/1.0/section-005/EV-005.001',
                                                            'section-005',
                                                            'EV-005.001'),
 'POL-EV-001:1.0:EV-005.002:policy-chunking.v1:chunk-001': ('41799b37369228fb26a93d02e5f8287a4e9ab9666f7a7c1ad32e75c4803bf40d',
                                                            'policy://POL-EV-001/1.0/section-005/EV-005.002',
                                                            'section-005',
                                                            'EV-005.002'),
 'POL-EV-001:1.0:EV-006.001:policy-chunking.v1:chunk-001': ('0d8d272e78eb53104f563bba779d4f169a2cc9f6546b56fc32f59c679d582404',
                                                            'policy://POL-EV-001/1.0/section-006/EV-006.001',
                                                            'section-006',
                                                            'EV-006.001'),
 'POL-EV-001:1.0:EV-006.002:policy-chunking.v1:chunk-001': ('afb4de03f953e81efcf499aaf677078a32c8e152bb5076243d9b78ee2f16138d',
                                                            'policy://POL-EV-001/1.0/section-006/EV-006.002',
                                                            'section-006',
                                                            'EV-006.002'),
 'POL-EV-001:1.0:EV-007.001:policy-chunking.v1:chunk-001': ('da3356de9ef92fc8131218ab65bedd08acbf4111fc305c93c88026a5b869b1ab',
                                                            'policy://POL-EV-001/1.0/section-007/EV-007.001',
                                                            'section-007',
                                                            'EV-007.001'),
 'POL-EV-001:1.0:EV-007.002:policy-chunking.v1:chunk-001': ('7d5a5c8328a0bcaeb6acf8ef97236d06b20caeeddd12e9f27b51c7362a36ccd8',
                                                            'policy://POL-EV-001/1.0/section-007/EV-007.002',
                                                            'section-007',
                                                            'EV-007.002'),
 'POL-GOV-001:1.0:GOV-001.001:policy-chunking.v1:chunk-001': ('bca42718bb02ec50bc347483e05527346c51f9cddfc5ac16460cbbb3a72f721b',
                                                              'policy://POL-GOV-001/1.0/section-001/GOV-001.001',
                                                              'section-001',
                                                              'GOV-001.001'),
 'POL-GOV-001:1.0:GOV-001.002:policy-chunking.v1:chunk-001': ('d301ae06aad149513a747117a1dc68063e03a7825f3a5c0519593e6de1fa8ac9',
                                                              'policy://POL-GOV-001/1.0/section-001/GOV-001.002',
                                                              'section-001',
                                                              'GOV-001.002'),
 'POL-GOV-001:1.0:GOV-001.1:policy-chunking.v1:chunk-001': ('f08851158127323d1ae58e8838a480e1541ee08e1302248ff5580c8b87143f62',
                                                            'policy://POL-GOV-001/1.0/section-004/GOV-001.1',
                                                            'section-004',
                                                            'GOV-001.1'),
 'POL-GOV-001:1.0:GOV-001.2:policy-chunking.v1:chunk-001': ('f11bf965f18556ba719479751c94672a29badfddbd3a1e9bd00042cbdd8dd862',
                                                            'policy://POL-GOV-001/1.0/section-004/GOV-001.2',
                                                            'section-004',
                                                            'GOV-001.2'),
 'POL-GOV-001:1.0:GOV-001.3:policy-chunking.v1:chunk-001': ('a7511add51f14398955f93ed5ac49ae3b2a16ddadeef32368995fff1edc3ff7f',
                                                            'policy://POL-GOV-001/1.0/section-004/GOV-001.3',
                                                            'section-004',
                                                            'GOV-001.3'),
 'POL-GOV-001:1.0:GOV-001.4:policy-chunking.v1:chunk-001': ('1b78be83fa78d325d51ad5ff561519b0268504e7e25a4df273375276a59eec7a',
                                                            'policy://POL-GOV-001/1.0/section-004/GOV-001.4',
                                                            'section-004',
                                                            'GOV-001.4'),
 'POL-GOV-001:1.0:GOV-001.5:policy-chunking.v1:chunk-001': ('0686087495c2ee9da75c234a171c3e51a64e07638bf413618059be2afb974b90',
                                                            'policy://POL-GOV-001/1.0/section-004/GOV-001.5',
                                                            'section-004',
                                                            'GOV-001.5'),
 'POL-GOV-001:1.0:GOV-001.6:policy-chunking.v1:chunk-001': ('79539e52878d2e08d9973d646755c3177debc94613ace6b035ac83655d74f324',
                                                            'policy://POL-GOV-001/1.0/section-004/GOV-001.6',
                                                            'section-004',
                                                            'GOV-001.6'),
 'POL-GOV-001:1.0:GOV-002.001:policy-chunking.v1:chunk-001': ('56ecd3354e29b836e3a6d07891721a9837c1541841faebeda58f717866a2eae5',
                                                              'policy://POL-GOV-001/1.0/section-002/GOV-002.001',
                                                              'section-002',
                                                              'GOV-002.001'),
 'POL-GOV-001:1.0:GOV-002.002:policy-chunking.v1:chunk-001': ('fe04541a5b1d59d5d927be690492299ae61472ec1063b86da84032fdb7c87c96',
                                                              'policy://POL-GOV-001/1.0/section-002/GOV-002.002',
                                                              'section-002',
                                                              'GOV-002.002'),
 'POL-GOV-001:1.0:GOV-003.001:policy-chunking.v1:chunk-001': ('f8c94782dd5473f0127b83be0da5bec85ca5937dede33fa41faab93483a7eff0',
                                                              'policy://POL-GOV-001/1.0/section-003/GOV-003.001',
                                                              'section-003',
                                                              'GOV-003.001'),
 'POL-GOV-001:1.0:GOV-003.002:policy-chunking.v1:chunk-001': ('5dbeca621dee1306ca5b7e6610a5a12451d3f3e65ca9094e0084bc277fbbf9f9',
                                                              'policy://POL-GOV-001/1.0/section-003/GOV-003.002',
                                                              'section-003',
                                                              'GOV-003.002'),
 'POL-GOV-001:1.0:GOV-003.003:policy-chunking.v1:chunk-001': ('13a529794e9ea69f8d2ce95dc293c3331fbe55e2813ae2d527976a9dc8e0a32f',
                                                              'policy://POL-GOV-001/1.0/section-003/GOV-003.003',
                                                              'section-003',
                                                              'GOV-003.003'),
 'POL-GOV-001:1.0:GOV-005.001:policy-chunking.v1:chunk-001': ('aea1a2d18aa303b558812fe786b69a93742e464c94296abd813ecb9c1b50070f',
                                                              'policy://POL-GOV-001/1.0/section-005/GOV-005.001',
                                                              'section-005',
                                                              'GOV-005.001'),
 'POL-GOV-001:1.0:GOV-005.002:policy-chunking.v1:chunk-001': ('2ecbc2bcc510662730ef563e14e127018b2b3cc932618b54d36dc3bfee983a2e',
                                                              'policy://POL-GOV-001/1.0/section-005/GOV-005.002',
                                                              'section-005',
                                                              'GOV-005.002'),
 'POL-GOV-001:1.0:GOV-005.003:policy-chunking.v1:chunk-001': ('084cd2b1fb212292267c19926be69713fdf091103d7edea772fca93e07d0f5f2',
                                                              'policy://POL-GOV-001/1.0/section-005/GOV-005.003',
                                                              'section-005',
                                                              'GOV-005.003'),
 'POL-GOV-001:1.0:GOV-006.001:policy-chunking.v1:chunk-001': ('c9779fab3df92a358c856f1a35e773dbf4ac61525d7812751993c93acec36c23',
                                                              'policy://POL-GOV-001/1.0/section-006/GOV-006.001',
                                                              'section-006',
                                                              'GOV-006.001'),
 'POL-GOV-001:1.0:GOV-006.002:policy-chunking.v1:chunk-001': ('7ab16531bd1137d80abe8b8513d0933386ce5a710c83421bf75ba8307caf1307',
                                                              'policy://POL-GOV-001/1.0/section-006/GOV-006.002',
                                                              'section-006',
                                                              'GOV-006.002'),
 'POL-GOV-001:1.0:GOV-007.001:policy-chunking.v1:chunk-001': ('09ecb9653f871e3d6e37bb565480ee62c6a4564ea4ecc5135ce19cc8b0170193',
                                                              'policy://POL-GOV-001/1.0/section-007/GOV-007.001',
                                                              'section-007',
                                                              'GOV-007.001'),
 'POL-GOV-001:1.0:GOV-007.002:policy-chunking.v1:chunk-001': ('12f98a8c3d1fb57e2f8c78f9e0145c9e83f528f0f43c5d60bbd774879427e812',
                                                              'policy://POL-GOV-001/1.0/section-007/GOV-007.002',
                                                              'section-007',
                                                              'GOV-007.002'),
 'POL-MR-001:1.0:MR-001.001:policy-chunking.v1:chunk-001': ('f46bbd590387b74bbb30f3bacdb64365fbe45ebd8db8eb6d6404ca032c8f3d6d',
                                                            'policy://POL-MR-001/1.0/section-001/MR-001.001',
                                                            'section-001',
                                                            'MR-001.001'),
 'POL-MR-001:1.0:MR-001.002:policy-chunking.v1:chunk-001': ('010d17ad0f11a1b7f83aa6a43aa55d1e81770d06993bb7e1f11ff8f7a0f1b853',
                                                            'policy://POL-MR-001/1.0/section-001/MR-001.002',
                                                            'section-001',
                                                            'MR-001.002'),
 'POL-MR-001:1.0:MR-001.1:policy-chunking.v1:chunk-001': ('8db2cdd450ac17039cd25413df9a83c5510fc017c57b21a794bf04e303b24e91',
                                                          'policy://POL-MR-001/1.0/section-004/MR-001.1',
                                                          'section-004',
                                                          'MR-001.1'),
 'POL-MR-001:1.0:MR-001.2:policy-chunking.v1:chunk-001': ('a8af89cacbf09f46ce11b3f7a4a965095d66bfe2441fe7573da7738aebe1c6b6',
                                                          'policy://POL-MR-001/1.0/section-004/MR-001.2',
                                                          'section-004',
                                                          'MR-001.2'),
 'POL-MR-001:1.0:MR-001.3:policy-chunking.v1:chunk-001': ('06b4c0921f57271fa2d2e5972ceefde57e8aab45f8f4adf8208395a410e264b0',
                                                          'policy://POL-MR-001/1.0/section-004/MR-001.3',
                                                          'section-004',
                                                          'MR-001.3'),
 'POL-MR-001:1.0:MR-001.4:policy-chunking.v1:chunk-001': ('464a169cc1af63d3e27afe34bd41387fa28d26c1ff08888e9e917306dc832582',
                                                          'policy://POL-MR-001/1.0/section-004/MR-001.4',
                                                          'section-004',
                                                          'MR-001.4'),
 'POL-MR-001:1.0:MR-001.5:policy-chunking.v1:chunk-001': ('adfd962ede4cee2fdfe61a78edf12a586e20a305c7eebce735ca96eb89a384b0',
                                                          'policy://POL-MR-001/1.0/section-004/MR-001.5',
                                                          'section-004',
                                                          'MR-001.5'),
 'POL-MR-001:1.0:MR-002.001:policy-chunking.v1:chunk-001': ('5c03d2aaa667d9452661fbb8ad6353974206bebe4a1a1a0ba18b10fe81eab409',
                                                            'policy://POL-MR-001/1.0/section-002/MR-002.001',
                                                            'section-002',
                                                            'MR-002.001'),
 'POL-MR-001:1.0:MR-002.002:policy-chunking.v1:chunk-001': ('3952d084ebf2837918186ecf33d74d2c580c70b9f19a5b02d2263f0228a1ad8a',
                                                            'policy://POL-MR-001/1.0/section-002/MR-002.002',
                                                            'section-002',
                                                            'MR-002.002'),
 'POL-MR-001:1.0:MR-003.001:policy-chunking.v1:chunk-001': ('55a8bcf5c6a0745ef2f0726cbbe6f1e8709de704022415a8edb28bd3f20c6cec',
                                                            'policy://POL-MR-001/1.0/section-003/MR-003.001',
                                                            'section-003',
                                                            'MR-003.001'),
 'POL-MR-001:1.0:MR-003.002:policy-chunking.v1:chunk-001': ('02b294566f8b2d17f095981b2866a3bca8253572c805be914659b63399668392',
                                                            'policy://POL-MR-001/1.0/section-003/MR-003.002',
                                                            'section-003',
                                                            'MR-003.002'),
 'POL-MR-001:1.0:MR-003.003:policy-chunking.v1:chunk-001': ('d9c85cd23fac04c80b647826a14adc003f53490d2066f48259f6800985af041b',
                                                            'policy://POL-MR-001/1.0/section-003/MR-003.003',
                                                            'section-003',
                                                            'MR-003.003'),
 'POL-MR-001:1.0:MR-005.001:policy-chunking.v1:chunk-001': ('6bf0aeaccebd82e6d3d2a161b1e2cd7764cd27b0f44bf22328c192353deb735f',
                                                            'policy://POL-MR-001/1.0/section-005/MR-005.001',
                                                            'section-005',
                                                            'MR-005.001'),
 'POL-MR-001:1.0:MR-005.002:policy-chunking.v1:chunk-001': ('1aebd2f576bf36be9f2545553fe87b8db42bb8b251bfe1001ba501fb3520da66',
                                                            'policy://POL-MR-001/1.0/section-005/MR-005.002',
                                                            'section-005',
                                                            'MR-005.002'),
 'POL-MR-001:1.0:MR-006.001:policy-chunking.v1:chunk-001': ('49061b24e290713895928c9dc8396cf7f1ad5e96899a68ac8109bfdfa64fe8e3',
                                                            'policy://POL-MR-001/1.0/section-006/MR-006.001',
                                                            'section-006',
                                                            'MR-006.001'),
 'POL-MR-001:1.0:MR-006.002:policy-chunking.v1:chunk-001': ('70dfe8017e449218a4f74d30725fead19eb0182d07e6f3625ae23fc9e1631531',
                                                            'policy://POL-MR-001/1.0/section-006/MR-006.002',
                                                            'section-006',
                                                            'MR-006.002'),
 'POL-MR-001:1.0:MR-007.001:policy-chunking.v1:chunk-001': ('49a1f35dafd2e0f9290cfad71e659a1ef01a006cec856c2ba0f817c5bb9219f0',
                                                            'policy://POL-MR-001/1.0/section-007/MR-007.001',
                                                            'section-007',
                                                            'MR-007.001'),
 'POL-MR-001:1.0:MR-007.002:policy-chunking.v1:chunk-001': ('cc4003673809fe26790a878213b8a9a5d767be0022afc9d78c6c098d36568db5',
                                                            'policy://POL-MR-001/1.0/section-007/MR-007.002',
                                                            'section-007',
                                                            'MR-007.002'),
 'POL-VER-001:1.0:VER-001.001:policy-chunking.v1:chunk-001': ('1808ab3c74792f6c2fae1052b46c4a83381689d0d43b39af47dc18590dd942fb',
                                                              'policy://POL-VER-001/1.0/section-001/VER-001.001',
                                                              'section-001',
                                                              'VER-001.001'),
 'POL-VER-001:1.0:VER-001.002:policy-chunking.v1:chunk-001': ('1780dc640305bc0e62d7b954c1777edb2f229c9b82d5f27b334920ba615e0c6b',
                                                              'policy://POL-VER-001/1.0/section-001/VER-001.002',
                                                              'section-001',
                                                              'VER-001.002'),
 'POL-VER-001:1.0:VER-001.1:policy-chunking.v1:chunk-001': ('ce43082bd7bb023148550893ebb3c41ea675bb6c1390938f18be36d74ba94303',
                                                            'policy://POL-VER-001/1.0/section-004/VER-001.1',
                                                            'section-004',
                                                            'VER-001.1'),
 'POL-VER-001:1.0:VER-001.2:policy-chunking.v1:chunk-001': ('4127448da064e22e061da4454cb2aff543246cfaa7c977813395ac2838304435',
                                                            'policy://POL-VER-001/1.0/section-004/VER-001.2',
                                                            'section-004',
                                                            'VER-001.2'),
 'POL-VER-001:1.0:VER-001.3:policy-chunking.v1:chunk-001': ('c453d66ab21c689457904a78cc702e9e7cde475361edeab8ce5c8488925070ff',
                                                            'policy://POL-VER-001/1.0/section-004/VER-001.3',
                                                            'section-004',
                                                            'VER-001.3'),
 'POL-VER-001:1.0:VER-001.4:policy-chunking.v1:chunk-001': ('0d881fbe7fd7342e2aa471f6e04c00a92c201cc38f16e14df5f682b26f0aee71',
                                                            'policy://POL-VER-001/1.0/section-004/VER-001.4',
                                                            'section-004',
                                                            'VER-001.4'),
 'POL-VER-001:1.0:VER-001.5:policy-chunking.v1:chunk-001': ('5170bfbfbaf9d4be3a1eec922e852b2912ead35a0c81426b4fd16e732eafcafa',
                                                            'policy://POL-VER-001/1.0/section-004/VER-001.5',
                                                            'section-004',
                                                            'VER-001.5'),
 'POL-VER-001:1.0:VER-002.001:policy-chunking.v1:chunk-001': ('79949bafdacfca67bd8a01000e7dc3aeeb9376239e3c31079254cef6625e0290',
                                                              'policy://POL-VER-001/1.0/section-002/VER-002.001',
                                                              'section-002',
                                                              'VER-002.001'),
 'POL-VER-001:1.0:VER-002.002:policy-chunking.v1:chunk-001': ('56388a7f60e0cc2b687fc4ba1953fc799ed7e8547b3de3e5490f090a4ca3e1b1',
                                                              'policy://POL-VER-001/1.0/section-002/VER-002.002',
                                                              'section-002',
                                                              'VER-002.002'),
 'POL-VER-001:1.0:VER-003.001:policy-chunking.v1:chunk-001': ('ce98ef517d172c91383366d6f6db396a24fe181ceaff7adf89f9deb842781cfb',
                                                              'policy://POL-VER-001/1.0/section-003/VER-003.001',
                                                              'section-003',
                                                              'VER-003.001'),
 'POL-VER-001:1.0:VER-003.002:policy-chunking.v1:chunk-001': ('fedc5def609dbcd3e1abf20e8bc863b292ede752940cd9a98665f1cfd58fe0ef',
                                                              'policy://POL-VER-001/1.0/section-003/VER-003.002',
                                                              'section-003',
                                                              'VER-003.002'),
 'POL-VER-001:1.0:VER-003.003:policy-chunking.v1:chunk-001': ('53c09233ed17065e98ea17a4eaf5f27e33186db3aa5d4b5fec21144494aadd0b',
                                                              'policy://POL-VER-001/1.0/section-003/VER-003.003',
                                                              'section-003',
                                                              'VER-003.003'),
 'POL-VER-001:1.0:VER-005.001:policy-chunking.v1:chunk-001': ('4ce739898715d2d1906a656b6c0fba830959e3a16e27eee00555d2845aac2ab3',
                                                              'policy://POL-VER-001/1.0/section-005/VER-005.001',
                                                              'section-005',
                                                              'VER-005.001'),
 'POL-VER-001:1.0:VER-005.002:policy-chunking.v1:chunk-001': ('703286fa50cd2239f5b43e4d43f7f29e43fed4020364a3234ba962e869df6afb',
                                                              'policy://POL-VER-001/1.0/section-005/VER-005.002',
                                                              'section-005',
                                                              'VER-005.002'),
 'POL-VER-001:1.0:VER-006.001:policy-chunking.v1:chunk-001': ('4bbec653809c90405b84bea6b7e47da7e7d51a2b7122b115730dd9ff109ea005',
                                                              'policy://POL-VER-001/1.0/section-006/VER-006.001',
                                                              'section-006',
                                                              'VER-006.001'),
 'POL-VER-001:1.0:VER-006.002:policy-chunking.v1:chunk-001': ('c465038bfa15e60f332ec1e09a6b1f403525ad4c4d18c844ddca72acce330977',
                                                              'policy://POL-VER-001/1.0/section-006/VER-006.002',
                                                              'section-006',
                                                              'VER-006.002'),
 'POL-VER-001:1.0:VER-007.001:policy-chunking.v1:chunk-001': ('ef1c814c8175c6013a712b4dac0e4df628260a7ddb781f7507c2bfbd8cb98342',
                                                              'policy://POL-VER-001/1.0/section-007/VER-007.001',
                                                              'section-007',
                                                              'VER-007.001'),
 'POL-VER-001:1.0:VER-007.002:policy-chunking.v1:chunk-001': ('82c063b6aea27c25163bca578afe964efc7d8f8004bf3f7d31f715689b867989',
                                                              'policy://POL-VER-001/1.0/section-007/VER-007.002',
                                                              'section-007',
                                                              'VER-007.002')}
