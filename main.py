'''
main.py
'''

import os
from time import time

import asyncio
from dotenv import load_dotenv
from prometheus_client import start_http_server


from config.config import tables
from collectors.applicant_no_extractor import get_applicant_number_async
from collectors.async_api_call2 import AsyncApiCall
from db.mysql_loader import Database
from preprocessors.preprocessor_baseline import DataParser

# from collectors.api_patent_corp import AsyncPatentDownloaderCorp
# from collectors.api_trademark_corp import AsyncTrademarkDownloaderCorp
# from collectors.api_design_corp import AsyncDesignDownloaderCorp
# from collectors.api_patent_univ import AsyncPatentDownloaderUniv
# from collectors.api_trademark_univ import AsyncTrademarkDownloaderUniv
# from collectors.api_design_univ import AsyncDesignDownloaderUniv


# async def collect_data():
#     design_corp = AsyncDesignDownloaderCorp()
#     patent_corp = AsyncPatentDownloaderCorp()
#     trademark_corp = AsyncTrademarkDownloaderCorp()
#     design_univ = AsyncDesignDownloaderUniv()
#     patent_univ = AsyncPatentDownloaderUniv()
#     trademark_univ = AsyncTrademarkDownloaderUniv()
#     await asyncio.wait([
#         asyncio.create_task(design_corp.process_all()),
#         asyncio.create_task(patent_corp.process_all()),
#         asyncio.create_task(trademark_corp.process_all()),
#         asyncio.create_task(design_univ.process_all()),
#         asyncio.create_task(patent_univ.process_all()),
#         asyncio.create_task(trademark_univ.process_all()),
#     ])

async def process_data(file_path, date, corp_info_list, univ_info_list):
    corp_api = AsyncApiCall(org_type='corp', file_path=file_path, date=date)
    univ_api = AsyncApiCall(org_type='univ', file_path=file_path, date=date)
    
    await asyncio.gather(
        corp_api.init_session(),
        univ_api.init_session()
    )
    try:
        tasks = [
            (corp_api.async_call_api_all(service_type='patent_utility', applicant_no_list=corp_info_list), 'corp-patent_utility'),
            (corp_api.async_call_api_all(service_type='design', applicant_no_list=corp_info_list), 'corp-design'),
            (corp_api.async_call_api_all(service_type='trademark', applicant_no_list=corp_info_list), 'corp-trademark'),
            (univ_api.async_call_api_all(service_type='patent_utility', applicant_no_list=univ_info_list), 'univ-patent_utility'),
            (univ_api.async_call_api_all(service_type='design', applicant_no_list=univ_info_list), 'univ-design'),
            (univ_api.async_call_api_all(service_type='trademark', applicant_no_list=univ_info_list), 'univ-trademark')
        ]
        
        for coro, name in tasks:
            task = asyncio.create_task(coro)
            try:
                await task
                print(f"✅ Completed: {name}")
            except Exception as e:
                print(f"❌ Error in {name}: {str(e)}")
    finally:
        # 세션 정리
        await asyncio.gather(
            corp_api.close_session(),
            univ_api.close_session()
        )


def main():
    '''
    main_flow 입니다.
    데이터를 수집, 파일로 저장, 파일을 읽어서 파싱 후 데이터베이스에 적재
    '''

    load_dotenv()
    key = os.getenv("KIPRIS_API_KEY")
    db = Database()
    file_path = './data'
    date = '20241101'

    start = time()
    ## 1 특허 고객번호 (작업 주기가 길다)
    ## csv에서 기업 사업자 번호 추출, api호출, 데이터베이스에 적재
    corp_nos = db.fetch_corp_numbers()
    ##  1-2 db 
    ## 데이터 파일을 데이터베이스에 적재
    org_info = asyncio.run(get_applicant_number_async(corp_no_list=corp_nos, access_key=key))
    db.load_applicant_no(table_to_load=tables['TB_200'], org_info=org_info)

    ## 2-1 특허 고객번호 받아오기
    corp_info_list = db.get_applicant_no(org_type=0)
    univ_info_list = db.get_applicant_no(org_type=1)

    ## 2 -2 api 호출 적재
    # 모니터링
    start_http_server(8000, addr='0.0.0.0')
    # api 호출
    asyncio.run(process_data(file_path, date, corp_info_list, univ_info_list))

    # 데이터 파일을 기준으로 데이터 전처리
    ## parsing(필요한 파일들로 파싱)
    data_paser = DataParser(date=date, path=file_path)
    
    ipr_reg_corp, ipc_cpc_corp, priority_corp =  data_paser.xml_to_list('corp')
    ipr_reg_univ, ipc_cpc_univ, priority_univ =  data_paser.xml_to_list('univ')
    
    ## 3 db 적재
    ## 데이터 베이스에 적재
    ## 기업
    # DBManager(file -> 데이터 베이스 적재, 300) (기업)
    ipr_reg_corp = db.append_biz_no(table_metadata=tables['TB_200'], dataset=ipr_reg_corp)
    db.upsert_data(org_type=0, service_type=0, table_to_load=tables['TB_300'], dataset=ipr_reg_corp)
    ## DBManager(file -> 데이터 베이스 적재, 310) (기업)
    db.upsert_data(org_type=0, service_type=1, table_to_load=tables['TB_310'], dataset=ipc_cpc_corp) # 함수명 수정 예정
    # ## DBManager(file -> 데이터 베이스 적재, 320) (기업)
    db.upsert_data(org_type=0, service_type=2, table_to_load=tables['TB_320'], dataset=priority_corp) # 함수명 수정 예정

    # ## 대학
    # ## DBManager(file -> 데이터 베이스 적재, 400) (대학)
    ipr_reg_univ = db.append_biz_no(table_metadata=tables['TB_210'], dataset=ipr_reg_univ)
    db.upsert_data(org_type=1, service_type=0, table_to_load=tables['TB_400'], dataset=ipr_reg_univ)
    # ## DBManager(file -> 데이터 베이스 적재, 410) (대학)
    db.upsert_data(org_type=1, service_type=1, table_to_load=tables['TB_410'], dataset=ipc_cpc_univ)
    # ## DBManager(file -> 데이터 베이스 적재, 420) (대학)
    db.upsert_data(org_type=1, service_type=2, table_to_load=tables['TB_420'], dataset=priority_univ)
    end = time()
    print(f"전체 플로우 시간 : {end - start}")

if __name__ == "__main__":
    main()