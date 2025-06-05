import sqlite3
import numpy as np
from numpy.linalg import norm
import time # For timestamp in store_embedding if we re-add it
from typing import Optional, List, Tuple # ADDED

class Database:
    def __init__(self, db_file_path: str = "qnatz_crew.db"):
        """
        Initializes the Database connection and creates the memory table if it doesn't exist.
        :param db_file_path: Path to the SQLite database file.
        """
        self.db_file_path = db_file_path
        self.conn: Optional[sqlite3.Connection] = None # Type hint for conn
        self.cursor: Optional[sqlite3.Cursor] = None # Type hint for cursor
        self._connect_and_initialize()

    def _connect_and_initialize(self):
        """Establishes connection and initializes the database table."""
        try:
            self.conn = sqlite3.connect(self.db_file_path)
            self.cursor = self.conn.cursor()
            self._create_memory_table()
            # Consider logging successful connection here if a logger is passed or available globally
        except sqlite3.Error as e:
            # Consider logging this error
            print(f"Error connecting to or initializing database {self.db_file_path}: {e}")
            raise  # Re-raise the exception to indicate failure to initialize

    def _create_memory_table(self):
        """Creates the memory table if it doesn't already exist."""
        if self.cursor:
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                item_id TEXT PRIMARY KEY,
                agent_id TEXT,
                role TEXT,
                content TEXT,
                embedding BLOB,
                creation_time REAL
            )
            """)
        if self.conn:
            self.conn.commit()

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float: # Type hint
        """Calculate cosine similarity between two numpy arrays."""
        norm_a = norm(a)
        norm_b = norm(b)
        if norm_a == 0 or norm_b == 0: # Handle zero vectors
            return 0.0
        return np.dot(a, b) / (norm_a * norm_b)

    def store_embedding(self, item_id: str, agent_id: str, role: str, content: str, embedding: np.ndarray) -> bool:
        """
        Stores an embedding in the database.
        Returns True on success, False otherwise.
        """
        if self.conn is None or self.cursor is None:
            print("Database connection not initialized. Call connect() first.")
            return False
        try:
            embedding_bytes = embedding.tobytes()
            self.cursor.execute(
                "INSERT OR REPLACE INTO memory (item_id, agent_id, role, content, embedding, creation_time) VALUES (?, ?, ?, ?, ?, ?)",
                (item_id, agent_id, role, content, embedding_bytes, time.time()),
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error storing embedding for item_id {item_id}: {e}")
            return False

    def retrieve_similar_items(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[str, str, str, str, float]]: # Type hint
        """
        Retrieves similar items based on cosine similarity.
        Returns a list of tuples: (item_id, agent_id, role, content, similarity)
        """
        if self.conn is None or self.cursor is None:
            print("Database connection not initialized. Call connect() first.")
            return []

        query_embedding_np = np.array(query_embedding, dtype=np.float32) # Ensure it's a numpy array

        try:
            self.cursor.execute("SELECT item_id, agent_id, role, content, embedding FROM memory")
            rows: List[Tuple[str, str, str, str, bytes]] = self.cursor.fetchall() # Type hint for rows

            results: List[Tuple[str, str, str, str, float]] = [] # Type hint for results
            for row_data in rows: # Renamed row to row_data to avoid conflict with outer scope (if any)
                item_id, agent_id, role, content, embedding_bytes = row_data
                embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                similarity = self._cosine_similarity(query_embedding_np, embedding)
                results.append((item_id, agent_id, role, content, float(similarity))) # Cast similarity to float

            results.sort(key=lambda x: x[4], reverse=True)
            return results[:top_k]
        except sqlite3.Error as e:
            print(f"Error retrieving similar items: {e}")
            return []

    def execute(self, sql: str, params: Optional[tuple] = None) -> Optional[sqlite3.Cursor]: # Type hint for params
        """Execute an SQL query. Useful for other operations if needed."""
        if not self.conn or not self.cursor:
            print("Not connected to database")
            return None
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
            self.conn.commit()
            return self.cursor
        except sqlite3.Error as e:
            print(f"Error executing SQL: {sql}, Error: {e}")
            return None

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
            # Consider logging successful disconnection

if __name__ == '__main__':
    # Added os import for file removal
    import os
    print("--- Testing Database Class ---")
    db_instance = Database(db_file_path="test_qnatz_crew.db") # Use a test DB file

    # 1. Store some memories
    item1_id = "memory_1_class"
    item1_agent_id = "agent_1_class"
    item1_role = "user_class"
    item1_content = "What is the capital of France using the class?"
    item1_embedding = np.random.rand(384).astype(np.float32)
    db_instance.store_embedding(item1_id, item1_agent_id, item1_role, item1_content, item1_embedding)

    item2_id = "memory_2_class"
    item2_agent_id = "agent_2_class"
    item2_role = "assistant_class"
    item2_content = "The capital of France is Paris, via class."
    item2_embedding = np.random.rand(384).astype(np.float32)
    db_instance.store_embedding(item2_id, item2_agent_id, item2_role, item2_content, item2_embedding)

    # 2. Create a query embedding
    query_content = "Tell me about France's capital city using the class"
    query_embedding_class = np.random.rand(384).astype(np.float32)

    # 3. Retrieve similar memories
    similar_items_class = db_instance.retrieve_similar_items(query_embedding_class)

    # 4. Print the results
    print("\nSimilar Memories (Class-based):")
    if similar_items_class:
        for item_id, agent_id, role, content, similarity in similar_items_class:
            print(f"Item ID: {item_id}")
            print(f"Agent ID: {agent_id}")
            print(f"Role: {role}")
            print(f"Content: {content}")
            print(f"Similarity: {similarity:.4f}")
            print("-" * 20)
    else:
        print("No similar items found or error occurred.")

    # Close the connection
    db_instance.close()
    print("\nDatabase connection closed.")

    # Clean up the test database file
    try:
        os.remove("test_qnatz_crew.db")
        print("Test database file 'test_qnatz_crew.db' removed.")
    except OSError as e:
        print(f"Error removing test database file: {e}")
