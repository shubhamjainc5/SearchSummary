# SearchSummary

uvicorn app:app --host 0.0.0.0 --workers 8 --port 9050

docker build -t myimage .

docker run -d -v /home/shubham/Downloads/LLMSearch/SearchSummary/webapp:/opt  --name mycontainer -p 8000:8000 myimage