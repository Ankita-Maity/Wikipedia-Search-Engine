import sys
import os
import re
import timeit
import xml.etree.ElementTree as ET
import nltk
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer

with open('hi_stopwords.txt', 'r') as f:
	hi_stopwords = [word.strip() for word in f]
hi_stopwords = set(hi_stopwords)
en_stopwords = set(stopwords.words('english'))
stopWords = hi_stopwords.union(en_stopwords)

with open('hi_stemwords.txt', 'r') as f:
	hi_stemwords = set([word.strip() for word in f])
snowStemmer = SnowballStemmer(language='english')

index = {}
stemmed = {}
batchSize = 10000
ctr = 0

def dump(outFolder, docs):
    global ctr, index

    filePath = os.path.join(outFolder, "{}.txt".format(ctr))
    indexWrite(filePath)
    titleWrite(docs[ctr * batchSize:], os.path.join(outFolder, "titles.txt"))
    ctr += 1

    print("Done with ", len(docs), " docs")
    index = {}

def titleWrite(docs, filePath):
    content = ""
    for i in range(len(docs)):
        content += docs[i] + "\n"

    titleFile = open(filePath, "a")
    titleFile.write(content)
    titleFile.close()

def indexWrite(filePath):
    labels = ["t", "b", "i", "c", "l", "r"]
    content = ""

    for word in sorted(index):
        line = word + "|"
        for idx, doc in enumerate(index[word]):
            totFreq = sum(index[word][doc])
            if(totFreq <= 1):
                continue

            line += doc
            ctr = 0

            for field in index[word][doc]:
                if(field):
                    line += labels[ctr] + str(field) 
                ctr += 1

            line += "|"

        if(line == word + "|"):
            continue

        line = line[:-1]
        line += "\n"
        content += line

    indexFile = open(filePath, "w")
    indexFile.write(content)
    indexFile.close()

def processing(text, id, field):
    #case folding
    text = text.lower()
    #tokenization
    tokens = re.split(r'[^a-z0-9]+', text)

    for token in tokens:
        c = 0
        #removing stopwords
        if len(token) > 1 and token not in stopWords:
            #stemming
            if token not in stemmed:
                for h in hi_stemwords:
                    if token.endswith(h):
                        stemmed[token] = token[:-len(h)]
                        c = 1
                if c==0:
                    stemmed[token] = snowStemmer.stem(token)
            word = stemmed[token]

            if word not in index:
                index[word] = { id: [0, 0, 0, 0, 0, 0] }
            elif id not in index[word]:
                index[word][id] = [0, 0, 0, 0, 0, 0]

            index[word][id][field] += 1

def getInfobox(text):
    string = ""
    regex = re.compile('{{ ?Infobox ', re.I)
    segs = regex.split(text)[1:]

    if len(segs):
        split = re.split('}}', segs[-1])
        for j in split:
            if '{{' not in j:
                segs[-1] = j
                break

        string = '\n'.join(segs)

    return string

def getCategory(text):
    string = ""
    regex = re.compile('\[\[Category:(.+)\]\]', re.I)

    for i in regex.finditer(text):
        string += '\n' + i.group(1)

    return string

def getLinks(text):
    string = ""
    regex = re.compile('== ?External Links ?==([\S\s]+)', re.I)
    segs = regex.split(text)[1:]

    if len(segs):
        split = re.split('\n\n', segs[-1])
        links = re.split('\*', split[0])
        string = '\n'.join(links)

    return string

def getRefs(text):
    string = ""
    regex = re.compile('== ?References ?==([\S\s]+)', re.I)
    segs = regex.split(text)[1:]

    if len(segs):
        endRex = re.compile('{{authority control|{{defaultsort|\[\[category|\n==\w+', re.I)
        refs = endRex.split(segs[-1])[0]

        cleanRex = re.compile('{{reflist', re.I)
        clean = cleanRex.split(refs)
        string = '\n'.join(clean)

    return string

def bodyParse(body, id, title):
    comps = {
            'title': title,
            'body': body,
            'infobox': getInfobox,
            'category': getCategory,
            'links': getLinks,
            'references': getRefs,
            }
    ctr = 0

    for key in comps:
        string = ""
        if isinstance(comps[key], str):
            string = comps[key]
        else:
            string = comps[key](body)

        words = processing(string, id, ctr)
        ctr += 1

