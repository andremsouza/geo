# %% [markdown]
# # Testes de desempenho para JSON, JSONB e TEXT\[\] (PostgreSQL 9.6)
# Neste documento, estão descritos testes de desempenho para tipos de dados
# JSON, JSONB, e TEXT\[\] complementando as séries de testes anteriores.
# Serão testadas as funcionalidades de full text search do PostgreSQL,
# utilizando 18 entrevistas reais.

# %%
# Imports
import psycopg2
from random import randint
import re
import seaborn as sns
import matplotlib.pyplot as plt
import getpass

# %%
# Estabilishing connection to database
conn = psycopg2.connect("host=%s port=%s dbname=%s user=%s password=%s" %
                        (input("Host: "), input("Port: "), input("DBName: "),
                         input("User: "), getpass.getpass("Password: ")))
cur = conn.cursor()

# %%
# Analyzing table sizes
cur.execute("""SELECT PG_SIZE_PRETTY(PG_TOTAL_RELATION_SIZE('JSONTEST'))""")
print('JSONTEST SIZE: ', cur.fetchall()[0][0])
cur.execute("""SELECT PG_SIZE_PRETTY(PG_TOTAL_RELATION_SIZE('JSONBTEST'))""")
print('JSONBTEST SIZE:', cur.fetchall()[0][0])
cur.execute("""SELECT PG_SIZE_PRETTY(PG_TOTAL_RELATION_SIZE('TEXTARRTEST'))""")
print('TEXTARRTEST SIZE:', cur.fetchall()[0][0])

# %% [markdown]
# ## Testes de desempenho para os tipos de dados JSON, JSONB e TEXT\[\]

# %%
# Preparing for N queries
times = []
labels = []

N = 1000

# %%
# Recovering available IDs
cur = conn.cursor()
cur.execute("""SELECT ID FROM TEXTARRTEST ORDER BY ID ASC;""")
ids = cur.fetchall()
ids = [i[0] for i in ids]

# %%
# Accessing  an entire tuple of JSONBTEST
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute(
        """EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT * FROM JSONBTEST WHERE ID = %(int)s;""",
        {'int': ids[randint(0,
                            len(ids) - 1)]})
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times.append(aux)
labels.append("JSONB entire row")

# Accessing  an entire tuple of JSONTEST
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute(
        """EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT * FROM JSONTEST WHERE ID = %(int)s;""",
        {'int': ids[randint(0,
                            len(ids) - 1)]})
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times.append(aux)
labels.append("JSON entire row")

# Accessing  an entire tuple of TEXT[]
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute(
        """EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT * FROM TEXTARRTEST WHERE ID = %(int)s;""",
        {'int': ids[randint(0,
                            len(ids) - 1)]})
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times.append(aux)
labels.append("TEXT[] entire row")

# %%
# Accessing an entire JSONB
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute(
        """EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT INTERVIEW FROM JSONBTEST WHERE ID = %(int)s;""",
        {'int': ids[randint(0,
                            len(ids) - 1)]})
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times.append(aux)
labels.append("JSONB entire object")

# Accessing an entire JSON
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute(
        """EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT INTERVIEW FROM JSONTEST WHERE ID = %(int)s;""",
        {'int': ids[randint(0,
                            len(ids) - 1)]})
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times.append(aux)
labels.append("JSON entire object")

# Accessing an entire TEXT[] data
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute(
        """EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT TEXTO, PERGUNTAS, RESPOSTAS FROM TEXTARRTEST
                WHERE ID = %(int)s;""", {'int': ids[randint(0,
                                                            len(ids) - 1)]})
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times.append(aux)
labels.append("TEXT[] entire object")

# %%
# Accessing 'text' from a JSONB
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute(
        """EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT INTERVIEW->'text' FROM JSONBTEST WHERE ID = %(int)s;""",
        {'int': ids[randint(0,
                            len(ids) - 1)]})
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times.append(aux)
labels.append("JSONB 'text'")

# Accessing 'text' from a JSON
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute(
        """EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT INTERVIEW->'text' FROM JSONTEST WHERE ID = %(int)s;""",
        {'int': ids[randint(0, len(ids)) - 1]})
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times.append(aux)
labels.append("JSON 'text'")

