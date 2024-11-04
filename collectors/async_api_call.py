"""
async_api_call.py

비동기 방식으로 API를 호출하고 데이터를 수집하는 클래스
"""

import os

import aiohttp
import asyncio
from lxml import etree
from lxml.etree import fromstring
from tqdm.asyncio import tqdm_asyncio
from collectors.api_call import ApiCall

from config.config import api_url, api_input_params

class AsyncApiCall(ApiCall):
    async def init_session(self):
        self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        if self.session:
            await self.session.close()

    async def async_call_api(self, service_type, applicant_no):
        """API를 호출하여 특허/실용신안/디자인/상표 데이터를 수집합니다.

        Args:
            service_type (str): 서비스 유형 ('patent_utility', 'design', 'trademark')
            applicant_no (str): 출원인 번호 또는 이름

        Returns:
            list: 수집된 데이터 항목들의 리스트
        """

        params = {}
        url = api_url[service_type]
        if service_type == 'patent_utility':
            params['applicant'] = applicant_no
        elif service_type in ['design', 'trademark']:
            params['applicantName'] = applicant_no

        data_list = []
        page_number = 1

        temp_params = {
            'ServiceKey' : self.service_key,
            'numOfRows' : 500,
            'pageNo' : page_number,
        }
        params.update(temp_params)
        params.update(api_input_params[service_type])
        
        async with self.session.get(url=url, params=params) as response:
            content = await response.text()
            root = fromstring(content.encode('utf-8'))
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
        
        # 나머지 페이지 비동기 요청
        async def fetch_page(page_number):
            page_params = params.copy()
            page_params['pageNo'] = page_number
            async with self.session.get(url=url, params=page_params) as response:
                content = await response.text()
                body = fromstring(content.encode('utf-8')).find('.//body')
                if body is None:
                    return []
                items = body.findall('.//item')
                for item in items:
                    item.append(etree.Element('applicantNo'))
                    item.find('applicantNo').text = applicant_no
                return items

        tasks = [
            asyncio.create_task(fetch_page(page))
            for page in range(2, total_pages + 1)
        ]
        
        # for task in asyncio.as_completed(tasks):
        #     items = await task
        #     if items:
        #         data_list.extend(items)
        
        # return data_list
        for task in tqdm_asyncio(
            asyncio.as_completed(tasks), 
            total=total_pages+1,
            desc=f"Processing pages for {applicant_no}",
            leave=False
        ):
            items = await task
            if items:
                data_list.extend(items)
        return data_list
    
    async def async_save_data(self, service_type, data_list):
        """수집된 데이터를 파일로 저장합니다."""
        if not data_list:
            return
    
        filename = f"{self.file_path}/{self.date}_{service_type}_{self.org_type}.xml"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        root = etree.Element("items")
        for item in data_list:
            root.append(item)
        tree = etree.ElementTree(root)
        tree.write(filename, encoding='utf-8', pretty_print=True, xml_declaration=True)

    async def async_call_api_all(self, service_type, applicant_no_list):
        """여러 출원인 번호에 대해 데이터를 수집하고 저장합니다."""
        all_data = []
        tasks = [
            self.async_call_api(service_type=service_type, applicant_no=applicant_no)
            for applicant_no in applicant_no_list
        ]
                # 태스크 실행 및 결과 수집
        for task in tqdm_asyncio(
            asyncio.as_completed(tasks), 
            total=len(tasks),
            desc=f"Processing {service_type}"
        ):
            data = await task
            if data:
                all_data.extend(data)
        
        await self.async_save_data(service_type, all_data)