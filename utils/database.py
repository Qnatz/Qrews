import sqlite3
import numpy as np
from numpy.linalg import norm

# Function to calculate cosine similarity
def cosine_similarity(a, b):
    return np.dot(a, b) / (norm(a) * norm(b))

# Connect to SQLite database (creates it if it doesn't exist)
conn = sqlite3.connect("qnatz_crew.db")
cursor = conn.cursor()

# Create the memory table (if it doesn't exist)
cursor.execute("""
CREATE TABLE IF NOT EXISTS memory (
    item_id TEXT PRIMARY KEY,
    agent_id TEXT,
    role TEXT,
    content TEXT,
    embedding BLOB
)
""")
conn.commit()

# Function to store an embedding in the database
def store_embedding(item_id, agent_id, role, content, embedding):
    embedding_bytes = embedding.tobytes()
    cursor.execute(
        "INSERT OR REPLACE INTO memory (item_id, agent_id, role, content, embedding) VALUES (?, ?, ?, ?, ?)",
        (item_id, agent_id, role, content, embedding_bytes),
    )
    conn.commit()

# Function to retrieve similar items based on cosine similarity
def retrieve_similar_items(query_embedding, top_k=5):
    query_embedding = np.array(query_embedding)
    cursor = conn.execute("SELECT item_id, agent_id, role, content, embedding FROM memory")
    results = []
    for row in cursor:
        item_id, agent_id, role, content, embedding_bytes = row
        embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
        similarity = cosine_similarity(query_embedding, embedding)
        results.append((item_id, agent_id, role, content, similarity))

    # Sort by similarity (descending)
    results.sort(key=lambda x: x[4], reverse=True)
    return results[:top_k]

# Example Usage
# 1. Store some memories
item1_id = "memory_1"
item1_agent_id = "agent_1"
item1_role = "user"
item1_content = "What is the capital of France?"
item1_embedding = np.random.rand(384).astype(np.float32)  # Replace with actual embedding
store_embedding(item1_id, item1_agent_id, item1_role, item1_content, item1_embedding)

item2_id = "memory_2"
item2_agent_id = "agent_2"
item2_role = "assistant"
item2_content = "The capital of France is Paris."
item2_embedding = np.random.rand(384).astype(np.float32)  # Replace with actual embedding
store_embedding(item2_id, item2_agent_id, item2_role, item2_content, item2_embedding)

# 2. Create a query embedding
query_content = "Tell me about France's capital city"
query_embedding = np.random.rand(384).astype(np.float32)  # Replace with actual embedding

# 3. Retrieve similar memories
similar_items = retrieve_similar_items(query_embedding)

# 4. Print the results
print("Similar Memories:")
for item_id, agent_id, role, content, similarity in similar_items:
    print(f"Item ID: {item_id}")
    print(f"Agent ID: {agent_id}")
    print(f"Role: {role}")
    print(f"Content: {content}")
    print(f"Similarity: {similarity:.4f}")
    print("-" * 20)

# Close the connection
conn.close()
