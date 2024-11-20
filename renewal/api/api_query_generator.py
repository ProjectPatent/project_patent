import os

from loguru import logger

from db.mysql_loader import Database
from config.api_config import API_URLS, API_INPUT_PARAMS, API_ITEMS_PER_PAGE
from config.fetcher_config import API_FETCHER_LOGGER
from utils.formatters import format_corporation_no


class APIQueryGenerator:
    def __init__(self):
        self.api_key = os.getenv('KIPRIS_API_KEY')
        self.database_loader = Database()

    def generate_ipr_fetch_query(self, org_type: str, ipr_mode: str) -> list[dict]:
        org_type = org_type if org_type in ['univ', 'corp'] else 'invalid'
        if org_type == 'invalid':
            raise ValueError(f"지원하지 않는 org_type: {org_type}")
        ipr_mode = ipr_mode if ipr_mode in [
            'patuti', 'design', 'trademark', 'mock_server'] else 'invalid'
        if ipr_mode == 'invalid':
            raise ValueError(f"지원하지 않는 ipr_mode: {ipr_mode}")

        requests_list = []
        url = API_URLS[ipr_mode]
        items_per_page = API_ITEMS_PER_PAGE[ipr_mode]
        api_input_params = API_INPUT_PARAMS[ipr_mode]

        applicants = self.database_loader.get_applicant_biz_no(
            org_type=org_type).keys()

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

        return requests_list

    def generate_applicant_no_fetch_query(self) -> list[dict]:
        requests_list = []
        url = API_URLS['applicant_no']
        api_input_params = API_INPUT_PARAMS['applicant_no']

        corp_numbers = format_corporation_no(
            self.database_loader.fetch_corp_no())

        for corp_number in corp_numbers:
            params = {}
            params.update(api_input_params)
            params['CorporationNumber'] = corp_number
            requests_list.append({
                'url': url,
                'params': params,
            })

        return requests_list

    def _calulate_last_page(self, total_count, items_per_page):
        last_page_no = 0
        if total_count <= items_per_page:
            last_page_no = 1
        elif total_count % items_per_page > 0:
            last_page_no = total_count // items_per_page + 1
        else:
            last_page_no = total_count // items_per_page
        return last_page_no

    def generate_paged_fetch_query(self, response_json: dict, request: dict) -> list[dict]:
        requests_list = []
        url = request['url']
        params = request['params']
        items_per_page = params['numOfRows']
        total_count = int(response_json['response']['count']['totalCount'])
        last_page_range = range(2, self._calulate_last_page(
            total_count, items_per_page) + 1)

        if total_count > items_per_page:
            for page_no in last_page_range:
                paged_params = params.copy()
                paged_params['pageNo'] = page_no
                requests_list.append({
                    'url': url,
                    'params': paged_params,
                })
        return requests_list