# Accessing 'text' from a TEXT[]
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute(
        """EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT TEXTO FROM TEXTARRTEST WHERE ID = %(int)s;""",
        {'int': ids[randint(0,
                            len(ids) - 1)]})
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times.append(aux)
labels.append("TEXT[] 'text'")

# %%
# Accessing 'bold' from a JSONB
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute(
        """EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT INTERVIEW->'bold' FROM JSONBTEST WHERE ID = %(int)s;""",
        {'int': ids[randint(0,
                            len(ids) - 1)]})
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times.append(aux)
labels.append("JSONB 'bold'")

# Accessing 'bold' from a JSON
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute(
        """EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT INTERVIEW->'bold' FROM JSONTEST WHERE ID = %(int)s;""",
        {'int': ids[randint(0,
                            len(ids) - 1)]})
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times.append(aux)
labels.append("JSON 'bold'")

# Accessing 'bold' from a TEXT[]
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute(
        """EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT PERGUNTAS FROM TEXTARRTEST WHERE ID = %(int)s;""",
        {'int': ids[randint(0,
                            len(ids) - 1)]})
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times.append(aux)
labels.append("TEXT[] 'bold'")

# %%
# Accessing 'nonbold' from a JSONB
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute(
        """EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT INTERVIEW->'nonbold' FROM JSONBTEST WHERE ID = %(int)s;""",
        {'int': ids[randint(0,
                            len(ids) - 1)]})
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times.append(aux)
labels.append("JSONB 'nonbold'")

# Accessing 'nonbold' from a JSON
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute(
        """EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT INTERVIEW->'nonbold' FROM JSONTEST WHERE ID = %(int)s;""",
        {'int': ids[randint(0,
                            len(ids) - 1)]})
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times.append(aux)
labels.append("JSON 'nonbold'")

# Accessing 'nonbold' from a TEXT[]
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute(
        """EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT RESPOSTAS FROM TEXTARRTEST WHERE ID = %(int)s;""",
        {'int': ids[randint(0,
                            len(ids) - 1)]})
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times.append(aux)
labels.append("TEXT[] 'nonbold'")

# %%
# Accessing entire table JSONB
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute("""EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT * FROM JSONBTEST;""")
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[2][0])[0]))
times.append(aux)
labels.append("JSONB *")

# Accessing entire table JSON
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute("""EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT * FROM JSONTEST;""")
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[2][0])[0]))
times.append(aux)
labels.append("JSON *")

# Accessing entire table TEXT[]
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute("""EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT * FROM TEXTARRTEST;""")
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[2][0])[0]))
times.append(aux)
labels.append("TEXT[] *")

# %%
print('Average access times (ms): ')
for i in range(len(times)):
    print(labels[i], '%.5f' % (sum(times[i]) / N), sep='\t\t')

# %%
# Graph comparison

sns.set()
plt.figure(figsize=(16, 9))
sns.boxplot(x=times[0:3], y=labels[0:3])
plt.xlim(0, 0.2)
plt.title(
    "Comparação de desempenho para queries em dados JSON, JSONB e TEXT[]")
plt.ylabel("Consulta")
plt.xlabel("Tempo de execução (ms)")
plt.plot()

sns.set()
plt.figure(figsize=(16, 9))
sns.boxplot(x=times[3:6], y=labels[3:6])
plt.xlim(0, 0.2)
plt.title(
    "Comparação de desempenho para queries em dados JSON, JSONB e TEXT[]")
plt.ylabel("Consulta")
plt.xlabel("Tempo de execução (ms)")
plt.plot()

sns.set()
plt.figure(figsize=(16, 9))
sns.boxplot(x=times[6:9], y=labels[6:9])
plt.xlim(0, 0.2)
plt.title(
    "Comparação de desempenho para queries em dados JSON, JSONB e TEXT[]")
plt.ylabel("Consulta")
plt.xlabel("Tempo de execução (ms)")
plt.plot()

