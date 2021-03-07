"""
module docstring here
"""

import bgtunnel
import os
import sys
from MySQLdb import connect, cursors
from dotenv import load_dotenv

def get_current_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

class MySqlTunnelError(Exception):
    pass


class TunnelSQL(object):
    def __init__(self, silent=True, cursor='Cursor',
                 ssh_host=None, ssh_port=None, ssh_user=None,
                 ssh_bind_port=None, ssh_host_port=None):
        self.cursorclass = getattr(cursors, cursor)
        self.logging= not silent
        self.ssh_host=os.getenv('SSH_HOST') or ssh_host
        self.ssh_port=int(os.getenv('SSH_PORT')) or ssh_port
        self.ssh_user=os.getenv('SSH_USER') or ssh_user
        self.ssh_bind_port=int(os.getenv('SSH_BIND_PORT')) or ssh_bind_port
        self.ssh_host_port=int(os.getenv('SSH_HOST_PORT')) or ssh_host_port

        self.user = os.getenv('DB_USER')
        self.passwd = os.getenv('DB_PASS')
        self.dbname = os.getenv('DB_NAME')
        self.mysql_port = int(os.getenv('DB_PORT')) or 3308
        self.mysql_host = self.ssh_host  or os.getenv('DB_HOST') or None
        self.conn = None
        self.cursor = None

        self.open_tunnel()
        self.open_connection()
        self.open_cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_tunnel()

    def if_error(self, test, message=None):
        """If test conditon true throw execption with optional message"""
        if test:
            raise MySqlTunnelError(message)

    def connected(self):
        """ test for connection"""
        self.if_error(not self.conn, 'Connection not open')

    def log(self, *messages, end="\n"):
        """log message to console if logging enabled"""
        if self.logging:
            for message in messages:
                print(message, end=end)

    def open_tunnel(self):
        """Open SSH tunnel for connection if needed"""
        if self.ssh_host is None:
            return
        self.forwarder = bgtunnel.open(ssh_address=self.ssh_host,
                                       ssh_port=self.ssh_port,
                                       ssh_user=self.ssh_user,
                                       host_port=self.ssh_host_port,
                                       bind_port=self.ssh_bind_port,
                                       silent=not self.logging)

    def close_tunnel(self):
        """Close the ssh tunnel and database connection and cursor"""
        self.close_connection()
        if self.forwarder:
            self.log('SSH Tunnel Closed')
            self.forwarder.close()
            self.forwarder = None

    def open_connection(self):
        message = ("Starting mysql with command: mysql -h {} -P {} "
                   "-u {} --password={}  {}")
        self.log(message.format(self.mysql_host, self.mysql_port, self.user,
                                self.passwd, self.dbname), end="")
        self.conn = connect(host=self.mysql_host,
                            port=self.mysql_port,
                            user=self.user,
                            passwd=self.passwd,
                            db=self.dbname,
                            cursorclass=self.cursorclass)
        self.if_error(self.conn is None, '...connection Failed')
        self.log("...started!")

    def close_connection(self):
        """Close the database connection and cursor"""
        self.close_cursor()
        if self.conn:
            self.log('Connection Closed')
            self.conn.close()
            self.conn = None

    def open_cursor(self):
        self.cursor = self.conn.cursor()
        self.if_error(self.cursor is None, 'Cound not create cursor')
        self.log('Cursor Created')
        self.log('=============================================')

    def close_cursor(self):
        """Close the database cursor"""
        self.log('=============================================')
        if self.cursor:
            self.log('Cursor Closed')
            self.cursor.close()
            self.cursor = None

    def open(self):
        """Open tunnel, connection and cursor as needed"""
        self.open_tunnel()
        self.open_connection()
        self.open_cursor()
        return self.conn

    def close(self):
        """Close the ssh tunnel and database connection and cursor"""
        self.close_tunnel()

    def query(self, sql, data=[]):
        self.connected()
        self.conn.query(sql, data)
        return self.conn.use_result()

    def execute(self, sql, data=[]):
        self.connected()
        self.log('Executing: ' + sql, data)
        self.cursor.execute(sql, data)
        return self.cursor.fetchall()

    def executemany(self, sql, data=[]):
        self.connected()
        self.cursor.executemany(sql, data)
        self.conn.commit()

    def info(self):
        self.connected()
        return self.conn.info()

    def insert_id(self):
        self.connected()
        return self.conn.insert_id()



if __name__ == '__main__':
    _ = load_dotenv(get_current_dir() + '/.env')

    print("========== TEST NORMALLY VERBOSE ========")
    db = TunnelSQL(silent=False, cursor='DictCursor')
    sql = 'SELECT COUNT(id) AS COUNT FROM wp_nrb_hulls'
    count = db.execute(sql)[0]['COUNT']
    print(count)
    db.close()

    print("\n\n=========== TEST NORMALLY SILENT =========")
    db = TunnelSQL(silent=True, cursor='DictCursor')
    sql = 'SELECT COUNT(id) AS COUNT FROM wp_nrb_hulls'
    count = db.execute(sql)[0]['COUNT']
    print(count)
    db.close()

    print("\n\n=========== TEST WITH VERBOSE ===========")
    with TunnelSQL(silent=False, cursor='DictCursor') as db:
        sql = 'SELECT COUNT(id) AS COUNT FROM wp_nrb_hulls'
        count = db.execute(sql)[0]['COUNT']
        print(count)

    print("\n\n============ TEST WITH SILENT ============")
    with TunnelSQL(silent=True, cursor='DictCursor') as db:
        sql = 'SELECT COUNT(id) AS COUNT FROM wp_nrb_hulls'
        count = db.execute(sql)[0]['COUNT']
        print(count)
