# project_patent
이어드림 기업 연계 프로젝트 - 준소프트웨어 2팀

# DataParser 모듈

Kipris Plus API로부터 XML 형식의 데이터를 가져와 데이터베이스 적재를 위해 전처리하는 모듈입니다. XML 파일에서 주요 정보를 추출하여 가공된 데이터를 리스트로 반환합니다.

## 주요 클래스 및 함수

### 1. DataParser 클래스

XML 파일을 읽고 데이터를 파싱하여 전처리하는 클래스입니다. 파일 경로와 날짜를 입력받아 XML 데이터를 읽고, 주요 데이터를 전처리하여 리스트에 저장합니다.

---

## 함수 설명

### `__init__(self, path, date=None)`

- **역할**: 파일 경로와 날짜를 설정하고, 데이터를 저장할 리스트를 초기화합니다.
- **입력**: 
  - `path`: XML 파일 경로
  - `date`: (옵션) YYYYMMDD 형식의 날짜 (없을 경우 오늘 날짜 사용)
- **출력**: 없음 (클래스 초기화)

### `xml_to_list(self, data_class='corp')`

- **역할**: 특허, 디자인, 상표 XML 데이터를 읽어 파싱된 데이터를 반환합니다.
- **입력**:
  - `data_class`: 기업(corp) 또는 대학(univ)
- **출력**: 파싱된 데이터 리스트 (`ipr_reg_data_list`, `ipc_cpc_data_list`, `priority_data_list`)

### `ipr_reg_parser(self, data_service, data_class)`

- **역할**: `data_service` 타입에 맞는 XML 데이터를 파싱하여 주요 데이터를 저장합니다.
- **입력**:
  - `data_service`: 데이터 타입 (특허/실용신안, 디자인, 상표)
  - `data_class`: 기업(corp) 또는 대학(univ)
- **출력**: 없음 (결과값은 클래스 변수에 저장)

### `ipc_cpc_parser(self, item)`

- **역할**: 특허 데이터의 IPC/CPC 코드를 파싱하여 `ipr_reg_data_list`와 `ipc_cpc_data_list`에 데이터를 저장합니다.
- **입력**:
  - `item`: XML 노드
- **출력**: `temp` (딕셔너리 형태로 파싱된 데이터)

### `priority_parser(self, data_service, item)`

- **역할**: 데이터에서 우선권 정보를 파싱하여 `priority_data_list`에 저장합니다.
- **입력**:
  - `data_service`: 데이터 타입 (디자인, 상표)
  - `item`: XML 노드
- **출력**: `temp` (딕셔너리 형태로 파싱된 데이터)

---

## 사용 예시

```python
from data_parser import DataParser

# XML 파일 경로 설정
path = '/path/to/xml/files'
date = '20231028'  # 데이터 날짜 설정

# DataParser 클래스 초기화
parser = DataParser(path=path, date=date)

# 데이터 파싱
ipr_data, ipc_data, priority_data = parser.xml_to_list(data_class='corp')

# 결과 출력
print(ipr_data)
print(ipc_data)
print(priority_data)

이 코드는 지정된 경로에서 XML 데이터를 읽고, 해당 데이터에서 필요한 정보를 파싱하여 리스트 형태로 반환합니다
