import json
from pathlib import Path
import pytest
from tools.proposal_lifecycle import PullRequest,ProposalError,decide_gate,read_pulls,read_branches,parse_pulls,propose,recovery_action

REPO='pyeuvics/pyeuvics.github.io';BRANCH='automation/source-lock-update-123';SHA='a'*40


def pull(state='open',repository=REPO,number=1,sha=SHA):
    return PullRequest(number,BRANCH,repository,state,sha,f'https://github.com/{REPO}/pull/{number}')


def raw_pull(item):
    return {'number':item.number,'head':{'ref':item.branch,'sha':item.sha,'repo':None if item.repository is None else {'full_name':item.repository}},'state':item.state,'html_url':item.url}


@pytest.mark.parametrize(('state','branches','expected'),[(None,{},True),('open',{},False),('closed',{BRANCH:SHA},True),('merged',{BRANCH:SHA},True),(None,{BRANCH:SHA},False)])
def test_gate_distinguishes_active_closed_merged_and_orphan(state,branches,expected):
    pulls=() if state is None else (pull('closed' if state=='merged' else state),)
    assert decide_gate(pulls,branches,REPO).proceed is expected


def test_deleted_head_repository_cannot_authorize_cleanup():
    item=pull(repository=None)
    assert not decide_gate((item,),{BRANCH:SHA},REPO).proceed
    assert recovery_action((item,),{BRANCH:SHA},REPO,BRANCH,SHA)==('retain',None)


def test_fork_pull_request_does_not_associate_local_branch():
    assert not decide_gate((pull(repository='someone/fork'),),{BRANCH:SHA},REPO).proceed


def test_paginated_discovery_includes_last_page():
    calls=[]
    def run(arguments):calls.append(arguments);return json.dumps([[],[],[raw_pull(pull())]])
    result=read_pulls(run,REPO)
    assert result==(pull(),)
    assert '--paginate' in calls[0] and '--slurp' in calls[0]
    assert not decide_gate(result,{},REPO).proceed


@pytest.mark.parametrize('response',['null','{}','[]','[{}]','[[false]]','[[{"number":true}]]'])
def test_malformed_github_response_never_means_no_proposals(response):
    with pytest.raises(ProposalError):parse_pulls(response,REPO)


def test_github_and_git_errors_are_not_empty_results():
    def unavailable(arguments):raise ProposalError('API unavailable')
    with pytest.raises(ProposalError):read_pulls(unavailable,REPO)
    with pytest.raises(ProposalError):read_branches(unavailable)


class FakeRunner:
    def __init__(self,mode='success'):
        self.mode=mode;self.calls=[];self.branches={};self.pulls=[];self.pushed=False
    def __call__(self,args):
        self.calls.append(args)
        if args[:2]==['gh','api']:
            if self.pushed and self.mode=='lookup-failure':raise ProposalError('API failure')
            return json.dumps([[raw_pull(item) for item in self.pulls]])
        if args[:2]==['git','ls-remote']:return ''.join(sha+'\trefs/heads/'+branch+'\n' for branch,sha in self.branches.items())
        if args[:2]==['git','status']:return '' if self.mode=='no-change' else ' M sources.lock.yml\0'
        if args[:2]==['git','rev-parse']:return SHA+'\n'
        if args[:2]==['git','push']:
            if args[-1].startswith(':'):
                if self.mode=='cleanup-failure':raise ProposalError('delete failed')
                assert args[-1]==':refs/heads/'+BRANCH
                assert '--force-with-lease=refs/heads/'+BRANCH+':'+SHA in args
                self.branches.pop(BRANCH);return ''
            assert '--force-with-lease=refs/heads/'+BRANCH+':' in args
            if self.mode=='push-before':raise ProposalError('push failed')
            self.pushed=True;self.branches[BRANCH]='b'*40 if self.mode=='changed-remote' else SHA
            if self.mode=='cancel':raise KeyboardInterrupt()
            if self.mode in {'push-after','changed-remote'}:raise ProposalError('lost push response')
            return ''
        if args[:3]==['gh','pr','create']:
            if self.mode in {'pr-failure','cleanup-failure','lookup-failure'}:raise ProposalError('create failed')
            self.pulls.append(pull())
            if self.mode=='lost-pr-response':raise ProposalError('lost create response')
            return pull().url+'\n'
        return ''


@pytest.mark.parametrize('mode',['success','no-change','push-before','push-after','pr-failure','lost-pr-response','cancel','cleanup-failure','lookup-failure','changed-remote'])
def test_proposal_and_recovery_only_touch_the_owned_ref(mode,tmp_path: Path):
    body=tmp_path/'body.md';body.write_text('review',encoding='utf-8');run=FakeRunner(mode)
    if mode in {'success','no-change','lost-pr-response'}:
        assert propose(run,REPO,BRANCH,body,True)==('no-change' if mode=='no-change' else pull().url)
    elif mode=='cancel':
        with pytest.raises(KeyboardInterrupt):propose(run,REPO,BRANCH,body,True)
    else:
        with pytest.raises(ProposalError):propose(run,REPO,BRANCH,body,True)
    if mode in {'push-before','push-after','pr-failure','cancel','no-change'}:assert not run.branches
    else:assert BRANCH in run.branches
    if mode in {'success','lost-pr-response'}:assert run.pulls
    if mode=='no-change':assert not any(args[:2] in [['git','commit'],['git','push']] for args in run.calls)
    deletes=[args for args in run.calls if args[:2]==['git','push'] and args[-1].startswith(':')]
    assert all(args[-1]==':refs/heads/'+BRANCH for args in deletes)
    if mode in {'changed-remote','lookup-failure'}:assert not deletes


def test_mutation_interface_requires_explicit_write_authority(tmp_path: Path):
    run=FakeRunner()
    with pytest.raises(ProposalError,match='explicit'):propose(run,REPO,BRANCH,tmp_path/'body',False)
    assert run.calls==[]


@pytest.mark.parametrize('branch',['main','automation/source-lock-update-manual','automation/other-123','--delete'])
def test_cleanup_rejects_unowned_branch_names(branch):
    with pytest.raises(ProposalError):recovery_action((),{branch:SHA},REPO,branch,SHA)
