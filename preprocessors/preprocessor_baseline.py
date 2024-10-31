'''
데이터 전처리하는 모듈
'''

from lxml import etree

from utils.time_utils import get_today_yymmdd, is_yymmdd_format
from config.config import api_params

class DataParser():
    '''
    XML 파일을 읽고 데이터를 전처리하는 클래스입니다.
    '''

    def __init__(self, path, date=None):
        self.path = path
        self.ipr_reg_data_list = []
        self.ipc_cpc_data_list = []
        self.priority_data_list = []
        
        if date is not None and is_yymmdd_format(date):
            self.date = date
        else:
            self.date = get_today_yymmdd()
        
    def xml_to_list(self, data_class='corp'):
        '''
        기업, 대학 | 특허/실용신안, 디자인, 상표 xml파일을 읽어서 데이터를 리턴
        input : data_service : patent_utility (특허/실용신안)
                             design (디자인)
                             trademark (상표)
                data_class : corp (기업)
                             univ (대학)
        '''

        self.ipr_reg_parser(data_service='patent_utility',  data_class=data_class)
        self.ipr_reg_parser(data_service='design', data_class=data_class)
        self.ipr_reg_parser(data_service='trademark', data_class=data_class)

        return self.ipr_reg_data_list, self.ipc_cpc_data_list, self.priority_data_list


    def ipr_reg_parser(self, data_service, data_class):
        '''
        data_service에 해당하는 파라미터에 맞춰서 클래스 변수에 저장합니다.
        서브 테이블인 ipc_code, priority 함수를 호출해서 함께 저장합니다.
        input : data_service : patent_utility (특허/실용신안)
                               design (디자인)
                               trademark (상표)
                data_class : corp (기업)
                             univ (대학)
        '''
        path = f'{self.path}/{self.date}_{data_service}_{data_class}.xml'
        # try:
        tree = etree.parse(path)
        root = tree.getroot()
        temp = None
        for item in root.iter('item'):
            if data_service == 'patent_utility':
                temp = self.ipc_cpc_parser(item)
            elif data_service in ('design', 'trademark'):
                temp = self.priority_parser(data_service, item)
            if temp is not None:
                self.ipr_reg_data_list.append(temp)
            

    def ipc_cpc_parser(self, item):
        '''
        ipc_code가 있다면 클래스 변수 (ipc_cpc_data_list)에 저장합니다.
        ipr_reg_data_list에 대한 key, value값을 딕셔너리에 저장 후 리턴합니다.
        '''

        temp = {}
        for key, value in api_params['patent_utility'].items():
            if value == 'applicationNumber':
                appl_no = str(item.find(f'.//{value}').text)
                temp[f'{key}'] = appl_no
                temp['ipr_code'] = appl_no[0] + '0'
            elif value == 'ipcNumber':
                ipc_codes = item.find(f'.//{value}').text.split('|')
                temp[f'{key}'] = ipc_codes[0]
            else:
                temp[f'{key}'] = item.find(f'.//{value}').text
        for code in ipc_codes:
            self.ipc_cpc_data_list.append({
                'appl_no' : temp['appl_no'], 
                'ipc_cpc' : code[0],
                'ipc_cpc_code' : code
            })

        return temp

    def priority_parser(self, data_service, item):
        '''
        priority에 대한 데이터가 존재한다면 클래스 변수(priority_data_list)에 저장합니다.
        ipr_reg_data_list에 대한 key, value값을 딕셔너리에 저장 후 리턴합니다.
        '''

        temp = {}
        for key, value in api_params[data_service].items():
            if value == 'applicationNumber':
                appl_no = str(item.find(f'.//{value}').text)
                temp[f'{key}'] = appl_no
                temp['ipr_code'] = appl_no[:1] + '0'
            else:
                temp[f'{key}'] = item.find(f'.//{value}').text

        priority_data = {}
        if temp['priority_no'] is not None:
            priority_data['priority_no'] = temp['priority_no']
        temp.pop('priority_no')
        if temp['priority_date'] is not None:
            priority_data['priority_date'] = temp['priority_date']
        temp.pop('priority_date')
        if len(priority_data) > 0:
            priority_data['applicant_no'] = temp['applicant_no']
            self.priority_data_list.append(priority_data)


        return temp
