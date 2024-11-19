import asyncio
import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

from api.api_query_generator import APIQueryGenerator
from api.api_fetcher import APIFetcher

def main():
    api_query_generator = APIQueryGenerator()

    # asyncio.run(fetch_corp_applicant_no(api_query_generator=api_query_generator))
    asyncio.run(fetch_ipr_data('univ', 'patuti', api_query_generator=api_query_generator))

async def fetch_corp_applicant_no(api_query_generator: APIQueryGenerator):
    requests_list = api_query_generator.generate_applicant_no_fetch_query()
    print(len(requests_list))
    api_fetcher = APIFetcher('corp', 'applicant_no', requests_list)
    await api_fetcher.start()

async def fetch_ipr_data(org_type, ipr_mode, api_query_generator: APIQueryGenerator):
    requests_list = api_query_generator.generate_ipr_fetch_query(org_type, ipr_mode)
    # print(requests_list)
    api_fetcher = APIFetcher(org_type, ipr_mode, requests_list)
    await api_fetcher.start()

def send_slack_message(message):
    webhook_url = os.getenv('SLACK_WEBHOOK_API')
    headers = {'Content-Type': 'application/json'}
    data = {'text': message}
    
    response = requests.post(webhook_url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        print("메시지 전송 성공!")
    else:
        print(f"메시지 전송 실패! 상태 코드: {response.status_code}, 응답: {response.text}")

if __name__ == "__main__":
    try:
        send_slack_message("<!here> 사용 시작 : 프로젝트커")
        main()
    finally:
        send_slack_message("<!here> 사용 완료 : 프로젝트커")
