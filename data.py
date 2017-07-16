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
warnings.simplefilter("ignore", UserWarning)

import utils


def write(out, id, s):

    out.write('{}\t{}\n'.format(
        id, s.encode('utf-8').replace('\n', '')))


def summary(id, title):

    try:
        print 'processing {} {} ...'.format(id, title)
        s = wikipedia.summary(title)
        write(output, id, s)
    except ConnectionError:
        print 'Connection error, retry...'
        summary(info[0], title)
    except RequestException:
        print 'Request error, retry...'
        summary(info[0], title)


def images(id, title):

    utils.ensure_folder_exists('images')
    try:
        print 'processing {} {} ...'.format(id, title)
        html = wikipedia.WikipediaPage(title).html()
        parsed_html = BeautifulSoup(html, 'html.parser')
        table = parsed_html.find('table', attrs={'class':'infobox vevent'})
        url = table.find_all('tr')[1].find('a').find('img')['src']
        if 'http' not in url:
            url = 'https:' + url
        print 'get image from: ' + url
        image = urllib.urlopen(url)
        with open(path.join('images',
                            id + '.' + url.split('.')[-1]),
                  'wb') as out:
            out.write(image.read())
    except ConnectionError:
        print 'Connection error, retry...'
        images(info[0], title)
    except RequestException:
        print 'Request error, retry...'
        images(info[0], title)


def handler(args, id, title):

    if args.summary:
        summary(id, title)
    if args.image:
        images(id, title)


def main(args):

    if not args.summary and not args.image:
        print 'nothing need to do'
        return

    output = codecs.open('output.txt', 'w')
    error_output = codecs.open('error.txt', 'w')
    pattern = re.compile(r'\([0-9]{4}\)')
    total = 0
    success = 0
    with codecs.open('movies.csv', 'r') as input:
        reader = csv.reader(input)
        firstline = True
        for info in reader:
            if firstline:    #skip first line
                firstline = False
                continue
            if len(info) != 3:
                print 'unhandle line: ' + line
                continue
            title = info[1]
            if ', The' in title:
                title = 'The ' + title.replace(', The', '')
            result = pattern.search(title)
            if result:
                index = result.end() - 1
                title = title[:index] + ' film' + title[index:]
            else:
                title = title + ' (film)'

            try:
                handler(args, info[0], title)
                success += 1
            except wikipedia.DisambiguationError:
                print 'Disambiguation error occur, retry...'
                if result:
                    index = result.start()
                    title = title[:index] + '(film)'
                    try:
                        handler(args, info[0], title)
                        success += 1
                    except Exception:
                        print 'get {} error again'.format(info[0])
                        traceback.print_exc()
                        error_output.write('{}\n'.format(info[0]))
            except Exception:
                print 'get {} error'.format(info[0])
                traceback.print_exc()
                error_output.write('{}\n'.format(info[0]))

            total += 1

    output.close()
    error_output.close()

    print 'total: {}, success: {}'.format(total, success)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--image', required=False,
            action='store_true', default=False, help='get image')
    parser.add_argument('-s', '--summary', required=False,
            action='store_true', default=False, help='get summary')
    args = parser.parse_args()
    main(args)