sns.set()
plt.figure(figsize=(16, 9))
sns.boxplot(x=times[9:12], y=labels[9:12])
plt.xlim(0, 0.2)
plt.title(
    "Comparação de desempenho para queries em dados JSON, JSONB e TEXT[]")
plt.ylabel("Consulta")
plt.xlabel("Tempo de execução (ms)")
plt.plot()

sns.set()
plt.figure(figsize=(16, 9))
sns.boxplot(x=times[12:15], y=labels[12:15])
plt.xlim(0, 0.2)
plt.title(
    "Comparação de desempenho para queries em dados JSON, JSONB e TEXT[]")
plt.ylabel("Consulta")
plt.xlabel("Tempo de execução (ms)")
plt.plot()

sns.set()
plt.figure(figsize=(16, 9))
sns.boxplot(x=times[15:18], y=labels[15:18])
plt.xlim(0, 0.2)
plt.title(
    "Comparação de desempenho para queries em dados JSON, JSONB e TEXT[]")
plt.ylabel("Consulta")
plt.xlabel("Tempo de execução (ms)")
plt.plot()

# %% [markdown]
# ## Testes de desempenho para busca por termos
#
# Para exemplificar, as consultas a seguir retornam todas as tuplas cujo
# a *string* "Londrina" é existente nos elementos *text*, *bold* e *nonbold*.
# Neste caso, todas as tuplas das tabelas de testes são retornadas após a
# verificação.

# %%
# Preparing for N queries
times2 = []
labels2 = []

N = 1000

# %%
# TERM SEARCH 'text' JSONB
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute("""EXPLAIN (ANALYZE TRUE, TIMING FALSE)
                    SELECT ID FROM JSONBTEST JBT
                        WHERE INTERVIEW->>'text' LIKE '%Londrina%';""")
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times2.append(aux)
labels2.append("JSONB 'text' TERM SEARCH")

# TERM SEARCH 'text' JSON
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute("""EXPLAIN (ANALYZE TRUE, TIMING FALSE)
                    SELECT ID FROM JSONTEST JT
                        WHERE INTERVIEW->>'text' LIKE '%Londrina%';""")
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times2.append(aux)
labels2.append("JSON 'text' TERM SEARCH")

# TERM SEARCH 'text' TEXTARRTEST
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute("""EXPLAIN (ANALYZE TRUE, TIMING FALSE)
                    SELECT ID FROM TEXTARRTEST
                        WHERE TEXTO LIKE '%Londrina%';""")
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times2.append(aux)
labels2.append("TEXT[] 'text' TERM SEARCH")

# %%
# TERM SEARCH 'bold' JSONB
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute("""EXPLAIN (ANALYZE TRUE, TIMING FALSE)
                    SELECT ID FROM JSONBTEST JBT
                        WHERE INTERVIEW->>'bold' LIKE '%Londrina%';""")
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times2.append(aux)
labels2.append("JSONB 'bold' TERM SEARCH")

# TERM SEARCH 'bold' JSON
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute("""EXPLAIN (ANALYZE TRUE, TIMING FALSE)
                    SELECT ID FROM JSONTEST JT
                        WHERE INTERVIEW->>'bold' LIKE '%Londrina%';""")
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times2.append(aux)
labels2.append("JSON 'bold' TERM SEARCH")

# TERM SEARCH 'bold' TEXTARRTEST
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute("""EXPLAIN (ANALYZE TRUE, TIMING FALSE)
                    SELECT ID FROM TEXTARRTEST
                        WHERE array_to_string(PERGUNTAS, '|')
                            LIKE '%Londrina%';""")
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times2.append(aux)
labels2.append("TEXT[] 'bold' TERM SEARCH")

# %%
# TERM SEARCH 'nonbold' JSONB
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute("""EXPLAIN (ANALYZE TRUE, TIMING FALSE)
                    SELECT ID FROM JSONBTEST JBT
                        WHERE INTERVIEW->>'nonbold' LIKE '%Londrina%';""")
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times2.append(aux)
labels2.append("JSONB 'nonbold' TERM SEARCH")

