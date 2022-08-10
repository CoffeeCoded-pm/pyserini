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
import jsonlines
import spacy
import sys
from REL.mention_detection import MentionDetectionBase
from REL.utils import process_results, split_in_words
from REL.entity_disambiguation import EntityDisambiguation
from REL.ner import Span
from wikimapper import WikiMapper
from typing import Dict, List, Tuple
from tqdm import tqdm

# Spacy Mention Detection class which overrides the NERBase class in the REL entity linking process
class NERSpacyMD(MentionDetectionBase):
    def __init__(self, base_url:str, wiki_version:str, spacy_model:str):
        super().__init__(base_url, wiki_version)
        # we only want to link entities of specific types
        self.ner_labels = ['PERSON', 'NORP', 'FAC', 'ORG', 'GPE', 'LOC', 'PRODUCT', 'EVENT', 'WORK_OF_ART',
                           'LAW', 'LANGUAGE', 'DATE', 'TIME', 'MONEY', 'QUANTITY']
        self.spacy_model = spacy_model
        spacy.prefer_gpu()
        self.tagger = spacy.load(spacy_model)

    # mandatory function which overrides NERBase.predict()
    def predict(self, doc: spacy.tokens.Doc) -> List[Span]:
        spans = []
        for ent in doc.ents:
            if ent.label_ in self.ner_labels:
                spans.append(Span(ent.text, ent.start_char, ent.end_char, 0, ent.label_))
        return spans

    """
    Responsible for finding mentions given a set of documents in a batch-wise manner. More specifically,
    it returns the mention, its left/right context and a set of candidates.
    :return: Dictionary with mentions per document.
    """

    def find_mentions(self, dataset: Dict[str, str]) -> Tuple[Dict[str, List[Dict]], int]:
        results = {}
        total_ment = 0
        for i, doc in tqdm(enumerate(dataset), desc='Finding mentions', total=len(dataset)):
            result_doc = []
            doc_text = dataset[doc]
            spacy_doc = self.tagger(doc_text)
            spans = self.predict(spacy_doc)
            for entity in spans:
                text, start_pos, end_pos, conf, tag = (
                    entity.text,
                    entity.start_pos,
                    entity.end_pos,
                    entity.score,
                    entity.tag,
                )
                m = self.preprocess_mention(text)
                cands = self.get_candidates(m)
                if len(cands) == 0:
                    continue
                total_ment += 1
                # Re-create ngram as 'text' is at times changed by Flair (e.g. double spaces are removed).
                ngram = doc_text[start_pos:end_pos]
                left_ctxt = " ".join(split_in_words(doc_text[:start_pos])[-100:])
                right_ctxt = " ".join(split_in_words(doc_text[end_pos:])[:100])
                res = {
                    "mention": m,
                    "context": (left_ctxt, right_ctxt),
                    "candidates": cands,
                    "gold": ["NONE"],
                    "pos": start_pos,
                    "sent_idx": 0,
                    "ngram": ngram,
                    "end_pos": end_pos,
                    "sentence": doc_text,
                    "conf_md": conf,
                    "tag": tag,
                }
                result_doc.append(res)
            results[doc] = result_doc
        return results, total_ment


# run REL entity linking on processed doc
def rel_entity_linking(docs: Dict[str,str], spacy_model:str, rel_base_url:str, rel_wiki_version:str, rel_ed_model_path:str) -> Dict[str, List[Tuple]]:
    mention_detection = NERSpacyMD(rel_base_url, rel_wiki_version, spacy_model)
    mentions_dataset, _ = mention_detection.find_mentions(docs)
    config = {
        'mode': 'eval',
        'model_path': rel_ed_model_path,
    }
    ed_model = EntityDisambiguation(rel_base_url, rel_wiki_version, config)
    predictions, _ = ed_model.predict(mentions_dataset)

    linked_entities = process_results(mentions_dataset, predictions, docs)
    return linked_entities


# read input pyserini json docs into a dictionary
def read_docs(input_path: str) -> Dict[str, str]:
    docs = {}
    with jsonlines.open(input_path) as reader:
        for obj in tqdm(reader, desc='Reading docs'):
            docs[obj['id']] = obj['contents']
    return docs


# enrich REL entity linking results with entities' wikidata ids, and write final results as json objects
# rel_linked_entities: Tuples of entities are composed by start_pos:int, mention_length:int, ent_text:str, ent_wikipedia_id:str, conf_score:float, ner_score:int, ent_type:str
def enrich_el_results(rel_linked_entities: Dict[str, List[Tuple]], docs: Dict[str, str], wikimapper_index:str) -> List[Dict]:
    wikimapper = WikiMapper(wikimapper_index)
    linked_entities_json = []
    for docid, doc_text in tqdm(docs.items(), desc='Enriching EL results', total=len(rel_linked_entities)):
        if docid not in rel_linked_entities:
            linked_entities_json.append({'id': docid, 'contents': doc_text, 'entities': []})
        else:
            linked_entities_info = []
            ents = rel_linked_entities[docid]
            for start_pos, mention_length, ent_text, ent_wikipedia_id, conf_score, ner_score, ent_type in ents:
                # find entities' wikidata ids using their REL results (i.e. linked wikipedia ids)
                ent_wikipedia_id = ent_wikipedia_id.replace('&amp;', '&')
                ent_wikidata_id = wikimapper.title_to_id(ent_wikipedia_id)

                # write results as json objects
                linked_entities_info.append({'start_pos': start_pos, 'end_pos': start_pos + mention_length, 'ent_text': ent_text,
                                             'wikipedia_id': ent_wikipedia_id, 'wikidata_id': ent_wikidata_id,
                                             'ent_type': ent_type})
            linked_entities_json.append({'id': docid, 'contents': doc_text, 'entities': linked_entities_info})
    return linked_entities_json

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--input_path', type=str, help='path to input texts')
    parser.add_argument('-u', '--rel_base_url', type=str, help='directory containing all required REL data folders')
    parser.add_argument('-m', '--rel_ed_model_path', type=str, help='path to the REL entity disambiguation model')
    parser.add_argument('-v', '--rel_wiki_version', type=str, help='wikipedia corpus version used for REL')
    parser.add_argument('-w', '--wikimapper_index', type=str, help='precomputed index used by Wikimapper')
    parser.add_argument('-s', '--spacy_model', type=str, help='spacy model type')
    parser.add_argument('-o', '--output_path', type=str, help='path to output json file')
    args = parser.parse_args()

    docs = read_docs(args.input_path)
    rel_linked_entities = rel_entity_linking(docs, args.spacy_model, args.rel_base_url, args.rel_wiki_version,
                                             args.rel_ed_model_path)
    linked_entities_json = enrich_el_results(rel_linked_entities, docs, args.wikimapper_index)
    with jsonlines.open(args.output_path, mode='w') as writer:
        writer.write_all(linked_entities_json)


if __name__ == '__main__':
    main()
    sys.exit(0)
