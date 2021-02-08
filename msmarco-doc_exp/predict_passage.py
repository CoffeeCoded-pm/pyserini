import argparse
import datetime
import glob
import hashlib
import json
import multiprocessing
import pickle
import os
import shutil
import subprocess
import uuid
import time

import numpy as np
import pandas as pd
import lightgbm as lgb
from collections import defaultdict
from tqdm import tqdm
from pyserini.analysis import Analyzer, get_lucene_analyzer
from pyserini.ltr import *
from pyserini.search import get_topics_with_reader


def dev_data_loader(file, format, top=100):
    if format == 'tsv':
        dev = pd.read_csv(file, sep="\t",
                          names=['qid', 'pid', 'rank'],
                          dtype={'qid': 'S','pid': 'S', 'rank':'i',})
    elif format == 'trec':
        dev = pd.read_csv(file, sep="\s+",
                    names=['qid', 'q0', 'pid', 'rank', 'score', 'tag'],
                    usecols=['qid', 'pid', 'rank'],
                    dtype={'qid': 'S','pid': 'S', 'rank':'i',})
    else:
        raise Exception('unknown parameters')
    assert dev['qid'].dtype == np.object
    assert dev['pid'].dtype == np.object
    assert dev['rank'].dtype == np.int32
    dev = dev[dev['rank']<=top]
    dev_qrel = pd.read_csv('../collections/msmarco-passage/qrels.dev.small.tsv', sep="\t",
                           names=["qid", "q0", "pid", "rel"], usecols=['qid', 'pid', 'rel'],
                           dtype={'qid': 'S','pid': 'S', 'rel':'i'})
    assert dev['qid'].dtype == np.object
    assert dev['pid'].dtype == np.object
    assert dev['rank'].dtype == np.int32
    dev = dev.merge(dev_qrel, left_on=['qid', 'pid'], right_on=['qid', 'pid'], how='left')
    dev['rel'] = dev['rel'].fillna(0).astype(np.int32)
    dev = dev.sort_values(['qid', 'pid']).set_index(['qid', 'pid'])

    print(dev.shape)
    print(dev.index.get_level_values('qid').drop_duplicates().shape)
    print(dev.groupby('qid').count().mean())
    print(dev.head(10))
    print(dev.info())

    dev_rel_num = dev_qrel[dev_qrel['rel'] > 0].groupby('qid').count()['rel']

    recall_point = [10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000]
    recall_curve = {k: [] for k in recall_point}
    for qid, group in tqdm(dev.groupby('qid')):
        group = group.reset_index()
        assert len(group['pid'].tolist()) == len(set(group['pid'].tolist()))
        total_rel = dev_rel_num.loc[qid]
        query_recall = [0 for k in recall_point]
        for t in group.sort_values('rank').itertuples():
            if t.rel > 0:
                for i, p in enumerate(recall_point):
                    if t.rank <= p:
                        query_recall[i] += 1
        for i, p in enumerate(recall_point):
            if total_rel > 0:
                recall_curve[p].append(query_recall[i] / total_rel)
            else:
                recall_curve[p].append(0.)

    for k, v in recall_curve.items():
        avg = np.mean(v)
        print(f'recall@{k}:{avg}')

    return dev, dev_qrel


def query_loader():
    queries = {}
    with open('queries.train.small.entity.json') as f:
        for line in f:
            query = json.loads(line)
            qid = query.pop('id')
            query['analyzed'] = query['analyzed'].split(" ")
            query['text'] = query['text_unlemm'].split(" ")
            query['text_unlemm'] = query['text_unlemm'].split(" ")
            query['text_bert_tok'] = query['text_bert_tok'].split(" ")
            queries[qid] = query
    with open('queries.dev.small.entity.json') as f:
        for line in f:
            query = json.loads(line)
            qid = query.pop('id')
            query['analyzed'] = query['analyzed'].split(" ")
            query['text'] = query['text_unlemm'].split(" ")
            query['text_unlemm'] = query['text_unlemm'].split(" ")
            query['text_bert_tok'] = query['text_bert_tok'].split(" ")
            queries[qid] = query
    with open('queries.eval.small.entity.json') as f:
        for line in f:
            query = json.loads(line)
            qid = query.pop('id')
            query['analyzed'] = query['analyzed'].split(" ")
            query['text'] = query['text_unlemm'].split(" ")
            query['text_unlemm'] = query['text_unlemm'].split(" ")
            query['text_bert_tok'] = query['text_bert_tok'].split(" ")
            queries[qid] = query
    return queries


