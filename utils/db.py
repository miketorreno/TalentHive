from typing import Any
import redis
import psycopg2
from psycopg2.extras import RealDictCursor

# Connect to PostgreSQL
# conn = psycopg2.connect(
#     host="localhost",
#     database="hulumjobs",
#     user="postgres",
#     password="postgres",
#     port="5432",
# )

# Connect to Redis
redis_client = redis.StrictRedis(host="localhost", port=6379, decode_responses=True)


def execute_query(query, params=None) -> list[tuple[Any, ...]] | None:
    """
    Execute a query on the PostgreSQL database.

    Args:
        query (str): The SQL query to execute.
        params (tuple, optional): The parameters to pass to the query. Defaults to None.

    Returns:
        list[tuple[Any, ...]] | None: The results of the query, or None if the query is a write operation.
    """

    try:
        # Establish a connection to the database
        conn = psycopg2.connect(
            host="localhost",
            database="hulumjobs",
            user="postgres",
            password="postgres",
            port="5432",
        )

        # Create a cursor object
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Execute the query
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        # Commit the transaction if it's a write operation
        if query.strip().lower().startswith(("insert", "update", "delete")):
            conn.commit()
            return True

        # Fetch results if it's a read operation
        if query.strip().lower().startswith("select"):
            return cursor.fetchall()
    except psycopg2.DatabaseError as db_error:
        raise Exception(f"Database error occurred: {db_error}") from db_error
    except psycopg2.Error as db_error:
        raise Exception(f"Database error occurred: {db_error}") from db_error
    except redis.RedisError as redis_error:
        raise Exception(f"Redis error occurred: {redis_error}") from redis_error
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}") from e
    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return None
