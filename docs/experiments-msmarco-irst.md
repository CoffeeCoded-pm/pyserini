# Pyserini: IRST on MS MARCO Passage and Document

This page describes how to reproduce IRST experiments with the IBM model on the MS MARCO collections.


## Passage Reranking 

### Data Preprocessing

For IRST, we make the corpus as well as the pre-built indexes available to download.

> You can skip the data prep and indexing steps if you use our pre-built indexes. 

Here, we start from MS MARCO [passage corpus](https://github.com/castorini/pyserini/blob/master/docs/experiments-msmarco-passage.md) that has already been processed.
As an alternative, we also make available pre-built indexes (in which case the indexing step can be skipped).


The below scripts convert queries to json objects with text, text_unlemm, raw, and text_bert_tok fields


```bash
mkdir irst_test
python scripts/ltr_msmarco/convert_queries.py --input path_to_topics --output irst_test/queries.irst_topics.dev.small.json
```
Here the path_to_topics represents the path to topics file saved in tools/topics-and-qrels/ folder, e.g., tools/topics-and-qrels/topics.msmarco-passage.dev-subset.txt


### Performing End-to-End Retrieval Using Pretrained Model

Download pretrained IBM models:
```bash
wget https://rgw.cs.uwaterloo.ca/JIMMYLIN-bucket0/pyserini-models/ibm_model_1_bert_tok_20211117.tar.gz -P irst_test/
tar -xzvf irst_test/ibm_model_1_bert_tok_20211117.tar.gz -C irst_test
```

Next we can run our script to get our end-to-end results.

IRST (Sum) 
```bash
python -m pyserini.search.lucene.irst \
  --tran_path irst_test/ibm_model_1_bert_tok_20211117/ \
  --query_path irst_test/queries.irst_topics.dev.small.json \
  --index msmarco-passage-ltr \
  --output irst_test/regression_test_sum.irst_topics.txt \
  --alpha 0.1
```

IRST (Max)
```bash
python -m pyserini.search.lucene.irst \
  --tran_path irst_test/ibm_model_1_bert_tok_20211117/ \
  --query_path irst_test/queries.irst_topics.dev.small.json \
  --index msmarco-passage-ltr \
  --output irst_test/regression_test_max.irst_topics.txt \
  --alpha 0.3 \
  --max_sim
```

For different topics, the `--input`,`--topics` and `--qrel` are different, since Pyserini has all these topics available, we can pass in
different values to run on different datasets.

`--input`: <br />
&nbsp;&nbsp;&nbsp;&nbsp;TREC DL 2019 Passage: `tools/topics-and-qrels/topics.dl19-passage.txt` <br />
&nbsp;&nbsp;&nbsp;&nbsp;TREC DL 2020 Passage: `tools/topics-and-qrels/topics.dl20.txt` <br />
&nbsp;&nbsp;&nbsp;&nbsp;MS MARCO Passage V1: `tools/topics-and-qrels/topics.msmarco-passage.dev-subset.txt` <br />

`--topics`: <br />
&nbsp;&nbsp;&nbsp;&nbsp;TREC DL 2019 Passage: `dl19-passage` <br />
&nbsp;&nbsp;&nbsp;&nbsp;TREC DL 2020 Passage: `dl20` <br />
&nbsp;&nbsp;&nbsp;&nbsp;MS MARCO Passage V1: `msmarco-passage-dev-subset` <br />



After the run finishes, we can also evaluate the results using the official MS MARCO evaluation script:

For TREC DL 2019, use this command to evaluate your run file:

```bash
python -m pyserini.eval.trec_eval -c -m map -m ndcg_cut.10 -l 2 dl19-passage irst_test/regression_test_sum.dl19-passage.txt
```

Similarly for TREC DL 2020,
```bash
python -m pyserini.eval.trec_eval -c -m map -m ndcg_cut.10 -l 2 dl20-passage irst_test/regression_test_sum.dl19-passage.txt
```

For MS MARCO Passage V1, no need to use -l 2 option:
```bash
python -m pyserini.eval.trec_eval -c -m ndcg_cut -m map -m recip_rank msmarco-passage-dev-subset irst_test/regression_test_sum.msmarco-passage-dev-subset.txt
```

`--qrel_file`: <br />
&nbsp;&nbsp;&nbsp;&nbsp;TREC DL 2019 Passage: `tools/topics-and-qrels/qrels.dl19-passage.txt` <br />
&nbsp;&nbsp;&nbsp;&nbsp;TREC DL 2020 Passage: `tools/topics-and-qrels/qrels.dl20-passage.txt` <br />
&nbsp;&nbsp;&nbsp;&nbsp;MS MARCO Passage V1: `tools/topics-and-qrels/qrels.msmarco-passage.dev-subset.txt` <br />


Note that we evaluate MRR and NDCG at a cutoff of 10 hits to match the official evaluation metrics.



## Document Reranking 


### Data Preprocessing

For MSMARCO DOC, each MS MARCO document is first segmented into passages, each passage is treated as a unit of indexing. 
We utilized the MaxP technique during the ranking, that is scoring documents based on one of its highest-scoring passage.

The below scripts convert queries to json objects with text, text_unlemm, raw, and text_bert_tok fields

```bash
mkdir irst_test
python scripts/ltr_msmarco/convert_queries.py --input path_to_topics --output irst_test/queries.irst_topics.dev.small.json
```

We can now perform retrieval in anserini to generate baseline:

### Performing End-to-End Retrieval Using Pretrained Model


Download pretrained IBM models. Please note that we did not have time to train a new IBM model on MSMARCO DOC data, we used the trained MSMARCO Passage IBM Model1 instead.

```bash
wget https://rgw.cs.uwaterloo.ca/JIMMYLIN-bucket0/pyserini-models/ibm_model_1_bert_tok_20211117.tar.gz -P irst_test/
tar -xzvf irst_test/ibm_model_1_bert_tok_20211117.tar.gz -C irst_test
```

Next we can run our script to get our retrieval results.

IRST (Sum) 
```bash
python -m pyserini.search.lucene.irst \
  --tran_path irst_test/ibm_model_1_bert_tok_20211117/ \
  --query_path irst_test/queries.irst_topics.dev.small.json \
  --index msmarco-document-segment-ltr \
  --output irst_test/regression_test_sum.irst_topics.txt \
  --alpha 0.3 \
  --hits 10000
```

IRST (Max)
```bash
python -m pyserini.search.lucene.irst \
  --tran_path irst_test/ibm_model_1_bert_tok_20211117/ \
  --query_path irst_test/queries.irst_topics.dev.small.json \
  --index msmarco-document-segment-ltr \
  --output irst_test/regression_test_max.irst_topics.txt \
  --alpha 0.3 \
  --hits 10000 \
  --max_sim 
```


For different topics, the `--input`,`--topics` and `--qrel` are different, since Pyserini has all these topics available, we can pass in
different values to run on different datasets.

`--input/topics`: <br />
&nbsp;&nbsp;&nbsp;&nbsp;TREC DL 2019 Passage: `tools/topics-and-qrels/topics.dl19-doc.txt` <br />
&nbsp;&nbsp;&nbsp;&nbsp;TREC DL 2020 Passage: `tools/topics-and-qrels/topics.dl20.txt` <br />
&nbsp;&nbsp;&nbsp;&nbsp;MS MARCO Passage V1: `tools/topics-and-qrels/topics.msmarco-doc.dev.txt` <br />

The reranked runfile contains top 10000 document segments, thus we need to use MaxP technique to get score for each document.

```bash
python scripts/ltr_msmarco/generate_document_score_withmaxP.py --input irst_test/regression_test_sum.irst_topics.txt --output irst_test/regression_test_sum_maxP.irst_topics.tsv
```

We can use the official TREC evaluation tool, trec_eval, to compute other metrics. For that we first need to convert the runs into TREC format:

```bash
python tools/scripts/msmarco/convert_msmarco_to_trec_run.py --input irst_test/regression_test_sum_maxP.irst_topics.tsv --output irst_test/regression_test_sum_maxP.irst_topics.trec
```


For TREC DL 2019, use this command to evaluate your run file:

```bash
python -m pyserini.eval.trec_eval -c -m map -m ndcg_cut.10 -l 2 dl19-doc irst_test/regression_test_sum_maxP.dl19-doc.trec
```

Similarly for TREC DL 2020,
```bash
python -m pyserini.eval.trec_eval -c -m map -m ndcg_cut.10 -l 2 dl20-doc irst_test/regression_test_sum_maxP.dl20-doc.trec
```

For MS MARCO Passage V1, no need to use -l 2 option:
```bash
python -m pyserini.eval.trec_eval -c -M 100 -m ndcg_cut -m map -m recip_rank msmarco-doc-dev irst_test/regression_test_sum_maxP.msmarco-doc.trec

`--qrel_file`: <br />
&nbsp;&nbsp;&nbsp;&nbsp;TREC DL 2019 Passage: `tools/topics-and-qrels/qrels.dl19-doc.txt` <br />
&nbsp;&nbsp;&nbsp;&nbsp;TREC DL 2020 Passage: `tools/topics-and-qrels/qrels.dl20-doc.txt` <br />
&nbsp;&nbsp;&nbsp;&nbsp;MS MARCO Passage V1: `tools/topics-and-qrels/qrels.msmarco-doc.dev.txt` <br />

## Results
### Passage Ranking Datasets

| Topics                | Method                        | MRR    | nDCG@10 | Map |
|:-------------------------|:------------------------|:------:|:--------:|:-----------:|
| DL19                | IRST(Sum)               | - | 0.526   | 0.328     |
| DL19                 | IRST(Max)              | - | 0.537   | 0.328      |
| DL20                | IRST(Sum)               | -| 0.558   | 0.352      |
| DL20                | IRST(Max)               | -| 0.546   | 0.337      |
| MS MARCO Dev                | IRST(Sum)               | 0.233| -   | -      |
| MS MARCO Dev                | IRST(Max)               | 0.227| -   | -      |


### Document Ranking Datasets

| Topics                | Method                  | MRR    | nDCG@10 | Map |
|:-------------------------|:------------------------|:------:|:--------:|:-----------:|
| DL19                | IRST(Sum)               | - | 0.567   | 0.352     |
| DL19                 | IRST(Max)              | - | 0.537   | 0.324      |
| DL20                | IRST(Sum)               | -| 0.561   | 0.363      |
| DL20                | IRST(Max)               | -| 0.524   | 0.332      |
| MS MARCO Dev                | IRST(Sum)               | 0.308| -   | -      |
| MS MARCO Dev                | IRST(Max)               | 0.273| -   | -      |

## Build Index from Scratch

Note that we have used our pre-built index in the above steps. You can also build index by yourself following instructions below.

### Passage Index
Please follow steps in [ltr experiment documentation](https://github.com/castorini/pyserini/blob/master/docs/experiments-ltr-msmarco-passage-reranking.md#building-the-index-from-scratch). 

### Document Index
We use the [script](https://github.com/castorini/docTTTTTquery/blob/master/convert_msmarco_passages_doc_to_anserini.py) in docTTTTTquery with default stride and window length to obtain segmented documents.

Then follow instructions in [ltr experiment](https://github.com/castorini/pyserini/blob/master/docs/experiments-ltr-msmarco-document-reranking.md#building-the-index-from-scratch).
