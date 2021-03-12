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

import unittest
import os
import shutil
from pyserini import search
from pyserini.util import get_cache_home


class TestIndexDownload(unittest.TestCase):

    def test_default_cache(self):
        os.unsetenv('PYSERINI_CACHE')
        search.SimpleSearcher.from_prebuilt_index('robust04')
        print(get_cache_home())
        self.assertTrue(os.path.exists(os.path.expanduser('~/.cache/pyserini/indexes')))

    def test_custom_cache(self):
        os.environ['PYSERINI_CACHE'] = 'temp_dir'
        search.SimpleSearcher.from_prebuilt_index('robust04')
        print(get_cache_home())
        self.assertTrue(os.path.exists('temp_dir/indexes'))

    def tearDown(self):
        if os.path.exists('temp_dir'):
            shutil.rmtree('temp_dir')
