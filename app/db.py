"""
Database connection layer using mysql-connector-python
Implements connection pooling and parameterized queries for security
"""
import mysql.connector
from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool
from config.settings import Config
import os

class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialize_pool()
        return cls._instance
    
    def _initialize_pool(self):
        """Initialize connection pool with security settings"""
        try:
            self.pool = MySQLConnectionPool(
                pool_name="grc_pool",
                pool_size=5,
                pool_reset_session=True,
                host=Config.MYSQL_HOST,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB,
                charset='utf8mb4',
                use_unicode=True,
                autocommit=False,
                ssl_disabled=True  # ← ONLY keep this line (REMOVE auth_plugin line)
            )
            print("✓ Database connection pool initialized")
        except Error as e:
            raise Exception(f"Database connection failed: {e}")
    def get_connection(self):
        """Get connection from pool with validation"""
        try:
            conn = self.pool.get_connection()
            # Verify connection is alive
            if not conn.is_connected():
                conn.reconnect(attempts=3, delay=2)
            return conn
        except Error as e:
            raise Exception(f"Failed to get database connection: {e}")
    
    def execute_query(self, query, params=None, fetch=False):
        """
        Execute parameterized query with automatic connection management
        Args:
            query: SQL query string with %s placeholders
            params: Tuple/list of parameters for query
            fetch: True to return results, False for INSERT/UPDATE/DELETE
        Returns:
            Result set (if fetch=True) or lastrowid/rowcount (if fetch=False)
        """
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            # Execute with parameterized query (prevents SQL injection)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch:
                result = cursor.fetchall()
                return result
            else:
                # For INSERT/UPDATE/DELETE
                if query.strip().upper().startswith("INSERT"):
                    last_id = cursor.lastrowid
                    conn.commit()
                    return last_id
                else:
                    row_count = cursor.rowcount
                    conn.commit()
                    return row_count
                    
        except Error as e:
            if conn:
                conn.rollback()
            raise Exception(f"Query execution failed: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

# Singleton instance for application-wide use
db = Database()