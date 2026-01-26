import chromadb

# 1. Connect to the same DB path your Agent uses
client = chromadb.PersistentClient(path="./agent_memory_db")

# 2. Get the collection
try:
    collection = client.get_collection(name="project_knowledge")
    print(f"✅ Collection found. Contains {collection.count()} memories.\n")

    # 3. Peek at the data (Get all items)
    data = collection.get()
    
    ids = data['ids']
    docs = data['documents']
    metas = data['metadatas']

    print("--- 🧠 CURRENT MEMORY DUMP ---")
    for i, doc in enumerate(docs):
        print(f"[{i}] ID: {ids[i]}")
        print(f"    Content: {doc}")
        print(f"    Metadata: {metas[i]}")
        print("-" * 40)

except Exception as e:
    print(f"❌ Could not read memory: {e}")