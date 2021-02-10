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

import os
import unittest

from pyserini import search


class TestLoadTopics(unittest.TestCase):

    def test_robust04(self):
        topics = search.get_topics('robust04')
        self.assertEqual(len(topics), 250)
        self.assertTrue(isinstance(next(iter(topics.keys())), int))

    def test_robust05(self):
        topics = search.get_topics('robust05')
        self.assertEqual(len(topics), 50)
        self.assertTrue(isinstance(next(iter(topics.keys())), int))

    def test_core17(self):
        topics = search.get_topics('core17')
        self.assertEqual(len(topics), 50)
        self.assertTrue(isinstance(next(iter(topics.keys())), int))

    def test_core18(self):
        topics = search.get_topics('core18')
        self.assertEqual(len(topics), 50)
        self.assertTrue(isinstance(next(iter(topics.keys())), int))

    def test_car15(self):
        topics = search.get_topics('car17v1.5-benchmarkY1test')
        self.assertEqual(len(topics), 2125)
        self.assertFalse(isinstance(next(iter(topics.keys())), int))

    def test_car20(self):
        topics = search.get_topics('car17v2.0-benchmarkY1test')
        self.assertEqual(len(topics), 2254)
        self.assertFalse(isinstance(next(iter(topics.keys())), int))

    def test_msmarco_doc(self):
        topics = search.get_topics('msmarco-doc-dev')
        self.assertEqual(len(topics), 5193)
        self.assertTrue(isinstance(next(iter(topics.keys())), int))

    def test_msmarco_passage(self):
        topics = search.get_topics('msmarco-passage-dev-subset')
        self.assertEqual(len(topics), 6980)
        self.assertTrue(isinstance(next(iter(topics.keys())), int))

    def test_nq_dev_dpr(self):
        topics = search.get_topics('nq_dev_dpr')
        self.assertEqual(len(topics), 8757)
        self.assertTrue(isinstance(next(iter(topics.keys())), int))

    def test_nq_test_dpr(self):
        topics = search.get_topics('nq_test_dpr')
        self.assertEqual(len(topics), 3610)
        self.assertTrue(isinstance(next(iter(topics.keys())), int))

    def test_wq_test_dpr(self):
        topics = search.get_topics('wq_test_dpr')
        self.assertEqual(len(topics), 2032)
        self.assertTrue(isinstance(next(iter(topics.keys())), int))

    def test_squad_test_dpr(self):
        topics = search.get_topics('squad_test_dpr')
        self.assertEqual(len(topics), 10570)
        self.assertTrue(isinstance(next(iter(topics.keys())), int))

    def test_curated_test_dpr(self):
        topics = search.get_topics('curated_test_dpr')
        self.assertEqual(len(topics), 694)
        self.assertTrue(isinstance(next(iter(topics.keys())), int))

    def test_trivia_test_dpr(self):
        topics = search.get_topics('trivia_test_dpr')
        self.assertEqual(len(topics), 11313)
        self.assertTrue(isinstance(next(iter(topics.keys())), int))

    def test_trivia_dev_dpr(self):
        topics = search.get_topics('trivia_dev_dpr')
        self.assertEqual(len(topics), 8837)
        self.assertTrue(isinstance(next(iter(topics.keys())), int))

    def test_covid_round1(self):
        topics = search.get_topics('covid-round1')
        self.assertEqual(len(topics), 30)
        self.assertEqual('coronavirus origin', topics[1]['query'])
        self.assertEqual('coronavirus remdesivir', topics[30]['query'])
        self.assertTrue(isinstance(next(iter(topics.keys())), int))

    def test_covid_round1_udel(self):
        topics = search.get_topics('covid-round1-udel')
        self.assertEqual(len(topics), 30)
        self.assertEqual('coronavirus origin origin COVID-19', topics[1]['query'])
        self.assertEqual('coronavirus remdesivir remdesivir effective treatment COVID-19', topics[30]['query'])
        self.assertTrue(isinstance(next(iter(topics.keys())), int))

    def test_covid_round2(self):
        topics = search.get_topics('covid-round2')
        self.assertEqual(len(topics), 35)
        self.assertEqual('coronavirus origin', topics[1]['query'])
        self.assertEqual('coronavirus public datasets', topics[35]['query'])
        self.assertTrue(isinstance(next(iter(topics.keys())), int))

    def test_covid_round2_udel(self):
        topics = search.get_topics('covid-round2-udel')
        self.assertEqual(len(topics), 35)
        self.assertEqual('coronavirus origin origin COVID-19', topics[1]['query'])
        self.assertEqual('coronavirus public datasets public datasets COVID-19', topics[35]['query'])
        self.assertTrue(isinstance(next(iter(topics.keys())), int))

    def test_covid_round3(self):
        topics = search.get_topics('covid-round3')
        self.assertEqual(len(topics), 40)
        self.assertEqual('coronavirus origin', topics[1]['query'])
        self.assertEqual('coronavirus mutations', topics[40]['query'])
        self.assertTrue(isinstance(next(iter(topics.keys())), int))

    def test_covid_round3_udel(self):
        topics = search.get_topics('covid-round3-udel')
        self.assertEqual(len(topics), 40)
        self.assertEqual('coronavirus origin origin COVID-19', topics[1]['query'])
        self.assertEqual('coronavirus mutations observed mutations SARS-CoV-2 genome mutations', topics[40]['query'])
        self.assertTrue(isinstance(next(iter(topics.keys())), int))

    def test_covid_round4(self):
        topics = search.get_topics('covid-round4')
        self.assertEqual(len(topics), 45)
        self.assertEqual('coronavirus origin', topics[1]['query'])
        self.assertEqual('coronavirus mental health impact', topics[45]['query'])
        self.assertTrue(isinstance(next(iter(topics.keys())), int))

    def test_covid_round4_udel(self):
        topics = search.get_topics('covid-round4-udel')
        self.assertEqual(len(topics), 45)
        self.assertEqual('coronavirus origin origin COVID-19', topics[1]['query'])
        self.assertEqual('coronavirus mental health impact COVID-19 pandemic impacted mental health',
                         topics[45]['query'])
        self.assertTrue(isinstance(next(iter(topics.keys())), int))

    def test_trec2018_bl(self):
        topics = search.get_topics('trec2018-bl')
        self.assertEqual(len(topics), 50)
        self.assertEqual('fef0f232a9bd94bdb96bac48c7705503', topics[393]['title'])
        self.assertEqual('a1c41a70-35c7-11e3-8a0e-4e2cf80831fc', topics[825]['title'])
        self.assertTrue(isinstance(next(iter(topics.keys())), int))
    
    def test_trec2019_bl(self):
        topics = search.get_topics('trec2019-bl')
        self.assertEqual(len(topics), 60)
        self.assertEqual('d7d906991e2883889f850de9ae06655e', topics[870]['title'])
        self.assertEqual('0d7f5e24cafc019265d3ee4b9745e7ea', topics[829]['title'])
        self.assertTrue(isinstance(next(iter(topics.keys())), int))

    def test_tsv_int_topicreader(self):
        # Running from command-line, we're in root of repo, but running in IDE, we're in tests/
        path = 'tools/topics-and-qrels/topics.msmarco-doc.dev.txt'
        if not os.path.exists(path):
            path = f'../{path}'

        self.assertTrue(os.path.exists(path))
        topics = search.get_topics_with_reader('io.anserini.search.topicreader.TsvIntTopicReader', path)
        self.assertEqual(len(topics), 5193)
        self.assertTrue(isinstance(next(iter(topics.keys())), int))

        self.assertEqual(search.get_topics('msmarco-doc-dev'), topics)

    def test_trec_topicreader(self):
        # Running from command-line, we're in root of repo, but running in IDE, we're in tests/
        path = 'tools/topics-and-qrels/topics.robust04.txt'
        if not os.path.exists(path):
            path = f'../{path}'

        self.assertTrue(os.path.exists(path))
        topics = search.get_topics_with_reader('io.anserini.search.topicreader.TrecTopicReader', path)
        self.assertEqual(len(topics), 250)
        self.assertTrue(isinstance(next(iter(topics.keys())), int))

        self.assertEqual(search.get_topics('robust04'), topics)


if __name__ == '__main__':
    unittest.main()
