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
warnings.simplefilter("ignore", UserWarning)


output = codecs.open('output.txt', 'w')
error_output = codecs.open('error.txt', 'w')


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


def images(id, title):

    utils.ensure_folder_exists('images')
    try:
        print('processing {} {} ...'.format(id, title))
        html = wikipedia.page(title).html()
        parsed_html = BeautifulSoup(html, 'html.parser')
        table = parsed_html.find('table', attrs={'class': 'infobox vevent'})
        url = table.find_all('tr')[1].find('a').find('img')['src']
        if 'http' not in url:
            url = 'https:' + url
        print('get image from: ' + url)
        image = urllib.urlopen(url)
        with open(path.join('images',
                            id + '.' + url.split('.')[-1]),
                  'wb') as out:
            out.write(image.read())
    except ConnectionError:
        print('Connection error, retry...')
        images(id, title)
    except RequestException:
        print('Request error, retry...')
        images(id, title)


def handler(args, id, title):

    if args.summary:
        summary(id, title)
    if args.image:
        images(id, title)


def main(args):

    if not args.summary and not args.image:
        print('nothing need to do')
        return

    year_pattern = re.compile(r'\([0-9]{4}\)')
    aka_pattern = re.compile(r'\(a\.k\.a\. (.+?)\)')
    total = 0
    success = 0
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
            if title.endswith(', The'):
                title = 'The ' + title.rreplace(', The', '', 1)
            if title.endswith(', A'):
                title = 'A ' + title.rreplace(', A', '', 1)

            akalist = aka_pattern.findall(title)
            if len(akalist) != 0:
                title = aka_pattern.sub('', title).strip()

            result = year_pattern.search(title)
            if result:
                index = result.end() - 1
                title = title[:index] + ' film' + title[index:]
            else:
                title = title + ' (film)'

            try:
                if try_all(args, info[0], akalist, result, title):
                    success += 1
            except Exception:
                print('get {} error'.format(info[0]))
                traceback.print_exc()
                error_output.write('{}\n'.format(info[0]))

            total += 1

    output.close()
    error_output.close()

    print('total: {}, success: {}'.format(total, success))


def try_all(args, id, akalist, result, title):

    if result:
        index = result.start() - 2
        title_noyear = title[:index]
    else:
        title_noyear = title

    akalist.insert(0, title_noyear)

    trylist = []
    for title_noyear in akalist:
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
    args = parser.parse_args()
    main(args)
