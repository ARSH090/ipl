try:
    from google import genai
    print("Success: from google import genai works")
except ImportError as e:
    print(f"Error: {e}")
