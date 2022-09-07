import sys
import os
import re
import time
import math
import numpy as np 
import nltk
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer

stopWords = set(stopwords.words('english'))
snowStemmer = SnowballStemmer(language='english')
docCount = 0
ans = ""

def indexToJson(doc):
    fields = {"t": 0, "b": 0, "i": 0, "c": 0, "l": 0, "r": 0}
    split = re.split(r"([a-z])", doc)
    id = split[0]

    for f in range(1, len(split), 2):
        fields[split[f]] = int(split[f + 1])

    return [id, fields]

def tfScore(fields, field):
    #weights given to the various sections of the page
    wts = [100, 1, 20, 15, 0.5, 0.15]
    if field > -1:
        wts[field] += 1000

    return (1 + math.log(np.dot(wts, fields) + 1))

#ranking the articles
def scoring(docs, postings, field):
    global docCount

    for doc in docs:
        [id, fields] = indexToJson(doc)
        if id not in postings.keys():
            postings[id] = 0
        postings[id] += tfScore(list(fields.values()), field) * math.log(docCount / len(docs))

    return postings

#document number to title mapping
def filePostMap(fileNums):
    fileMap = {}

    for term in fileNums.keys():
        fileName = "{}.txt".format(fileNums[term])
        if fileName not in fileMap.keys():
            fileMap[fileName] = []

        fileMap[fileName].append(term)

    return fileMap

def binarySearch(filePath, strgs, postings, fieldQueries):
    f = open(filePath, "r")
    lines = f.readlines()
    low = 0

    for strg in strgs:
        mid = low
        high = len(lines)

        while low <= high:
            mid = (low + high) // 2
            parts = lines[mid].split('|')
            term = parts[0]

            if strg == term:
                fnum = -1
                for field in fieldQueries:
                    if strg in fieldQueries[field]: 
                        postings = scoring(parts[1:], postings, fnum)
                    fnum += 1

                break

            elif strg > term:
                low = mid + 1

            else:
                high = mid - 1

        low = mid

    return postings

def searchFile(filePath, strgs, postings, fieldQueries):
    f = open(filePath, "r")
    parts = f.readline().split('|')
    line = parts[0]

    ctr = 0
    lineNums = {}

    while line:
        for strg in strgs:
            if strg in lineNums.keys():
                continue

            if strg == line:
                lineNums[strg] = ctr
                if len(parts) > 1:
                    fnum = -1
                    for field in fieldQueries:
                        if strg in fieldQueries[field]: 
                            postings = scoring(parts[1:], postings, fnum)
                        fnum += 1

            elif strg < line:
                lineNums[strg] = ctr - 1

            else:
                break

        if len(lineNums.keys()) == len(strgs):
            break

        parts = f.readline().split('|')
        line = parts[0]
        ctr += 1

    if len(parts) > 1:
        return postings 

    return lineNums

def search(indexPath, terms, fieldQueries):
    postings = {}
    fileNums = searchFile(os.path.join(indexPath, "secondary.txt"), terms, postings, fieldQueries)
    fileMap = filePostMap(fileNums) 

    for indexFileName in fileMap.keys():
        postings = binarySearch(os.path.join(indexPath, indexFileName), fileMap[indexFileName], postings, fieldQueries)

    return postings

def queryProc(queryStrg):
    query = queryStrg.lower()
    parts = re.split(r"[^a-z0-9:]", query)
    #n is used for plain queries and t/b/i/c/l/r is used to store the corresponding segment of the field query
    fieldQueries = {"n": [], "t": [], "b": [], "i": [], "c": [], "l": [], "r": []}
    terms = set()
    cur = "n"

    for part in parts:
        subparts = re.split(":", part)

        if(len(subparts) == 1 and len(subparts[0])):
            if len(part) > 1 and part not in stopWords:
                term = snowStemmer.stem(part)
                fieldQueries[cur].append(term)
                terms.add(term)

        else:
            for i, subpart in enumerate(subparts):
                if(subpart in fieldQueries and subpart != "n" and i < len(subparts) - 1):
                    cur = subpart

                elif(len(subpart)):
                    if len(subpart) > 1 and subpart not in stopWords:
                        term = snowStemmer.stem(subpart)
                        fieldQueries[cur].append(term)
                        terms.add(term)

    return [terms, fieldQueries]

def disp(titlesFilePath, results, runtime):
    global ans

    titleFile = open(titlesFilePath, 'r')
    titles = titleFile.readlines()

    for res in results:
        print (res[0])
        ans += res[0] + ", " + titles[int(res[0])]

    ans += str(runtime) + "\n"
    opFile = open('queries_op.txt', 'a')
    opFile.write(ans)
    opFile.close()
    titleFile.close()
    ans = "\n"
        
def main(): 
    global docCount
    indexPath = sys.argv[1]
    queryFile = sys.argv[2]
    titlesFilePath = os.path.join(indexPath, 'titles.txt')
    docCount = sum(1 for line in open(titlesFilePath))
    if os.path.exists(indexPath):
        if os.path.exists(queryFile):
            f = open(queryFile, 'r')
            queries = f.readlines()

            for query in queries:
                start = time.time()

                [terms, fieldQueries] = queryProc(query)
                postings = search(indexPath, terms, fieldQueries)
                print (query+ str(postings))
                results = sorted(postings.items(), reverse=True, key=lambda item: item[1])[:10]
                end = time.time()
                disp(titlesFilePath, results, end - start)

            f.close()

        else:
            print("Query file does not exist")

    else:
        print("Index dir does not exist")

if __name__ == '__main__':
    main()
