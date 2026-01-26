from core.memory import memory

print("\n--- TEST 1: Learning ---")
memory.save_memory("The user prefers using 'urllib' instead of 'yfinance' because pip is broken.")
memory.save_memory("Project Alpha is a weather app using OpenWeatherMap API.")
print("✅ Memories saved.")

print("\n--- TEST 2: Remembering ---")
query = "Why shouldn't I use yfinance?"
print(f"Question: {query}")

results = memory.search_memory(query)
print(f"Answer found in memory: {results}")

if "urllib" in str(results):
    print("\n✅ SUCCESS: The Agent remembers the preference!")
else:
    print("\n❌ FAILURE: Amnesia detected.")