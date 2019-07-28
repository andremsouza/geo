import flask
import flask_restful
import psycopg2
import config
import nltk
nltk.download('stopwords')


def dbconnect():
    return psycopg2.connect(host=config.HOST,
                            dbname=config.DBNAME,
                            user=config.USER,
                            password=config.PASSWORD)


class InterviewAll(flask_restful.Resource):
    def get(self):
        try:
            conn = dbconnect()
            data = {}
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, text, questions, answers FROM interviews
                        ORDER BY id;""")
                data['row_count'] = cur.rowcount
                data['column_names'] = [desc[0] for desc in cur.description]
                data['rows'] = cur.fetchall()
                cur.close()
            conn.close()
        except Exception:
            flask.abort(500)
        except psycopg2.Error:
            flask.abort(500)
        return data


class InterviewAllText(flask_restful.Resource):
    def get(self):
        try:
            conn = dbconnect()
            with conn.cursor() as cur:
                data = {}
                cur.execute("""SELECT id, text FROM interviews
                        ORDER BY id;""")
                data['row_count'] = cur.rowcount
                data['column_names'] = [desc[0] for desc in cur.description]
                data['rows'] = cur.fetchall()
                cur.close()
            conn.close()
        except Exception:
            flask.abort(500)
        except psycopg2.Error:
            flask.abort(500)
        return data


class InterviewAllQuestions(flask_restful.Resource):
    def get(self):
        try:
            conn = dbconnect()
            data = {}
            with conn.cursor() as cur:
                cur.execute("""SELECT id, questions FROM interviews
                        ORDER BY id;""")
                data['row_count'] = cur.rowcount
                data['column_names'] = [desc[0] for desc in cur.description]
                data['rows'] = cur.fetchall()
                cur.close()
            conn.close()
        except Exception:
            flask.abort(500)
        except psycopg2.Error:
            flask.abort(500)
        return data


class InterviewAllAnswers(flask_restful.Resource):
    def get(self):
        try:
            conn = dbconnect()
            data = {}
            with conn.cursor() as cur:
                cur.execute("""SELECT id, answers FROM interviews
                    ORDER BY id;""")
                data['row_count'] = cur.rowcount
                data['column_names'] = [desc[0] for desc in cur.description]
                data['rows'] = cur.fetchall()
                cur.close()
            conn.close()
        except Exception:
            flask.abort(500)
        except psycopg2.Error:
            flask.abort(500)
        return data


class InterviewAllMeta(flask_restful.Resource):
    def get(self):
        try:
            conn = dbconnect()
            data = {}
            with conn.cursor() as cur:
                cur.execute("""SELECT id, meta FROM interviews
                    ORDER BY id;""")
                data['row_count'] = cur.rowcount
                data['column_names'] = [desc[0] for desc in cur.description]
                data['rows'] = cur.fetchall()
                data['stemmer'] = 'RSLP Stemmer'
                data['stopwords'] = nltk.corpus.stopwords.words('portuguese')
                cur.close()
            conn.close()
        except Exception:
            flask.abort(500)
        except psycopg2.Error:
            flask.abort(500)
        return data


class InterviewAny(flask_restful.Resource):
    def get(self, ids):
        try:
            conn = dbconnect()
            data = {}
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, text, questions, answers FROM interviews
                        WHERE id IN %(id_list)s
                        ORDER BY id;""", {"id_list": tuple(ids)})
                data['search_ids_count'] = len(ids)
                data['search_ids'] = ids
                data['row_count'] = cur.rowcount
                data['column_names'] = [desc[0] for desc in cur.description]
                data['rows'] = cur.fetchall()
                cur.close()
            conn.close()
        except Exception:
            flask.abort(500)
        except psycopg2.Error:
            flask.abort(500)
        return data


class InterviewAnyText(flask_restful.Resource):
    def get(self, ids):
        try:
            conn = dbconnect()
            data = {}
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, text FROM interviews
                    WHERE id IN %(id_list)s
                    ORDER BY id;""", {"id_list": tuple(ids)})
                data['search_ids_count'] = len(ids)
                data['search_ids'] = ids
                data['row_count'] = cur.rowcount
                data['column_names'] = [desc[0] for desc in cur.description]
                data['rows'] = cur.fetchall()
                cur.close()
            conn.close()
        except Exception:
            flask.abort(500)
        except psycopg2.Error:
            flask.abort(500)
        return data


class InterviewAnyQuestions(flask_restful.Resource):
    def get(self, ids):
        try:
            conn = dbconnect()
            data = {}
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, questions FROM interviews
                    WHERE id IN %(id_list)s
                    ORDER BY id;""", {"id_list": tuple(ids)})
                data['search_ids_count'] = len(ids)
                data['search_ids'] = ids
                data['row_count'] = cur.rowcount
                data['column_names'] = [desc[0] for desc in cur.description]
                data['rows'] = cur.fetchall()
                cur.close()
            conn.close()
        except Exception:
            flask.abort(500)
        except psycopg2.Error:
            flask.abort(500)
        return data


