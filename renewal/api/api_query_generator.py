import os

from loguru import logger

from db.mysql_loader import Database
from config.api_config import API_URLS, API_INPUT_PARAMS, API_ITEMS_PER_PAGE
from config.fetcher_config import API_FETCHER_LOGGER
from utils.formatters import format_corporation_no

from prometheus_client import Counter, Summary
from config.fetcher_config import METRICS

# 쿼리 생성 관련 메트릭
QUERY_GENERATION_TIME = Summary(
    f'{METRICS["PREFIX"]}query_generation_seconds',
    'Time spent generating queries',
    ['query_type']  # ipr_fetch, applicant_no_fetch, paged_fetch
)

GENERATED_QUERIES_COUNTER = Counter(
    f'{METRICS["PREFIX"]}generated_queries_total',
    'Number of queries generated',
    ['query_type', 'org_type', 'ipr_mode']
)

class APIQueryGenerator:
    def __init__(self):
        self.api_key = os.getenv('KIPRIS_API_KEY')

    def generate_ipr_fetch_query(self, org_type: str, ipr_mode: str) -> list[dict]:
        start_time = time.time()
        try:
            org_type = org_type if org_type in ['univ', 'corp'] else 'invalid'
            if org_type == 'invalid':
                raise ValueError(f"지원하지 않는 org_type: {org_type}")
            ipr_mode = ipr_mode if ipr_mode in [
                'patuti', 'design', 'trademark'] else 'invalid'
            if ipr_mode == 'invalid':
                raise ValueError(f"지원하지 않는 ipr_mode: {ipr_mode}")

            requests_list = []
            mysql_loader = Database()
            url = API_URLS[ipr_mode]
            items_per_page = API_ITEMS_PER_PAGE[ipr_mode]
            api_input_params = API_INPUT_PARAMS[ipr_mode]

            applicants = mysql_loader.get_applicant_no(org_type=org_type)

            for applicant in applicants:
                params = {}
                params.update(api_input_params)

                if 'applicant' in params:
                    params['applicant'] = applicant
                elif 'applicantName' in params:
                    params['applicantName'] = applicant

                if 'pageNo' in params:
                    params['pageNo'] = 1
                if 'numOfRows' in params:
                    params['numOfRows'] = items_per_page

                requests_list.append({
                    'url': url,
                    'params': params,
                })

            GENERATED_QUERIES_COUNTER.labels(
                query_type='ipr_fetch',
                org_type=org_type,
                ipr_mode=ipr_mode
            ).inc(len(requests_list))

            return requests_list
            
        finally:
            QUERY_GENERATION_TIME.labels(
                query_type='ipr_fetch'
            ).observe(time.time() - start_time)



    def generate_applicant_no_fetch_query(self) -> list[dict]:
        start_time = time.time()
        try:
            requests_list = []
            url = API_URLS['applicant_no']
            api_input_params = API_INPUT_PARAMS['applicant_no']

            corp_numbers = format_corporation_no(
                Database.fetch_corp_no())

            for corp_number in corp_numbers:
                params = {}
                params.update(api_input_params)
                params['CorporationNumber'] = corp_number
                requests_list.append({
                    'url': url,
                    'params': params,
                })

            GENERATED_QUERIES_COUNTER.labels(
                query_type='applicant_no_fetch',
                org_type='all',
                ipr_mode='applicant_no'
            ).inc(len(requests_list))

            return requests_list
            
        finally:
            QUERY_GENERATION_TIME.labels(
                query_type='applicant_no_fetch'
            ).observe(time.time() - start_time)

    def generate_paged_fetch_query(self, response_json: dict, request: dict) -> list[dict]:
        start_time = time.time()
        try:
            requests_list = []
            url = request['url']
            params = request['params']
            items_per_page = params['numOfRows']
            total_count = response_json['response']['count']['totalCount']
            paged_params = params.copy()

            if total_count > items_per_page:
                for page_no in range(2, total_count // items_per_page + 1):
                    paged_params['pageNo'] = page_no
                    requests_list.append({
                    'url': url,
                    'params': paged_params,
                    })
            GENERATED_QUERIES_COUNTER.labels(
                query_type='paged_fetch',
                org_type='all',
                ipr_mode='all'
            ).inc(len(requests_list))

            return requests_list
    
        finally:
                QUERY_GENERATION_TIME.labels(
                    query_type='paged_fetch'
                ).observe(time.time() - start_time)
