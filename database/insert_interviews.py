"""Script to insert interviews to GEO database. Use "-h" for more help."""
import argparse
import json

import docx2json
import getpass
import psycopg2

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
        description='Python script to import new interviews to GEO database ' +
        'from .docx files.',
        epilog='Report bugs to <https://github.com/andremsouza/ic-geo>')
    parser.add_argument('id',
                        type=int,
                        help='id for interview. ' +
                        'Must be a positive integer.',
                        metavar='ID')
    parser.add_argument('filepath',
                        type=str,
                        help='path to file for insertion. ' +
                        'May be an absolute or relative path.',
                        metavar='FILEPATH')
    parser.add_argument('-t',
                        '--type',
                        action='store',
                        default='docx',
                        type=str,
                        choices=['docx', 'json'],
                        required=False,
                        help='type of file for input. ' +
                        'May be either "docx" or "json" ' + '(default="docx")',
                        metavar='FILETYPE',
                        dest='filetype')
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

    return parser


if __name__ == "__main__":
    # Get arguments and connect to database
    parser = generate_argparser()
    args = parser.parse_args()
    conn = psycopg2.connect(host=args.hostname,
                            port=args.port,
                            dbname=args.dbname,
                            user=args.username,
                            password=args.password)
    # Delete sensitive data
    del args.password

    # Convert .docx to .json, if needed
    if (args.filetype == 'docx'):
        doc = docx2json.convert(args.filepath)
    else:
        doc = json.load(args.filepath)

    # Call stored procedure to insert interview
    with conn.cursor() as cur:
        cur.execute('CALL interview_insert(%(id)s, %(doc)s);', {
            'id': args.id,
            'doc': doc
        })
        cur.close()

    # Commit and close database connection
    conn.commit()
    conn.close()