def parse(file_path, outFolder, statFile):
    docs = []

    context = ET.iterparse(file_path, events=("start", "end"))
    event, root = next(context)

    for event, elem in context:
        if event == "end":
            _, _, elem.tag = elem.tag.rpartition('}')

            if elem.tag == 'title':
                docs.append(elem.text)

            elif elem.tag == 'text' and elem.text != None:
                docId = len(docs) - 1
                bodyParse(elem.text, str(docId), docs[docId])

            elif elem.tag == 'page':
                if len(docs) % batchSize == 0:
                    dump(outFolder, docs)

            elif elem.tag == 'mediawiki':
                dump(outFolder, docs)

            root.clear()
#splitting the index and maintaining a secondary index
def split(indexPath, folder):

    secondary = os.path.join(folder, "secondary.txt")
    ctr = 0
    currName = ""
    curr = None

    with open(indexPath, 'r') as inp, open(secondary, 'w') as sec:
        while True:
            line = inp.readline()
            if not line:
                break

            if not curr:
                print("Making file {}.txt".format(ctr))
                currName = os.path.join(folder, "{}.txt".format(ctr))
                curr = open(currName, 'w')
                sec.write(line.split('|')[0] + "\n")

            curr.write(line)
            size = os.path.getsize(currName) / (1024 * 1024)
            if size > 16:
                curr.close()
                curr = None
                ctr += 1

    curr.close()

def merge(file1, file2, mergeFile):  
    with open(mergeFile, 'w') as op, open(file1, 'r') as f1, open(file2, 'r') as f2:
        line1 = f1.readline()
        line2 = f2.readline()

        while line1 or line2:
            if not line1:
                op.write(line2)
                line2 = f2.readline()

            elif not line2:
                op.write(line1)
                line1 = f1.readline()

            else:
                parts1 = line1.split('|')
                parts2 = line2.split('|')
                w1 = parts1[0]
                postings1 = '|'.join(parts1[1:])
                w2 = parts2[0]
                postings2 = '|'.join(parts2[1:])
                
                if w1 < w2:  
                    op.write(line1)  
                    line1 = f1.readline()

                elif w1 > w2:  
                    op.write(line2)  
                    line2 = f2.readline()

                else:
                    line = w1 + '|' + postings1.strip('\n') + '|' + postings2
                    op.write(line)

                    line1 = f1.readline()
                    line2 = f2.readline()

        os.remove(file1)
        os.remove(file2)

def mergeSort(folder):
    files = os.listdir(folder)

    while len(files) > 2:
        print("Number of index files: {}".format(len(files) - 1))

        for i in range(0, len(files) - 1, 2):
            old = os.path.join(folder, "{}.txt".format(i))
            new = os.path.join(folder, "{}.txt".format(i // 2))

            if(i + 1 < len(files) - 1):
                f1 = os.path.join(folder, "{}.txt".format(i))
                f2 = os.path.join(folder, "{}.txt".format(i + 1))
                old = os.path.join(folder, "merge.txt")
                merge(f1, f2, old)

            os.rename(old, new)

        files = os.listdir(folder)

    old = os.path.join(folder, "0.txt")
    new = os.path.join(folder, "index.txt")
    os.rename(old, new)
    return new

def finalInd(folder):
    indexPath = mergeSort(folder)
    split(indexPath, folder)
    os.remove(indexPath)

def saveStats(statsPath, filePath):
	with open(statsPath, 'w') as f:
		f.write("%.2f\n" % getDirectorySizeGB(filePath))
		f.write(str(len(os.listdir(filePath))) + '\n')
		f.write(str(len(stemmed)) + '\n')


def getDirectorySizeGB(filePath):
	if not os.path.isdir(filePath):
		return 0
	return sum(os.path.getsize(os.path.join(filePath, f)) for f in os.listdir(filePath) if os.path.isfile(os.path.join(filePath, f))) / (1024*1024*1024)

def main(): 
    wikiPath = sys.argv[1]
    indexPath = sys.argv[2]
    indexStat = sys.argv[3]

    start = timeit.default_timer()
    try:
        os.mkdir(indexPath)
    except FileExistsError:
        print("Directory already exists")

    parse(wikiPath, indexPath, indexStat)
    finalInd(indexPath)
    saveStats(indexStat, indexPath)
    stop = timeit.default_timer()
    print('Time taken for indexing:', stop - start)

if __name__ == '__main__':
    main()
