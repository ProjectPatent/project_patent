'''
main.py
'''

import os

from dotenv import load_dotenv

from config.config import tables
# from collectors.api_call import KiprisAPI
from db.mysql_loader import Database
from preprocessors.preprocessor_baseline import DataParser
from collectors.api_patent import PatentDownloader
from collectors.api_design import DesignDownloader
from collectors.api_trademark import TrademarkDownloader

def main():
    '''
    main_flow 입니다.
    데이터를 수집, 파일로 저장, 파일을 읽어서 파싱 후 데이터베이스에 적재
    '''

    load_dotenv()
    key = os.getenv("KIPRIS_API_KEY")
    # kipris_api = KiprisAPI(service_key=key)
    db = Database()

    ## 1 특허 고객번호 (작업 주기가 길다)
    ## csv에서 기업 사업자 번호 추출, api호출, 특허고객번호 파일로 저장
    ## kipris(사업자번호 -> 특허고객번호, 기업)->file
    ## kipris(사업자번호 -> 특허고객번호, 대학)->file   ## 생략
    ##  1-2 db 
    ## 데이터 파일을 데이터베이스에 적재
    ## DBManager(특허고객번호 -> 200) (기업)
    ## DBManager(특허고객번호 -> 210) (대학)            ## 생략
    ## 특허고객번호 선언함수
    ## 2-1 특허 고객번호 받아오기
    ## 200, 210 데이터베이스에서 특허고객번호 추출
    # applicant_no_corp_list = db.함수명(corp)
    # applicant_no_univ_list = db.함수명(univ)

    ## 2 -2 api 호출 적재
    ## kipris(특허고객번호 -> 데이터 수집) (기업)
    ## 파일로 적재
    # kipris.api_call('corp', 'patent_utility')
    # kipris.api_call('corp', 'design')
    # kipris.api_call('corp', 'trademark')
    ## kipris(특허고객번호 -> 데이터 수집) (대학)
    ## 파일로 적재
    # kipris.api_call('univ', 'patent_utility')
    # kipris.api_call('univ', 'design')
    # kipris.api_call('univ', 'trademark')

    # try:
    PatentDownloader().process_all()
    DesignDownloader().process_all()
    TrademarkDownloader().process_all()
        
    # except Exception as e:
    #     logging.error(f"Application failed: {e}")
    #     raise

    # 데이터 파일을 기준으로 데이터 전처리
    ## parsing(필요한 파일들로 파싱)
    data_path = './data'
    data_paser = DataParser(date='20241028', path=data_path)
    
    ipr_reg_corp, ipc_cpc_corp, priority_corp =  data_paser.xml_to_list('corp')
    # ipr_reg_univ, ipc_cpc_univ, priority_univ =  data_paser.xml_to_list('univ')
    
    ## 3 db 적재
    ## 데이터 베이스에 적재
    ## 기업
    ## DBManager(file -> 데이터 베이스 적재, 300) (기업)
    ipr_reg_corp = db.append_biz_no(table_metadata=tables['TB_200'], dataset=ipr_reg_corp)
    db.upsert_data('ipr', table_metadata=tables['TB_300'], dataset=ipr_reg_corp)
    ## DBManager(file -> 데이터 베이스 적재, 310) (기업)
    db.upsert_data('ipc', table_metadata=tables['TB_310'], dataset=ipc_cpc_corp) # 함수명 수정 예정
    # ## DBManager(file -> 데이터 베이스 적재, 320) (기업)
    db.upsert_data('pri', table_metadata=tables['TB_320'], dataset=priority_corp) # 함수명 수정 예정

    # ## 대학
    # ## DBManager(file -> 데이터 베이스 적재, 400) (대학)
    # ipr_reg_univ = db.append_additional_data(table_metadata=tables['TB_200'], dataset=ipr_reg_univ)
    # db.upsert_data(table_metadata=tables['TB_400'], dataset=ipr_reg_univ)
    # ## DBManager(file -> 데이터 베이스 적재, 410) (대학)
    # db.upset_data(table_metadata=tables['TB_410'], data_set=ipc_cpc_univ) # 함수명 수정 예정
    # ## DBManager(file -> 데이터 베이스 적재, 420) (대학)
    # db.upset_data(table_metadata=tables['TB_410'], data_set=priority_univ) # 함수명 수정 예정



if __name__ == "__main__":
    main()