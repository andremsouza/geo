"""Flask application for connection to GEO database. Use -h for more help."""
import argparse
import re

import flask
import flask_httpauth
import flask_restful
import getpass
import nltk
import psycopg2
import psycopg2.errors
import psycopg2.pool
import werkzeug.routing

try:
    import config  # Try to import attributes from config.py
except Exception as e:  # If no config.py, define Object with empty attributes
    print('Warning: No config.py found. ' +
          'Using empty values for non-provided connection attributes. ' +
          str(e))
    import passlib  # for default pwd_context

    class Object(object):
        """Dummy class for config attributes."""
        pass

    config = Object()
    config.MIN_CONNECTIONS = -1
    config.MAX_CONNECTIONS = -1
    config.HOSTNAME = ''
    config.PORT = -1
    config.DBNAME = ''
    config.USERNAME = ''
    config.PASSWORD = ''
    config.pwd_context = passlib.context.CryptContext(
        schemes=["pbkdf2_sha256"], deprecated="auto")


class PasswordPromptAction(argparse.Action):
    """Custom class for argparse.Action for password prompt with getpass."""
    def __init__(self,
                 option_strings,
                 dest=None,
                 nargs=0,
                 default=None,
                 required=False,
                 type=None,
                 metavar=None,
                 help=None):
        super(PasswordPromptAction,
              self).__init__(option_strings=option_strings,
                             dest=dest,
                             nargs=nargs,
                             default=default,
                             required=required,
                             metavar=metavar,
                             type=type,
                             help=help)

    def __call__(self, parser, args, values, option_string=None):
        password = getpass.getpass()
        setattr(args, self.dest, password)


def generate_argparser():
    """Return ArgumentParser object for database connection."""
    parser = argparse.ArgumentParser(
        description='Flask application for connection to GEO database.',
        epilog='Report bugs to <https://github.com/andremsouza/ic-geo>')
    parser.add_argument('-H',
                        '--host',
                        action='store',
                        default=config.HOSTNAME,
                        type=str,
                        required=False,
                        help='database server host or socket directory ' +
                        '(default=config.HOSTNAME)',
                        metavar='HOSTNAME',
                        dest='hostname')
    parser.add_argument('-p',
                        '--port',
                        action='store',
                        default=config.PORT,
                        type=int,
                        required=False,
                        help='database server port ' + '(default=config.PORT)',
                        metavar='PORT',
                        dest='port')
    parser.add_argument('-d',
                        '--dbname',
                        action='store',
                        default=config.DBNAME,
                        type=str,
                        required=False,
                        help='database name to connect to ' +
                        '(default=config.DBNAME)',
                        metavar='DBNAME',
                        dest='dbname')
    parser.add_argument('-u',
                        '--username',
                        action='store',
                        default=config.USERNAME,
                        type=str,
                        required=False,
                        help='database user name ' +
                        '(default=config.USERNAME)',
                        metavar='USERNAME',
                        dest='username')
    parser.add_argument('--password',
                        action=PasswordPromptAction,
                        default=config.PASSWORD,
                        type=str,
                        required=False,
                        help='password prompt ' + '(default=config.PASSWORD)',
                        metavar='',
                        dest='password')
    parser.add_argument('--min-connections',
                        action='store',
                        default=config.MIN_CONNECTIONS,
                        type=int,
                        required=False,
                        help='minimum number of connections in pool' +
                        '(default=config.MIN_CONNECTIONS)',
                        metavar='MIN-CONNECTIONS',
                        dest='min_connections')
    parser.add_argument('--max-connections',
                        action='store',
                        default=config.MAX_CONNECTIONS,
                        type=int,
                        required=False,
                        help='maximum number of connections in pool' +
                        '(default=config.MAX_CONNECTIONS)',
                        metavar='MAX-CONNECTIONS',
                        dest='max_connections')
    parser.add_argument("--debug",
                        action="store_true",
                        help="Activate debug mode for Flask")
    return parser


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
        """Override for conversion of string to python variable (list of ints).

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


# Main script #1
if __name__ == "__main__":
    # Parse command line arguments
    parser = generate_argparser()
    args = parser.parse_args()

    # defining pwd_context from passlib
    pwd_context = config.pwd_context

    # Setting up nltk resources and database connection pool
    nltk.download('stopwords')
    try:
        postgresql_pool = psycopg2.pool.SimpleConnectionPool(
            args.min_connections,
            args.max_connections,
            dbname=args.dbname,
            user=args.username,
            password=args.password,
            host=args.hostname,
            port=args.port)
        if postgresql_pool:
            print("Connection pool created successfully")
    except (Exception, psycopg2.Error) as e:
        print("Error while connecting to database: ", e)
        raise

    # Initializing app and api
    app = flask.Flask(__name__)
    app.url_map.converters['int_list'] = IntListConverter
    api = flask_restful.Api(app)
    auth = flask_httpauth.HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password):
    """Password verification function for user authentication.

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
        return {"message": "Insufficient privileges for this operation."}, 401
    except psycopg2.errors.UniqueViolation:
        return {"message": "Unique Violation. This user already exists."}, 409
    except psycopg2.OperationalError as e:
        return {
            "message": "Unable to connect to database. " + str(e),
        }, 500
    except (Exception, psycopg2.Error) as e:
        return {
            "message": str(e),
        }, 500


