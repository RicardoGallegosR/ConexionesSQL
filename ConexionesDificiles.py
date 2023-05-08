from sqlalchemy.engine import URL
from sqlalchemy import create_engine
import pyodbc
###########################################
server = 'RGALLEGOS\\SQLEXPRESS'
database = 'PortalDenunciaSedema' 
username = 'Ricardo' 
password = 'Nacho.12'

cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};'
                      f'SERVER={server};'
                      f'DATABASE={database};'
                      f'UID={username};'
                      f'PWD={password}')

cursor = cnxn.cursor()

# codigo

cursor.close()
cnxn.close()
############################################

server = 'RGALLEGOS\\SQLEXPRESS'
database = 'PortalDenunciaSedema' 
username = 'Ricardo' 
password = 'Nacho.12'

url = URL.create(drivername='mssql+pyodbc',
        username= username,
        password= password,
        host= server,
        database= database,
        query={'driver': 'ODBC Driver 18 for SQL Server'})
engine = create_engine(url)
engine
