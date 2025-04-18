# Omim Parse Tools

對 [OMIM Entry](https://omim.org/) 輸入指定gene, 爬取phenotype, description

**Note**: 延遲4秒每次 by [robots.txt](https://omim.org/robots.txt)


## Env Installation

We have already integrate the environment in `conda_env.yaml`. 
execute 
```console
$ conda env create -f conda_env.yaml
```
to install packages required in a new created `omimParseEnv` conda env.


Enter the enviornment with 
```console
$ conda activate omimParseEnv
```
before further executions.

**Note**: Please ensure that all dependencies are installed before using omimParser



## Getting started

```
Parse HTML table and optionally print additional fields.

example:

% python omimParse.py -i examples/gene_4826.txt -o output.txt -m benches/mim2gene.txt --outformat configs/outFormat.json --all -q


usage: omimParse.py [-h] [-i /path/to/input.txt] [-o OUTPUT] [-m /path/to/mim2gene.txt] [--all] [--outformat /path/to/outFormat.json] [-q]

optional arguments:
  -h, --help            show this help message and exit
  -i /path/to/input.txt, --input /path/to/input.txt
                        Input gene list. Example is 'examples/gene_4826.txt'.
  -o OUTPUT, --output OUTPUT
                        Path to the output text file.
  -m /path/to/mim2gene.txt, --mim2gene /path/to/mim2gene.txt
                        Input MIM numbers file. Default is 'benches/mim2gene.txt'.
  --all                 Print all fields including description.
  --outformat /path/to/outFormat.json
                        Path to the JSON file for output format. Default is 'configs/outFormat.json'.
  -q, --quiet           Do not print progress.
```