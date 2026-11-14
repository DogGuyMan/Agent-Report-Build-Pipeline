"""Read-only repository review; all specimen files live in a temporary directory."""
import contextlib
from collections import Counter
import io
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / p) for p in (
    'src', 'src/codewiki/python/runner', 'src/codewiki/python/machine')]
import verify_graph as V
import survey_plan
import terms_db
import normalize
from core import pipeline as P
from mode1 import context as X, edges as E, graph as G
from codewiki.python.runner.wiki import prep, compdb


def node(id, name='pkg.f', module='pkg'):
    return dict(id=id, name=name, kind='function', module=module, file='a.py', line=1)


def graph():
    return dict(schema_version=2, language='python', platform='linux', source_tool='probe',
                repo_commit=None, nodes=[node('C1')], edges=[],
                modules=[dict(id='pkg', depends_on=[])])


with tempfile.TemporaryDirectory() as tmp:
    repo = Path(tmp)
    raw = repo / 'out/codegraph-raw'
    raw.mkdir(parents=True)
    src = repo / 'a.py'
    src.write_text('def f(): return 1\n')
    cg, passed, faults = [raw / p for p in ('codegraph.json', 'graph-verified.json', 'graph-faults.json')]
    ctx = X.Mode1Context(root=str(ROOT), model='never-called', repo=tmp, cold=True)
    results = {}

    cg.write_text('{')
    pipeline = E.build_mode1_graph(ctx, only=['verify-graph'], skip=None)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        rows = P.Pipeline().run(pipeline, ctx)
    results['broken_json_pipeline'] = dict(ok=rows[0]['ok'], faults=faults.exists(),
                                         handoff=(raw / 'graph-handoff.md').exists(), why=rows[0]['why'])

    cg.write_text(json.dumps(graph()))
    before = V.verify(str(cg), tmp)
    passed.write_text(json.dumps(before))
    src.write_text('def completely_different(): return 2\n')
    results['same_line_source_replacement'] = dict(before=before['status'],
        after=V.verify(str(cg), tmp)['status'],
        accepted_receipt=not G.ScheduleBatchesStage.stale_verification(str(cg), str(passed)))
    src.unlink()
    unchecked = V.verify(str(cg), None)
    passed.write_text(json.dumps(unchecked))
    results['v3_skipped'] = dict(with_repo=V.verify(str(cg), tmp)['status'], without_repo=unchecked['status'],
        accepted_receipt=not G.ScheduleBatchesStage.stale_verification(str(cg), str(passed)))
    src.write_text('def f(): return 1\n')

    batch_plan = survey_plan.plan(graph(), 8)
    (raw / 'batches.json').write_text(json.dumps(batch_plan))
    cg.write_text('{')
    passed.unlink()
    pipeline = E.build_mode1_graph(ctx, only=['annotate-symbols'], skip=None)
    results['annotate_only_without_verified_graph'] = dict(order=pipeline.order,
        missing_reads=P.missing_reads(pipeline.stages['annotate-symbols'], ctx))

    g = graph()
    g['language'] = 'csharp'
    (repo / 'a.cs').write_text('class P { void f(int x) {} void f(float x) {} }\n')
    g['nodes'] = [node('cs:pkg.f(int)'), node('cs:pkg.f(float)')]
    for n in g['nodes']:
        n['file'] = 'a.cs'
    cg.write_text(json.dumps(g))
    terms = terms_db.build_terms(g, {}, [])
    results['unique_ids_duplicate_names'] = dict(status=V.verify(str(cg), tmp)['status'],
        graph_symbols=len(g['nodes']), term_symbols=len([r for r in terms.values() if r['kind'] != 'module']),
        retained_id=terms['pkg.f']['id'])

    g = graph()
    g['nodes'].append(node('C2', 'pkg2.g', 'pkg2'))
    g['edges'] = [dict({'from':'C1', 'to':'C2'}, kind='dependency', label='call', file='a.py', line=1, occurrences=-5)]
    g['modules'].append(dict(id='pkg2', depends_on=[]))
    cg.write_text(json.dumps(g))
    results['missing_module_dependency_and_negative_occurrences'] = V.verify(str(cg), tmp)['status']

    g = graph()
    g['nodes'] = [dict(id='X:std', name='std', kind='external', module='__external__', file=None, line=None)]
    g['modules'] = []
    cg.write_text(json.dumps(g))
    results['external_only_graph'] = V.verify(str(cg), tmp)['status']

    toolroot = repo / 'toolroot'
    for rel in prep.COLLECT_CODE:
        dst = toolroot / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes((ROOT / rel).read_bytes())
    helper = toolroot / 'src/codewiki/python/runner/wiki/compdb.py'
    helper.write_text('before\n')
    fp_before = prep.collect_fingerprint(str(toolroot), {})
    helper.write_text('changed behavior\n')
    results['helper_code_change_invalidates_fingerprint'] = fp_before != prep.collect_fingerprint(str(toolroot), {})
    results['csharp_force_steps'] = prep.prepPlan('roslyn-dump', True, False, True, False, force=True)['steps']
    entries = [dict(file=tmp+'/a.cpp', directory=tmp, command='clang++ -DMODE=1 a.cpp'),
               dict(file=tmp+'/a.cpp', directory=tmp, command='clang++ -DMODE=2 a.cpp')]
    results['build_configuration_merge'] = dict(inputs=len(entries), outputs=len(compdb.mergeEntries([entries], tmp)))

    nodes = {'C1': node('C1'), 'C2': node('C2', 'pkg.g')}
    ids = {'pkg.f':'C1', 'pkg.g':'C2'}
    edges, stats = {}, Counter()
    normalize.merge_py_calls(nodes, ids, edges, {'symbols':[], 'calls':[
        dict(caller='pkg.f', callee='pkg.f', file='a.py', line=1)]}, stats)
    results['recursive_call'] = dict(edges=len(edges), stats=dict(stats))
    edges = {('C1','C2','dependency'):dict({'from':'C1','to':'C2'}, kind='dependency', label='type annotation', file='a.py', line=1)}
    stats = Counter()
    normalize.merge_py_calls(nodes, ids, edges, {'symbols':[], 'calls':[
        dict(caller='pkg.f', callee='pkg.g', file='a.py', line=9)]}, stats)
    results['call_merged_into_type_dependency'] = list(edges.values())
    print(json.dumps(results, ensure_ascii=False, indent=2))
