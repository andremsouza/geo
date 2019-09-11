# %% [markdown]
# # Extracting named entities from interviews, with NTLK

# %%
import psycopg2
import nltk
import nltk.tokenize
import nltk.tag
import nltk.chunk
# import getpass
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')
# %% [markdown]
# ## Setting up database connection
# %%
PASSWORD = None
# %%
# conn = psycopg2.connect(
#     "host=%s port=%s dbname=%s user=%s password=%s" %
#     ((str(input("Host: "))).strip(), (str(input("Port: "))).strip(),
#      (str(input("DatabaseName: "))).strip(),
#      (str(input("User: "))).strip(), getpass.getpass("Password: ")))
conn = psycopg2.connect(host='localhost',
                        dbname='icgeo',
                        user='andre',
                        password=PASSWORD)
cur = conn.cursor()
cur.close()

# %% [markdown]
# ## Getting a random interview from the database
# %%
try:
    with conn.cursor() as cur:
        cur.execute("""SELECT id, text FROM interviews
                    ORDER BY RANDOM()
                    LIMIT 1;""")
        id, text = cur.fetchone()
        cur.close()
        print(id)
except Exception as e:
    print(e)
    conn.rollback()
# %% [markdown]
# ## Testing NLTK named entity recognition
# ### Segmenting text into sentences and words, with tagging
# %%
sentences = nltk.tokenize.sent_tokenize(text, language='portuguese')
words = [
    nltk.tokenize.word_tokenize(sent, language='portuguese')
    for sent in sentences
]
tagged = nltk.tag.pos_tag_sents(words, lang='por')
# tagged = [nltk.tag.pos_tag(sent, lang='por') for sent in words]
ents = [nltk.chunk.ne_chunk(i, binary=True) for i in tagged]
# %%
