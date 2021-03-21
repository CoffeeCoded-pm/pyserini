import json
import os

from abc import ABC, abstractmethod
from enum import Enum, unique
from typing import List

from pyserini.search import JSimpleSearcherResult


@unique
class OutputFormat(Enum):
    TREC = 'trec'
    MSMARCO = "msmarco"
    KILT = 'kilt'


class OutputWriter(ABC):

    def __init__(self, file_path: str, mode: str = 'w',
                 max_hits: int = float('inf'), tag: str = None, topics: dict = None,
                 use_max_passage: bool = False, max_passage_delimiter: str = None):
        self.file_path = file_path
        self.mode = mode
        self.max_hits = max_hits
        self.tag = tag
        self.topics = topics
        self.use_max_passage = use_max_passage
        self.max_passage_delimiter = max_passage_delimiter
        self.file = None

    def __enter__(self):
        dirname = os.path.dirname(self.file_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        self.file = open(self.file_path, self.mode)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.file.close()

    def hits_iterator(self, hits: List[JSimpleSearcherResult]):
        unique_docs = set()
        rank = 1
        for hit in hits:
            if self.use_max_passage and self.max_passage_delimiter:
                docid = hit.docid.split(self.max_passage_delimiter)[0]
            else:
                docid = hit.docid.strip()

            if self.use_max_passage:
                if docid in unique_docs:
                    continue
                unique_docs.add(docid)

            yield docid, rank, hit.score, hit

            rank = rank + 1
            if rank > self.max_hits:
                break

    @abstractmethod
    def write(self, topic: str, hits: List[JSimpleSearcherResult]):
        raise NotImplementedError()


class TrecWriter(OutputWriter):
    def write(self, topic: str, hits: List[JSimpleSearcherResult]):
        for docid, rank, score, _ in self.hits_iterator(hits):
            self.file.write(f'{topic} Q0 {docid} {rank} {score:.6f} {self.tag}\n')


class MsMarcoWriter(OutputWriter):
    def write(self, topic: str, hits: List[JSimpleSearcherResult]):
        for docid, rank, score, _ in self.hits_iterator(hits):
            self.file.write(f'{topic}\t{docid}\t{rank}\n')


class KiltWriter(OutputWriter):
    def write(self, topic: str, hits: List[JSimpleSearcherResult]):
        datapoint = self.topics[topic]
        provenance = []
        for docid, rank, score, _ in self.hits_iterator(hits):
            provenance.append({"wikipedia_id": docid})
        datapoint["output"] = [{"provenance": provenance}]
        json.dump(datapoint, self.file)
        self.file.write('\n')


def get_output_writer(file_path: str, output_format: OutputFormat, *args, **kwargs) -> OutputWriter:
    mapping = {
        OutputFormat.TREC: TrecWriter,
        OutputFormat.MSMARCO: MsMarcoWriter,
        OutputFormat.KILT: KiltWriter,
    }
    return mapping[output_format](file_path, *args, **kwargs)
