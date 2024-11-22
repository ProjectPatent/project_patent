import asyncio
import json
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

from api.api_query_generator import APIQueryGenerator
from api.api_fetcher import APIFetcher
from preprocessors.preprocessor import DataParser
from db.mysql_loader import Database
from prometheus_client import start_http_server
from config.fetcher_config import METRICS

def main():
    # 메트릭 서버들을 한 번에 시작
    if METRICS['ENABLED']:
        for service, port in METRICS['PORTS'].items():
            try:
                start_http_server(port)
                print(f"Started metrics server for {service} on port {port}")
            except Exception as e:
                print(f"Failed to start metrics server on port {port}: {e}")

    api_query_generator = APIQueryGenerator()
    ipr_data_parser = DataParser(raw_data_path='/home/ubuntu/wooyeol/project_patent/renewal/raw_data/final_20241121', output_data_path='/home/ubuntu/wooyeol/project_patent/renewal/db_dataset', date='20241121')
    mysql_loader = Database()

    # asyncio.run(fetch_corp_applicant_no(api_query_generator=api_query_generator))
    # time.sleep(3)
    # asyncio.run(fetch_ipr_data('corp', 'patuti', api_query_generator=api_query_generator))
    # time.sleep(3)
    # asyncio.run(fetch_ipr_data('univ', 'patuti', api_query_generator=api_query_generator))
    # time.sleep(3)
    # asyncio.run(fetch_ipr_data('corp', 'design', api_query_generator=api_query_generator))
    # time.sleep(3)
    # asyncio.run(fetch_ipr_data('univ', 'design', api_query_generator=api_query_generator))
    # time.sleep(3)
    # asyncio.run(fetch_ipr_data('corp', 'trademark', api_query_generator=api_query_generator))
    # time.sleep(3)
    # asyncio.run(fetch_ipr_data('univ', 'trademark', api_query_generator=api_query_generator))

    ipr_data_parser.applicant_no_parser()
    mysql_loader.upsert_data(json_file_path='/home/ubuntu/wooyeol/project_patent/renewal/db_dataset/applicant_no_20241121_corp_values.json')
    ipr_data_parser.json_to_query_values(org_type='corp')
    ipr_data_parser.json_to_query_values(org_type='univ')

    mysql_loader.upsert_data(json_file_path='/home/ubuntu/wooyeol/project_patent/renewal/db_dataset/ipr_reg_20241121_corp_values.json')
    mysql_loader.upsert_data(json_file_path='/home/ubuntu/wooyeol/project_patent/renewal/db_dataset/ipr_reg_20241121_univ_values.json')
    ipr_data_parser.ipr_seq_parser(org_type='corp')
    ipr_data_parser.ipr_seq_parser(org_type='univ')
    mysql_loader.upsert_data(json_file_path='/home/ubuntu/wooyeol/project_patent/renewal/db_dataset/ipc_cpc_20241121_corp_values.json')
    mysql_loader.upsert_data(json_file_path='/home/ubuntu/wooyeol/project_patent/renewal/db_dataset/ipc_cpc_20241121_univ_values.json')
    mysql_loader.upsert_data(json_file_path='/home/ubuntu/wooyeol/project_patent/renewal/db_dataset/priority_20241121_corp_values.json')
    mysql_loader.upsert_data(json_file_path='/home/ubuntu/wooyeol/project_patent/renewal/db_dataset/priority_20241121_univ_values.json')
    

    # requests_list = api_query_generator.generate_ipr_fetch_query('univ', 'trademark')
    # requests_list = api_query_generator.generate_applicant_no_fetch_query()
    # print(requests_list)

    # single_request_test()


async def fetch_corp_applicant_no(api_query_generator: APIQueryGenerator):
    requests_list = api_query_generator.generate_applicant_no_fetch_query()
    # print(requests_list[:5])
    api_fetcher = APIFetcher('corp', 'applicant_no', requests_list)
    await api_fetcher.start()

async def fetch_ipr_data(org_type, ipr_mode, api_query_generator: APIQueryGenerator):
    requests_list = api_query_generator.generate_ipr_fetch_query(org_type, ipr_mode)
    # print(requests_list[:5])
    api_fetcher = APIFetcher(org_type, ipr_mode, requests_list, enable_progress_bar=True)
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

def single_request_test():
    api_query_generator = APIQueryGenerator()
    requests_list = api_query_generator.generate_ipr_fetch_query('corp', 'patuti')
    print(requests_list[:5])
    for request in requests_list:
        response = requests.get(url=request['url'], params=request['params'], timeout=10)
        print(response.status_code)
        print(response.text)
        print(response.url)

if __name__ == "__main__":
    IS_ACTUAL_TEST = 0
    if IS_ACTUAL_TEST == 1:
        try:
            send_slack_message("<!here> 사용 시작 : 프로젝트커")
            main()
        finally:
            send_slack_message("<!here> 사용 완료 : 프로젝트커")
    else:
        main()
        print('테스트 완료')