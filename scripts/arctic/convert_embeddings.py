"""Converts the hgf embeddings for documents into pyserini compatible format."""

import argparse
import os
import pandas as pd
import faiss
import numpy as np
from tqdm import tqdm

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--embeddings_folder",
        type=str,
        required=True,
        help="Path to corpus embeddings folder downloaded from hgf.",
    )
    parser.add_argument(
        "--output", type=str, help="Path to store faiss IndexFlatIP.", required=True
    )
    parser.add_argument(
        "--indices",
        type=str,
        help="Start and end index seperated with _ or full.",
        required=False,
        default="full",
    )
    parser.add_argument(
        "--start_filter",
        type=str,
        help="Filter to be used with string start.",
        required=False,
        default="",
    )

    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    folder_path = args.embeddings_folder

    files = [file for file in os.listdir(folder_path) if file.endswith(".parquet") and file.startswith(args.start_filter)]

    if args.indices == "full":
        start = 0
        end = len(files)
    else:
        indices = args.indices.split("_")
        start = int(indices[0])
        end = int(indices[1])

    all_embeddings = []
    doc_ids = []
    for file_name in tqdm(files[start:end]):
        file_path = os.path.join(folder_path, file_name)
        df = pd.read_parquet(file_path)
        if "VECTOR_MAIN" in df.columns:
            embeddings = df["VECTOR_MAIN"].tolist()
        elif "embedding" in df.columns:
            embeddings = df["embedding"].tolist()
        else:
            print("Error!!")
        embeddings = np.array(embeddings)
        dim = embeddings[0].shape[0]
        faiss.normalize_L2(embeddings)
        all_embeddings.append(embeddings.reshape(-1, dim))
        if "DOC_ID" in df.columns:
            doc_ids.extend(df["DOC_ID"].tolist())
        elif "doc_id" in df.columns:
            doc_ids.extend(df["doc_id"].tolist())
        else:
            print("Error!!")

    combined_embeddings = np.vstack(all_embeddings)

    index = faiss.IndexFlatIP(combined_embeddings.shape[1])
    index.add(combined_embeddings)
    faiss.write_index(index, os.path.join(args.output, "index"))

    file_path = os.path.join(args.output, "docid")

    with open(file_path, "w") as file:
        for value in doc_ids:
            file.write(f"{value}\n")
