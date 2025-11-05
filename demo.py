# import os
# from tavily import TavilyClient
# from dotenv import load_dotenv

# # Load environment variables from .env
# load_dotenv()

# # Initialize Tavily client
# client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# # Example search query
# response = client.search("Latest advancements in kidney transplant aftercare")

# # Print the first search result
# print(response)
import os

print(os.getenv("GROQ_API_KEY"))
print(os.getenv("TAVILY_API_KEY"))
print(os.getenv("HUGGINGFACE_API_KEY"))
