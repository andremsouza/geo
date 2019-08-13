import flask
import flask_restful
import flask_httpauth
import psycopg2
import psycopg2.pool
import psycopg2.errors
import werkzeug.routing
import nltk
import re
import config

# Setting up nltk resources and database connection pool
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
    """Custom converter for parsing of a list of integers in the request URL.

    Utilizes BaseConverter class for routing purposes. The format for the
    int_list converts a string of integers, separated by commas (',').
    Trailing spaces or commas are supported.

    Example:
        str('1, 2, 3 ,4,5 , 6, 11, 20, ') -> list([1, 2, 3, 4, 5, 11, 20])
    """
    # Defining regular expressions for pattern matching
    regex = r'\s*\d+\s*(?:,\s*\d+\s*)*,?\s*'

    def to_python(self, value):
        """Override for conversion of string to python variable (list of ints)

        Converts string matched by regex to a representation in a list of ints
        in python. This method also treats trailing whitespace or commas,
        ignoring null values.
        """
        return [
            int(i.strip()) for i in value.split(',')
            if re.match(r'\d+', i.strip())
        ]

    def to_url(self, value):
        """Override for conversion of the identified list of ints to a string.

        Converts a list of ints to a standardized string representation.
        """
        return ','.join(str(i) for i in value)


# Initializing app and api

app = flask.Flask(__name__)
app.url_map.converters['int_list'] = IntListConverter
api = flask_restful.Api(app)
auth = flask_httpauth.HTTPBasicAuth()

# Defining authentication functions


@auth.verify_password
def verify_password(username, password):
    """Password verification function for user authentication

    Compares given username and password with the data stored in the database,
    using the current pwd_context.
    """
    try:
        conn = postgresql_pool.getconn()
        with conn.cursor() as cur:
            cur.execute(
                """SELECT username, password FROM api_users
                    WHERE username = %(username)s;""", {"username": username})
            user = cur.fetchone()
            cur.close()
        postgresql_pool.putconn(conn)
        if (not user or not config.pwd_context.verify(password, user[1])):
            return False
        flask.g.user = user
        return True
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


class Users(flask_restful.Resource):
    def post(self):
        db_username = flask.request.authorization['username']
        db_password = flask.request.authorization['password']
        new_username = flask.request.json.get('new_username')
        new_password = flask.request.json.get('new_password')
        if None in [db_username, db_password, new_username, new_password]:
            return {
                "message":
                "Required parameters:\n" +
                "json:[new_username, new_password]\n" +
                "authorization:[username, password]",
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
        return {
            'message': 'API user created successfully.',
            'username': new_username
        }, 201

    @auth.login_required
    def put(self):
        username = flask.request.authorization['username']
        password = flask.request.authorization['password']
        new_password = flask.request.json.get['password']
        if None in [username, password, new_password]:
            return {
                "message":
                "Required parameters:\n" + "json:[new_password]\n" +
                "authorization:[username, password]",
            }, 400
        try:
            conn = postgresql_pool.getconn()
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE api_users SET password = %(new_password)s
                    WHERE username = %(username)s;""", {
                        'username': username,
                        'new_password': config.pwd_context.hash(new_password),
                    })
                cur.close()
            postgresql_pool.putconn(conn)
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
        return {
            'message': 'Password changed successfully.',
            'username': username,
        }, 200

    def delete(self):
        db_username = flask.request.authorization['username']
        db_password = flask.request.authorization['password']
        username = flask.request.json.get('username')
        if None in [db_username, db_password, username]:
            return {
                "message":
                "Required parameters:\n" + "json:[username]\n" +
                "authorization:[username, password]",
            }, 400
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
        return {'username': username}, 200


class InterviewAll(flask_restful.Resource):
    decorators = [auth.login_required]

    def get(self):
        print(flask.request.authorization)
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