def batch_extract(df, queries, fe):
    tasks = []
    task_infos = []
    group_lst = []

    for qid, group in tqdm(df.groupby('qid')):
        task = {
            "qid": qid,
            "docIds": [],
            "rels": [],
            "query_dict": queries[qid]
        }
        for t in group.reset_index().itertuples():
            task["docIds"].append(t.pid)
            task_infos.append((qid, t.pid, t.rel))
        tasks.append(task)
        group_lst.append((qid, len(task['docIds'])))
        if len(tasks) == 1000:
            features = fe.batch_extract(tasks)
            task_infos = pd.DataFrame(task_infos, columns=['qid', 'pid', 'rel'])
            group = pd.DataFrame(group_lst, columns=['qid', 'count'])
            print(features.shape)
            print(task_infos.qid.drop_duplicates().shape)
            print(group.mean())
            print(features.head(10))
            print(features.info())
            yield task_infos, features, group
            tasks = []
            task_infos = []
            group_lst = []
    # deal with rest
    if len(tasks) > 0:
        features = fe.batch_extract(tasks)
        task_infos = pd.DataFrame(task_infos, columns=['qid', 'pid', 'rel'])
        group = pd.DataFrame(group_lst, columns=['qid', 'count'])
        print(features.shape)
        print(task_infos.qid.drop_duplicates().shape)
        print(group.mean())
        print(features.head(10))
        print(features.info())
        yield task_infos, features, group

    return

def batch_predict(models, dev_extracted, feature_name):
    task_infos, features, group = dev_extracted
    dev_X = features.loc[:, feature_name]

    task_infos['score'] = 0.
    for gbm in models:
        task_infos['score'] += gbm.predict(dev_X)


def eval_mrr(dev_data):
    score_tie_counter = 0
    score_tie_query = set()
    MRR = []
    for qid, group in tqdm(dev_data.groupby('qid')):
        group = group.reset_index()
        rank = 0
        prev_score = None
        assert len(group['pid'].tolist()) == len(set(group['pid'].tolist()))
        # stable sort is also used in LightGBM

        for t in group.sort_values('score', ascending=False, kind='mergesort').itertuples():
            if prev_score is not None and abs(t.score - prev_score) < 1e-8:
                score_tie_counter += 1
                score_tie_query.add(qid)
            prev_score = t.score
            rank += 1
            if t.rel > 0:
                MRR.append(1.0 / rank)
                break
            elif rank == 10 or rank == len(group):
                MRR.append(0.)
                break

    score_tie = f'score_tie occurs {score_tie_counter} times in {len(score_tie_query)} queries'
    print(score_tie)
    mrr_10 = np.mean(MRR).item()
    print(f'MRR@10:{mrr_10} with {len(MRR)} queries')
    return {'score_tie': score_tie, 'mrr_10': mrr_10}


def eval_recall(dev_qrel, dev_data):
    dev_rel_num = dev_qrel[dev_qrel['rel'] > 0].groupby('qid').count()['rel']

    score_tie_counter = 0
    score_tie_query = set()

    recall_point = [10,20,50,100,200,250,300,333,400,500,1000]
    recall_curve = {k: [] for k in recall_point}
    for qid, group in tqdm(dev_data.groupby('qid')):
        group = group.reset_index()
        rank = 0
        prev_score = None
        assert len(group['pid'].tolist()) == len(set(group['pid'].tolist()))
        # stable sort is also used in LightGBM
        total_rel = dev_rel_num.loc[qid]
        query_recall = [0 for k in recall_point]
        for t in group.sort_values('score', ascending=False, kind='mergesort').itertuples():
            if prev_score is not None and abs(t.score - prev_score) < 1e-8:
                score_tie_counter += 1
                score_tie_query.add(qid)
            prev_score = t.score
            rank += 1
            if t.rel > 0:
                for i, p in enumerate(recall_point):
                    if rank <= p:
                        query_recall[i] += 1
        for i, p in enumerate(recall_point):
            if total_rel > 0:
                recall_curve[p].append(query_recall[i] / total_rel)
            else:
                recall_curve[p].append(0.)

    score_tie = f'score_tie occurs {score_tie_counter} times in {len(score_tie_query)} queries'
    print(score_tie)
    res = {'score_tie': score_tie}

    for k, v in recall_curve.items():
        avg = np.mean(v)
        print(f'recall@{k}:{avg}')
        res[f'recall@{k}'] = avg

    return res


