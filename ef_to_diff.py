# -*- coding: utf-8 -*-
import re
import sys
from bs4 import BeautifulSoup

REPLACE_TOKEN = '[-{0}//{2}-]{{+{1}//{2}+}}'
INSERT_TOKEN = '{{+{0}//{1}+}}'
DELETE_TOKEN = '[-{0}//{1}-]'

edit_re = re.compile('<change>(((?!<change>).)*?)</change>')


def restore_space_escape(text):
    while '&amp;' in text:
        text = text.replace('&amp;', '&')
    text = text.replace('&nbsp;', ' ')
    return text


def parse_change(content):
    soup = BeautifulSoup(content, 'lxml')
    original = soup.select_one('selection').text
    corrected = soup.select_one('tag correct').text
    error_type = soup.select_one('tag symbol').text

    error_type = error_type.replace(' and ', ',')
    return original, corrected, error_type


def change_to_diff(change_token, ignore_type=[]):
    original, corrected, error_type = parse_change(change_token)

    if any(t in ignore_type for t in error_type.split(',')):
        return ' ' + corrected + ' '
    elif original and corrected:  # replace
        return REPLACE_TOKEN.format(original, corrected, error_type)
    elif original:  # delete
        return DELETE_TOKEN.format(original, error_type)
    elif corrected:  # insert
        return INSERT_TOKEN.format(corrected, error_type)
    else:
        return ' '


def convert2wdiff(text, ignore_type=[]):
    while edit_re.search(text):
        for match in edit_re.finditer(text):
            change_token = match.group(0)
            diff_token = change_to_diff(change_token, ignore_type=ignore_type)

            text = text.replace(change_token, diff_token)

    # remove consecutive spaces
    return ' '.join(token for token in text.split(' ') if token)


def main():
    ignore_type = set(sys.argv[1:])

    for text in sys.stdin:
        text = restore_space_escape(text.strip())
        print(convert2wdiff(text, ignore_type))


if __name__ == '__main__':
    main()