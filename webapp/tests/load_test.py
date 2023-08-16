import grequests

headers = {
    'accept': 'application/json',
    'content-type': 'application/x-www-form-urlencoded',
}

rs = (grequests.post('http://0.0.0.0:8000/llm_api/get_relqa', headers=headers) for i in range(5))
grequests.map(rs)