class InterviewAnyAnswers(flask_restful.Resource):
    def get(self, ids):
        try:
            conn = dbconnect()
            data = {}
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, answers FROM interviews
                    WHERE id IN %(id_list)s
                    ORDER BY id;""", {"id_list": tuple(ids)})
                data['search_ids_count'] = len(ids)
                data['search_ids'] = ids
                data['row_count'] = cur.rowcount
                data['column_names'] = [desc[0] for desc in cur.description]
                data['rows'] = cur.fetchall()
                cur.close()
            conn.close()
        except Exception:
            flask.abort(500)
        except psycopg2.Error:
            flask.abort(500)
        return data


class InterviewAnyMeta(flask_restful.Resource):
    def get(self, ids):
        try:
            conn = dbconnect()
            data = {}
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, meta FROM interviews
                    WHERE id IN %(id_list)s
                    ORDER BY id;""", {"id_list": tuple(ids)})
                data['search_ids_count'] = len(ids)
                data['search_ids'] = ids
                data['row_count'] = cur.rowcount
                data['column_names'] = [desc[0] for desc in cur.description]
                data['rows'] = cur.fetchall()
                data['stemmer'] = 'RSLP Stemmer'
                data['stopwords'] = nltk.corpus.stopwords.words('portuguese')
                cur.close()
            conn.close()
        except Exception:
            flask.abort(500)
        except psycopg2.Error:
            flask.abort(500)
        return data


class InterviewSearch(flask_restful.Resource):
    def get(self, search_string):
        try:
            conn = dbconnect()
            data = {}
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, text, questions, answers FROM interviews
                        WHERE tstext @@
                            phraseto_tsquery('portuguese', %(search_string)s)
                        ORDER BY id;""", {"search_string": search_string})
                data['search_string'] = search_string
                data['row_count'] = cur.rowcount
                data['column_names'] = [desc[0] for desc in cur.description]
                data['rows'] = cur.fetchall()
                cur.close()
            conn.close()
        except Exception:
            flask.abort(500)
        except psycopg2.Error:
            flask.abort(500)
        return data


class InterviewSearchText(flask_restful.Resource):
    def get(self, search_string):
        try:
            conn = dbconnect()
            data = {}
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, text FROM interviews
                        WHERE tstext @@
                            phraseto_tsquery('portuguese', %(search_string)s)
                        ORDER BY id;""", {"search_string": search_string})
                data['search_string'] = search_string
                data['row_count'] = cur.rowcount
                data['column_names'] = [desc[0] for desc in cur.description]
                data['rows'] = cur.fetchall()
                cur.close()
            conn.close()
        except Exception:
            flask.abort(500)
        except psycopg2.Error:
            flask.abort(500)
        return data


class InterviewSearchQuestions(flask_restful.Resource):
    def get(self, search_string):
        try:
            conn = dbconnect()
            data = {}
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, questions FROM interviews
                        WHERE tstext @@
                            phraseto_tsquery('portuguese', %(search_string)s)
                        ORDER BY id;""", {"search_string": search_string})
                data['search_string'] = search_string
                data['row_count'] = cur.rowcount
                data['column_names'] = [desc[0] for desc in cur.description]
                data['rows'] = cur.fetchall()
                cur.close()
            conn.close()
        except Exception:
            flask.abort(500)
        except psycopg2.Error:
            flask.abort(500)
        return data


class InterviewSearchAnswers(flask_restful.Resource):
    def get(self, search_string):
        try:
            conn = dbconnect()
            data = {}
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, answers FROM interviews
                        WHERE tstext @@
                            phraseto_tsquery('portuguese', %(search_string)s)
                        ORDER BY id;""", {"search_string": search_string})
                data['search_string'] = search_string
                data['row_count'] = cur.rowcount
                data['column_names'] = [desc[0] for desc in cur.description]
                data['rows'] = cur.fetchall()
                cur.close()
            conn.close()
        except Exception:
            flask.abort(500)
        except psycopg2.Error:
            flask.abort(500)
        return data


class InterviewSearchMeta(flask_restful.Resource):
    def get(self, search_string):
        try:
            conn = dbconnect()
            data = {}
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, meta FROM interviews
                        WHERE tstext @@
                            phraseto_tsquery('portuguese', %(search_string)s)
                        ORDER BY id;""", {"search_string": search_string})
                data['search_string'] = search_string
                data['row_count'] = cur.rowcount
                data['column_names'] = [desc[0] for desc in cur.description]
                data['rows'] = cur.fetchall()
                data['stemmer'] = 'RSLP Stemmer'
                data['stopwords'] = nltk.corpus.stopwords.words('portuguese')
                cur.close()
            conn.close()
        except Exception:
            flask.abort(500)
        except psycopg2.Error:
            flask.abort(500)
        return data
