try:
    from google.adk.runners import Runner
    print("Runner found in google.adk.runners")
except ImportError:
    print("Runner NOT found in google.adk.runners")

try:
    from google.adk.sessions import InMemorySessionService
    print("InMemorySessionService found in google.adk.sessions")
except ImportError:
    print("InMemorySessionService NOT found in google.adk.sessions")

try:
    from google.adk.sessions.in_memory import InMemorySessionService
    print("InMemorySessionService found in google.adk.sessions.in_memory")
except ImportError:
    print("InMemorySessionService NOT found in google.adk.sessions.in_memory")
