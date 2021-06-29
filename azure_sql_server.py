import textwrap
import pyodbc
from azure.storage.blob import BlobClient

class Database:
    is_connection = False
    _CONNECTION_STRING = 'DefaultEndpointsProtocol=https;' \
                         'AccountName=faceimages2;' \
                         'AccountKey=vlaKfbwxn8eU1kZGo3KjuFIsgQ0BGot1MRCvs6x0mB923Yx2FOXv4XQ82Hgi' \
                         '/l4iKb4iM/DSNcAeezmYYxxFxw==;' \
                         'EndpointSuffix=core.windows.net'
    _CONTAINER = 'pictures'
    _IMAGES_FILE_NAME = 'list_images.txt'

    def open_connection(self):
        if not Database.is_connection:
            driver = '{ODBC Driver 17 for SQL Server}'
            server_name = 'mysqlservercovid'
            database_name = 'myCovidKeeper'
            server = '{server_name}.database.windows.net'.format(server_name=server_name)
            username = 'azureuser'
            password = 'Amitai5925'

            connection_string = textwrap.dedent(f'''
                Driver={driver};
                Server={server};
                Database={database_name};
                Uid={username};
                Pwd={password};
                Encrypt=yes;
                TrustServerCertification=no;
                Connection Timeout=30;
            ''')

            self.cnxn: pyodbc.Connection = pyodbc.connect(connection_string)
            Database.is_connection = True

    def close_connection(self):
        self.cnxn.close()
        Database.is_connection = False

    def open_cursor(self):
        self.crsr: pyodbc.Cursor = self.cnxn.cursor()

    def close_cursor(self):
        self.crsr.close()

    def start_or_close_threads(self):
        result = self.select_query_of_one_row("select Handle from [dbo].[Starter]")
        if not result:
            return None
        return result[0]

    def update_query(self, query):
        self.open_connection()
        self.open_cursor()
        self.crsr.execute(query)
        self.crsr.commit()
        self.close_cursor()



    def get_ip_port_config(self, table_name):
        result = self.select_query_of_one_row("select Manager_port, Manager_ip, Analayzer_port, Analayzer_ip, "
                                              "Camera_port, Camera_ip from [dbo].[Ip_port_components]")
        if not result:
            return None
        self.update_query("update [dbo].[Ip_port_components] set " + table_name + "_handle = 0")
        config_dict = {"Manager_port": result[0],
                       "Manager_ip": result[1],
                       "Analayzer_port": result[2],
                       "Analayzer_ip": result[3],
                       "Camera_port": result[4],
                       "Camera_ip": result[5]}
        return config_dict

    def set_ip_by_table_name(self, table_name):
        import socket
        my_ip = socket.gethostbyname(socket.gethostname())
        print('ip:', my_ip)
        self.update_query("update [dbo].[Ip_port_components] set " + table_name + "_ip = '" + my_ip + "'")
        self.turn_on_components_ip_port_flags()

    def set_port_by_table_name(self, table_name, port):
        self.update_query("update [dbo].[Ip_port_components] set " + table_name + "_port = " + port)
        self.turn_on_components_ip_port_flags()

    def turn_on_components_ip_port_flags(self):
        self.update_query("update [dbo].[Ip_port_components] set Manager_handle = 1, "
                          "Analayzer_handle = 1, Camera_handle = 1")

    def get_flag_ip_port_by_table_name(self, table_name):
        result = self.select_query_of_one_row("select " + table_name + "_handle "
                                                                       "from [dbo].[Ip_port_components]")
        if not result:
            return None
        return result[0]

    def get_camera_config_flag(self):
        result = self.select_query_of_one_row("select Handle from [dbo].[Camera_config]")
        if not result:
            return None
        return result[0]

    def set_camera_config_flag_from_camera(self):
        self.update_query("update [dbo].[Camera_config] set Handle = 0")

    def upload_images_txt_to_storage(self, images):
        with open(self._IMAGES_FILE_NAME, "wb") as myfile:
            myfile.write(images)
        blob_client = BlobClient.from_connection_string(conn_str=self._CONNECTION_STRING, container_name=self.
                                                        _CONTAINER, blob_name=self._IMAGES_FILE_NAME)
        with open(self._IMAGES_FILE_NAME, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        self.set_camera_config_flag_from_camera()

    def select_query_of_one_row(self, query):
        self.open_connection()
        self.open_cursor()
        select_sql = query
        self.crsr.execute(select_sql)
        result = self.crsr.fetchone()
        self.close_cursor()
        return result
