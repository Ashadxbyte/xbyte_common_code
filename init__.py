import json
import pymysql
import requests
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem

class ScrapyAutomation:

    @staticmethod
    def get_useragent(os_type='WINDOWS'):
        """
               Generate Random UserAgents Android/IOS/Windows.

               Args:
               - os_type (str): Android/Windows/IOS types.

               Returns:
               - UserAgent: String like UserAgents.
               """
        if str(os_type).upper() == 'ANDROID' or str(os_type).upper() == 'IOS':
            software_names = [SoftwareName.CHROME.value,SoftwareName.SAFARI.value]
            operating_systems = [OperatingSystem.ANDROID.value,OperatingSystem.IOS.value]
            user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems)
            return user_agent_rotator.get_random_user_agent()
        elif str(os_type).upper() == 'LINUX':
            software_names = [SoftwareName.CHROME.value]
            operating_systems = [OperatingSystem.LINUX.value]
            user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems)
            return user_agent_rotator.get_random_user_agent()
        else:
            software_names = [SoftwareName.CHROME.value]
            operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]
            user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems)
            return user_agent_rotator.get_random_user_agent()

    @staticmethod
    def create_table(conn_string, columns):
        """
        Creates a table in the database with the given columns.

        Args:
        - conn_string (obj): The connection string of the database, containing db host, db name, table name.
        - columns (dict): Dictionary containing column names and their data types.

        Returns:
        - bool: True if the table is created successfully, False otherwise.
        - con, cursor: Returns con and cursor if successfully executed.
        """

        if not columns or not conn_string:
            print("No columns provided / No conn_string provided")
            return False

        #todo - fetch data from conn string
        conn_data = json.loads(conn_string)
        db_host = conn_data.get('db_host')
        db_user = conn_data.get('db_user')
        db_passwd = conn_data.get('db_passwd')
        db_name = conn_data.get('db_name')
        table_name = conn_data.get('table_name')

        con = pymysql.connect(host=db_host, user=db_user, password=db_passwd)
        db_cursor = con.cursor()

        try:
            create_db = f"create database if not exists {db_name} CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci"
            db_cursor.execute(create_db)

            con = pymysql.connect(host=db_host, user=db_user, password=db_passwd, database=db_name, autocommit=True, use_unicode =True, charset="utf8")
            cursor = con.cursor()

            #todo - Constructing the CREATE TABLE query dynamically
            column_definitions = ', '.join([f"{col_name} {col_type}" for col_name, col_type in columns.items()])
            create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({column_definitions})"

            cursor.execute(create_table_query)
            con.commit()
            cursor.close()

            print(f"Table '{table_name}' created successfully.")
            return con,cursor
        except Exception as e:
            print(f"Error creating table: {str(e)}")
            con.rollback()
            return False

    @staticmethod
    def fetch_pending_data(conn, database_type, params):
        """
        Fetch data from database

        Args:
        - conn (obj): The connection of the Database.
        - cursor (obj): The cursor of the database.
        - database_type (str): SQL/Mongo database types.
        - params (dict): conditions for fetch database.

        Returns:
        - data (tuple): Data which fetched from database.
        """
        if database_type.lower() == "mysql":
            # Assuming 'params' contains the necessary SQL command and table/collection name

            query = params['query']  # SQL query to fetch data where status is "Pending"
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            return result

        elif database_type.lower() == "mongodb":
            # Assuming 'params' contains the necessary MongoDB commands and collection name

            collection = conn[params['db']][params['collection']]
            query = params['query']  # MongoDB query to fetch data where status is "Pending"
            # query['status'] = 'Pending'
            result = collection.find(query)
            return list(result)

        else:
            print("Invalid database type specified")
            return None

    @staticmethod
    def save_page(response, file_path):
        """
        Saves the content of a web page to a file.

        Args:
        - response (obj): The response of the request Url.
        - file_path (str): The path where the content will be saved.

        Returns:
        - bool: True if the content is successfully saved, False otherwise.
        """
        if response.status_code == 200 or response.status_code == 404:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(response.content)
                return True
        return False

    @staticmethod
    def read_page(file_path):
        """
        Reads the content of a file.

        Args:
        - file_path (str): The path of the file to be read.

        Returns:
        - bytes or None: Content of the file if found, None otherwise.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            return None

    @staticmethod
    def make_request(url, headers, request_type="GET", proxy=None, payload=None):
        """
            Sends a request to the specified URL.

            Args:
            - url (str): The URL for the GET/POST request.
            - headers (dict, optional): Headers for the request.
            - proxy (dict, optional): Proxy for the request.
            - payload (dict, optional): Payload for the POST request.
            - request_type (dict, optional): request_type like GET/POST request.

            Returns:
            - ResponseStatuscode : The response Statuscode.
            - ResponseText : The response object.
        """
        retries = 3
        blocked_responses = ['Limit Reach', 'Max Retries Exceed', 'Too Many Requests', ' Download attempts failed',
                             'Forbidden Error', 'Permission To Access']
        allowed_status_codes = ['200', '404']

        for _ in range(retries):
            if proxy:
                proxy_obj = {'http': proxy, 'https': proxy}
                if 'scraper' in proxy:
                    your_key = ''
                    link = f'http://api.scraperapi.com?api_key={your_key}&url={url}&keep_headers=true&country_code=us'
                    response = requests.get(link, headers=headers)
                elif 'crawlera' in proxy:
                    headers['x-requested-with'] = "XMLHttpRequest"
                    headers['X-Crawlera-Cookies'] = "disable"
                    if request_type.upper() == "GET":
                        response = requests.get(url, proxies=proxy_obj, headers=headers, verify=False)
                    else:
                        response = requests.post(url, proxies=proxy_obj, headers=headers, data=payload,
                                                 verify=False)
                else:
                    if request_type.upper() == "GET":
                        response = requests.get(url, proxies=proxy_obj, headers=headers, verify=False)
                    else:
                        response = requests.post(url, proxies=proxy_obj, headers=headers, data=payload,
                                                 verify=False)
            else:
                if request_type.upper() == "GET":
                    response = requests.get(url, headers=headers)
                else:
                    response = requests.post(url, headers=headers, data=payload)

            response_text = response.text
            response_status_code = response.status_code

            if all(str(checkpoint).lower() not in str(response_text).lower() for checkpoint in blocked_responses) and str(
                    response_status_code) in allowed_status_codes:
                return response_text, response_status_code

        return 'Error in request', 'Error in request'  # Or handle the case when all retries fail

    @staticmethod
    def insert(conn, database_type, params):
        """
        Fetch data from database

        Args:
        - conn (obj): The connection of the Database.
        - cursor (obj): The cursor of the database.
        - database_type (str): SQL/Mongo database types.
        - params (dict): conditions for fetch database.

        Returns:
        - data (tuple): Data inserted in given database.
        """
        if database_type.lower() == "mysql":
            # Assuming 'params' contains the necessary SQL command and table/collection name

            query = params['query']  # SQL query to fetch data where status is "Pending"
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            return result

        elif database_type.lower() == "mongodb":
            # Assuming 'params' contains the necessary MongoDB commands and collection name

            collection = conn[params['db']][params['collection']]
            item = params['item']  # MongoDB query to fetch data where status is "Pending"
            collection.insert_one(item)
            return print("Data inserted successfully")

        else:
            print("Invalid database type specified")
            return None

    @staticmethod
    def update(conn, database_type, params):
        """
        Fetch data from database

        Args:
        - conn (obj): The connection of the Database.
        - cursor (obj): The cursor of the database.
        - database_type (str): SQL/Mongo database types.
        - params (dict): conditions for fetch database.

        Returns:
        - data (tuple): Data updated in given database.
        """
        if database_type.lower() == "mysql":
            # Assuming 'params' contains the necessary SQL command and table/collection name

            query = params['query']  # SQL query to update data where status is "Pending"
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            return result

        elif database_type.lower() == "mongodb":
            # Assuming 'params' contains the necessary MongoDB commands and collection name

            collection = conn[params['db']][params['collection']]
            item = params['item']  # MongoDB query to update data where status is "Pending"
            collection.update_one(params['condition'],{"$set":item})
            return print("Data inserted successfully")
        else:
            print("Invalid database type specified")
            return None