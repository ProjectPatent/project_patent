import os
import time

from dotenv import load_dotenv

# from call_api.utils.db_trademark import DatabaseManager
# from call_api.utils.kipris_trademark import KiprisAPI
# from utils.batch_process import BatchProcess

def main():
    key = os.getenv("KIPRIS_API_KEY")

    # 1 특허 고객번호
    # csv에서 기업 사업자 번호 추출, api호출, 특허고객번호 파일로 저장
    ## kipris(사업자번호 -> 특허고객번호, 기업)->file
    ## kipris(사업자번호 -> 특허고객번호, 대학)->file   ### 생략
    #  1-2 db 
    # 데이터 파일을 데이터베이스에 적재
    ## DBManager(특허고객번호 -> 200) (기업)
    ## DBManager(특허고객번호 -> 210) (대학)            ### 생략


    # 2-1 특허 고객번호 받아오기
    # 200, 210 데이터베이스에서 특허고객번호 추출
    ## DBManager(200 -> 특허고객번호 추출) (기업)
    ### return 자료값

    ## DBManager(200 -> 특허고객번호 추출) (대학)
    ### return 자료값

    # 2 -2 api 호출 적재
    ## kipris(특허고객번호 -> 데이터 수집) (기업)
    ### return 파일로 적재

    ## kipris(특허고객번호 -> 데이터 수집) (대학)
    ### return 파일로 적재

    # 데이터 파일을 기준으로 데이터 전처리
    ## parsing(필요한 파일들로 파싱)

    # 3 db 적재
    # 데이터 베이스에 적재
    ## 기업
    ### DBManager(file -> 데이터 베이스 적재, 300) (기업)
    ### DBManager(file -> 데이터 베이스 적재, 310) (기업)
    ### DBManager(file -> 데이터 베이스 적재, 320) (기업)
    ## 대학
    ### DBManager(file -> 데이터 베이스 적재, 300) (대학)
    ### DBManager(file -> 데이터 베이스 적재, 310) (대학)
    ### DBManager(file -> 데이터 베이스 적재, 320) (대학)
    

    pass

if __name__ == "__main__":
    main()