'''
API 호출 모듈
'''

import os

import requests
from lxml import etree
from lxml.etree import fromstring
from tqdm import tqdm


from utils.time_utils import is_yymmdd_format, get_today_yymmdd
from config.config import api_input_params, api_url


class ApiCall():
    def __init__(self, org_type, file_path, date=None):
        self.service_key = os.getenv('KIPRIS_API_KEY')
        self.org_type = org_type
        if date is not None and is_yymmdd_format(date):
            self.date = date
        else:
            self.date = get_today_yymmdd()
        self.file_path = file_path
        self.session = None

    def call_api(self, service_type, applicant_no):
        params = {}
        url = api_url[service_type]
        if service_type == 'patent_utility':
            params['applicant'] = applicant_no
        elif service_type in ['design', 'trademark']:
            params['applicantName'] = applicant_no

        data_list = []
        page_number = 1

        temp_params = {
            'ServiceKey': self.service_key,
            'numOfRows': 500,
            'pageNo': page_number,
        }
        params.update(temp_params)
        params.update(api_input_params[service_type])

        response = requests.get(url=url, params=params)
        content = response.text
        root = etree.fromstring(content.encode('utf-8'))
        body = root.find('.//body')
        if body is None:
            return []
        items = body.findall('.//item')
        data_list = []
        for item in items:
            item.append(etree.Element('applicantNo'))
            item.find('applicantNo').text = applicant_no
            data_list.append(item)
        
        total_count = int(root.find('.//totalCount').text)
        total_pages = (total_count + 499) // 500
        # 나머지 페이지 순차 요청
        for page in range(2, total_pages + 1):
            page_params = params.copy()
            page_params['pageNo'] = page

            response = requests.get(url=url, params=page_params)
            content = response.text
            body = etree.fromstring(content.encode('utf-8')).find('.//body')
            items = body.findall('.//item')
            for item in items:
                item.append(etree.Element('applicantNo'))
                item.find('applicantNo').text = applicant_no
                data_list.append(item)

        return data_list

    def save_data(self, service_type, data_list):
        if not data_list:
            return

        filename = f"{self.file_path}/{self.date}_{service_type}_{self.org_type}.xml"
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        root = etree.Element("items")
        for item in data_list:
            root.append(item)

        tree = etree.ElementTree(root)
        tree.write(filename, encoding='utf-8', pretty_print=True, xml_declaration=True)

    def call_api_all(self, applicant_no_list):
        service_type_list = ['patent_utility', 'design', 'trademark']
        all_data = []
        for service_type in service_type_list:
            for applicant_no in tqdm(applicant_no_list):
                data = self.call_api(service_type=service_type, applicant_no=applicant_no)
                all_data.extend(data)
            self.save_data(service_type, all_data)
