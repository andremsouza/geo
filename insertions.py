# %% [markdown]
# # Interview processing and insertion into test database

# %%
import psycopg2
# import getpass
import os
import docx2json
import json
import re
import nltk.tokenize
import nltk.corpus
import nltk.stem
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('rslp')

# %% [markdown]
# ## Setting up database connection

# %%
# conn = psycopg2.connect(
#     "host=%s port=%s dbname=%s user=%s password=%s" %
#     ((str(input("Host: "))).strip(), (str(input("Port: "))).strip(),
#      (str(input("DatabaseName: "))).strip(),
#      (str(input("User: "))).strip(), getpass.getpass("Password: ")))
PASSWORD = None
conn = psycopg2.connect(host='localhost',
                        dbname='icgeo',
                        user='andre',
                        password=PASSWORD)
cur = conn.cursor()
cur.close()

# %% [markdown]
# ## Processing interviews with simple pattern recognition / standardizing
# %% [markdown]
# ### Listing input files

# %%
# Get all input files and sort by athlete id
input_files = sorted(
    os.listdir('./source-files/GRD Pronto/Entrevistas Completas'),
    key=lambda id: int(id[:2]))
input_files_ids = [int(f[:2]) for f in input_files]
input_files = [
    os.getcwd() + '/source-files/GRD Pronto/Entrevistas Completas/' + file
    for file in input_files
]
print("Interviews (number of documents = %d):" % len(input_files),
      input_files_ids,
      *input_files,
      sep='\n')

# %% [markdown]
# ### Converting input files to JSON with docx2json

# %%
# Convert all documents into a JSON (dict) list
json_arr = [json.loads(docx2json.convert(f)) for f in input_files]

# %% [markdown]
# ### Simple pattern recognition

# %%
# Separating pattern indexes
# I may need to make those recognitions more complex, depending on new
# patterns and possible match in existing ones
json_patterns = {}
json_patterns['bold-nonbold'] = [
    idx for idx, f in enumerate(json_arr)
    if f['text'][0] == 'Início da transcrição'
]
json_patterns['athlete-name'] = [
    idx for idx, f in enumerate(json_arr) if 'Atleta: ' in f['text'][0]
]
json_patterns['one-one-abbr'] = [
    idx for idx, f in enumerate(json_arr)
    if 'USP – ' in f['text'][1] or 'USP – ' in f['text'][2]
]
json_patterns['black-colored'] = [
    idx for idx, f in enumerate(json_arr)
    if (' nascida em ' in f['text'][0] or ' nascido em ' in f['text'][0])
]
json_patterns['all-nonbold-names'] = [
    idx for idx, f in enumerate(json_arr) if 'Transcrição' in f['text'][0]
]
json_patterns

# %% [markdown]
# ### Processing each pattern

# %%
# Processing 'bold-nonbold' pattern files
# Removing 'Início da transcrição' from 'bold-nonbold' pattern files
for idx in json_patterns['bold-nonbold']:
    if json_arr[idx]['text'][0] == 'Início da transcrição':
        del json_arr[idx]['text'][0]
    if json_arr[idx]['bold'][0] == 'Início da transcrição':
        del json_arr[idx]['bold'][0]
    if 'Início da transcrição ' in json_arr[idx]['bold'][0]:
        json_arr[idx]['bold'][0] = json_arr[idx]['bold'][0].replace(
            'Início da transcrição ', '')
#   Removing trailing spaces
    for idx2, s in enumerate(json_arr[idx]['text']):
        json_arr[idx]['text'][idx2] = s.strip(' ')
    for idx2, s in enumerate(json_arr[idx]['bold']):
        json_arr[idx]['bold'][idx2] = s.strip(' ')
    for idx2, s in enumerate(json_arr[idx]['nonbold']):
        json_arr[idx]['nonbold'][idx2] = s.strip(' ')

# %%
# Processing 'athlete-name' pattern files
# Removing names from paragraph authors and trailing spaces, along other
# redundant information
questionset = set(['Kátia', 'Entrevistador'
                   ])  # to determine if the paragraph is 'bold' or 'nonbold'
for idx in json_patterns['athlete-name']:
    if 'Atleta: ' in json_arr[idx]['text'][0]:
        del json_arr[idx]['text'][0:2]
        json_arr[idx]['nonbold'] = []
        for idx2, s in enumerate(json_arr[idx]['text']):
            json_arr[idx]['text'][idx2] = s.strip(' ')
            splitpar = s.split(': ', 1)
            if (len(splitpar) == 2):
                json_arr[idx]['text'][idx2] = splitpar[1]
                if (splitpar[0] in questionset):
                    json_arr[idx]['bold'].append(splitpar[1])
                else:
                    json_arr[idx]['nonbold'].append(splitpar[1])
            else:
                json_arr[idx]['nonbold'].append(splitpar[0])
