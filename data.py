import wikipedia
from requests.exceptions import ConnectionError
import codecs
import re
import traceback
import csv
import warnings
warnings.simplefilter("ignore", UserWarning)


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
            title = 'The ' + title.encode('utf-8').replace(', The', '')
        result = pattern.search(title)
        if result:
            index = result.end() - 1
            title = title[:index] + ' film' + title[index:]
        else:
            title = title + ' (film)'
        try:
            summary(info[0], title)
            success += 1
        except wikipedia.DisambiguationError:
            print 'Disambiguation error occur, retry...'
            if result:
                index = result.start()
                title = title[:index] + '(film)'
                try:
                    summary(info[0], title)
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