# TERM SEARCH 'nonbold' JSON
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute("""EXPLAIN (ANALYZE TRUE, TIMING FALSE)
                    SELECT ID FROM JSONTEST JT
                        WHERE INTERVIEW->>'nonbold' LIKE '%Londrina%';""")
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times2.append(aux)
labels2.append("JSON 'nonbold' TERM SEARCH")

# TERM SEARCH 'nonbold' TEXTARRTEST
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute("""EXPLAIN (ANALYZE TRUE, TIMING FALSE)
                    SELECT ID FROM TEXTARRTEST
                        WHERE array_to_string(RESPOSTAS, '|')
                            LIKE '%Londrina%';""")
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times2.append(aux)
labels2.append("TEXT[] 'nonbold' TERM SEARCH")

# %%
print('Average access times (ms): ')
for i in range(len(times2)):
    print(labels2[i], '%.5f' % (sum(times2[i]) / N), sep='\t\t')

# %%
# Graph comparison

sns.set()
plt.figure(figsize=(16, 9))
sns.boxplot(x=times2[0:3], y=labels2[0:3])
plt.xlim(0, 0.2)
plt.title(
    "Comparação de desempenho para queries em dados JSON, JSONB e TEXT[], \
    com buscas por termos")
plt.ylabel("Consulta")
plt.xlabel("Tempo de execução (ms)")
plt.plot()
sns.set()

plt.figure(figsize=(16, 9))
sns.boxplot(x=times2[3:6], y=labels2[3:6])
plt.xlim(0, 0.2)
plt.title(
    "Comparação de desempenho para queries em dados JSON, JSONB e TEXT[], \
    com buscas por termos")
plt.ylabel("Consulta")
plt.xlabel("Tempo de execução (ms)")
plt.plot()

plt.figure(figsize=(16, 9))
sns.boxplot(x=times2[6:9], y=labels2[6:9])
plt.xlim(0, 0.2)
plt.title(
    "Comparação de desempenho para queries em dados JSON, JSONB e TEXT[], \
    com buscas por termos")
plt.ylabel("Consulta")
plt.xlabel("Tempo de execução (ms)")
plt.plot()

# %% [markdown]
# ## Testes de desempenho para busca por termos, utilizando recursos de
# Full Text Search
# Utilizaremos as funções de full text search do PostgreSQL 9.6, comparando o
# desempenho e qualidade destas buscas com os resultados anteriores.

# %%
# Preparing for N queries
times2 = []
labels2 = []

N = 1000

# %%
# Example of document pre-processing
cur = conn.cursor()
cur.execute(
    """SELECT ID, to_tsvector('portuguese', TEXTO) FROM TEXTARRTEST;""")
print(cur.fetchone()[1], sep='\n')

# %%
# Example result of ts_headline function
cur = conn.cursor()
cur.execute(
    """SELECT ID, ts_rank(to_tsvector('portuguese', TEXTO),
            phraseto_tsquery('portuguese', %(query)s), 32|16|1) AS RANK,
            ts_headline('portuguese', TEXTO,
            plainto_tsquery('portuguese', %(query)s)) AS HEADLINE
        FROM TEXTARRTEST ORDER BY RANK DESC;""",
    {'query': 'Nasci em Londrina'})
print(*cur.fetchall(), sep='\n')

# %%
# TERM SEARCH 'text' JSONB
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute("""EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT ID FROM JSONBTEST JBT
                    WHERE to_tsvector('portuguese', INTERVIEW->>'text')
                        @@ phraseto_tsquery('portuguese', 'Londrina');""")
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times2.append(aux)
labels2.append("JSONB 'text' ts TERM SEARCH")

# TERM SEARCH 'text' JSON
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute("""EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT ID FROM JSONTEST JT
                    WHERE to_tsvector('portuguese', INTERVIEW->>'text')
                        @@ phraseto_tsquery('portuguese', 'Londrina');""")
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times2.append(aux)
labels2.append("JSON 'text' ts TERM SEARCH")

