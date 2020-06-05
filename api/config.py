from passlib.context import CryptContext

MIN_CONNECTIONS = 1
MAX_CONNECTIONS = 100
HOSTNAME = 'localhost'
PORT = 32768
DBNAME = 'geo'
USERNAME = 'api'
PASSWORD = 'api'
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
