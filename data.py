"-*- coding: utf-8 -*-"

try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup
import wikipedia
import argparse
import urllib
from requests.exceptions import ConnectionError
from requests.exceptions import RequestException
from os import path
import codecs
import re
import traceback
import csv
import warnings
import utils
import yaml
warnings.simplefilter("ignore", UserWarning)


output = codecs.open('output.txt', 'w')
error_output = codecs.open('error.txt', 'w')

year_pattern = re.compile(r'\([0-9]{4}\)')
aka_pattern = re.compile(r'\(a\.k\.a\. (.+?)\)')
date_pattern = re.compile(r'\((.+?)\)')

def write(out, id, s):

    out.write('{}\t{}\n'.format(
        id, s.encode('utf-8').replace('\n', '')))


def summary(id, title):

    try:
        print('processing {} {} ...'.format(id, title))
        s = wikipedia.summary(title)
        write(output, id, s)
    except ConnectionError:
        print('Connection error, retry...')
        summary(id, title)
    except RequestException:
        print('Request error, retry...')
        summary(id, title)


def search_page(id, title, callbacks):

    try:
        print('processing {} {} ...'.format(id, title))
        html = wikipedia.page(title).html()
        html = re.sub('<br.*?>', '\n', html)
        parsed_html = BeautifulSoup(html, 'html.parser')
        table = parsed_html.find('table', attrs={'class': 'infobox vevent'})
        for callback in callbacks:
            callback(table, id)
    except ConnectionError:
        print('Connection error, retry...')
        search_page(id, title, callbacks)
    except RequestException:
        print('Request error, retry...')
        search_page(id, title, callbacks)


def images(table, id):

    url = table.find_all('tr')[1].find('a').find('img')['src']
    if 'http' not in url:
        url = 'https:' + url
    print('get image from: ' + url)
    image = urllib.urlopen(url)
    with open(path.join('images',
                        id + '.' + url.split('.')[-1]),
              'wb') as out:
        out.write(image.read())


def structual(table, id):

    infos = {}
    for tr in table.find_all('tr'):
        th = tr.find('th')
        td = tr.find('td')
        if th and td:
            key = th.get_text().replace('\n', ' ').strip()
            texts = []
            for text in td.get_text().splitlines():
                text = text.strip()
                if text:
                    text = text.encode('utf-8')
                    text = text.replace('\xe2\x80\x93', '-')
                    if key == 'Release date':
                        text = date_pattern.findall(text)[0]
                    texts.append(text)
            infos[str(key)] = texts
    with codecs.open(path.join('structual', id + '.yaml'), 'w',
                     'utf8') as out:
        out.write(yaml.dump(infos,
                            encoding='utf-8',
                            default_flow_style=False))


def handler(args, id, title):

    if args.summary:
        summary(id, title)
    callbacks = []
    if args.image:
        callbacks.append(images)
    if args.structual:
        callbacks.append(structual)
    if len(callbacks):
        search_page(id, title, callbacks)


def main(args):

    if not args.summary and not args.image and not args.structual:
        print('nothing need to do')
        return

    total = 0
    success = 0
    utils.ensure_folder_exists('images')
    utils.ensure_folder_exists('structual')
    with codecs.open('movies.csv', 'r') as input:
        reader = csv.reader(input)
        firstline = True
        for info in reader:
            if firstline:    # skip first line
                firstline = False
                continue
            if len(info) != 3:
                print('unhandle line: ' + info)
                continue
            title = info[1]

            try:
                if try_all(args, info[0], title):
                    success += 1
                else:
                    error_output.write('{}\n'.format(info[0]))
            except Exception:
                print('get {} error'.format(info[0]))
                traceback.print_exc()
                error_output.write('{}\n'.format(info[0]))

            total += 1

    output.close()
    error_output.close()

    print('total: {}, success: {}'.format(total, success))


def try_all(args, id, title):

    akalist = aka_pattern.findall(title)
    if len(akalist) != 0:
        title = aka_pattern.sub('', title)
        title = ' '.join(title.split())
        title = title.strip()

    result = year_pattern.search(title)

    if result:
        index = result.start() - 1
        title_noyear = title[:index]
    else:
        title_noyear = title

    akalist.insert(0, title_noyear)
    title_nobrace = re.sub('\(.+?\)', '', title_noyear, 1)
    if title_nobrace != title_noyear:
        akalist.insert(0, title_nobrace)

    trylist = []
    for title_noyear in akalist:
        if title_noyear.endswith(', The'):
            title_noyear = 'The ' \
                + utils.replace_last(title_noyear,
                                     ', The',
                                     '')
        if title_noyear.endswith(', A'):
            title_noyear = 'A ' \
                    + utils.replace_last(title_noyear,
                                         ', A',
                                         '')
        if result:
            title_year = title_noyear + ' (' \
                         + title[result.start()+1:result.end()-1] \
                         + ' film)'
            trylist.append(title_year)

        title_film = title_noyear + ' (film)'
        trylist.append(title_film)
        trylist.append(title_noyear)

    for try_title in trylist:
        success = True
        try:
            handler(args, id, try_title)
        except (wikipedia.DisambiguationError,
                wikipedia.PageError) as ex:
            print(type(ex).__name__ + ' error occur, retry...')
            success = False
        if success:
            return True

    return False


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--image',
                        required=False,
                        action='store_true',
                        default=False,
                        help='get image')
    parser.add_argument('-s', '--summary',
                        required=False,
                        action='store_true',
                        default=False,
                        help='get summary')
    parser.add_argument('-t', '--structual',
                        required=False,
                        action='store_true',
                        default=False,
                        help='get structual')
    args = parser.parse_args()
    main(args)
