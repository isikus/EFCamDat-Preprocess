# -*- coding: utf-8 -*-
import fileinput
import os
import sys
import re

from multiprocessing.pool import ThreadPool
from multiprocessing import cpu_count
from nltk.tokenize import word_tokenize as tokenize


def diff2before_after(text, report_crs):
    crs = None
    if report_crs:
        crs = len(re.findall(r'\{\+.*?//.*?\}', text)) + len(re.findall(r'\[\-.*?//.*?\]', text))
    src = re.sub(r'\{\+(.*?)//.*?\}', '', re.sub(r'\[\-(.*?)//.*?\]', r'\1', text))
    trg = re.sub(r'\{\+(.*?)//.*?\}', r'\1', re.sub(r'\[\-(.*?)//.*?\]', '', text))
    return src, trg, crs


def main(ignore_len=3, report_crs=False):
    for line in fileinput.input():
        src, trg, crs = diff2before_after(line.strip(), report_crs)

        before = tokenize(src)
        after = tokenize(trg)
        if len(before) > ignore_len and len(after) > ignore_len:
            print(src, file=sys.stderr)
            print(trg)
            if report_crs:
                with open("crs.txt", "w", encoding="utf-8") as outfile:
                    outfile.write(str(crs))


def parallel_process(fpath, report_crs=True):
    global N
    
    with open(fpath, "r", encoding="utf-8", errors="replace") as infile:
        text = infile.read()
    namebase = os.path.splitext(fpath)[0]
    root = namebase[:len(namebase)-namebase[::-1].find("/")]
    fname = namebase[len(namebase)-namebase[::-1].find("/"):]
    
    src, trg, crs = diff2before_after(text, report_crs)
    
    with open(root+"/src/"+fname+".txt", "w", encoding="utf-8") as outfile:
        outfile.write(src)
    with open(root+"/trg/"+fname+".txt", "w", encoding="utf-8") as outfile:
        outfile.write(trg)
    with open(root+"/crs/"+fname+".txt", "w", encoding="utf-8") as outfile:
        outfile.write(str(crs))
    
    N += 1
    if not(N % 5000):
        print(str(N), "files processed")


# single process strategy (for smaller collections)
# call from bash
# cat diff.txt|python diff_to_parallel.py 1>trg.txt 2>src.txt
if __name__ == '__main__':
    main(report_crs=True)


# parallel process strategy (for large collections)
# call from python
# from diff_to_parallel import run
# run(texts_dir)   # where texts_dir is a path
def run(texts_dir):
    global N
    N = 0
    files = [os.path.abspath(texts_dir+"/"+file) for file in os.listdir(texts_dir)]
    os.makedirs(texts_dir+"/src", exist_ok=True)
    os.makedirs(texts_dir+"/trg", exist_ok=True)
    os.makedirs(texts_dir+"/crs", exist_ok=True)
    print("Processing", str(len(files)), "files")
    results = ThreadPool(16).imap_unordered(parallel_process, files)