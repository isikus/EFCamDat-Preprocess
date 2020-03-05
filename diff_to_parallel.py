# -*- coding: utf-8 -*-
import fileinput
import sys
import re

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


if __name__ == '__main__':
    main(report_crs=True)

# cat diff.txt|python diff_to_parallel.py 1>trg.txt 2>src.txt