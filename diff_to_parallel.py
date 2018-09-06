# -*- coding: utf-8 -*-
import fileinput
import sys
import re

from nltk.tokenize import word_tokenize as tokenize

edit_re = re.compile('\[\-(((?!\[-).)*?)\-\]|\{\+(((?!\{\+).)*?)\+\}')


def parse_edit_token(token):
    delete = insert = ''
    if token.startswith('{+'):
        insert = token[2:-2].rsplit('//', 1)[0]
    elif token.startswith('[-'):
        if token.endswith('+}'):
            delete, insert = token[2:-2].rsplit('-]{+', 1)
            delete = delete.rsplit('//', 1)[0]
            insert = insert.rsplit('//', 1)[0]
        else:
            delete = token[2:-2].rsplit('//', 1)[0]
    return delete, insert


def flattern_edit_token(text, to_before=True):
    while edit_re.search(text):
        for match in edit_re.finditer(text):
            edit_token = match.group(0)
            insert, delete = edit_token_to_parallel(edit_token)
            text = text.replace(edit_token, delete if to_before else insert)
    return text


def edit_token_to_parallel(token):
    delete, insert = parse_edit_token(token)
    delete = flattern_edit_token(delete)
    insert = flattern_edit_token(insert, to_before=False)
    return insert, delete


def diff2before_after(text):
    before, after = [], []
    for token in text.split(' '):
        # restore fullwidth space to halfwidth
        token = token.replace('\u3000', ' ')
        if token.startswith('{+') or token.startswith('[-'):
            insert, delete = edit_token_to_parallel(token)
        else:
            insert = delete = token

        if delete:
            before.append(delete)
        if insert:
            after.append(insert)

    return ' '.join(before), ' '.join(after)


def main(ignore_len=3):
    for line in fileinput.input():
        src, trg = diff2before_after(line.strip())

        before = tokenize(src)
        after = tokenize(trg)
        if len(before) > ignore_len and len(after) > ignore_len:
            print(' '.join(before), file=sys.stderr)
            print(' '.join(after))


if __name__ == '__main__':
    main()

# cat diff.txt|python diff_to_parallel.py 1>trg.txt 2>src.txt
