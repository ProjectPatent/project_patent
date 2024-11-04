"""특허정보 API를 사용하여 기업의 출원인 번호를 추출하는 모듈입니다."""

import os
import xml.etree.ElementTree as ET

import requests
from dotenv import load_dotenv
from tqdm import tqdm
from tqdm.asyncio import tqdm_asyncio
import aiohttp

from db.mysql_loader import Database


load_dotenv()


def _format_corporation_number(corp_no_list: list[str]) -> list[str]:
    """
    기업번호를 형식화하는 함수

    Args:
    corp_no_list (list[str]): 13자리 기업번호 리스트

    Returns:
    str: 'XXXXXX-XXXXXXX' 형식으로 변환된 기업번호
    """
    formatted_corp_no_list = []
    for corp_no in corp_no_list:
        formatted_corp_no_list.append(
            "-".join([corp_no[0][:6], corp_no[0][6:]]))
    return formatted_corp_no_list


def get_applicant_number_sync(corp_no_list: list[str], access_key: str) -> tuple[list[dict], str]:
    """
    API를 호출하여 기업의 출원인 정보를 조회하는 함수

    Args:
    corp_no_list (list[str]): 기업번호 리스트
    access_key (str): API 접근 키

    Returns:
    tuple: (정보 딕셔너리 리스트, 오류 메시지)
           성공 시 ([{
               'applicant_no': str,
               'applicant': str,
               'corp_no': str,
               'biz_no': str
           }, ...], None)
           실패 시 (None, 오류 메시지)
    """
    url = "http://plus.kipris.or.kr/openapi/rest/CorpBsApplicantService/corpBsApplicantInfoV2"
    formatted_corp_no_list = _format_corporation_number(corp_no_list)
    results = []

    for corp_no in tqdm(formatted_corp_no_list, desc="기업 출원인 정보 조회 중"):
        params = {
            "CorporationNumber": corp_no,
            "accessKey": access_key
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            root = ET.fromstring(response.content)
            info = root.find(".//corpBsApplicantInfo")

            if info is not None:
                result = {
                    'applicant_no': info.findtext('ApplicantNumber'),
                    'applicant': info.findtext('ApplicantName'),
                    'corp_no': info.findtext('CorporationNumber').replace("-", ""),
                    'biz_no': info.findtext('BusinessRegistrationNumber').replace("-", "")
                }

                if not result['applicant_no']:
                    continue  # 해당 기업은 건너뛰고 다음 기업 처리

                results.append(result)

    if not results:
        return None, "No valid applicant information found for any corporation"

    return results, None


async def get_applicant_number_async(corp_no_list: list[str], access_key: str) -> tuple[list[dict], str]:
    """
    API를 비동기적으로 호출하여 기업의 출원인 정보를 조회하는 함수

    Args:
    corp_no_list (list[str]): 기업번호 리스트
    access_key (str): API 접근 키

    Returns:
    tuple: (정보 딕셔너리 리스트, 오류 메시지)
           성공 시 ([{
               'applicant_no': str,
               'applicant': str,
               'corp_no': str,
               'biz_no': str
           }, ...], None)
           실패 시 (None, 오류 메시지)
    """
    url = "http://plus.kipris.or.kr/openapi/rest/CorpBsApplicantService/corpBsApplicantInfoV2"
    formatted_corp_no_list = _format_corporation_number(corp_no_list)
    results = []

    async with aiohttp.ClientSession() as session:
        async def fetch_applicant_info(corp_no: str) -> dict:
            params = {
                "CorporationNumber": corp_no,
                "accessKey": access_key
            }

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    content = await response.text()
                    root = ET.fromstring(content)
                    info = root.find(".//corpBsApplicantInfo")

                    if info is not None:
                        result = {
                            'applicant_no': info.findtext('ApplicantNumber'),
                            'applicant': info.findtext('ApplicantName'),
                            'corp_no': info.findtext('CorporationNumber').replace("-", ""),
                            'biz_no': info.findtext('BusinessRegistrationNumber').replace("-", "")
                        }

                        if result['applicant_no']:
                            return result
            return None

        tasks = [fetch_applicant_info(corp_no)
                 for corp_no in formatted_corp_no_list]
        results = [result for result in await tqdm_asyncio.gather(*tasks, desc="기업 출원인 정보 조회 중") if result]

    if not results:
        return None, "No valid applicant information found for any corporation"

    return results, None


def main():
    """
    메인 함수: 
    """

    access_key = os.getenv("KIPRIS_API_KEY")

    db = Database()

    corp_no_list = db.fetch_corp_no()
    get_applicant_number_sync(corp_no_list, access_key)

# if __name__ == "__main__":
#     main()
