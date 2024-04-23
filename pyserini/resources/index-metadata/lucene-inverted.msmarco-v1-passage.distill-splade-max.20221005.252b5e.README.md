# msmarco-v1-passage-distill-splade-max

Lucene impact index of the MS MARCO V1 passage corpus for `distill-splade-max`.

This index was generated on 2022/10/05 at Anserini commit [`252b5e`](https://github.com/castorini/anserini/commit/252b5e2087dd7b3b994d41a444d4ae0044519819) on `tuna` with the following command:

```bash
nohup target/appassembler/bin/IndexCollection \
 -collection JsonVectorCollection \
 -input /tuna1/collections/msmarco/msmarco-passage-distill-splade-max/ \
 -index indexes/lucene-index.msmarco-v1-passage-distill-splade-max.20221005.252b5e/ \
 -generator DefaultLuceneDocumentGenerator \
 -threads 16 -impact -pretokenized -optimize >& logs/log.msmarco-v1-passage-distill-splade-max.20221005.252b5e &
```
