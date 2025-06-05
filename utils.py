import os
from pathlib import Path
import logging
import datetime
import requests  # Added missing import
import sqlite3
import numpy as np  # Import NumPy
from typing import Optional # Added Optional

DEEPSEEK_TIMEOUT = 120 # Default timeout for local LLM calls

# Create and configure logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Best approach: Construct the path relative to the script's location
BASE_DIR = Path(__file__).resolve().parent  # Directory where utils.py is located
DATABASE_FILE = BASE_DIR / "qnatz_crew.db"

class Logger:
    """Simple logger wrapper"""
    def log(self, message, name="System", level="INFO"):
        # Use the root logger with proper level
        log_method = getattr(logging.getLogger(), level.lower(), logging.getLogger().info)
        log_method(f"[{name}] {message}")

class Database:
    """Database connection and utility functions"""
    def __init__(self, db_file=DATABASE_FILE):
        self.db_file = db_file
        self.conn = None

    def connect(self):
        """Connect to the SQLite database"""
        try:
            self.conn = sqlite3.connect(self.db_file)
            logger.info(f"Connected to database: {self.db_file}")
            return self.conn
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")
            return None

    def disconnect(self):
        """Disconnect from the SQLite database"""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from database")

    def execute(self, sql, params=None):
        """Execute an SQL query"""
        if not self.conn:
            logger.error("Not connected to database")
            return None
        try:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            self.conn.commit()
            return cursor
        except sqlite3.Error as e:
            logger.error(f"Error executing SQL: {sql}, Error: {e}")
            return None

    def fetchone(self, sql, params=None):
      """Fetch a single row from the database"""
      try:
        cursor = self.execute(sql, params)
        if cursor:
          return cursor.fetchone()
        return None
      except sqlite3.Error as e:
        logger.error(f"Error executing SQL: {sql}, Error: {e}")
        return None

    def fetchall(self, sql, params=None):
        """Fetch all rows from the database"""
        try:
            cursor = self.execute(sql, params)
            if cursor:
                return cursor.fetchall()
            return None
        except sqlite3.Error as e:
            logger.error(f"Error executing SQL: {sql}, Error: {e}")
            return None

    def store_embedding(self, item_id, agent_id, role, content, embedding):
        """Store vector embeddings as BLOBs in SQLite.
           The item_id should be unique, and passed."""
        try:
            embedding_bytes = embedding.tobytes()
            # Added import for time
            import time
            self.execute(
                "INSERT OR REPLACE INTO memory (item_id, agent_id, role, content, embedding, creation_time) VALUES (?, ?, ?, ?, ?, ?)",
                (item_id, agent_id, role, content, embedding_bytes, time.time()),
            )
            logger.info(f"Stored embedding for item_id: {item_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error storing embedding: {e}")
            return False

    def retrieve_similar_items(self, query_embedding, top_k=5):
        """Retrieve similar items based on cosine similarity"""
        try:
            query_embedding = np.array(query_embedding)
            cursor = self.execute("SELECT item_id, agent_id, role, content, embedding FROM memory")
            results = []
            for row in cursor:
                item_id, agent_id, role, content, embedding_bytes = row
                embedding = np.frombuffer(embedding_bytes, dtype=np.float32) # Assumes float32
                similarity = self.cosine_similarity(query_embedding, embedding)
                results.append((item_id, agent_id, role, content, similarity))

            # Sort by similarity (descending)
            results.sort(key=lambda x: x[4], reverse=True)
            return results[:top_k]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving similar items: {e}")
            return None

    def cosine_similarity(self, a, b):
        """Calculate cosine similarity"""
        # Added import for norm
        from numpy.linalg import norm
        return np.dot(a, b) / (norm(a) * norm(b))

class LocalLLMClient:
    """Client for local LLM server (OpenAI compatible)"""
    def __init__(self, default_timeout=240):
        self.default_timeout = default_timeout
    
    def generate(self, base_api_url: str, prompt: str, model_name: Optional[str] = None, max_tokens: int = 2048, temperature: float = 0.1, request_timeout: Optional[int] = None) -> str:
        """Generate text with configurable timeout and model"""
        actual_timeout = request_timeout if request_timeout is not None else self.default_timeout

        # Ensure base_api_url does not have a trailing slash before appending /completions
        target_url = base_api_url.rstrip('/') + "/completions"

        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if model_name:
            payload["model"] = model_name

        try:
            response = requests.post(
                target_url,
                json=payload, 
                timeout=actual_timeout
            )
            response.raise_for_status() # Raises an HTTPError for bad responses (4XX or 5XX)

            # Assuming the local server returns OpenAI compatible completion format
            # "text" is common for older completion endpoints, "message" for chat.
            # For simplicity, let's assume "text" or adapt if a specific local server format is known.
            response_json = response.json()
            if "choices" in response_json and len(response_json["choices"]) > 0:
                if "text" in response_json["choices"][0]:
                    return response_json["choices"][0]["text"]
                elif "message" in response_json["choices"][0] and "content" in response_json["choices"][0]["message"]: # For chat completion format
                    return response_json["choices"][0]["message"]["content"]

            logger.error(f"LocalLLMClient: Unexpected response format from {target_url}: 'choices' or 'text'/'message' field missing. Response: {response.text[:200]}")
            return f"Error: Unexpected response format from local LLM server at {target_url}"

        except requests.exceptions.ConnectionError:
            logger.error(f"LocalLLMClient: Could not connect to local LLM server at {target_url}")
            return f"Error: Could not connect to local LLM server at {target_url}"
        except requests.exceptions.Timeout:
            logger.error(f"LocalLLMClient: Request to {target_url} timed out after {actual_timeout} seconds")
            return f"Error: Local LLM request timed out after {actual_timeout} seconds to {target_url}"
        except requests.exceptions.HTTPError as e: # Handles 4xx and 5xx errors
            logger.error(f"LocalLLMClient: HTTP error {e.response.status_code} from {target_url}. Response: {e.response.text[:200]}")
            return f"Error: Local LLM API call to {target_url} failed with status {e.response.status_code}: {e.response.text[:100]}"
        except requests.exceptions.RequestException as e: # Catch-all for other requests issues
            logger.error(f"LocalLLMClient: Request to {target_url} failed: {str(e)}")
            return f"Error: Local LLM API call to {target_url} failed: {str(e)}"
        except KeyError as e: # If expected keys are missing in JSON response
            logger.error(f"LocalLLMClient: Unexpected response format from {target_url}: missing key {str(e)}. Response: {response.text[:200]}")
            return f"Error: Unexpected response format from local LLM server at {target_url}: missing {str(e)}"
        except Exception as e: # General catch-all for other errors (e.g., JSON parsing if not valid JSON)
            logger.error(f"LocalLLMClient: An unexpected error occurred while calling {target_url}: {str(e)}")
            return f"Error: Local LLM API call to {target_url} failed with an unexpected error: {str(e)}"

# Constants (can be removed or adapted if no longer directly used by a default LocalLLMClient instance)
# DEEPSEEK_PORT = 5000
# DEEPSEEK_TIMEOUT = 120