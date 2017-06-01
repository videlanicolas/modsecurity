#!/usr/bin/python
import re, datetime, logging, argparse
from time import sleep
from sqlalchemy import *
from sqlalchemy.exc import OperationalError

logging.basicConfig(filename='/var/log/molopa.log',level=logging.DEBUG,format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d/%m/%Y %H:%M:%S')

class log():
	def __init__(self,data):
		logging.debug("log -> __init__( {0} )".format(str(data)))
		self.__data = data
		"""
		id -> 
		time -> 
		source_ip -> 
		destination_ip -> 
		source_port -> 
		destination_port -> 
		method -> 
		request_headers -> 
		response_headers -> 
		uri -> 
		params -> 
		request_body -> 
		response_body -> 
		status -> 
		CREATE TABLE `logs` (
	`id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
	`server_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	`modsecurity_id` INT NOT NULL,
	`modsecurity_time` DATETIME NOT NULL,
	`source_ip` VARCHAR(15) NOT NULL,
	`destination_ip` VARCHAR(15) NOT NULL,
	`source_port` SMALLINT UNSIGNED NOT NULL,
	`destination_port` SMALLINT UNSIGNED NOT NULL,
	`method` VARCHAR(50) NULL DEFAULT NULL,
	`request_headers` MEDIUMTEXT NULL DEFAULT NULL,
	`response_headers` MEDIUMTEXT NULL DEFAULT NULL,
	`uri` VARCHAR(50) NULL DEFAULT NULL,
	`params` MEDIUMTEXT NULL DEFAULT NULL,
	`request_body` MEDIUMTEXT NULL DEFAULT NULL,
	`response_body` MEDIUMTEXT NULL DEFAULT NULL,
	`status` SMALLINT NULL DEFAULT NULL,
	`message` TEXT NULL DEFAULT NULL,
	PRIMARY KEY (`id`)
)
COMMENT='Logs from Modsecurity.'
COLLATE='latin1_spanish_ci'
ENGINE=InnoDB
;
		"""
		self.id = str(self.__data.split('\n')[0].split('-')[2])
		logging.debug("class log(): id -> {0}".format(self.id))
		self.__parts = self.parts()
		logging.debug("class log(): __parts -> {0}".format(self.__parts))
		self.time = datetime.datetime.fromtimestamp(int(re.findall('Stopwatch.*?\(',self.__parts['H'])[0].split()[1])/1000000).strftime('%Y-%m-%d %H:%M:%S')
		logging.debug("class log(): time -> {0}".format(self.time))
		self.source_ip = self.__parts['A'].split()[3]
		logging.debug("class log(): source_ip -> {0}".format(self.source_ip))
		self.destination_ip = self.__parts['A'].split()[5]
		logging.debug("class log(): destination_ip -> {0}".format(self.destination_ip))
		self.source_port = self.__parts['A'].split()[4]
		logging.debug("class log(): source_port -> {0}".format(self.source_port))
		self.destination_port = self.__parts['A'].split()[6]
		logging.debug("class log(): destination_port -> {0}".format(self.destination_port))
		self.method = self.__parts['B'].split()[0]
		logging.debug("class log(): method -> {0}".format(self.method))
		headers = dict()
		for h in self.__parts['B'].split('\n')[1:]:
			headers[h.split(': ')[0]] = h.split(': ')[1]
		self.request_headers = headers
		logging.debug("class log(): request_headers -> {0}".format(self.request_headers))
		headers = dict()
		for h in self.__parts['F'].split('\n')[1:]:
			headers[h.split(': ')[0]] = h.split(': ')[1]
		self.response_headers = headers
		logging.debug("class log(): response_headers -> {0}".format(self.response_headers))
		self.uri = self.__parts['B'].split()[1].split('?')[0]
		logging.debug("class log(): uri -> {0}".format(self.uri))
		self.params = self.__parts['B'].split()[1].split('?')[1] if len(self.__parts['B'].split()[1].split('?')) > 1 else ''
		logging.debug("class log(): params -> {0}".format(self.params))
		self.request_body = self.__parts['C']
		logging.debug("class log(): request_body -> {0}".format(self.request_body))
		self.response_body = self.__parts['E']
		logging.debug("class log(): response_body -> {0}".format(self.response_body))
		self.status = self.__parts['F'].split()[1]
		logging.debug("class log(): status -> {0}".format(self.status))
		self.msg = re.search(r'(\[msg.*?\])',self.__parts['H'])
		self.msg = re.search(r'\".*\"',self.msg)
		logging.debug("class log(): msg -> {0}".format(self.msg))
		#self.md5 = self.__parts['F'].split()[1]
		#logging.debug("class log(): md5 -> {0}".format(self.status))
	def parts(self):
		logging.debug("log -> parts()")
		parts = dict()
		letras = ['A','B','C','D','F','E','G','H','I','J','K','Z']
		for letra_start in letras:
			if self.has_part(letra_start):
				for letra_fin in letras[letras.index(letra_start)+1:]:
					try:
						if self.has_part(letra_fin):
							logging.debug("Letra start: {0} Letra fin: {1}".format(letra_start,letra_fin))
							logging.debug(re.findall('--{0}-{1}--.*--{0}-{2}--'.format(self.id,letra_start,letra_fin),self.__data,re.DOTALL))
							parts[letra_start] = re.findall('--{0}-{1}--.*--{0}-{2}--'.format(self.id,letra_start,letra_fin),self.__data,re.DOTALL)[0].strip('--{0}-{1}--'.format(self.id,letra_start)).strip('--{0}-{1}--'.format(self.id,letra_fin)).strip('\n')
						else:
							continue
					except Exception as e:
						logging.error("Error parsing parts: {0}".format(str(e)))
						raise Exception("Error parsing parts: {0}".format(str(e)))
					else:
						break
			else:
				parts[letra_start] = ''
		return parts
	def has_part(self,part):
		logging.debug("log -> has_part( {0} )".format(str(part)))
		return True if re.findall('--{0}-{1}--'.format(self.id,part),self.__data,re.DOTALL) else False
	def session_info(self):
		logging.debug("log -> session_info()")
		if not self.has_part('H'):
			return ''
		else:
			r = self.parts()['H']
		return {'rule_id' : re.findall('\[id.*?]',r)[0], 'latency' : re.findall('Stopwatch.*?\(',r)[0].split()[2], 'raw' : r}

class db():
	def __init__(self,host,port,user,password,db_type='sql'):
		self.host = host
		self.user = user
		self.password = password
		self.port = port
		self.db_type = db_type
		try:
			if db_type == 'sql':
				self.connection = create_engine('mysql+mysqlconnector://{0}:{1}@{2}:{3}/modsecurity'.format(self.user,self.password,self.host,str(self.port)))
				metadata = MetaData(self.connection)
				logs = Table('logs', metadata, autoload=True)
				self.__i = logs.insert()
			elif db_type == 'elasticsearch':
				pass
			else:
				raise Exception("Dataabase type unknown.")
		except sqlalchemy.exc.OperationalError as e:
			if 'Unknown database \'modsecurity\'' in str(e):
				logging.error("No database named 'modsecurity'. Create it with: CREATE DATABASE modsecurity;")
				raise Exception("No database named 'modsecurity'. Create it with: CREATE DATABASE modsecurity;")
			else:
				logging.error("Connection error: {0}".format(str(e)))
				raise Exception("Connection error: {0}".format(str(e)))
		else:
			logging.info("Successfully connected to {0}:{1}.".format(self.host,self.port))
	def insert(self,data):
		if self.db_type == 'sql':
			logging.debug("INSERT: {0}".format(str(data)))
			self.__i.execute(data)
		elif self.db_type == 'elasticsearch':
			pass
		else:
			raise Exception("Database type unknown.")
		logging.info("Inserted data to database.")
	def close(self):
		self.connection.dispose()

def main(audit_log,audit_storage,user,password,database_type,database_location,database_port):
	logging.debug("main()")
	#Continuously read log file
	database = db(host=database_location,port=database_port,user=user,password=password,db_type=database_type)
	with open(audit_log,'rt') as f:
		while True:
			line = f.readline()
			if line:
				#Look for the file
				try:
					data = ""
					logging.debug("Line: {0}".format(line))
					logging.debug("Opening {0}".format(audit_storage + line.split()[14]))
					with open(audit_storage + line.split()[14],'rt') as g:
						data = log(g.read())
					#Send to database
					logging.debug("Sending to database.")
					database.insert({	'modsecurity_id' : data.id,\
										'modsecurity_time' : data.time,\
										'source_ip' : data.source_ip,\
										'destination_ip' : data.destination_ip,\
										'source_port' : data.source_port,\
										'destination_port' : data.destination_port,\
										'method' : data.method,\
										'request_headers' : str(data.request_headers),\
										'response_headers' : str(data.response_headers),\
										'uri' : data.uri,\
										'params' : data.params,\
										'request_body' : data.request_body,\
										'response_body' : data.response_body,\
										'status' : data.status,\
										'message' : data.msg })
				except IOError:
					logging.warning("Cannot open audit storage file, moving on to next log line.")
				except Exception as e:
					logging.error("Error parsing audit file configuration: {0}.".format(str(e)))
					raise Exception("Error parsing audit file configuration: {0}.".format(str(e)))
			else:
				#No audit files
				sleep(0.1)

if __name__ == '__main__':
	try:
		parser = argparse.ArgumentParser(description='ModSecurity python log parser and transmiter (Py-MoLoPa TX).')
		requiredNamed = parser.add_argument_group('required arguments')
		optionalNamed = parser.add_argument_group('optional arguments')
		requiredNamed.add_argument('-a','--audit-log', required=True, help='Location of audit log (SecAuditLog).')
		requiredNamed.add_argument('-s','--audit-storage', required=True, help='Location of audit log storage (SecAuditLogStorageDir).')
		requiredNamed.add_argument('-u','--user', required=True, help='Database user.')
		requiredNamed.add_argument('-w','--password', required=True, help='Database password.')
		optionalNamed.add_argument('-d','--database', required=False, default='localhost', help='Location of log database.')
		optionalNamed.add_argument('-p','--port', required=False, type=int, default=None, help='Database port.')
		optionalNamed.add_argument('-t','--database-type', required=False, default='sql', choices=['sql','elasticsearch'], help='Databse Type.')
		args = parser.parse_args()
		if not args.database:
			logging.warning("No database location entered, defaulting to 'localhost'.")
		if not args.database_type:
			logging.warning("No database type entered, defaulting to sql.")
		if not args.port:
			if args.database_type == 'sql':
				args.port = 3306
			elif args.database_type == 'elasticsearch':
				args.port = 443
		main(audit_log=args.audit_log,audit_storage=args.audit_storage,user=args.user,password=args.password,database_type=args.database_type,database_location=args.database, database_port=str(args.port))
	except Exception as e:
		logging.critical("Runtime exception on main: {0}".format(str(e)))
	else:
		logging.info("Script ended with no errors.")
	logging.info("Ending audit log tx.")