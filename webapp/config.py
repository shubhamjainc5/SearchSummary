BASE_DIR = "static"

# azure deployment name
AZURE_DEPLOYMENT_NAME = "ss-summary-qa"
# azure model version name
AZURE_MODEL_NAME = "gpt-35-turbo"
# Set this to `azure`
OPENAI_API_TYPE = "azure"
# The API version you want to use: set this to `2022-12-01` for the released version.
OPENAI_API_VERSION = "2023-09-15-preview"
# The base URL for your Azure OpenAI resource.  You can find this in the Azure portal under your Azure OpenAI resource.
OPENAI_API_BASE = "https://c5-openai-accelerate.openai.azure.com/"
# The API key for your Azure OpenAI resource.  You can find this in the Azure portal under your Azure OpenAI resource.
OPEN_AI_API_KEY = "ed946fc86f5b43bab0dcbc105b9edd03"
# Elastic search endpoint url
ELASTIC_HOST_URL = "http://3.111.180.30:6000/haystack"