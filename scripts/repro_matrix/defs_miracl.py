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

languages = [
    ['ar', 'arabic'],
    ['bn', 'bengali'],
    ['en', 'english'],
    ['es', 'spanish'],
    ['fa', 'persian'],
    ['fi', 'finnish'],
    ['fr', 'french'],
    ['hi', 'hindi'],
    ['id', 'indonesian'],
    ['ja', 'japanese'],
    ['ko', 'korean'],
    ['ru', 'russian'],
    ['sw', 'swahili'],
    ['te', 'telugu'],
    ['th', 'thai'],
    ['zh', 'chinese'],
    ['de', 'german'],
    ['yo', 'yoruba']
]

models = ['bm25', 'mdpr-tied-pft-msmarco', 'mdpr-tied-pft-msmarco-ft-all']

html_display = {
    'bm25': 'BM25',
    'mdpr-tied-pft-msmarco': 'mDPR (tied encoders), pre-FT w/ MS MARCO',
    'mdpr-tied-pft-msmarco-ft-all': 'mDPR (tied encoders), pre-FT w/ MS MARCO then FT w/ all Mr. TyDi',
}

trec_eval_metric_definitions = {
    'nDCG@10': '-c -M 100 -m ndcg_cut.10',
    'R@100': '-c -m recall.100',
}
