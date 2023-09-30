# Indexing the ACL Anthology with Anserini

Anserini provides code for indexing the ACL anthology. Here we will use Pyserini (Python toolkit for Anserini) to do the indexing task.

## Generating ACL Anthology Data

**IMPORTANT:** The ACL Anthology requires Python 3.7+; no, it won't work with Python 3.6.

First, clone the ACL anthology repository containing the raw XML data:

```bash
git clone git@github.com:acl-org/acl-anthology.git
```

Next, create a conda environment, and activate it:

```bash
conda create -n pyserini_acl python=3.8
conda activate pyserini_acl
```

Next, navigate to the `acl-anthology` folder and install dependencies:

```bash
cd acl-anthology
pip install -r bin/requirements.txt
```

Generate cleaned YAML data:

1. Add the following lines to `bin/create_hugo_yaml.py` before function `export_anthology`
```python
# Prevent yaml from creating aliases which can't be parsed by anserini
Dumper.ignore_aliases = lambda self, data: True
```

2. Execute the following script:
```bash
python bin/create_hugo_yaml.py
```

Generated ACL files can now be found in `acl-anthology/build/data/`

## Indexing Data

Now we should install Pyserini. You can follow the installation [here](https://github.com/castorini/pyserini/blob/master/docs/installation.md). After you did the `Preliminaries` section, make sure to skip the `Pip Installation` and follow the `Development Installation`. 
Note that you should be using the already created `pyserini_acl` conda environment rather than making a new one that was instructed [here](https://github.com/castorini/pyserini/blob/master/docs/installation.md#:~:text=conda%20create%20%2Dn%20pyserini%20python%3D3.8). 
Just the `Development Installation` will give us the latest features we want.

Once you completely installed Pyserini, navigate to `acl-anthology` folder and run this line of code.

```
python -m pyserini.index -collection AclAnthology -generator AclAnthologyGenerator -threads 8 -input build/data/ -index index/lucene-index-acl-paragraph -storePositions -storeDocvectors -storeContents -storeRaw -optimize
```
You can find the output files in the `index/lucene-index-acl-paragraph` directory.

## Reproduction Log[*](reproducibility.md)

+ Results reproduced by [@billcui57](https://github.com/billcui57) on 2023-06-04 (commit [9fe7836](https://github.com/castorini/pyserini/commit/9fe78365eea89bc93c3a819b7be567d3e1a791eb))
