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
import sys

# Use Pyserini in this repo (as opposed to pip install)
sys.path.insert(0, './')

from pyserini.util import download_url
from pyserini.prebuilt_index_info import TF_INDEX_INFO, IMPACT_INDEX_INFO, FAISS_INDEX_INFO


def check(index):
    for entry in index:
        print(f'# Checking "{entry}"...')
        md5sum = TF_INDEX_INFO[entry]['md5']
        for url in TF_INDEX_INFO[entry]['urls']:
            print(url)
            destination = download_url(url, '.', md5=md5sum)
            print(f'Finished downloading to {destination}, removing...')
            os.remove(destination)
        print('\n')


if __name__ == '__main__':
    check(TF_INDEX_INFO)
    check(IMPACT_INDEX_INFO)
    check(FAISS_INDEX_INFO)
