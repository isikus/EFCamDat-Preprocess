# -*- coding: utf-8 -*-
import os
import re
import fileinput
import spacy
import time
from collections import defaultdict
from nltk.tokenize import sent_tokenize, word_tokenize
from spacy.lang.en import English
from spacy.attrs import ORTH
import kenlm


KnModel = kenlm.Model('../jjc/1b.bin')
SPACY_MODEL = os.environ.get('SPACY_MODEL', 'en')
nlp = spacy.load(SPACY_MODEL)
tokenizer = English().Defaults.create_tokenizer(nlp)

edit_re = re.compile('\[\-(((?!\[\-).)*?)\-\]|\{\+(((?!\{\+).)*?)\+\}')
sep_sents_re = r'\w\.\w'


def init_tokenizer_option():
    #  add special segmenting case for spacy tokenizer
    tokenizer.add_special_case("{}", [{ORTH: "{}"}])
    tokenizer.add_special_case("{{", [{ORTH: "{{"}])
    tokenizer.add_special_case("}}", [{ORTH: "}}"}])


def restore_line_break(text):
    return text.replace('<br/>', '\n').replace('<br>', '\n')


def restore_xmlescape(text):
    while '&amp;' in text:
        text = text.replace('&amp;', '&')
    text = text.replace('&quote;', '"')
    text = text.replace('&quot;', '"')
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    return text


def tokenize_edit(edit_token):
    def _tokenize(text):
        # remove nested edit tokens
        while edit_re.search(text):
            text = edit_re.sub(' ', text).strip()
        # nltk word_tokenize
        return '\u3000'.join(token for token in word_tokenize(text))
        # spacy word_tokenize (TODO: clean fixed space token)
        # return '\u3000'.join(token.text for token in tokenizer(text.replace('\u3000', ' ')))

    if edit_token.startswith('[-'):
        if edit_token.endswith('+}'):  # replace
            delete, insert = edit_token[2:-2].rsplit('-]{+', 1)
            delete, err_type = delete.rsplit('//', 1)
            insert, err_type = insert.rsplit('//', 1)
            delete, insert = _tokenize(delete), _tokenize(insert)
            return '[-{0}//{2}-]{{+{1}//{2}+}}'.format(delete, insert, err_type)
        else:  # delete
            delete, err_type = edit_token[2:-2].rsplit('//', 1)
            delete = _tokenize(delete)
            return '[-{0}//{1}-]'.format(delete, err_type)
    else:  # insert
        insert, err_type = edit_token[2:-2].rsplit('//', 1)
        insert = _tokenize(insert)
        return '{{+{0}//{1}+}}'.format(insert, err_type)


def mask_edits(text):
    edits = []
    tokens = []

    for token in text.split(' '):
        token = token.strip()
        if token.startswith('{+') or token.startswith('[-'):
            tokens.append('{}')
            edits.append(tokenize_edit(token))
        elif token:
            tokens.append(token.replace('{', ' {{ ').replace('}', ' }} '))

    return ' '.join(token.strip() for token in tokens), edits

def seperate_sents(last_sent):
    seg_sents = []
    keep_seg = True
    bef_sent = ''
    while keep_seg:
        
        com_sent, last_sent = last_sent.split('.', 1)
        com_sent = bef_sent + com_sent
        com_sent += '.'
    
        if not last_sent: # prevent it is the last sent
            seg_sents.append(reorganize_sent(com_sent))
            break
    
        com_token = ' '.join(word_tokenize(com_sent))
        last_token = ' '.join(word_tokenize(last_sent))
        last_token = last_token.capitalize()
        com_token = com_token.capitalize()
        sep_scores = KnModel.score(com_token) + KnModel.score(last_token)
        total_scores = KnModel.score(com_token + ' ' + last_token)
    
        if sep_scores > total_scores: # should seperate these sentences
            bef_sent = ''
            seg_sents.append(reorganize_sent(com_sent))

        else:
            bef_sent = com_sent
        
        if not re.search(r'\.', last_sent):
            keep_seg = False
            seg_sents.append(reorganize_sent(last_sent))
    
    return seg_sents
def reorganize_sent(sent):
    return ' '.join(token.text for token in tokenizer(sent) if token.text).strip()

def tokenize_doc(text):
    text = restore_line_break(text)
    text = restore_xmlescape(text)

    # mask edit tokens first to prevent being segmented
    # I have {+a+} pen. => I have {} pen.
    text_masked, edits = mask_edits(text)

    tokenized_sents = []
    for line in text_masked.splitlines():
        # sentence tokenize (using nltk)
        for sent in sent_tokenize(line.strip()):
            # print(sent)
            # sent sep again (using nltk)
            # if re.search(sep_sents_re, sent):
                # tokenized_sents += seperate_sents(sent)
            # else:
            # word tokenize (using spacy)
            # else:
                # text = ' '.join(token.text for token in tokenizer(sent) if token.text).strip()
                # tokenized_sents.append(reorganize_sent(sent))
            tokenized_sents.append(sent)
    # restore masked edit
    return '\n'.join(tokenized_sents).format(*edits)


def main():
    revise_type = defaultdict(int)
    for doc in fileinput.input():
        doc = doc.strip()
        # print('#', 'doc', '=', doc)
        print(tokenize_doc(doc))

    return revise_type


if __name__ == '__main__':
    start = time.time()
    init_tokenizer_option()
    main()
    end = time.time()
    #print('Time Cost: ', end - start)
    #print('edit count')
    #for key, count in revise_type.items():
        #print('edit_count: ', key,'times: ', count)
