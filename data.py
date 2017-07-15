import wikipedia
import codecs
import re


output = codecs.open('output.txt', 'w')
error_output = codecs.open('error.txt', 'w')
pattern = re.compile(r'\([0-9]{4}\)')
total = 0
success = 0
with codecs.open('movies.csv', 'r') as input:
    lines = input.read().splitlines()
    for line in lines[1:]:
        info = line.split(',')
        title = info[1]
        result = pattern.search(title)
        if result:
            index = result.start() - 1
            title = title[:index] + ' film' + title[index:]
        else:
            title = title + ' (film)'
        try:
            s = wikipedia.summary(title)
            output.write('{}\t{}\n'.format(
                    info[0],
                   s.replace('\n', ' ')))
            success += 1
        except Exception, e:
            print 'get {} error'.format(info[0])
            error_output.write('{}\n'.format(info[0]))
        total += 1

output.close()
error_output.close()

print 'total: {}, success: {}'.format(total, success)
