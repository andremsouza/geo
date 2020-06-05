# %% [markdown]
# # Performance tests for full-text search

# %%
# Imports
import psycopg2
from random import randint
import re
import seaborn as sns
import matplotlib.pyplot as plt
import requests
import requests.auth
import json

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
# Estabilishing connection to database
conn = psycopg2.connect(host=config.HOSTNAME,
                        port=config.PORT,
                        dbname=config.DBNAME,
                        user=config.USERNAME,
                        password=config.PASSWORD)
cur = conn.cursor()
cur.close()

# %%
# Preparing for N queries
times = []
labels = []

N = 1000

# Using an excerpt from an interview in the dataset
search_string = 'Aí depois desse pan-americano, desse pan-americano de 91 a gente continuou se dedicando à conjunto de solo'

# %% [markdown]
# ## Testing example of query plan
# %%
cur = conn.cursor()
cur.execute(
    """EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT id, text, questions, answers, meta,
                            ts_rank_cd(tstext,
                                       websearch_to_tsquery('portuguese',
                                                            %(search_string)s),
                                        1|4|32)
                                as rank
                        FROM interviews
                        WHERE tstext @@
                            websearch_to_tsquery('portuguese',
                                                 %(search_string)s)
                        ORDER BY rank DESC;
    """, {"search_string": search_string})
print(*cur.fetchall(), sep='\n')
cur.close()
conn.rollback()

# %% [markdown]
# ## Query 1: Using LIKE operator, without full-text search functionalities
# Note: in this query, ranking by relevance is not available
# %%
cur = conn.cursor()
cur.execute('SET enable_seqscan=true')
cur.execute('drop index interviews_idx_tstext;')
cur.execute(
    """EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT id, text, questions, answers, meta
                        FROM interviews
                        WHERE text LIKE %(search_string)s;
    """, {"search_string": '%' + search_string + '%'})
print(*cur.fetchall(), sep='\n')
cur.close()
conn.rollback()

# %%
# Getting execution times
cur = conn.cursor()
cur.execute('SET enable_seqscan=true')
cur.execute('drop index interviews_idx_tstext;')
aux = []
for i in range(N):
    cur.execute(
        """EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT id, text, questions, answers, meta
                        FROM interviews
                        WHERE text LIKE %(search_string)s;
    """, {"search_string": '%' + search_string + '%'})
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
cur.close()
conn.rollback()
times.append(aux)
labels.append("LIKE operator")

# %% [markdown]
# ## Query 2: Using @@ operator, without tsvector index

# %%
cur = conn.cursor()
cur.execute('SET enable_seqscan=true')
cur.execute('drop index interviews_idx_tstext;')
cur.execute(
    """EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT id, text, questions, answers, meta,
                            ts_rank_cd(tstext,
                                       websearch_to_tsquery('portuguese',
                                                            %(search_string)s),
                                        1|4|32)
                                as rank
                        FROM interviews
                        WHERE tstext @@
                            websearch_to_tsquery('portuguese',
                                                 %(search_string)s)
                        ORDER BY rank DESC;
    """, {"search_string": search_string})
print(*cur.fetchall(), sep='\n')
cur.close()
conn.rollback()

# %%
# Getting execution times
cur = conn.cursor()
cur.execute('SET enable_seqscan=true')
cur.execute('drop index interviews_idx_tstext;')
aux = []
for i in range(N):
    cur.execute(
        """EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT id, text, questions, answers, meta,
                            ts_rank_cd(tstext,
                                       websearch_to_tsquery('portuguese',
                                                            %(search_string)s),
                                        1|4|32)
                                as rank
                        FROM interviews
                        WHERE tstext @@
                            websearch_to_tsquery('portuguese',
                                                 %(search_string)s)
                        ORDER BY rank DESC;
    """, {"search_string": search_string})
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
cur.close()
conn.rollback()
times.append(aux)
labels.append("@@ operator")

# %% [markdown]
# ## Query 3: Using @@ operator, forcing usage of tsvector index

# %%
cur = conn.cursor()
cur.execute('SET enable_seqscan=false')
cur.execute('alter table interviews drop constraint interviews_pkey cascade;')
cur.execute(
    """EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT id, text, questions, answers, meta,
                            ts_rank_cd(tstext,
                                       websearch_to_tsquery('portuguese',
                                                            %(search_string)s),
                                        1|4|32)
                                as rank
                        FROM interviews
                        WHERE tstext @@
                            websearch_to_tsquery('portuguese',
                                                 %(search_string)s)
                        ORDER BY rank DESC;
    """, {"search_string": search_string})
print(*cur.fetchall(), sep='\n')
cur.close()
conn.rollback()

# %%
# Getting execution times
cur = conn.cursor()
cur.execute('SET enable_seqscan=false')
cur.execute('alter table interviews drop constraint interviews_pkey cascade;')
aux = []
for i in range(N):
    cur.execute(
        """EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT id, text, questions, answers, meta,
                            ts_rank_cd(tstext,
                                       websearch_to_tsquery('portuguese',
                                                            %(search_string)s),
                                        1|4|32)
                                as rank
                        FROM interviews
                        WHERE tstext @@
                            websearch_to_tsquery('portuguese',
                                                 %(search_string)s)
                        ORDER BY rank DESC;
    """, {"search_string": search_string})
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
cur.close()
conn.rollback()
times.append(aux)
labels.append("@@ operator with index")

# %% [markdown]
# ## Query 4: Using @@ operator, with access through the API

# %%
# creating API user
headers = {'Content-type': 'application/json'}
req = requests.post('http://localhost:5000/users',
                    auth=requests.auth.HTTPBasicAuth('api_admin', 'api_admin'),
                    data=json.dumps({
                        'new_username': 'test',
                        'new_password': 'test'
                    }),
                    headers=headers)
print('Status code: ', req.status_code)
print('JSON response: ', req.json())

# %%
# getting data from API
req = requests.get('http://localhost:5000/interviews/' + search_string,
                   auth=requests.auth.HTTPBasicAuth('test', 'test'))
print('Status code: ', req.status_code)
print('Elapsed time: ', req.elapsed.total_seconds() * 1000)

# %% getting execution times
for i in range(N):
    req = requests.get('http://localhost:5000/interviews/' + search_string,
                       auth=requests.auth.HTTPBasicAuth('test', 'test'))
    aux.append(req.elapsed.total_seconds() * 1000)
times.append(aux)
labels.append("@@ operator, wich index, API")

# %% [markdown]
# ## Graph comparison

# %%

sns.set()
plt.figure(figsize=(16, 9))
sns.boxplot(x=times, y=labels)
# plt.xlim(0, 0.2)
plt.title("Comparação de desempenho para consultas sobre entrevistas")
plt.ylabel("Consulta")
plt.xlabel("Tempo de execução (ms)")
plt.plot()
sns.set()
