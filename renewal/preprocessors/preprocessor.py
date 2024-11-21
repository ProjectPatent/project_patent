'''
데이터 전처리하는 모듈
'''

import json

from utils.time_utils import get_today_yyyymmdd, is_yyyymmdd_format
from config.api_config import API_PARAMS_TO_PARSE, TABLES

from db.mysql_loader import Database


class DataParser():
    '''
    XML 파일을 읽고 데이터를 전처리하는 클래스입니다.
    '''

    def __init__(self, raw_data_path, output_data_path, date=None):
        self.raw_data_path = raw_data_path
        self.output_data_path = output_data_path
        self.mysql_loader = Database()
        self.biz_nos = self.mysql_loader.get_applicant_biz_no(
            org_type='all')

        self.ipr_reg_data = {}
        self.ipc_cpc_data = {}
        self.priority_data = {}

        if date is not None and is_yyyymmdd_format(date):
            self.date = date
        else:
            self.date = get_today_yyyymmdd()

    def json_to_query_values(self, org_type):
        '''
        기업, 대학 | 특허/실용신안, 디자인, 상표 xml파일을 읽어서 데이터를 리턴
        input : data_service : patuti (특허/실용신안)
                             design (디자인)
                             trademark (상표)
                data_class : corp (기업)
                             univ (대학)
        '''
        self.ipr_reg_data['table_name'] = TABLES[org_type.upper()]['IPR_REG'][0]
        self.ipr_reg_data['values'] = []
        self.ipc_cpc_data['table_name'] = TABLES[org_type.upper()]['IPC_CPC'][0]
        self.ipc_cpc_data['values'] = []
        self.priority_data['table_name'] = TABLES[org_type.upper()]['PRIORITY'][0]
        self.priority_data['values'] = []

        self.ipr_reg_parser(org_type, ipr_mode='patuti')
        self.ipr_reg_parser(org_type, ipr_mode='design')
        self.ipr_reg_parser(org_type, ipr_mode='trademark')

        open(f'{self.output_data_path}/ipr_reg_{self.date}_{org_type}_values.json', 'w',
             encoding='utf-8').write(json.dumps(self.ipr_reg_data, ensure_ascii=False))
        open(f'{self.output_data_path}/ipc_cpc_{self.date}_{org_type}_values.json', 'w',
             encoding='utf-8').write(json.dumps(self.ipc_cpc_data, ensure_ascii=False))
        open(f'{self.output_data_path}/priority_{self.date}_{org_type}_values.json', 'w',
             encoding='utf-8').write(json.dumps(self.priority_data, ensure_ascii=False))
        
        self.ipr_reg_data = {}
        self.ipc_cpc_data = {}
        self.priority_data = {}

    def ipr_reg_parser(self, org_type, ipr_mode):
        '''
        data_service에 해당하는 파라미터에 맞춰서 클래스 변수에 저장합니다.
        서브 테이블인 ipc_code, priority 함수를 호출해서 함께 저장합니다.
        input : data_service : patuti (특허/실용신안)
                               design (디자인)
                               trademark (상표)
        '''
        path = f'{self.raw_data_path}/{ipr_mode}_{self.date}_{org_type}.json'
        ipr_data = None
        try:
            with open(path, 'r', encoding='utf-8') as file:
                # 파일 내용을 문자열로 읽어서 정리
                content = file.read().strip()
                # 혹시 여러 JSON 객체가 있다면 마지막 쉼표나 추가 데이터 제거
                if content.endswith(','):
                    content = content[:-1]
                json_data = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류 발생: {path}")
            print(f"오류 위치: 라인 {e.lineno}, 컬럼 {e.colno}")
            print(f"오류 메시지: {str(e)}")
            raise

        for item in json_data['data']:
            if item['applicationNumber'] is None:
                continue
            if ipr_mode == 'patuti':
                ipr_data = self.ipc_cpc_parser(item, org_type, ipr_mode)
            elif ipr_mode in ('design', 'trademark'):
                ipr_data = self.priority_parser(item, org_type, ipr_mode)
            if ipr_data is not None:
                self.ipr_reg_data['values'].append(ipr_data)

    def ipc_cpc_parser(self, item, org_type, ipr_mode):
        '''
        ipc_code가 있으면 클래스 변수 (ipc_cpc_data_list)에 저장합니다.
        ipr_reg_data_list에 대한 key, value값을 딕셔너리에 저장 후 리턴합니다.
        '''

        ipr_data = {}
        ipc_codes = []
        table_name = TABLES[org_type.upper()]['IPR_REG'][0]
        table_columns = TABLES[org_type.upper()]['IPR_REG'][1]

        for column in table_columns:
            if column == 'biz_no':
                ipr_data[column] = self.biz_nos[item['applicantNo']]
            elif column == 'ipr_code':
                ipr_data[column] = item['applicationNumber'][0:2]
            elif column in API_PARAMS_TO_PARSE[ipr_mode]:
                output_param = API_PARAMS_TO_PARSE[ipr_mode][column]
                if column == 'main_ipc':
                    ipc_codes = item[output_param].split('|')
                    ipr_data[column] = ipc_codes[0]
                else:
                    ipr_data[column] = item[output_param]
            else:
                ipr_data[column] = None
        for ipc_code in ipc_codes:
            self.ipc_cpc_data['values'].append({
                'appl_no': ipr_data['appl_no'],
                'ipc_cpc': 'ipc',
                'ipc_cpc_code': ipc_code,
            })

        return ipr_data

    def priority_parser(self, item, org_type, ipr_mode):
        '''
        priority에 대한 데이터가 존재한다면 클래스 변수(priority_data_list)에 저장합니다.
        ipr_reg_data_list에 대한 key, value값을 딕셔너리에 저장 후 리턴합니다.
        '''

        ipr_data = {}
        priority_data = {}
        table_name = TABLES[org_type.upper()]['IPR_REG'][0]
        table_columns = TABLES[org_type.upper()]['IPR_REG'][1]

        for column in table_columns:
            if column == 'biz_no':
                ipr_data[column] = self.biz_nos[item['applicantNo']]
            elif column == 'ipr_code':
                ipr_data[column] = item['applicationNumber'][0:2]
            elif column in API_PARAMS_TO_PARSE[ipr_mode]:
                output_param = API_PARAMS_TO_PARSE[ipr_mode][column]
                ipr_data[column] = item[output_param]
            else:
                ipr_data[column] = None

        priority_number = item['priorityNumber']
        priority_date = item['priorityDate']
        if priority_number or priority_date:
            priority_data['appl_no'] = ipr_data['appl_no']
            try:
                priority_data['priority_date'] = priority_date
            except KeyError:
                priority_data['priority_date'] = None
            try:
                priority_data['priority_no'] = priority_number
            except KeyError:
                priority_data['priority_no'] = None
            self.priority_data['values'].append(priority_data)

        return ipr_data

    def applicant_no_parser(self):
        applicant_no_data = {}
        
        path = f'{self.raw_data_path}/applicant_no_{self.date}_corp.json'
        json_data = None
        try:
            with open(path, 'r', encoding='utf-8') as file:
                # 파일 내용을 문자열로 읽어서 정리
                content = file.read().strip()
                # 혹시 여러 JSON 객체가 있다면 마지막 쉼표나 추가 데이터 제거
                if content.endswith(','):
                    content = content[:-1]
                json_data = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류 발생: {path}")
            print(f"오류 위치: 라인 {e.lineno}, 컬럼 {e.colno}")
            print(f"오류 메시지: {str(e)}")
            raise
        
        table_name = TABLES['CORP']['APPLICANT'][0]
        table_columns = TABLES['CORP']['APPLICANT'][1]

        applicant_no_data['table_name'] = table_name
        applicant_no_data['values'] = []

        for item in json_data['data']:
            applicant_no = {}
            for column in table_columns:
                output_param = API_PARAMS_TO_PARSE['applicant_no'][column]
                if column in API_PARAMS_TO_PARSE['applicant_no']:
                    if column == 'biz_no' or column == 'corp_no':
                        applicant_no[column] = item[output_param].replace('-', '') if item[output_param] else None
                    else:
                        applicant_no[column] = item[output_param] if item[output_param] else None
                else:
                    applicant_no[column] = None
            applicant_no_data['values'].append(applicant_no)

        open(f'{self.output_data_path}/applicant_no_{self.date}_corp_values.json', 'w',
             encoding='utf-8').write(json.dumps(applicant_no_data, ensure_ascii=False))

    def ipr_seq_parser(self, org_type):
        path = f'{self.output_data_path}/ipc_cpc_{self.date}_{org_type}_values.json'
        json_data = None
        try:
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                if content.endswith(','):
                    content = content[:-1]
                json_data = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류 발생: {path}")
            print(f"오류 위치: 라인 {e.lineno}, 컬럼 {e.colno}")
            print(f"오류 메시지: {str(e)}")
            raise

        ipr_seqs = self.mysql_loader.get_ipr_seqs(org_type)

        for idx, item in enumerate(json_data['values']):
            if item['appl_no'] in ipr_seqs:
                json_data['values'][idx]['ipr_seq'] = ipr_seqs[item['appl_no']]
            else:
                json_data['values'][idx]['ipr_seq'] = None

        open(f'{self.output_data_path}/ipc_cpc_{self.date}_{org_type}_values.json', 'w',
             encoding='utf-8').write(json.dumps(json_data, ensure_ascii=False))
