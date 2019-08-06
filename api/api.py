import flask
import flask_restful
import flask_httpauth
import psycopg2
import psycopg2.pool
import psycopg2.errors
import werkzeug.routing
import nltk
import config

# Setting up nltk resources and database connection
nltk.download('stopwords')
try:
    postgresql_pool = psycopg2.pool.SimpleConnectionPool(
        config.MIN_CONNECTIONS,
        config.MAX_CONNECTIONS,
        dbname=config.DBNAME,
        user=config.USER,
        password=config.PASSWORD,
        host=config.HOST,
        port=config.PORT)
    if postgresql_pool:
        print("Connection pool created successfully")
except (Exception, psycopg2.Error) as e:
    print("Error while connecting to database: ", e)
    exit(-1)

# Defining int_list for batch GET requests


class IntListConverter(werkzeug.routing.BaseConverter):
    regex = r'\d+(?:,\d+)*'

    def to_python(self, value):
        return [int(i) for i in value.split(',')]

    def to_url(self, value):
        return ','.join(str(i) for i in value)


# Initializing app and api

app = flask.Flask(__name__)
app.url_map.converters['int_list'] = IntListConverter
api = flask_restful.Api(app)
auth = flask_httpauth.HTTPBasicAuth()

# Defining authentication functions


@auth.verify_password
def verify_password(username, password):
    try:
        conn = postgresql_pool.getconn()
        with conn.cursor() as cur:
            cur.execute(
                """SELECT username, password FROM api_users
                    WHERE username = %(username)s;""", {"username": username})
            user = cur.fetchone()
            if (not user or not config.pwd_context.verify(password, user[1])):
                return False
            flask.g.user = user
            cur.close()
        postgresql_pool.putconn(conn)
    except (Exception, psycopg2.Error):
        flask_restful.abort(500)
    return True


class Users(flask_restful.Resource):
    def post(self):
        db_username = flask.request.json.get('db_username')
        db_password = flask.request.json.get('db_password')
        new_username = flask.request.json.get('new_username')
        new_password = flask.request.json.get('new_password')
        if None in [db_username, db_password, new_username, new_password]:
            return {
                "message":
                "Required parameters: " +
                "[db_username, db_password, new_username, new_password]",
            }, 400
        try:
            print(db_username, db_password)
            conn = psycopg2.connect(dbname=config.DBNAME,
                                    user=db_username,
                                    password=db_password,
                                    host=config.HOST,
                                    port=config.PORT)
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO api_users
                            VALUES(%(username)s, %(password)s);""", {
                        'username': new_username,
                        'password': config.pwd_context.hash(new_password)
                    })
                cur.close()
            conn.commit()
            conn.close()
        except psycopg2.errors.InsufficientPrivilege:
            return {
                "message": "Insufficient privileges for this operation."
            }, 401
        except psycopg2.errors.UniqueViolation:
            return {
                "message": "Unique Violation. This user already exists."
            }, 409
        except psycopg2.OperationalError as e:
            return {
                "message": "Unable to connect to database. " + str(e),
            }, 500
        except (Exception, psycopg2.Error) as e:
            return {
                "message": str(e),
            }, 500
            flask_restful.abort(500)
        return {'username': new_username}, 201

    @auth.login_required
    def put(self):
        pass

    def delete(self):
        db_username = flask.request.json.get('db_username')
        db_password = flask.request.json.get('db_password')
        username = flask.request.json.get('username')
        if None in [db_username, db_password, username]:
            return {
                "message":
                "Required parameters: " +
                "[db_username, db_password, username]",
            }, 400
            flask_restful.abort(400)
        try:
            conn = psycopg2.connect(dbname=config.DBNAME,
                                    user=db_username,
                                    password=db_password,
                                    host=config.HOST,
                                    port=config.PORT)
            with conn.cursor() as cur:
                cur.execute(
                    """DELETE FROM api_users WHERE username = %(username)s;""",
                    {
                        'username': username,
                    })
                cur.close()
            conn.commit()
            conn.close()
        except psycopg2.errors.InsufficientPrivilege:
            return {
                "message": "Insufficient privileges for this operation."
            }, 401
        except psycopg2.errors.UniqueViolation:
            return {
                "message": "Unique Violation. This user already exists."
            }, 409
        except psycopg2.OperationalError as e:
            return {
                "message": "Unable to connect to database. " + str(e),
            }, 500
        except (Exception, psycopg2.Error) as e:
            return {
                "message": str(e),
            }, 500
            flask_restful.abort(500)
        return {'username': username}, 200


class InterviewAll(flask_restful.Resource):
    decorators = [auth.login_required]

    def get(self):
        try:
            conn = postgresql_pool.getconn()
            data = {}
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, text, questions, answers FROM interviews
                        ORDER BY id;""")
                data['row_count'] = cur.rowcount
                data['column_names'] = [desc[0] for desc in cur.description]
                data['rows'] = cur.fetchall()
                cur.close()
            postgresql_pool.putconn(conn)
        except (Exception, psycopg2.Error) as e:
            return {
                "message": str(e),
            }, 500
            flask_restful.abort(500)
        return data


