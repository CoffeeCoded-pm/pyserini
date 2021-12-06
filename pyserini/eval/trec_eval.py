#
# Pyserini: Reproducible IR research with sparse and dense representations
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import subprocess
import sys
import platform
import pandas as pd
import tempfile

from pyserini.search import get_qrels_file
from pyserini.util import download_evaluation_script

script_path = download_evaluation_script('trec_eval')
cmd_prefix = ['java', '-jar', script_path]
args = sys.argv
# Option to discard non-judged hits in run file
judged_only = ''
judgeds = []
cutoffs = [10, 20]
if '-judged-only' in args:
    judged_only = args.pop(args.index('-judged-only'))
if any([i.startswith('-cutoffs.') for i in args]):
    cutoffs = args.pop([i.startswith('-cutoffs.') for i in args].index(True))
    cutoffs = list(map(int, cutoffs[9:].split(',')))
temp_file = ''

if len(args) > 1:
    if not os.path.exists(args[-2]):
        args[-2] = get_qrels_file(args[-2])
    if os.path.exists(args[-1]):
        # Convert run to trec if it's on msmarco
        with open(args[-1]) as f:
            first_line = f.readline()
        if 'Q0' not in first_line:
            temp_file = tempfile.NamedTemporaryFile(delete=False).name
            print('msmarco run detected. Converting to trec...')
            run = pd.read_csv(args[-1], delim_whitespace=True, header=None, names=['query_id', 'doc_id', 'rank'])
            run['score'] = 1 / run['rank']
            run.insert(1, 'Q0', 'Q0')
            run['name'] = 'TEMPRUN'
            run.to_csv(temp_file, sep='\t', header=None, index=None)
            args[-1] = temp_file

    run = pd.read_csv(args[-1], delim_whitespace=True, header=None)
    qrels = pd.read_csv(args[-2], delim_whitespace=True, header=None)
    # Discard non-judged hits
    if judged_only:
        if not temp_file:
            temp_file = tempfile.NamedTemporaryFile(delete=False).name
        judged_indexes = pd.merge(run[[0,2]].reset_index(), qrels[[0,2]], on = [0,2])['index']
        run = run.loc[judged_indexes]
        run.to_csv(temp_file, sep='\t', header=None, index=None)
        args[-1] = temp_file
    # Measure judged@cutoffs
    for cutoff in cutoffs:
        run_cutoff = run.groupby(0).head(cutoff)
        judged = len(pd.merge(run_cutoff[[0,2]], qrels[[0,2]], on = [0,2])) / len(run_cutoff)
        judgeds.append(f'J@{cutoff}: {judged}')
    cmd = cmd_prefix + args[1:]
else:
    cmd = cmd_prefix
print(f'Running command: {cmd}')
shell = platform.system() == "Windows"
process = subprocess.Popen(cmd,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           shell=shell)
stdout, stderr = process.communicate()
if stderr:
    print(stderr.decode("utf-8"))
print('Results:')
print(stdout.decode("utf-8"))
if temp_file:
    os.remove(temp_file)
for judged in judgeds:
    print(judged)