#   Removing trailing spaces
    for idx2, s in enumerate(json_arr[idx]['text']):
        json_arr[idx]['text'][idx2] = s.strip(' ')
    for idx2, s in enumerate(json_arr[idx]['bold']):
        json_arr[idx]['bold'][idx2] = s.strip(' ')
    for idx2, s in enumerate(json_arr[idx]['nonbold']):
        json_arr[idx]['nonbold'][idx2] = s.strip(' ')

# %%
# Processing 'one-one-abbr' pattern files
# Removing names from paragraph authors and trailing spaces, along other
# redundant information
questionset = set(['USP'])
for idx in json_patterns['one-one-abbr']:
    if ('USP – ' in json_arr[idx]['text'][1] or
            'USP – ' in json_arr[idx]['text'][2]):
        del json_arr[idx]['text'][0]
        json_arr[idx]['nonbold'] = []
        for idx2, s in enumerate(json_arr[idx]['text']):
            json_arr[idx]['text'][idx2] = s.strip(' ')
            splitpar = s.split(' – ', 1)
            if (len(splitpar) == 2):
                json_arr[idx]['text'][idx2] = splitpar[1]
                if (splitpar[0] in questionset):
                    json_arr[idx]['bold'].append(splitpar[1])
                else:
                    json_arr[idx]['nonbold'].append(splitpar[1])
            else:
                json_arr[idx]['nonbold'].append(splitpar[0])
#   Removing trailing spaces
    for idx2, s in enumerate(json_arr[idx]['text']):
        json_arr[idx]['text'][idx2] = s.strip(' ')
    for idx2, s in enumerate(json_arr[idx]['bold']):
        json_arr[idx]['bold'][idx2] = s.strip(' ')
    for idx2, s in enumerate(json_arr[idx]['nonbold']):
        json_arr[idx]['nonbold'][idx2] = s.strip(' ')

# %%
# Processing 'black-colored' pattern files
check = False
for idx in json_patterns['black-colored']:
    json_arr[idx]['nonbold'] = []
    json_arr[idx]['bold'] = []
    # Removing unwanted information
    for idx2, s in enumerate(json_arr[idx]['text']):
        if (not check):
            check = 'Entrevista realizada em ' in s
        else:
            del json_arr[idx]['text'][0:idx2]
            break
# Separating questions and answers
    for idx2, s in enumerate(json_arr[idx]['text']):
        if (idx2 % 2 == 0):
            json_arr[idx]['bold'].append(s)
        else:
            json_arr[idx]['nonbold'].append(s)
# Removing trailing spaces
    for idx2, s in enumerate(json_arr[idx]['text']):
        json_arr[idx]['text'][idx2] = s.strip(' ')
    for idx2, s in enumerate(json_arr[idx]['bold']):
        json_arr[idx]['bold'][idx2] = s.strip(' ')
    for idx2, s in enumerate(json_arr[idx]['nonbold']):
        json_arr[idx]['nonbold'][idx2] = s.strip(' ')

# %%
# Processing 'all-nonbold-names' pattern files

# Processing 'athlete-name' pattern files
# Removing names from paragraph authors and trailing spaces, along other
# redundant information
questionset = set(['Kátia', 'Entrevistador', 'ENTREVISTADORA'
                   ])  # to determine if the paragraph is 'bold' or 'nonbold'
for idx in json_patterns['all-nonbold-names']:
    if 'Transcrição ' in json_arr[idx]['text'][0]:
        del json_arr[idx]['text'][0]
        json_arr[idx]['nonbold'] = []
        for idx2, s in enumerate(json_arr[idx]['text']):
            json_arr[idx]['text'][idx2] = s.strip(' ')
            splitpar = s.split(': ', 1)
            if (len(splitpar) == 2):
                json_arr[idx]['text'][idx2] = splitpar[1]
                if (splitpar[0] in questionset):
                    json_arr[idx]['bold'].append(splitpar[1])
                else:
                    json_arr[idx]['nonbold'].append(splitpar[1])
            else:
                json_arr[idx]['nonbold'].append(splitpar[0])
#   Removing trailing spaces
    for idx2, s in enumerate(json_arr[idx]['text']):
        json_arr[idx]['text'][idx2] = s.strip(' ')
    for idx2, s in enumerate(json_arr[idx]['bold']):
        json_arr[idx]['bold'][idx2] = s.strip(' ')
    for idx2, s in enumerate(json_arr[idx]['nonbold']):
        json_arr[idx]['nonbold'][idx2] = s.strip(' ')

# %% [markdown]
# ## Generating META Information

