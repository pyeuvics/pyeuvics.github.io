import yaml
from tests.support.paths import ROOT
from tests.support.workflows import APPROVED_ACTIONS,SETUP_PYTHON,SETUP_VALIDATION,load_setup_action


def test_shared_action_contains_only_python_cache_and_dependency_setup():
    action=load_setup_action()
    assert set(action)=={'name','description','runs'}
    assert action['runs']['using']=='composite'
    steps=action['runs']['steps'];assert len(steps)==2
    assert steps[0]['uses']==SETUP_PYTHON
    assert steps[0]['with']=={'python-version':'3.13','cache':'pip','cache-dependency-path':'requirements-docs.txt\nrequirements-notebooks.txt\nsources.lock.yml\n'}
    assert steps[1]['shell']=='bash'
    assert steps[1]['run']=='python -m pip install -r requirements-docs.txt -r requirements-notebooks.txt'
    assert all(set(step)<= {'name','uses','with','run','shell'} for step in steps)


def test_common_setup_is_before_source_credentials_and_writer_stays_uncached():
    for filename,job in [('site-check.yml','validate'),('pages.yml','build'),('source-update.yml','validate')]:
        data=yaml.load((ROOT/'.github/workflows'/filename).read_text(encoding='utf-8'),Loader=yaml.BaseLoader)
        steps=data['jobs'][job]['steps'];setup=next(i for i,step in enumerate(steps) if step.get('uses')==SETUP_VALIDATION)
        assert setup>0
        for index,step in enumerate(steps):
            if 'create-github-app-token@' in step.get('uses',''):assert setup<index
        if filename=='source-update.yml':
            assert steps[setup]['if']=="steps.gate.outputs.proceed == 'true'"
            writer=data['jobs']['propose']['steps']
            assert all(step.get('uses')!=SETUP_VALIDATION for step in writer)
            python=next(step for step in writer if step.get('uses')==SETUP_PYTHON)
            assert python['with']=={'python-version':'3.13'}


def test_every_workflow_action_matches_independently_reviewed_pins():
    for path in (ROOT/'.github/workflows').glob('*.yml'):
        data=yaml.load(path.read_text(encoding='utf-8'),Loader=yaml.BaseLoader)
        for job in data['jobs'].values():
            for step in job.get('steps',[]):
                if 'uses' in step:assert step['uses'] in APPROVED_ACTIONS
