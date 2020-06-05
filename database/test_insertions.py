# Script to test processing and insertion of interviews into PostgreSQL
# %% [markdown]
# # Interview processing and insertion into test database

# %%
import psycopg2
import os
import docx2json
import json
import re
import random
import nltk.tokenize
import nltk.corpus
import nltk.stem
import spacy

try:
    import config  # Try to import attributes from config.py
except Exception as e:  # If no config.py, define Object with empty attributes
    print('Warning: No config.py found. ' +
          'Using empty values for non-provided connection attributes. ' +
          str(e))

    class Object(object):
        """Dummy class for config attributes."""
        pass

    config = Object()
    config.HOSTNAME = ''
    config.PORT = -1
    config.DBNAME = ''
    config.USERNAME = ''
    config.PASSWORD = ''

# %%
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('rslp')
nltk.download('words')

# %% [markdown]
# ## Setting up database connection

# %%
conn = psycopg2.connect(host=config.HOSTNAME,
                        port=config.PORT,
                        dbname=config.DBNAME,
                        user=config.USERNAME,
                        password=config.PASSWORD)
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
# patterns and possible false match in existing ones
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
    if ('USP – ' in json_arr[idx]['text'][1]
            or 'USP – ' in json_arr[idx]['text'][2]):
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
        'questions': [
            y for x in [
                nltk.tokenize.word_tokenize(i, language='portuguese')
                for i in nltk.tokenize.sent_tokenize(
                    '\n'.join(x['bold']).lower(), language='portuguese')
            ] for y in x
        ],
        'answers': [
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
    for idx2, tok in enumerate(interviews_split[-1]['questions']):
        if re.match(dot_re, tok):
            interviews_split[-1]['questions'][idx2] = tok[:-1]
    for idx2, tok in enumerate(interviews_split[-1]['answers']):
        if re.match(dot_re, tok):
            interviews_split[-1]['answers'][idx2] = tok[:-1]

    # Generating token set, removing stopwords
    tokens.append({
        'text':
        set(interviews_split[idx]['text']) -
        set(nltk.corpus.stopwords.words('portuguese')),
        'questions':
        set(interviews_split[idx]['questions']) -
        set(nltk.corpus.stopwords.words('portuguese')),
        'answers':
        set(interviews_split[idx]['answers']) -
        set(nltk.corpus.stopwords.words('portuguese'))
    })

# %%
# Generating bag-of-words (stemmed or not) for insertion at the database
stemmer = nltk.stem.rslp.RSLPStemmer()
# stemmer = nltk.stem.snowball.SnowballStemmer('portuguese') # optional
metas = []
for idx, x in enumerate(interviews_split):
    meta = {
        'text': {
            'bow': {},
            'bow_stemmed': {}
        },
        'questions': {
            'bow': {},
            'bow_stemmed': {}
        },
        'answers': {
            'bow': {},
            'bow_stemmed': {}
        }
    }
    for token in tokens[idx]['text']:
        meta['text']['bow'][token] = x['text'].count(token)
        meta['text']['bow_stemmed'][
            stemmer.stem(token)] = meta['text']['bow_stemmed'].get(
                stemmer.stem(token), 0) + meta['text']['bow'][token]
    for token in tokens[idx]['questions']:
        meta['questions']['bow'][token] = x['questions'].count(token)
        meta['questions']['bow_stemmed'][stemmer.stem(
            token)] = meta['questions']['bow_stemmed'].get(
                stemmer.stem(token), 0) + meta['questions']['bow'][token]
    for token in tokens[idx]['answers']:
        meta['answers']['bow'][token] = x['answers'].count(token)
        meta['answers']['bow_stemmed'][stemmer.stem(
            token)] = meta['answers']['bow_stemmed'].get(
                stemmer.stem(token), 0) + meta['answers']['bow'][token]
    metas.append(meta)

# %%
# Extracting named entities with spaCy
nlp = spacy.load('pt_core_news_sm')
for idx, meta in enumerate(metas):
    doc = nlp('\n'.join(json_arr[idx]['text']))
    meta['named_entities'] = [{
        'text': ent.text,
        'start_char': ent.start_char,
        'end_char': ent.end_char,
        'label': ent.label_
    } for ent in doc.ents]

# %% [markdown]
# ## Insertion of data into the database

# %%
try:
    cur = conn.cursor()
    for idx, data in enumerate(json_arr):
        cur.execute(
            """INSERT INTO interviews (id, text, questions, answers, meta)
                VALUES
                    (%(id)s, %(texto)s, %(perguntas)s, %(respostas)s, %(meta)s)
                ON CONFLICT DO NOTHING;""", {
                'id': input_files_ids[idx],
                'texto': '\n'.join(data['text']),
                'perguntas': data['bold'],
                'respostas': data['nonbold'],
                'meta': json.dumps(metas[idx])
            })
    conn.commit()
    cur.close()
except Exception as e:
    print(e)
    conn.rollback()

# %% [markdown]
# ## Making an additional number of insertions, for tests with a high number of rows

# %%
num_iterations = 10000
try:
    cur = conn.cursor()
    for i in range(num_iterations):
        idx = random.randint(0, len(input_files_ids) - 1)
        data = json_arr[idx]
        cur.execute(
            """INSERT INTO interviews (id, text, questions, answers, meta)
                VALUES
                    (%(id)s, %(texto)s, %(perguntas)s, %(respostas)s, %(meta)s)
                ON CONFLICT DO NOTHING;""", {
                'id': 100 + i,
                'texto': '\n'.join(data['text']),
                'perguntas': data['bold'],
                'respostas': data['nonbold'],
                'meta': json.dumps(metas[idx])
            })
    conn.commit()
    cur.close()
except Exception as e:
    print(e)
    conn.rollback()

# %%
cur = conn.cursor()
cur.execute("""SELECT COUNT(*) FROM INTERVIEWS;""")
print(cur.fetchall())
cur.close()

# %% [markdown]
# ## Updating statistics for index usage

# %%
conn.rollback()
conn.set_session(autocommit=True)
cur = conn.cursor()
cur.execute("""VACUUM ANALYZE interviews;""")
conn.commit()
cur.close()
conn.set_session(autocommit=False)

# %%
