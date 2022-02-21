# wikipedia-dpr-dkrr-tqa
Faiss FlatIP index of Wikipedia DPR encoded by the retriever model from: 'Distilling Knowledge from Reader to Retriever for Question Answering' trained on TriviaQA.
This index was generated on 2022/02/17 on `orca` at commits:

+ pyserini commit [`cc91b2`](https://github.com/castorini/pyserini/commit/cc91b22f549702068cea1283f91b31d28d127b2f) (2022/02/17)
+ FiD (https://github.com/facebookresearch/FiD) commit [`25ed1f`](https://github.com/facebookresearch/FiD/commit/25ed1ff0fe0288b80fb5e9e5de8d6346b94b8d48) (2022/02/17)

with the following command to generate the embeddings (from FiD repo):

```bash
python3 generate_passage_embeddings.py \
        --model_path tqa_retriever \
        --passages passages.tsv \
        --output_path wikipedia_embeddings_tqa \
        --shard_id 0 \
        --num_shards 1 \
        --per_gpu_batch_size 500
```

and the following command to convert the embeddings to faiss IndexFlatIP form

```bash
python3 convert_dkrr_embeddings_to_faiss.py \
        --embeddings wikipedia_embeddings_tqa \
        --output faiss-flat.wikipedia.dkrr-dpr-tqa-retriever
```
		
faiss-flat.wikipedia.dkrr-dpr-tqa-retriever.20220217.25ed1f.cc91b2.tar.gz MD5 checksum = a6b02d33c9c0376ad1bf6550212ecdcb
