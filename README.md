# Wikipedia-Search-Engine
This project aims to design and develop a scalable and efficient search engine using Wikipedia data. The creation of the search engine is divided into two parts: indexing (creating an inverted index from the given Wikipedia dump) and then searching based on the index created. The first part is being handled by `indexer.py` and the second by `query.py`.

The code is organized into two folders:
### English

- `indexer.py` handles the creation of the inverted index and the merging.
- `query.py` takes the query file (`queries.txt`) and gives the top ten hits as a `queries_op.txt` file.
- `stat.txt` gives the statistics regarding index size, number of files in the index and the number of tokens.

### Codemixed

- `indexer.py` creates the index and handles merging for the codemixed XML dump.
- `query.py` handles querying for the codemixed dump. The input queries are stored in `queries.txt` and the output will be stored in `queries_op.txt`.
- `stat.txt` gives the statistics regarding index size, number of files in the index and the number of tokens.
- `hi_stopwords.txt` stores Hindi stopwords.
- `hi_stemwords.txt` stores Hindi suffixes.

To optimize storage, the index format was chosen to keep only the necessary information, like the tokens and the parts of which documents they occur in. Blocked sort-based indexing algorithm was used, and the primary index was split up, followed by the creation of a secondary index. JSON format was used for easier processing.

These optimizations for the inverted index created from the larger English dump made it possible for the code to work with limited main memory. Getting rid of unnecessary symbols like commas in the index reduced storage by almost 20 percent. The codemixed indexer was directly built on the optimized code.

When using 4 CPUs, each with 2 GB memory, the inverted index for the smaller English dump is created in **387.62 seconds** with a total size of **191.4 MB**. For the codemixed dump, it takes about **79.1 seconds** with a total size of **35.9 MB**.

Format of the final index:
[token]|[docID][tn<sub>1</sub>|bn<sub>2</sub>|in<sub>3</sub>|cn<sub>4</sub>|ln<sub>5</sub>|rn<sub>6</sub>], where the keys are the different tokens sorted in alphabetical order, and the docIDs where a particular token occurs are listed one after the other separated by '|' symbol. t/b/i/c/l/r are used to specify the section of the article the word occurs in and are included only when the frequency n<sub>1</sub>/n<sub>2</sub>/n<sub>3</sub>/n<sub>4</sub>/n<sub>5</sub>/n<sub>6</sub> is greater than 0.
