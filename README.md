# project_patent
이어드림 기업 연계 프로젝트 - 준소프트웨어 2팀

이 코드의 목적은 특허, 디자인, 상표 데이터에 대해 API 호출을 통해 정보를 수집하고, 각 테이블 및 컬럼에 맞춰 데이터를 저장하기 위한 매핑 구성을 제공합니다. tables 딕셔너리는 데이터베이스 테이블 구조를 정의하고, api_params 딕셔너리는 API 응답 필드를 테이블 컬럼에 맞게 매핑하며, url 딕셔너리는 API 엔드포인트를 정의하고 있습니다. 또한, BATCH_SIZE는 데이터를 한 번에 가져올 배치 크기를 설정합니다.


## 주요 코드 구성요소

#1. 데이터베이스 테이블 정보 (`tables`)

각 테이블의 약어 (`TB_000`)와 해당 테이블의 이름 및 컬럼 정보를 저장한 사전입니다.

예시:
```python
'tables = {
 'TB_100' : ['tb24_100_biz_info', [
        'company_seq', 
        'biz_no', 
        ...
    ]],
}

테이블 구조
TB_100: 기업 정보
TB_200: 기업 출원인 정보
TB_210: 대학 출원인 정보
TB_300, TB_400: 특허 및 디자인 등록 정보
TB_310, TB_410: IPC/CPC 분류 정보
TB_320, TB_420: 우선권 정보


#2. API 파라미터 매핑 (api_params)
Kipris Plus API에서 출력된 파라미터를 데이터베이스 테이블 컬럼에 매핑하여, 데이터 저장 시 일관성을 유지합니다. 각 특허, 디자인, 상표 유형에 맞는 API 파라미터와 컬럼명이 연결되어 있습니다.

예시
특허/실용신안 (patent_utility)
applicant_no: 특허고객번호 - applicantNo
title: 발명의 명칭 - inventionTitle
디자인 (design)
title: 디자인물품명칭 - articleName
상표 (trademark)
title: 상표명 - title

#3. URL (url)
Kipris Plus API에서 데이터 수집을 위해 호출할 각 데이터 유형별 API 엔드포인트 URL을 정의합니다.

applicant_no: http://plus.kipris.or.kr/openapi/rest/CorpBsApplicantService/corpBsApplicantInfoV2
patent_utility: http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getAdvancedSearch

#4. 배치 크기 (BATCH_SIZE)
대량의 데이터를 효율적으로 처리하기 위한 배치 크기를 설정합니다.

기본 배치 크기: 50


##사용 방법
tables, api_params, url, BATCH_SIZE를 참고하여 데이터를 적재하고 관리할 데이터베이스 테이블과 컬럼 구조를 설정합니다.
api_params를 사용하여 API 응답 데이터를 데이터베이스에 맞게 매핑하고 변환하여 일관된 형식으로 저장합니다.
각 URL을 이용해 Kipris Plus API로부터 데이터를 수집합니다.
BATCH_SIZE에 맞춰 데이터를 배치 단위로 관리하며, 필요한 경우 여러 번의 API 요청을 통해 대량의 데이터를 효과적으로 처리합니다.
