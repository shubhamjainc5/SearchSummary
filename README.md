# SearchSummary

uvicorn app:app --host 0.0.0.0 --workers 5 --port 9050

docker build -t summary_qa .


for Development

docker run -it -d --restart=always -p 9050:9050 -v /home/shubham/Downloads/LLMSearch/SearchSummary/webapp:/opt --name=summary_qa 00a395218d12

for Production 

docker run -it -d --restart=always -p 9050:9050 -v /home/ubuntu/summary_qa/SearchSummary/webapp:/opt --name=summary_qa eec0a00fb58b