class Users(flask_restful.Resource):
    """Users resource for management of the API's users.

    This resource class accepts POST, PUT and DELETE requests to respectively
    create, update password and delete an user from the API. All requests
    to this resource require autentication parameters (in the Authorization
    header) and data provided in the JSON object (such as new_password).
    For POST and DELETE requests, the API will set up a connection the the
    database using the username and password provided in the Authorization
    header. The provided user must have permission for INSERT and DELETE
    operations on the api_users table.
    For PUT requests, an API user may authenticate and change its own password.
    """
    def post(self):
        """POST requests' handler. Creates a new API user.

        Requires database user/role data in the Authorization header, with
        INSERT permission for the api_users table. The new user's data must be
        given in the JSON object of the request, in the 'new_username' and
        'new_password' keys.
        """
        db_username = flask.request.authorization['username']
        db_password = flask.request.authorization['password']
        new_username = flask.request.json.get('new_username')
        new_password = flask.request.json.get('new_password')
        if None in [db_username, db_password, new_username, new_password]:
            return {
                "message":
                "Required parameters:\n" +
                "json:[new_username, new_password]\n" +
                "authorization:[username, password]\n",
            }, 400
        try:
            conn = psycopg2.connect(dbname=args.dbname,
                                    user=db_username,
                                    password=db_password,
                                    host=args.hostname,
                                    port=args.port)
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
        """PUT requests' handler. Changes an API user's password.

        The API user's username and password must be given in the Authorization
        header. The new password must be given in the JSON object of the
        request, in the 'new_password' key.
        """
        username = flask.request.authorization['username']
        password = flask.request.authorization['password']
        new_password = flask.request.json.get['new_password']
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
            conn.commit()
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
        """DELETE requests' handler. Deletes an API user.

        Requires database user/role data in the Authorization header, with
        DELETE permission for the api_users table. The user's data must be
        given in the JSON object of the request, in the 'username' key.
        """
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
            conn = psycopg2.connect(dbname=args.dbname,
                                    user=db_username,
                                    password=db_password,
                                    host=args.hostname,
                                    port=args.port)
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
    """Resource class for access to all data from the interviews.

    This resource class accepst GET requests. All requests to this resource
    require user authentication parameters (in the Authorization header).
    The response data is JSON formatted.
    """
    decorators = [auth.login_required]

    def get(self):
        try:
            conn = postgresql_pool.getconn()
            data = {}
            with conn.cursor() as cur:
                cur.execute("""SELECT id, text, questions, answers, meta
                        FROM interviews
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
    """Resource class for access to all interviews' text.

    This resource class accepst GET requests. All requests to this resource
    require user authentication parameters (in the Authorization header).
    The response data is JSON formatted.
    """
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
    """Resource class for access to all interviews' questions.

    This resource class accepst GET requests. All requests to this resource
    require user authentication parameters (in the Authorization header).
    The response data is JSON formatted.
    """
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
    """Resource class for access to all interviews' answers.

    This resource class accepst GET requests. All requests to this resource
    require user authentication parameters (in the Authorization header).
    The response data is JSON formatted.
    """
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
    """Resource class for access to all interviews' metadata.

    This resource class accepst GET requests. All requests to this resource
    require user authentication parameters (in the Authorization header).
    The response data is JSON formatted.
    """
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
    """Resource class for access to all data of a list of interviews.

    This resource class accepst GET requests. All requests to this resource
    require user authentication parameters (in the Authorization header).
    The response data is JSON formatted.
    The list of interviews should be a list of integers.
    """
    decorators = [auth.login_required]

    def get(self, ids):
        try:
            conn = postgresql_pool.getconn()
            data = {}
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, text, questions, answers, meta
                        FROM interviews
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
    """Resource class for access to the text of a list of interviews.

    This resource class accepst GET requests. All requests to this resource
    require user authentication parameters (in the Authorization header).
    The response data is JSON formatted.
    The list of interviews should be a list of integers.
    """
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
    """Resource class for access to the questions of a list of interviews.

    This resource class accepst GET requests. All requests to this resource
    require user authentication parameters (in the Authorization header).
    The response data is JSON formatted.
    The list of interviews should be a list of integers.
    """
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
    """Resource class for access to the answers of a list of interviews.

    This resource class accepst GET requests. All requests to this resource
    require user authentication parameters (in the Authorization header).
    The response data is JSON formatted.
    The list of interviews should be a list of integers.
    """
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
    """Resource class for access to the metadata of a list of interviews.

    This resource class accepst GET requests. All requests to this resource
    require user authentication parameters (in the Authorization header).
    The response data is JSON formatted.
    The list of interviews should be a list of integers.
    """
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
    """Resource class for access to interview data, searching by a string.

    This resource class accepst GET requests. All requests to this resource
    require user authentication parameters (in the Authorization header).
    The response data is JSON formatted.
    """
    decorators = [auth.login_required]

    def get(self, search_string):
        try:
            conn = postgresql_pool.getconn()
            data = {}
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, text, questions, answers, meta
                        FROM interviews
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
    """Resource class for access to interview text, searching by a string.

    This resource class accepst GET requests. All requests to this resource
    require user authentication parameters (in the Authorization header).
    The response data is JSON formatted.
    """
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
    """Resource class for access to interview questions, searching by a string.

    This resource class accepst GET requests. All requests to this resource
    require user authentication parameters (in the Authorization header).
    The response data is JSON formatted.
    """
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
    """Resource class for access to interview answers, searching by a string.

    This resource class accepst GET requests. All requests to this resource
    require user authentication parameters (in the Authorization header).
    The response data is JSON formatted.
    """
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
    """Resource class for access to interview metadata, searching by a string.

    This resource class accepst GET requests. All requests to this resource
    require user authentication parameters (in the Authorization header).
    The response data is JSON formatted.
    """
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


# Main script #2
if __name__ == "__main__":
    # Adding resources to api
    api.add_resource(Users, '/users')
    api.add_resource(InterviewAll, '/interviews/all')
    api.add_resource(InterviewAllText, '/interviews/all/text')
    api.add_resource(InterviewAllQuestions, '/interviews/all/questions')
    api.add_resource(InterviewAllAnswers, '/interviews/all/answers')
    api.add_resource(InterviewAllMeta, '/interviews/all/meta')
    api.add_resource(InterviewAny, '/interviews/<int_list:ids>')
    api.add_resource(InterviewAnyText, '/interviews/<int_list:ids>/text')
    api.add_resource(InterviewAnyQuestions,
                     '/interviews/<int_list:ids>/questions')
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
    # TODO: configure ssl_context for secure (https) connections
    app.run(debug=args.debug, ssl_context='adhoc')
