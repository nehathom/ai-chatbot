import os 
from dotenv import load_dotenv

load_dotenv()

#azure opepnai configurations
AZURE_OPENAI_ENDPOINT=os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY=os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_EMBEGGINI_MODEL="text-embedding-3-small"
AZURE_OPENAI_CHAT_MODEL="gpt-4o"

#azure ai search configurations
AZURE_SEARCH_ENPOINT=os.getenv("AZURE_SEARCH_ENPOINT")
AZURE_SEARCH_KEY=os.getenv("AZURE_SEARCH_KEY")
AZURE_SEARCH_INDEX_NAME="enterprise-knowlege-index"