def output(file, dev_data):
    score_tie_counter = 0
    score_tie_query = set()
    output_file = open(file,'w')

    for qid, group in tqdm(dev_data.groupby('qid')):
        group = group.reset_index()
        rank = 0
        prev_score = None
        assert len(group['pid'].tolist()) == len(set(group['pid'].tolist()))
        # stable sort is also used in LightGBM

        for t in group.sort_values('score', ascending=False, kind='mergesort').itertuples():
            if prev_score is not None and abs(t.score - prev_score) < 1e-8:
                score_tie_counter += 1
                score_tie_query.add(qid)
            prev_score = t.score
            rank += 1
            output_file.write(f"{qid}\tQ0\t{t.pid}\t{rank}\t{t.score}\t'ltr'\n")

    score_tie = f'score_tie occurs {score_tie_counter} times in {len(score_tie_query)} queries'
    print(score_tie)


if __name__ == '__main__':
    os.environ["ANSERINI_CLASSPATH"] = "../pyserini/resources/jars"
    parser = argparse.ArgumentParser(description='Learning to rank')
    parser.add_argument('--rank_list_path', required=True)
    parser.add_argument('--rank_list_top', type=int, default=10000)
    parser.add_argument('--rank_list_format', required=True)
    parser.add_argument('--ltr_model_path', required=True)
    parser.add_argument('--ltr_output_path', required=True)

    args = parser.parse_args()
    print("load dev")
    dev, dev_qrel = dev_data_loader(args.rank_list_path, args.rank_list_format, args.rank_list_top)
    print("load queries")
    queries = query_loader()
    print("add feature")
    fe = FeatureExtractor('../indexes/msmarco-passage/lucene-index-msmarco/', max(multiprocessing.cpu_count()//2, 1))
    for qfield, ifield in [('analyzed', 'contents'),
                           ('text', 'text'),
                           ('text_unlemm', 'text_unlemm'),
                           ('text_bert_tok', 'text_bert_tok')]:
        print(qfield, ifield)
        fe.add(BM25Stat(SumPooler(), k1=2.0, b=0.75, field=ifield, qfield=qfield))
        fe.add(BM25Stat(AvgPooler(), k1=2.0, b=0.75, field=ifield, qfield=qfield))
        fe.add(BM25Stat(MedianPooler(), k1=2.0, b=0.75, field=ifield, qfield=qfield))
        fe.add(BM25Stat(MaxPooler(), k1=2.0, b=0.75, field=ifield, qfield=qfield))
        fe.add(BM25Stat(MinPooler(), k1=2.0, b=0.75, field=ifield, qfield=qfield))
        fe.add(BM25Stat(MaxMinRatioPooler(), k1=2.0, b=0.75, field=ifield, qfield=qfield))

        fe.add(LMDirStat(SumPooler(), mu=1000, field=ifield, qfield=qfield))
        fe.add(LMDirStat(AvgPooler(), mu=1000, field=ifield, qfield=qfield))
        fe.add(LMDirStat(MedianPooler(), mu=1000, field=ifield, qfield=qfield))
        fe.add(LMDirStat(MaxPooler(), mu=1000, field=ifield, qfield=qfield))
        fe.add(LMDirStat(MinPooler(), mu=1000, field=ifield, qfield=qfield))
        fe.add(LMDirStat(MaxMinRatioPooler(), mu=1000, field=ifield, qfield=qfield))

        #     fe.add(LMDirStat(SumPooler(), mu=1500, field=ifield, qfield=qfield))
        #     fe.add(LMDirStat(AvgPooler(), mu=1500, field=ifield, qfield=qfield))
        #     fe.add(LMDirStat(MedianPooler(), mu=1500, field=ifield, qfield=qfield))
        #     fe.add(LMDirStat(MaxPooler(), mu=1500, field=ifield, qfield=qfield))
        #     fe.add(LMDirStat(MinPooler(), mu=1500, field=ifield, qfield=qfield))
        #     fe.add(LMDirStat(MaxMinRatioPooler(), mu=1500, field=ifield, qfield=qfield))

        #     fe.add(LMDirStat(SumPooler(), mu=2500, field=ifield, qfield=qfield))
        #     fe.add(LMDirStat(AvgPooler(), mu=2500, field=ifield, qfield=qfield))
        #     fe.add(LMDirStat(MedianPooler(), mu=2500, field=ifield, qfield=qfield))
        #     fe.add(LMDirStat(MaxPooler(), mu=2500, field=ifield, qfield=qfield))
        #     fe.add(LMDirStat(MinPooler(), mu=2500, field=ifield, qfield=qfield))
        #     fe.add(LMDirStat(MaxMinRatioPooler(), mu=2500, field=ifield, qfield=qfield))

        fe.add(NTFIDF(field=ifield, qfield=qfield))
        fe.add(ProbalitySum(field=ifield, qfield=qfield))

        fe.add(DFR_GL2Stat(SumPooler(), field=ifield, qfield=qfield))
        fe.add(DFR_GL2Stat(AvgPooler(), field=ifield, qfield=qfield))
        fe.add(DFR_GL2Stat(MedianPooler(), field=ifield, qfield=qfield))
        fe.add(DFR_GL2Stat(MaxPooler(), field=ifield, qfield=qfield))
        fe.add(DFR_GL2Stat(MinPooler(), field=ifield, qfield=qfield))
        fe.add(DFR_GL2Stat(MaxMinRatioPooler(), field=ifield, qfield=qfield))

        fe.add(DFR_In_expB2Stat(SumPooler(), field=ifield, qfield=qfield))
        fe.add(DFR_In_expB2Stat(AvgPooler(), field=ifield, qfield=qfield))
        fe.add(DFR_In_expB2Stat(MedianPooler(), field=ifield, qfield=qfield))
        fe.add(DFR_In_expB2Stat(MaxPooler(), field=ifield, qfield=qfield))
        fe.add(DFR_In_expB2Stat(MinPooler(), field=ifield, qfield=qfield))
        fe.add(DFR_In_expB2Stat(MaxMinRatioPooler(), field=ifield, qfield=qfield))

        fe.add(DPHStat(SumPooler(), field=ifield, qfield=qfield))
        fe.add(DPHStat(AvgPooler(), field=ifield, qfield=qfield))
        fe.add(DPHStat(MedianPooler(), field=ifield, qfield=qfield))
        fe.add(DPHStat(MaxPooler(), field=ifield, qfield=qfield))
        fe.add(DPHStat(MinPooler(), field=ifield, qfield=qfield))
        fe.add(DPHStat(MaxMinRatioPooler(), field=ifield, qfield=qfield))

        fe.add(Proximity(field=ifield, qfield=qfield))
        fe.add(TPscore(field=ifield, qfield=qfield))
        fe.add(tpDist(field=ifield, qfield=qfield))

        fe.add(DocSize(field=ifield))

        fe.add(QueryLength(qfield=qfield))
        fe.add(QueryCoverageRatio(qfield=qfield))
        fe.add(UniqueTermCount(qfield=qfield))
        fe.add(MatchingTermCount(field=ifield, qfield=qfield))
        fe.add(SCS(field=ifield, qfield=qfield))

        fe.add(tfStat(AvgPooler(), field=ifield, qfield=qfield))
        fe.add(tfStat(MedianPooler(), field=ifield, qfield=qfield))
        fe.add(tfStat(SumPooler(), field=ifield, qfield=qfield))
        fe.add(tfStat(MinPooler(), field=ifield, qfield=qfield))
        fe.add(tfStat(MaxPooler(), field=ifield, qfield=qfield))
        fe.add(tfStat(MaxMinRatioPooler(), field=ifield, qfield=qfield))

        #     fe.add(tfIdfStat(False, AvgPooler(), field=ifield, qfield=qfield))
        #     fe.add(tfIdfStat(False, MedianPooler(), field=ifield, qfield=qfield))
        #     fe.add(tfIdfStat(False, SumPooler(), field=ifield, qfield=qfield))
        #     fe.add(tfIdfStat(False, MinPooler(), field=ifield, qfield=qfield))
        #     fe.add(tfIdfStat(False, MaxPooler(), field=ifield, qfield=qfield))
        #     fe.add(tfIdfStat(False, MaxMinRatioPooler(), field=ifield, qfield=qfield))

        fe.add(tfIdfStat(True, AvgPooler(), field=ifield, qfield=qfield))
        fe.add(tfIdfStat(True, MedianPooler(), field=ifield, qfield=qfield))
        fe.add(tfIdfStat(True, SumPooler(), field=ifield, qfield=qfield))
        fe.add(tfIdfStat(True, MinPooler(), field=ifield, qfield=qfield))
        fe.add(tfIdfStat(True, MaxPooler(), field=ifield, qfield=qfield))
        fe.add(tfIdfStat(True, MaxMinRatioPooler(), field=ifield, qfield=qfield))

        fe.add(normalizedTfStat(AvgPooler(), field=ifield, qfield=qfield))
        fe.add(normalizedTfStat(MedianPooler(), field=ifield, qfield=qfield))
        fe.add(normalizedTfStat(SumPooler(), field=ifield, qfield=qfield))
        fe.add(normalizedTfStat(MinPooler(), field=ifield, qfield=qfield))
        fe.add(normalizedTfStat(MaxPooler(), field=ifield, qfield=qfield))
        fe.add(normalizedTfStat(MaxMinRatioPooler(), field=ifield, qfield=qfield))

        fe.add(idfStat(AvgPooler(), field=ifield, qfield=qfield))
        fe.add(idfStat(MedianPooler(), field=ifield, qfield=qfield))
        fe.add(idfStat(SumPooler(), field=ifield, qfield=qfield))
        fe.add(idfStat(MinPooler(), field=ifield, qfield=qfield))
        fe.add(idfStat(MaxPooler(), field=ifield, qfield=qfield))
        fe.add(idfStat(MaxMinRatioPooler(), field=ifield, qfield=qfield))

        fe.add(ictfStat(AvgPooler(), field=ifield, qfield=qfield))
        fe.add(ictfStat(MedianPooler(), field=ifield, qfield=qfield))
        fe.add(ictfStat(SumPooler(), field=ifield, qfield=qfield))
        fe.add(ictfStat(MinPooler(), field=ifield, qfield=qfield))
        fe.add(ictfStat(MaxPooler(), field=ifield, qfield=qfield))
        fe.add(ictfStat(MaxMinRatioPooler(), field=ifield, qfield=qfield))

        fe.add(UnorderedSequentialPairs(3, field=ifield, qfield=qfield))
        fe.add(UnorderedSequentialPairs(8, field=ifield, qfield=qfield))
        fe.add(UnorderedSequentialPairs(15, field=ifield, qfield=qfield))
        fe.add(OrderedSequentialPairs(3, field=ifield, qfield=qfield))
        fe.add(OrderedSequentialPairs(8, field=ifield, qfield=qfield))
        fe.add(OrderedSequentialPairs(15, field=ifield, qfield=qfield))
        fe.add(UnorderedQueryPairs(3, field=ifield, qfield=qfield))
        fe.add(UnorderedQueryPairs(8, field=ifield, qfield=qfield))
        fe.add(UnorderedQueryPairs(15, field=ifield, qfield=qfield))
        fe.add(OrderedQueryPairs(3, field=ifield, qfield=qfield))
        fe.add(OrderedQueryPairs(8, field=ifield, qfield=qfield))
        fe.add(OrderedQueryPairs(15, field=ifield, qfield=qfield))

    # fe.add(EntityHowLong())
    # fe.add(EntityHowMany())
    # fe.add(EntityHowMuch())
    # fe.add(EntityWhen())
    # fe.add(EntityWhere())
    # fe.add(EntityWho())
    # fe.add(EntityWhereMatch())
    # fe.add(EntityWhoMatch())

    start = time.time()
    fe.add(
        IBMModel1("../FlexNeuART/collections/msmarco_doc/derived_data/giza/title_unlemm", "text_unlemm", "title_unlemm",
                  "text_unlemm"))
    end = time.time()
    print('IBM model Load takes %.2f seconds' % (end - start))
    start = end
    fe.add(IBMModel1("../FlexNeuART/collections/msmarco_doc/derived_data/giza/url_unlemm", "text_unlemm", "url_unlemm",
                     "text_unlemm"))
    end = time.time()
    print('IBM model Load takes %.2f seconds' % (end - start))
    start = end
    fe.add(
        IBMModel1("../FlexNeuART/collections/msmarco_doc/derived_data/giza/body", "text_unlemm", "body", "text_unlemm"))
    end = time.time()
    print('IBM model Load takes %.2f seconds' % (end - start))
    start = end
    fe.add(IBMModel1("../FlexNeuART/collections/msmarco_doc/derived_data/giza/text_bert_tok", "text_bert_tok",
                     "text_bert_tok", "text_bert_tok"))
    end = time.time()
    print('IBM model Load takes %.2f seconds' % (end - start))
    start = end

    models = pickle.load(open(args.ltr_model_path+'/model.pkl','rb'))
    metadata = json.load(open(args.ltr_model_path+'/metadata.json','r'))
    feature_used = metadata['feature_names']

    batch_info = []
    start_extract = time.time()
    for dev_extracted in batch_extract(dev, queries, fe):
        end_extract = time.time()
        print(f'extract 1000 queries take {end_extract - start_extract}s')
        task_infos, features, group = dev_extracted
        start_predict = time.time()
        batch_predict(models, dev_extracted, feature_used)
        end_predict = time.time()
        print(f'predict 1000 queries take {end_predict - start_predict}s')
        batch_info.append(task_infos)
        start_extract = time.time()
    batch_info = pd.concat(batch_info, axis=0, ignore_index=True)
    del dev, queries, fe

    eval_res = eval_mrr(batch_info)
    eval_recall(dev_qrel, batch_info)
    output(args.ltr_output_path, batch_info)
    print('Done!')