class InterviewAllText(flask_restful.Resource):
    decorators = [auth.login_required]

    def get(self):
        try:
            conn = postgresql_pool.getconn()
            with conn.cursor() as cur:
                data = {}
                cur.execute("""SELECT id, text FROM interviews
                        ORDER BY id;""")
                data['row_count'] = cur.rowcount
                data['column_names'] = [desc[0] for desc in cur.description]
                data['rows'] = cur.fetchall()
                cur.close()
            postgresql_pool.putconn(conn)
        except (Exception, psycopg2.Error) as e:
            return {
                "message": str(e),
            }, 500
            flask_restful.abort(500)
        return data


class InterviewAllQuestions(flask_restful.Resource):
    decorators = [auth.login_required]

    def get(self):
        try:
            conn = postgresql_pool.getconn()
            data = {}
            with conn.cursor() as cur:
                cur.execute("""SELECT id, questions FROM interviews
                        ORDER BY id;""")
                data['row_count'] = cur.rowcount
                data['column_names'] = [desc[0] for desc in cur.description]
                data['rows'] = cur.fetchall()
                cur.close()
            postgresql_pool.putconn(conn)
        except (Exception, psycopg2.Error) as e:
            return {
                "message": str(e),
            }, 500
            flask_restful.abort(500)
        return data


class InterviewAllAnswers(flask_restful.Resource):
    decorators = [auth.login_required]

    def get(self):
        try:
            conn = postgresql_pool.getconn()
            data = {}
            with conn.cursor() as cur:
                cur.execute("""SELECT id, answers FROM interviews
                    ORDER BY id;""")
                data['row_count'] = cur.rowcount
                data['column_names'] = [desc[0] for desc in cur.description]
                data['rows'] = cur.fetchall()
                cur.close()
            postgresql_pool.putconn(conn)
        except (Exception, psycopg2.Error) as e:
            return {
                "message": str(e),
            }, 500
            flask_restful.abort(500)
        return data


class InterviewAllMeta(flask_restful.Resource):
    decorators = [auth.login_required]

    def get(self):
        try:
            conn = postgresql_pool.getconn()
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
            postgresql_pool.putconn(conn)
        except (Exception, psycopg2.Error) as e:
            return {
                "message": str(e),
            }, 500
            flask_restful.abort(500)
        return data


class InterviewAny(flask_restful.Resource):
    decorators = [auth.login_required]

    def get(self, ids):
        try:
            conn = postgresql_pool.getconn()
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
            postgresql_pool.putconn(conn)
        except (Exception, psycopg2.Error) as e:
            return {
                "message": str(e),
            }, 500
            flask_restful.abort(500)
        return data


class InterviewAnyText(flask_restful.Resource):
    decorators = [auth.login_required]

    def get(self, ids):
        try:
            conn = postgresql_pool.getconn()
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
            postgresql_pool.putconn(conn)
        except (Exception, psycopg2.Error) as e:
            return {
                "message": str(e),
            }, 500
            flask_restful.abort(500)
        return data


class InterviewAnyQuestions(flask_restful.Resource):
    decorators = [auth.login_required]

    def get(self, ids):
        try:
            conn = postgresql_pool.getconn()
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
            postgresql_pool.putconn(conn)
        except (Exception, psycopg2.Error) as e:
            return {
                "message": str(e),
            }, 500
            flask_restful.abort(500)
        return data


class InterviewAnyAnswers(flask_restful.Resource):
    decorators = [auth.login_required]

    def get(self, ids):
        try:
            conn = postgresql_pool.getconn()
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
            postgresql_pool.putconn(conn)
        except (Exception, psycopg2.Error) as e:
            return {
                "message": str(e),
            }, 500
            flask_restful.abort(500)
        return data


class InterviewAnyMeta(flask_restful.Resource):
    decorators = [auth.login_required]

    def get(self, ids):
        try:
            conn = postgresql_pool.getconn()
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
            postgresql_pool.putconn(conn)
        except (Exception, psycopg2.Error) as e:
            return {
                "message": str(e),
            }, 500
            flask_restful.abort(500)
        return data


