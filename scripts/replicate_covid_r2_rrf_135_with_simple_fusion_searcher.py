#
# Pyserini: Python interface to the Anserini IR toolkit built on Lucene
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

import sys
sys.path.insert(0, './')

from tqdm import tqdm
from pyserini.trectools import FusionMethod, TrecRun
from pyserini.search import get_topics, SimpleFusionSearcher, SimpleSearcher
import os
import filecmp


if not os.path.exists('lucene-index-cord19-abstract-2020-05-01/'):
    os.system('wget -nc https://www.dropbox.com/s/wxjoe4g71zt5za2/lucene-index-cord19-abstract-2020-05-01.tar.gz')
    os.system('tar -xvzf lucene-index-cord19-abstract-2020-05-01.tar.gz')
    os.system('rm lucene-index-cord19-abstract-2020-05-01.tar.gz')

if not os.path.exists('lucene-index-cord19-full-text-2020-05-01/'):
    os.system('wget -nc https://www.dropbox.com/s/di27r5o2g5kat5k/lucene-index-cord19-full-text-2020-05-01.tar.gz')
    os.system('tar -xvzf lucene-index-cord19-full-text-2020-05-01.tar.gz')
    os.system('rm lucene-index-cord19-full-text-2020-05-01.tar.gz')


if not os.path.exists('lucene-index-cord19-paragraph-2020-05-01/'):
    os.system('wget -nc https://www.dropbox.com/s/6ib71scm925mclk/lucene-index-cord19-paragraph-2020-05-01.tar.gz')
    os.system('tar -xvzf lucene-index-cord19-paragraph-2020-05-01.tar.gz')
    os.system('rm lucene-index-cord19-paragraph-2020-05-01.tar.gz')


if not os.path.exists('anserini.covid-r2.fusion1.txt'):
    os.system('wget -q -nc https://www.dropbox.com/s/wqb0vhxp98g7dxh/anserini.covid-r2.fusion1.txt.gz')
    os.system('gunzip -f anserini.covid-r2.fusion1.txt.gz')


index_dirs = [
    'lucene-index-cord19-abstract-2020-05-01/',
    'lucene-index-cord19-full-text-2020-05-01/',
    'lucene-index-cord19-paragraph-2020-05-01/']

searcher = SimpleFusionSearcher(index_dirs, method=FusionMethod.RRF)

runs,topics = [], get_topics('covid_round2')
for topic in tqdm(sorted(topics.keys())):
    query = topics[topic]['question'] + ' ' + topics[topic]['query']
    hits = searcher.search(query, k=10000)
    docid_score_pair = [(hit.docid, hit.score) for hit in hits]
    run = TrecRun.from_search_results(docid_score_pair, topic=topic)
    runs.append(run)

all_topics_run = TrecRun.concat(runs)
all_topics_run.save_to_txt(output_path='fused.txt', tag='reciprocal_rank_fusion_k=60')

lines1 = [' '.join(line.split(' ')[:3]) for line in open('fused.txt', 'r')]
lines2 = [' '.join(line.split(' ')[:3]) for line in open('anserini.covid-r2.fusion1.txt', 'r')]

for a,b in zip (lines1, lines2):
    if a!=b:
        print('not the same')
    else:
        print('same')
    
    print(a)
    print(b)

os.system("""awk '{print $1" "$3" "$4}' fused.txt > this.txt""")
os.system("""awk '{print $1" "$3" "$4}' anserini.covid-r2.fusion1.txt > that.txt""")

does_match = filecmp.cmp('fused.txt', 'anserini.covid-r2.fusion1.txt')
print('Result does match:', does_match)

# os.system('rm anserini.covid-r2.fusion1.txt fused.txt')
