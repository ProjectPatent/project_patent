'''
데이터 전처리하는 모듈
'''

from lxml import etree

from utils.time_utils import get_today_yymmdd, is_yymmdd_format
from config.config import api_output_params, tables


class DataParser():
    '''
    XML 파일을 읽고 데이터를 전처리하는 클래스입니다.
    '''

    def __init__(self, path, date=None):
        self.path = path

        if date is not None and is_yymmdd_format(date):
            self.date = date
        else:
            self.date = get_today_yymmdd()

    def xml_to_list(self, data_class):
        '''
        기업, 대학 | 특허/실용신안, 디자인, 상표 xml파일을 읽어서 데이터를 리턴
        input : data_service : patent_utility (특허/실용신안)
                             design (디자인)
                             trademark (상표)
                data_class : corp (기업)
                             univ (대학)
        '''
        self.ipr_reg_data_list = []
        self.ipc_cpc_data_list = []
        self.priority_data_list = []

        self.ipr_reg_parser(data_class, data_service='patent_utility')
        self.ipr_reg_parser(data_class, data_service='design')
        self.ipr_reg_parser(data_class, data_service='trademark')

        return self.ipr_reg_data_list, self.ipc_cpc_data_list, self.priority_data_list

    def ipr_reg_parser(self, data_class, data_service):
        '''
        data_service에 해당하는 파라미터에 맞춰서 클래스 변수에 저장합니다.
        서브 테이블인 ipc_code, priority 함수를 호출해서 함께 저장합니다.
        input : data_service : patent_utility (특허/실용신안)
                               design (디자인)
                               trademark (상표)
        '''
        path = f'{self.path}/{self.date}_{data_service}_{data_class}.xml'
        # try:
        tree = etree.parse(path)
        root = tree.getroot()
        ipr_data = None
        for item in root.iter('item'):
            if item.find('.//applicationNumber').text is None:
                continue
            if data_service == 'patent_utility':
                ipr_data = self.ipc_cpc_parser(item, data_service)
            elif data_service in ('design', 'trademark'):
                ipr_data = self.priority_parser(item, data_service)
            if ipr_data is not None:
                self.ipr_reg_data_list.append(ipr_data)

    def ipc_cpc_parser(self, item, data_service):
        '''
        ipc_code가 있으면 클래스 변수 (ipc_cpc_data_list)에 저장합니다.
        ipr_reg_data_list에 대한 key, value값을 딕셔너리에 저장 후 리턴합니다.
        '''

        ipr_data = {}
        ipc_codes = []
        for value in tables['TB_300'][1]:
            if value == 'appl_no':
                appl_no = item.find(
                    f'.//{api_output_params[data_service][value]}').text
                ipr_data[value] = appl_no
            elif value == 'ipr_code':
                ipr_data[value] = item.find(
                    f'.//{api_output_params[data_service]['appl_no']}').text[0:2]
            elif value == 'main_ipc':
                ipc_codes = item.find(
                    f'.//{api_output_params[data_service][value]}').text.split('|')
                ipr_data[value] = ipc_codes[0]
            elif value in api_output_params[data_service]:
                ipr_data[value] = item.find(
                    f'.//{api_output_params[data_service][value]}').text
            else:
                ipr_data[value] = None
        for code in ipc_codes:
            self.ipc_cpc_data_list.append({
                'appl_no': ipr_data['appl_no'],
                'ipc_cpc': 'ipc',  # 추후 ipc, cpc 구분 필요
                'ipc_cpc_code': code,
            })

        return ipr_data

    def priority_parser(self, item, data_service):
        '''
        priority에 대한 데이터가 존재한다면 클래스 변수(priority_data_list)에 저장합니다.
        ipr_reg_data_list에 대한 key, value값을 딕셔너리에 저장 후 리턴합니다.
        '''

        ipr_data = {}
        for value in tables['TB_300'][1]:
            if value == 'appl_no':
                appl_no = item.find(
                    f'.//{api_output_params[data_service][value]}').text
                ipr_data[value] = appl_no
            elif value == 'ipr_code':
                ipr_data[value] = item.find(
                    f'.//{api_output_params[data_service]['appl_no']}').text[0:2]
            elif value in api_output_params[data_service]:
                ipr_data[value] = item.find(
                    f'.//{api_output_params[data_service][value]}').text
            else:
                ipr_data[value] = None
        # for column in tables['TB_300'][1]:
        #     if column == 'appl_no':
        #         appl_no = item.find(
        #             f'.//{api_output_params[data_service][column]}').text
        #         ipr_data[column] = appl_no
        #         continue
        #     elif column == 'ipr_code':
        #         ipr_data[column] = item.find(
        #             f'.//{api_output_params[data_service]['appl_no']}').text[0:2]
        #         continue
        #     elif column in api_output_params[data_service]:
        #         element = item.find(
        #             f'.//{api_output_params[data_service][column]}')
        #         if element is not None and element.text:
        #             ipr_data[column] = element.text
        #             continue
        #     else:
        #         ipr_data[column] = None

        priority_data = {}
        priority_number = item.find('.//priorityNumber').text
        priority_date = item.find('.//priorityDate').text
        if priority_number or priority_date:
            priority_data['applicant_no'] = ipr_data['applicant_no']
            try:
                priority_data['priority_date'] = priority_date
            except KeyError:
                priority_data['priority_date'] = None
            try:
                priority_data['priority_no'] = priority_number
            except KeyError:
                priority_data['priority_no'] = None
            priority_data['appl_no'] = ipr_data['appl_no']
            self.priority_data_list.append(priority_data)

        return ipr_data
