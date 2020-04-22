"""TODO: Extend documentation."""
import argparse
# import json
# import os
# import re

# import docx2json
import getpass
# import nltk.tokenize
# import nltk.corpus
# import nltk.tag
# import nltk.chunk
# import nltk.stem
import psycopg2

import config


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
        description='Python script to import new interviews to GEO database.',
        epilog='Report bugs to <https://github.com/andremsouza/ic-geo>')
    parser.add_argument('filepath',
                        nargs='+',
                        type=str,
                        help='Path to file for insertion',
                        metavar='FILEPATH')
    parser.add_argument('-H',
                        '--host',
                        action='store',
                        default=config.HOSTNAME,
                        type=str,
                        required=False,
                        help='database server host or socket directory' +
                        '(default=config.HOSTNAME)',
                        metavar='HOSTNAME',
                        dest='host')
    parser.add_argument('-p',
                        '--port',
                        action='store',
                        default=config.PORT,
                        type=str,
                        required=False,
                        help='database server port' + '(default=config.PORT)',
                        metavar='PORT',
                        dest='port')
    parser.add_argument('-d',
                        '--dbname',
                        action='store',
                        default=config.DBNAME,
                        type=str,
                        required=False,
                        help='database name to connect to' +
                        '(default=config.DBNAME)',
                        metavar='DBNAME',
                        dest='dbname')
    parser.add_argument('-u',
                        '--username',
                        action='store',
                        default=config.USERNAME,
                        type=str,
                        required=False,
                        help='database user name' +
                        '(default=config.USERNAME)',
                        metavar='USERNAME',
                        dest='username')
    parser.add_argument('--password',
                        action=PasswordPromptAction,
                        default=config.PASSWORD,
                        type=str,
                        required=False,
                        help='password prompt' + '(default=config.PASSWORD)',
                        metavar='',
                        dest='password')

    return parser


if __name__ == "__main__":
    # Get arguments and connect to database
    parser = generate_argparser()
    args = parser.parse_args()
    print(args.filepath)
    conn = psycopg2.connect(host=args.host,
                            port=args.port,
                            dbname=args.dbname,
                            user=args.username,
                            password=args.password)
    # delete sensitive data
    del args.password

    # TODO: List files to pass as function arguments
    # TODO: Add support for directories

    # Get directory/file names

    # close connection
    conn.close()