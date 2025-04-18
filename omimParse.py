import os
import sys
import json
from bs4 import BeautifulSoup
import pandas as pd
import requests
import logging
import subprocess
import time
import random

class pkg():
    """omimParse.py: 
    Parse omim gene phenotype information.
    """
    def __init__(self, args={}):
        "add all options into self"
        self.args = {}
        self.args.update(args)

        os.makedirs('/tmp/omimParse', exist_ok=True)

    def loadMimGeneList(self, pathMimGeneList):
        mim2gene = {}
        for tline in open(pathMimGeneList):
            if tline[0] == '#':
                continue
            tline = tline.strip(' \n\r')
            if not tline:
                continue
            trow = tline.split('\t')
            # Assuming the file has at least 5 columns as per the colnames
            if len(trow) >= 5:
                MIMNo, EntryType, GeneID, Symbol, EnsemblID = trow
                if EntryType.lower() == 'gene' and Symbol:
                    mim2gene[MIMNo] = {
                        'EntryType': EntryType,
                        'GeneID': GeneID,
                        'Symbol': Symbol,
                        'EnsemblID': EnsemblID
                    }
        return mim2gene

    def parseHtmlTable(self, html):
        soup = BeautifulSoup(html, "html.parser")
        table = soup.table
        location, phenotype, mimNumber, inheritance, mappingKey = "", "", "", "", ""
        description, geneName = "", ""

        # 提取 gene name
        geneList = soup.select("#approvedGeneSymbols")
        if len(geneList) > 0:
            geneName = geneList[0].find_next('a').get_text().strip()
        
        if not table:
            result = "ERROR"
        else:
            result = "SUCCESS"
            trs = table.find_all('tr')
            for tr in trs:
                tds = tr.find_all('td')
                if len(tds) == 0:
                    continue
                elif len(tds) == 4:
                    phenotype += "|" + (tds[0].get_text().strip() if tds[0].get_text().strip() != '' else '.')
                    mimNumber += "|" + (tds[1].get_text().strip() if tds[1].get_text().strip() != '' else '.')
                    inheritance += "|" + (tds[2].get_text().strip() if tds[2].get_text().strip() != '' else '.')
                    mappingKey += "|" + (tds[3].get_text().strip() if tds[3].get_text().strip() != '' else '.')
                elif len(tds) == 5:
                    location = tds[0].get_text().strip() if tds[0].get_text().strip() != '' else '.'
                    phenotype = tds[1].get_text().strip() if tds[1].get_text().strip() != '' else '.'
                    mimNumber = tds[2].get_text().strip() if tds[2].get_text().strip() != '' else '.'
                    inheritance = tds[3].get_text().strip() if tds[3].get_text().strip() != '' else '.'
                    mappingKey = tds[4].get_text().strip() if tds[4].get_text().strip() != '' else '.'
                else:
                    result = "ERROR"
            
        descriptionList = soup.select("#mimDescriptionFold")
        description = "." if len(descriptionList) == 0 else descriptionList[0].get_text().strip()


        return {
            "result": result,
            "Gene": geneName,
            "location": location,
            "phenotype": phenotype,
            "mimNumber": mimNumber,
            "inheritance": inheritance,
            "mappingKey": mappingKey,
            "description": description
        }

    def processGene(self, gene_name, mim2gene):
        mim_number = None
        for mim, gene_info in mim2gene.items():
            if gene_info['Symbol'] == gene_name:
                mim_number = mim
                break
        
        if mim_number:
            url = f"https://www.omim.org/entry/{mim_number}"
            tmp_file_path = f'/tmp/omimParse/{mim_number}.xml'
            try:
                subprocess.run(['wget', '-q', '-O', tmp_file_path, url], check=True)
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to download {url}: {e}")
                return None

            with open(tmp_file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            result = self.parseHtmlTable(html_content)
            os.remove(tmp_file_path)
            
            return result
        return None

    def main(self):
        outFormatJson = self.args['outformat'].name
        if not os.path.exists(outFormatJson):
            logging.error(f"OutFormat Json({outFormatJson}) do not exists!")
        outFormat = json.load(self.args['outformat'])

        pathMim2GeneList = self.args['mim2gene'].name
        if not os.path.exists(pathMim2GeneList):
            logging.error(f"Mim2Gene list({pathMim2GeneList}) do not exists!")
        mim2gene = self.loadMimGeneList(pathMim2GeneList)


        with open(self.args['input'].name, 'r') as gene_file:
            gene_names = [line.strip() for line in gene_file.readlines()]

        total_genes = len(gene_names)
        fields = outFormat.get("outColnames", [])
        self.args['output'].write('\t'.join(fields) + '\n')

        for index, gene_name in enumerate(gene_names, start=1):
            # 規避爬蟲法條 每次休息4-6秒
            time.sleep(random.uniform(4, 6))
            
            result = self.processGene(gene_name, mim2gene)
            if result is None:
                continue
            
            if not self.args['quiet']:
                print(f"{index}/{total_genes}: {gene_name}")
            
            data = {field: [result.get(field, ".")] for field in fields}
            df = pd.DataFrame(data)
            
            if self.args['all']:
                extra_fields = outFormat.get("extraColnames", [])
                for field in extra_fields:
                    df[field] = result.get(field, ".")
            
            for trow in df.itertuples(index=False, name=None):
                self.args['output'].write('\t'.join(map(str, trow)) + '\n')

        self.args['output'].close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Parse HTML table and optionally print additional fields.")
    parser.add_argument('-i', '--input', help="Input gene list. Example is 'examples/gene_4826.txt'.", metavar="/path/to/input.txt", type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('-o', '--output', help="Path to the output text file.", type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('-m', '--mim2gene', help="Input MIM numbers file. Default is 'benches/mim2gene.txt'.", metavar="/path/to/mim2gene.txt", default="benches/mim2gene.txt", type=argparse.FileType('r'))
    parser.add_argument('--all', action='store_true', help="Print all fields including description.")
    parser.add_argument('--outformat', help="Path to the JSON file for output format. Default is 'configs/outFormat.json'.", metavar="/path/to/outFormat.json", default="configs/outFormat.json", type=argparse.FileType('r'))
    parser.add_argument('-q', '--quiet', action='store_true', help="Do not print progress.")
    args = parser.parse_args()
    
    a=pkg(vars(args))
    a.main()
