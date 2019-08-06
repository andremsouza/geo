from passlib.context import CryptContext

MIN_CONNECTIONS = 1
MAX_CONNECTIONS = 100
HOST = 'localhost'
PORT = 5432
DBNAME = 'icgeo'
USER = 'miner'
PASSWORD = 'minerpass'

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