class InterviewSearch(flask_restful.Resource):
    decorators = [auth.login_required]

    def get(self, search_string):
        try:
            conn = postgresql_pool.getconn()
            data = {}
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, text, questions, answers FROM interviews
                        WHERE tstext @@
                            websearch_to_tsquery('portuguese',
                                                 %(search_string)s)
                        ORDER BY id;""", {"search_string": search_string})
                data['search_string'] = search_string
                data['row_count'] = cur.rowcount
                data['column_names'] = [desc[0] for desc in cur.description]
                data['rows'] = cur.fetchall()
                cur.close()
            postgresql_pool.putconn(conn)
        except (Exception, psycopg2.Error) as e:
            return {
                "message": str(e),
            }, 500
            flask_restful.abort(500)
        return data


class InterviewSearchText(flask_restful.Resource):
    decorators = [auth.login_required]

    def get(self, search_string):
        try:
            conn = postgresql_pool.getconn()
            data = {}
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, text FROM interviews
                        WHERE tstext @@
                            websearch_to_tsquery('portuguese',
                                                 %(search_string)s)
                        ORDER BY id;""", {"search_string": search_string})
                data['search_string'] = search_string
                data['row_count'] = cur.rowcount
                data['column_names'] = [desc[0] for desc in cur.description]
                data['rows'] = cur.fetchall()
                cur.close()
            postgresql_pool.putconn(conn)
        except (Exception, psycopg2.Error) as e:
            return {
                "message": str(e),
            }, 500
            flask_restful.abort(500)
        return data


class InterviewSearchQuestions(flask_restful.Resource):
    decorators = [auth.login_required]

    def get(self, search_string):
        try:
            conn = postgresql_pool.getconn()
            data = {}
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, questions FROM interviews
                        WHERE tstext @@
                            websearch_to_tsquery('portuguese',
                                                 %(search_string)s)
                        ORDER BY id;""", {"search_string": search_string})
                data['search_string'] = search_string
                data['row_count'] = cur.rowcount
                data['column_names'] = [desc[0] for desc in cur.description]
                data['rows'] = cur.fetchall()
                cur.close()
            postgresql_pool.putconn(conn)
        except (Exception, psycopg2.Error) as e:
            return {
                "message": str(e),
            }, 500
            flask_restful.abort(500)
        return data


class InterviewSearchAnswers(flask_restful.Resource):
    decorators = [auth.login_required]

    def get(self, search_string):
        try:
            conn = postgresql_pool.getconn()
            data = {}
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, answers FROM interviews
                        WHERE tstext @@
                            websearch_to_tsquery('portuguese',
                                                 %(search_string)s)
                        ORDER BY id;""", {"search_string": search_string})
                data['search_string'] = search_string
                data['row_count'] = cur.rowcount
                data['column_names'] = [desc[0] for desc in cur.description]
                data['rows'] = cur.fetchall()
                cur.close()
            postgresql_pool.putconn(conn)
        except (Exception, psycopg2.Error) as e:
            return {
                "message": str(e),
            }, 500
            flask_restful.abort(500)
        return data


class InterviewSearchMeta(flask_restful.Resource):
    decorators = [auth.login_required]

    def get(self, search_string):
        try:
            conn = postgresql_pool.getconn()
            data = {}
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, meta FROM interviews
                        WHERE tstext @@
                            websearch_to_tsquery('portuguese',
                                                 %(search_string)s)
                        ORDER BY id;""", {"search_string": search_string})
                data['search_string'] = search_string
                data['row_count'] = cur.rowcount
                data['column_names'] = [desc[0] for desc in cur.description]
                data['rows'] = cur.fetchall()
                data['stemmer'] = 'RSLP Stemmer'
                data['stopwords'] = nltk.corpus.stopwords.words('portuguese')
                cur.close()
            postgresql_pool.putconn(conn)
        except (Exception, psycopg2.Error) as e:
            return {
                "message": str(e),
            }, 500
            flask_restful.abort(500)
        return data


# Adding resources to api
api.add_resource(Users, '/users')
api.add_resource(InterviewAll, '/interviews/all')
api.add_resource(InterviewAllText, '/interviews/all/text')
api.add_resource(InterviewAllQuestions, '/interviews/all/questions')
api.add_resource(InterviewAllAnswers, '/interviews/all/answers')
api.add_resource(InterviewAllMeta, '/interviews/all/meta')
api.add_resource(InterviewAny, '/interviews/<int_list:ids>')
api.add_resource(InterviewAnyText, '/interviews/<int_list:ids>/text')
api.add_resource(InterviewAnyQuestions, '/interviews/<int_list:ids>/questions')
api.add_resource(InterviewAnyAnswers, '/interviews/<int_list:ids>/answers')
api.add_resource(InterviewAnyMeta, '/interviews/<int_list:ids>/meta')
api.add_resource(InterviewSearch, '/interviews/<string:search_string>')
api.add_resource(InterviewSearchText,
                 '/interviews/<string:search_string>/text')
api.add_resource(InterviewSearchQuestions,
                 '/interviews/<string:search_string>/questions')
api.add_resource(InterviewSearchAnswers,
                 '/interviews/<string:search_string>/answers')
api.add_resource(InterviewSearchMeta,
                 '/interviews/<string:search_string>/meta')

# Main script
if __name__ == "__main__":
    app.run(debug=True, ssl_context='adhoc')
