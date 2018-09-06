# -*- coding: utf-8 -*-
import os
import re
import fileinput
import spacy

from nltk.tokenize import sent_tokenize, word_tokenize
from spacy.lang.en import English
from spacy.attrs import ORTH

SPACY_MODEL = os.environ.get('SPACY_MODEL', 'en')
nlp = spacy.load(SPACY_MODEL)
tokenizer = English().Defaults.create_tokenizer(nlp)

edit_re = re.compile('\[\-(((?!\[\-).)*?)\-\]|\{\+(((?!\{\+).)*?)\+\}')


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
            # word tokenize (using spacy)
            text = ' '.join(token.text for token in tokenizer(sent) if token.text).strip()
            tokenized_sents.append(text)

    # restore masked edit
    return '\n'.join(tokenized_sents).format(*edits)


def main():
    for doc in fileinput.input():
        doc = doc.strip()
        # print('#', 'doc', '=', doc)
        print(tokenize_doc(doc))


if __name__ == '__main__':
    init_tokenizer_option()
    main()