# %%
# Duplicate, remove punctation and split into single words for each interview
# Create set of tokens for each interview, removing stopwords in the process
interviews_split = []
tokens = []
for idx, x in enumerate(json_arr):
    # Tokenize using NLTK
    interviews_split.append({
        'text': [
            y for x in [
                nltk.tokenize.word_tokenize(i, language='portuguese')
                for i in nltk.tokenize.sent_tokenize(
                    '\n'.join(x['text']).lower(), language='portuguese')
            ] for y in x
        ],
        'q': [
            y for x in [
                nltk.tokenize.word_tokenize(i, language='portuguese')
                for i in nltk.tokenize.sent_tokenize(
                    '\n'.join(x['bold']).lower(), language='portuguese')
            ] for y in x
        ],
        'a': [
            y for x in [
                nltk.tokenize.word_tokenize(i, language='portuguese')
                for i in nltk.tokenize.sent_tokenize(
                    '\n'.join(x['nonbold']).lower(), language='portuguese')
            ] for y in x
        ],
    })

    # Removing tokens with trailing dots.
    dot_re = r'^[^\.]+\.$'
    for idx2, tok in enumerate(interviews_split[-1]['text']):
        if re.match(dot_re, tok):
            interviews_split[-1]['text'][idx2] = tok[:-1]
    for idx2, tok in enumerate(interviews_split[-1]['q']):
        if re.match(dot_re, tok):
            interviews_split[-1]['q'][idx2] = tok[:-1]
    for idx2, tok in enumerate(interviews_split[-1]['a']):
        if re.match(dot_re, tok):
            interviews_split[-1]['a'][idx2] = tok[:-1]

    # Generating token set, removing stopwords
    tokens.append({
        'text':
        set(interviews_split[idx]['text']) -
        set(nltk.corpus.stopwords.words('portuguese')),
        'q':
        set(interviews_split[idx]['q']) -
        set(nltk.corpus.stopwords.words('portuguese')),
        'a':
        set(interviews_split[idx]['a']) -
        set(nltk.corpus.stopwords.words('portuguese'))
    })

# %%
# Generating bag-of-words (stemmed or not) for insertion at the database
# stemmer = nltk.stem.snowball.SnowballStemmer('portuguese')
stemmer = nltk.stem.rslp.RSLPStemmer()
metas = []
for idx, x in enumerate(interviews_split):
    meta = {
        'text': {
            'bag': {},
            'bag_stemmed': {}
        },
        'q': {
            'bag': {},
            'bag_stemmed': {}
        },
        'a': {
            'bag': {},
            'bag_stemmed': {}
        }
    }
    for token in tokens[idx]['text']:
        meta['text']['bag'][token] = x['text'].count(token)
        meta['text']['bag_stemmed'][
            stemmer.stem(token)] = meta['text']['bag_stemmed'].get(
                stemmer.stem(token), 0) + meta['text']['bag'][token]
    for token in tokens[idx]['q']:
        meta['q']['bag'][token] = x['q'].count(token)
        meta['q']['bag_stemmed'][
            stemmer.stem(token)] = meta['q']['bag_stemmed'].get(
                stemmer.stem(token), 0) + meta['q']['bag'][token]
    for token in tokens[idx]['a']:
        meta['a']['bag'][token] = x['a'].count(token)
        meta['a']['bag_stemmed'][
            stemmer.stem(token)] = meta['a']['bag_stemmed'].get(
                stemmer.stem(token), 0) + meta['a']['bag'][token]
    metas.append(meta)

# %% [markdown]
# ## Insertion of data into the database

# %%
cur = conn.cursor()
for idx, data in enumerate(json_arr):
    cur.execute(
        """INSERT INTO interviews (id, text, questions, answers)
            VALUES (%(id)s, %(texto)s, %(perguntas)s, %(respostas)s)
            ON CONFLICT DO UPDATE;""", {
            'id': input_files_ids[idx],
            'texto': '\n'.join(data['text']),
            'perguntas': data['bold'],
            'respostas': data['nonbold']
        })
conn.commit()
cur.close()

# %% [markdown]
# ## Setting up database connection for performance testing
# %% [markdown]
# ## Testing full-text search tools and comparing META information

# %%
cur = conn.cursor()
cur.execute("""SELECT ID, tsvector_to_array(TO_TSVECTOR('portuguese', text))
        FROM interviews
        ORDER BY ID ASC;""")
dbout = cur.fetchall()
cur.close()

# %%
# Differences between my extraction method and the one done by the DBMS
for idx, i in enumerate(dbout):
    print("ID: ", i[0])
    print("Lista A (in postgres, not in metas):")
    for j in i[1]:
        if j not in list(metas[idx]['text']['bag_stemmed'].keys()):
            print(j)
    print("Lista B (in metas, not in postgres):")
    for j in list(metas[idx]['text']['bag_stemmed'].keys()):
        if j not in i[1]:
            print(j)
    print("")
