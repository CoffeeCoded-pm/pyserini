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

import argparse
import math
import os
import subprocess
import time
from collections import defaultdict
from string import Template

import yaml

from scripts.repro_matrix.defs_miracl import models, languages, trec_eval_metric_definitions
from scripts.repro_matrix.utils import run_eval_and_return_metric, ok_str, okish_str, fail_str


def print_results(metric, split):
    print(f'Metric = {metric}, Split = {split}')
    print(' ' * 32, end='')
    for lang in languages:
        print(f'{lang[0]:3}    ', end='')
    print('')
    for model in models:
        print(f'{model:30}', end='')
        for lang in languages:
            key = f'{model}.{lang[0]}'
            print(f'{table[key][split][metric]:7.3f}', end='')
        print('')
    print('')


def extract_topic_fn_from_cmd(cmd):
    cmd = cmd.split()
    topic_idx = cmd.index('--topics')
    return cmd[topic_idx + 1]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate regression matrix for MIRACL.')
    parser.add_argument('--skip-eval', action='store_true', default=False, help='Skip running trec_eval.')
    args = parser.parse_args()

    start = time.time()

    table = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0.0)))

    with open('pyserini/resources/miracl.yaml') as f:
        yaml_data = yaml.safe_load(f)
        for condition in yaml_data['conditions']:
            name = condition['name']
            eval_key = condition['eval_key']
            cmd_template = condition['command']

            print(f'condition {name}:')
            lang = name.split('.')[-1]

            for splits in condition['splits']:
                split = splits['split']

                print(f'  - split: {split}')

                runfile = f'runs/run.miracl.{name}.{split}.txt'
                cmd = Template(cmd_template).substitute(split=split, output=runfile)

                # In the yaml file, the topics are written as something like '--topics miracl-v1.0-ar-${split}'
                # This works for the dev split because the topics are directly included in Anserini/Pyserini.
                # For this training split, we have to map the symbol into a file in tools/topics-and-qrels/
                # Here, we assume that the developer has cloned the miracl repo and placed the topics there.
                if split == 'train':
                    cmd = cmd.replace(f'--topics miracl-v1.0-{lang}-{split}',
                                      f'--topics tools/topics-and-qrels/topics.miracl-v1.0-{lang}-{split}.tsv')

                if not os.path.exists(runfile):
                    print(f'    Running: {cmd}')
                    rtn = subprocess.run(cmd.split(), capture_output=True)
                    stderr = rtn.stderr.decode()
                    topic_fn = extract_topic_fn_from_cmd(cmd)
                    if f'ValueError: Topic {topic_fn} Not Found' in stderr:
                        print(f'Skipping {topic_fn}: file not found.')
                        continue

                for expected in splits['scores']:
                    for metric in expected:
                        if not args.skip_eval:
                            # We have the translate the training qrels into a file located in tools/topics-and-qrels/
                            # because they are not included with Anserini/Pyserini by default.
                            # Here, we assume that the developer has cloned the miracl repo and placed the qrels there.
                            if split == 'train':
                                qrels = f'tools/topics-and-qrels/qrels.{eval_key}-train.tsv'
                            else:
                                qrels = f'{eval_key}-{split}'
                            score = float(run_eval_and_return_metric(metric, qrels,
                                                                     trec_eval_metric_definitions[metric], runfile))
                            if math.isclose(score, float(expected[metric])):
                                result_str = ok_str
                            # Flaky test: small difference on Mac Studio (M1 chip)
                            elif name == 'mdpr-tied-pft-msmarco.hi' and split == 'train' \
                                    and math.isclose(score, float(expected[metric]), abs_tol=2e-4):
                                result_str = okish_str
                            else:
                                result_str = fail_str + f' expected {expected[metric]:.4f}'
                            print(f'      {metric:7}: {score:.4f} {result_str}')
                            table[name][split][metric] = score
                        else:
                            table[name][split][metric] = expected[metric]

            print('')

    for metric in ['nDCG@10', 'R@100']:
        for split in ['dev', 'train']:
            print_results(metric, split)

    end = time.time()
    print(f'Total elapsed time: {end - start:.0f}s')
