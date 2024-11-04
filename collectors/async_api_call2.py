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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.semaphore = asyncio.Semaphore(50)
    
    async def init_session(self):
        self.session = aiohttp.ClientSession()
        
    async def close_session(self):
        if self.session:
            await self.session.close()

    async def async_call_api(self, service_type, applicant_no):
        """API를 호출하여 특허/실용신안/디자인/상표 데이터를 수집합니다."""
        params = {
            'ServiceKey': self.service_key,
            'numOfRows': 500,
            'pageNo': 1
        }
        
        if service_type == 'patent_utility':
            params['applicant'] = applicant_no
        else:
            params['applicantName'] = applicant_no
        params.update(api_input_params[service_type])
        
        url = api_url[service_type]
        data_list = []
        
        # API 요청 함수 (재시도 로직 포함)
        async def make_request(params):
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    async with self.semaphore:
                        async with self.session.get(url=url, params=params) as response:
                            content = await response.text()
                            return content
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt == max_retries - 1:
                        print(f"Failed after {max_retries} attempts: {str(e)}")
                        raise
                    await asyncio.sleep(1 * (attempt + 1))  # 점진적으로 대기 시간 증가
        
        # 첫 페이지 요청
        try:
            content = await make_request(params)
            root = fromstring(content.encode('utf-8'))
            body = root.find('.//body')
            
            if body is None:
                return []
                
            items = body.findall('.//item')
            for item in items:
                item.append(etree.Element('applicantNo'))
                item.find('applicantNo').text = applicant_no
                data_list.append(item)
            
            total_count = int(root.find('.//totalCount').text)
            total_pages = (total_count + 499) // 500
            
        except Exception as e:
            print(f"Error fetching first page for {applicant_no}: {str(e)}")
            return []
        
        # 나머지 페이지 비동기 요청
        async def fetch_page(page_number):
            try:
                page_params = params.copy()
                page_params['pageNo'] = page_number
                content = await make_request(page_params)
                
                body = fromstring(content.encode('utf-8')).find('.//body')
                if body is None:
                    return []
                    
                items = body.findall('.//item')
                for item in items:
                    item.append(etree.Element('applicantNo'))
                    item.find('applicantNo').text = applicant_no
                return items
            except Exception as e:
                print(f"Error fetching page {page_number} for {applicant_no}: {str(e)}")
                return []

        tasks = [
            asyncio.create_task(fetch_page(page))
            for page in range(2, total_pages + 1)
        ]
        
        for task in tqdm_asyncio(
            asyncio.as_completed(tasks),
            total=len(tasks),
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