# TERM SEARCH 'text' TEXTARRTEST
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute("""EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT ID FROM TEXTARRTEST
                    WHERE to_tsvector('portuguese', TEXTO)
                        @@ phraseto_tsquery('portuguese', 'Londrina');""")
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times2.append(aux)
labels2.append("TEXT[] 'text' ts TERM SEARCH")

# %%
# TERM SEARCH 'bold' JSONB
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute("""EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT ID FROM JSONBTEST JBT
                    WHERE to_tsvector('portuguese', INTERVIEW->>'bold')
                        @@ phraseto_tsquery('portuguese', 'Londrina');""")
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times2.append(aux)
labels2.append("JSONB 'bold' ts TERM SEARCH")

# TERM SEARCH 'bold' JSON
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute("""EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT ID FROM JSONTEST JT
                    WHERE to_tsvector('portuguese', INTERVIEW->>'bold')
                        @@ phraseto_tsquery('portuguese', 'Londrina');""")
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times2.append(aux)
labels2.append("JSON 'bold' ts TERM SEARCH")

# TERM SEARCH 'bold' TEXTARRTEST
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute("""EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT ID FROM TEXTARRTEST
                    WHERE to_tsvector('portuguese',
                                        array_to_string(PERGUNTAS, ' | '))
                        @@ phraseto_tsquery('portuguese', 'Londrina');""")
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times2.append(aux)
labels2.append("TEXT[] 'bold' TERM SEARCH")

# %%
# TERM SEARCH 'nonbold' JSONB
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute("""EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT ID FROM JSONBTEST JBT
                    WHERE to_tsvector('portuguese', INTERVIEW->>'nonbold')
                        @@ phraseto_tsquery('portuguese', 'Londrina');""")
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times2.append(aux)
labels2.append("JSONB 'nonbold' TERM SEARCH")

# TERM SEARCH 'nonbold' JSON
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute("""EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT ID FROM JSONTEST JT
                    WHERE to_tsvector('portuguese',
                                        INTERVIEW->>'nonbold')
                        @@ phraseto_tsquery('portuguese', 'Londrina');""")
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times2.append(aux)
labels2.append("JSON 'nonbold' TERM SEARCH")

# TERM SEARCH 'nonbold' TEXTARRTEST
cur = conn.cursor()
aux = []
for i in range(N):
    cur.execute("""EXPLAIN (ANALYZE TRUE, TIMING FALSE)
            SELECT ID FROM TEXTARRTEST
                    WHERE to_tsvector('portuguese',
                                        array_to_string(RESPOSTAS, ' | '))
                        @@ phraseto_tsquery('portuguese', 'Londrina');""")
    aux.append(float(re.findall(r"\d+\.\d+", cur.fetchall()[3][0])[0]))
times2.append(aux)
labels2.append("TEXT[] 'nonbold' ts TERM SEARCH")

# %%
print('Average access times (ms): ')
for i in range(len(times2)):
    print(labels2[i], '%.5f' % (sum(times2[i]) / N), sep='\t\t')

# %%
# Graph comparison

sns.set()
plt.figure(figsize=(16, 9))
sns.boxplot(x=times2[0:3], y=labels2[0:3])
plt.xlim(0, 0.2)
plt.title(
    "Comparação de desempenho para queries em dados JSON, JSONB e TEXT[], \
    com buscas por termos")
plt.ylabel("Consulta")
plt.xlabel("Tempo de execução (ms)")
plt.plot()
sns.set()

plt.figure(figsize=(16, 9))
sns.boxplot(x=times2[3:6], y=labels2[3:6])
plt.xlim(0, 0.2)
plt.title(
    "Comparação de desempenho para queries em dados JSON, JSONB e TEXT[], \
    com buscas por termos")
plt.ylabel("Consulta")
plt.xlabel("Tempo de execução (ms)")
plt.plot()

plt.figure(figsize=(16, 9))
sns.boxplot(x=times2[6:9], y=labels2[6:9])
plt.xlim(0, 0.2)
plt.title(
    "Comparação de desempenho para queries em dados JSON, JSONB e TEXT[], \
    com buscas por termos")
plt.ylabel("Consulta")
plt.xlabel("Tempo de execução (ms)")
plt.plot()
