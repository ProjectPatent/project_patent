"""
mysql_loader 모듈

이 모듈은 MySQL 데이터베이스와의 연결 및 데이터 조작을 위한 기능을 제공합니다.
환경 변수에서 데이터베이스 연결 정보를 로드하고, 데이터베이스 연결, 쿼리 실행,
데이터 삽입 및 업데이트 등의 기능을 포함하는 Database 클래스를 정의합니다.

사용된 라이브러리:
- os: 환경 변수 접근을 위해 사용
- dotenv: .env 파일에서 환경 변수를 로드하기 위해 사용
- MySQLdb: MySQL 데이터베이스와의 연결 및 쿼리 실행을 위해 사용
"""

import os

from dotenv import load_dotenv
from MySQLdb import OperationalError, connect


load_dotenv()


class Database:
    """MySQL 데이터베이스 연결 및 쿼리 실행을 관리하는 클래스.

    환경 변수에서 데이터베이스 연결 정보를 가져와 초기화하고,
    데이터베이스 연결, 쿼리 실행, 데이터 삽입 등의 기능을 제공합니다.
    """

    def __init__(self) -> None:
        """Database 클래스 초기화.

        환경 변수에서 데이터베이스 연결 정보를 가져와 인스턴스 변수로 설정합니다.
        """
        self.host = os.getenv("MYSQL_HOST", "localhost")
        self.user = os.getenv("MYSQL_USER")
        self.password = os.getenv("MYSQL_PASSWORD")
        self.db_name = os.getenv("MYSQL_DB")
        self.connection = None

    def connect(self):
        """데이터베이스 연결을 생성합니다.

        Returns:
            None

        동작 방식:
            1. 연결이 없거나 닫혀있는 경우에만 새로운 연결을 생성
            2. 환경 변수에서 가져온 접속 정보를 사용하여 연결

        Raises:
            OperationalError: 데이터베이스 연결 실패 시
        """
        if not self.connection or not self.connection.open:
            self.connection = connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.db_name
            )

    def close(self):
        """데이터베이스 연결을 종료합니다.

        Returns:
            None

        동작 방식:
            - 활성화된 연결이 있는 경우에만 연결을 종료
            - 연결이 없거나 이미 닫혀있는 경우 아무 동작도 하지 않음
        """
        if self.connection and self.connection.open:
            self.connection.close()

    def execute_query(self, query: str):
        """SQL 쿼리를 실행합니다.

        Args:
            query (str): 실행할 SQL 쿼리문

        Returns:
            bool | None: 쿼리 실행 성공 시 True, 실패 시 None

        동작 방식:
            1. 데이터베이스에 연결
            2. 쿼리 실행
            3. 변경사항 커밋
            4. 연결 종료

        Raises:
            OperationalError: 데이터베이스 연결 또는 쿼리 실행 중 오류 발생 시
        """
        try:
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute(query)
            self.connection.commit()
            return True
        except OperationalError as e:
            print(f"쿼리 실행 실패: {str(e)}")
            return None
        finally:
            cursor.close()
            self.close()

    def append_biz_no(self,
                      table_metadata: list[str, list[str]],
                      dataset: list[dict],
                      ) -> list[dict]:
        """데이터셋에 사업자등록번호(biz_no) 컬럼을 추가합니다.

        Args:
            table_metadata (list[str, list[str]]): [테이블명, 컬럼목록]을 포함하는 리스트
            dataset (list[dict]): 사업자등록번호를 추가할 데이터 리스트

        Returns:
            list[dict] | None: 사업자등록번호가 추가된 데이터 리스트, 실패 시 None

        동작 방식:
            1. 지정된 테이블에서 applicant_no와 biz_no 매핑 정보를 조회
            2. 조회된 정보를 딕셔너리로 변환하여 빠른 검색이 가능하도록 함
            3. dataset의 각 데이터에 대해 applicant_no에 해당하는 biz_no를 추가

        Raises:
            OperationalError: 데이터베이스 연결 또는 쿼리 실행 중 오류 발생 시
            KeyError: dataset의 데이터에 applicant_no가 없거나, 
                     해당 applicant_no에 대응하는 biz_no를 찾을 수 없는 경우
        """
        cursor = None
        try:
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute(
                f"SELECT applicant_no, biz_no FROM {table_metadata[0]}"
            )
            rows = cursor.fetchall()

            biz_no_dict = {}
            for applicant_no, biz_no in rows:
                biz_no_dict[applicant_no] = biz_no

            for data_seq, data in enumerate(dataset):
                applicant_no = dataset[data_seq]['applicant_no']
                biz_no = biz_no_dict[applicant_no]
                dataset[data_seq]['biz_no'] = biz_no

            return dataset
        except OperationalError as e:
            print("Error:", e)
            return None
        finally:
            if cursor:
                cursor.close()
            self.close()

    def insert_data(self,
                    table_metadata: list[str, list[str]],
                    dataset: list[dict],
                    ):
        """데이터를 데이터베이스 테이블에 삽입합니다.

        Args:
            table_metadata (list[str, list[str]]): [테이블명, 컬럼목록]을 포함하는 리스트
            dataset (list[dict]): 삽입할 데이터 리스트. 각 딕셔너리는 컬럼명을 키로 가짐

        Returns:
            bool | None: 삽입 성공 시 True, 실패 시 None

        동작 방식:
            1. 데이터베이스에 연결
            2. dataset의 각 데이터를 순회하며 INSERT 쿼리 실행
            3. 모든 데이터는 자동으로 SQL 인젝션 방지를 위한 이스케이프 처리됨
            4. 모든 삽입이 성공적으로 완료되면 commit 실행

        Raises:
            OperationalError: 데이터베이스 연결 또는 쿼리 실행 중 오류 발생 시
        """
        cursor = None
        try:
            self.connect()
            cursor = self.connection.cursor()
            for data in dataset:
                columns = ', '.join(data.keys())
                placeholders = ', '.join(['%s'] * len(data))
                query = f"INSERT INTO {self.db_name}.{
                    table_metadata[0]}({columns}) VALUES({placeholders})"

                # dict의 values를 리스트로 변환하여 파라미터로 전달
                values = list(data.values())
                cursor.execute(query, values)

            return self.connection.commit()
        except OperationalError as e:
            print(f"쿼리 실행 실패: {str(e)}")
            return None
        finally:
            if cursor:
                cursor.close()
            self.close()

    def upsert_data(self,
                    org_type: int,
                    service_type: int,
                    table_to_load: list[str, list[str]],
                    dataset: list[dict],
                    ):
        """데이터를 데이터베이스에 삽입하거나 업데이트합니다.

        Args:
            org_type (int): 기관 타입 코드
                - 0: 기업
                - 1: 대학
            data_type (int): 데이터 타입 코드
                - 0: 산업재산권 데이터
                - 1: IPC/CPC 분류 데이터
                - 2: 우선권 데이터
            table_to_load (list[str, list[str]]): [테이블명, 컬럼목록]을 포함하는 리스트
            dataset (list[dict]): 삽입 또는 업데이트할 데이터 리스트

        Returns:
            None

        데이터 타입별 처리 규칙:
            산업재산권 데이터 (data_type=0):
                - 다음 필드는 업데이트하지 않음:
                    survey_year, survey_month, write_time, modify_time,
                    legal_status_desc, appl_no, applicant_no
                - legal_status_desc는 값이 다른 경우에만 업데이트

            우선권 데이터 (data_type=1):
                - ipr_seq는 기존 산업재산권 테이블에서 조회하여 자동 설정
                - priority_nation은 값이 다른 경우에만 업데이트
                - 그 외 필드는 모두 업데이트 가능

            IPC/CPC 분류 데이터 (data_type=2):
                - ipr_seq는 기존 산업재산권 테이블에서 조회하여 자동 설정
                - 다음 필드는 업데이트하지 않음:
                    ipr_seq, ipc_seq, applicant_no
                - 그 외 필드는 모두 업데이트 가능

        동작 방식:
            1. 데이터베이스에 연결
            2. 각 데이터에 대해:
                - 데이터가 존재하지 않으면 새로 삽입
                - 데이터가 존재하면 데이터 타입별 규칙에 따라 업데이트
            3. 모든 처리가 성공하면 변경사항 커밋
            4. 오류 발생 시 롤백

        Raises:
            OperationalError: 데이터베이스 연결 또는 쿼리 실행 중 오류 발생 시
        """
        cursor = None
        try:
            self.connect()
            cursor = self.connection.cursor()
            table_name = table_to_load[0]

            for data in dataset:
                columns = ', '.join(data.keys())
                placeholders = ', '.join(['%s'] * len(data))
                values = list(data.values())

                update_clauses = []

                if service_type == 0:
                    for column in data.keys():
                        if column not in [
                            'survey_year',
                            'survey_month',
                            'write_time',
                            'modify_time',
                            'legal_status_desc',
                            'appl_no',
                            'applicant_no',
                        ]:
                            update_clauses.append(
                                f"{column} = VALUES({column})")
                        elif column == 'legal_status_desc':
                            update_clauses.append(
                                f"{column} = CASE WHEN {column} != VALUES({column}) THEN VALUES({
                                    column}) ELSE {column} END"
                            )

                elif service_type == 1:
                    columns = columns.removesuffix(', appl_no')
                    for column in data.keys():
                        if column not in [
                            'ipr_seq',
                            'ipc_seq',
                            'applicant_no',
                            'appl_no',
                        ]:
                            update_clauses.append(
                                f"{column} = VALUES({column})")

                    # ipr_seq 컬럼 추가
                    values.append(data['appl_no'])
                    columns = columns + ', ipr_seq'
                    if org_type == 0:
                        placeholders = placeholders + \
                            ', (SELECT ipr_seq FROM junesoft.tb24_300_corp_ipr_reg WHERE appl_no = %s)'
                    elif org_type == 1:
                        placeholders = placeholders + \
                            ', (SELECT ipr_seq FROM junesoft.tb24_400_univ_ipr_reg WHERE appl_no = %s)'

                elif service_type == 2:
                    columns = columns.removesuffix(', appl_no')
                    placeholders = placeholders.removesuffix(', %s')
                    for column in data.keys():
                        if column not in [
                            'ipr_seq',
                            'appl_no'
                        ]:
                            update_clauses.append(
                                f"{column} = VALUES({column})")
                        elif column == 'priority_nation':
                            update_clauses.append(
                                f"{column} = CASE WHEN {column} != VALUES({column}) THEN VALUES({
                                    column}) ELSE {column} END"
                            )

                    # ipr_seq 컬럼 추가
                    columns = columns + ', ipr_seq'
                    if org_type == 0:
                        placeholders = placeholders + \
                            ', (SELECT ipr_seq FROM junesoft.tb24_300_corp_ipr_reg WHERE appl_no = %s)'
                    elif org_type == 1:
                        placeholders = placeholders + \
                            ', (SELECT ipr_seq FROM junesoft.tb24_400_univ_ipr_reg WHERE appl_no = %s)'

                else:
                    print('\n정의되지 않은 data type입니다.')
                    return

                update_query = ', '.join(update_clauses)

                print(values)

                query = f"""
                INSERT INTO {self.db_name}.{table_name} ({columns})
                VALUES ({placeholders})
                ON DUPLICATE KEY UPDATE
                {update_query};
                """
                print(query)
                cursor.execute(query, values)

            self.connection.commit()
        except OperationalError as e:
            print(f"Error: {e}")
            self.connection.rollback()
        finally:
            if cursor:
                cursor.close()
            self.close()

    def fetch_corp_numbers(self) -> list[str]:
        """
        tb24_100_bizinfo 테이블에서 모든 corp_no 값을 조회합니다.

        Returns:
            list[str]: 조회된 corp_no 리스트
            None: 오류 발생 시

        Raises:
            OperationalError: 데이터베이스 연결 또는 쿼리 실행 중 오류 발생 시
        """
        cursor = None
        try:
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute("SELECT corp_no FROM tb24_100_bizinfo")
            rows = cursor.fetchall()

            return rows

        except OperationalError as e:
            print(f"기업번호 조회 실패: {str(e)}")
            return None
        finally:
            if cursor:
                cursor.close()
            self.close()

    def load_applicant_no(self,
                          table_to_load: list[str, list[str]],
                          org_info: tuple[list[dict], str]):
        self.connect()
        cursor = None
        table_name = table_to_load[0]
        org_data_list = org_info[0]

        try:
            self.connect()
            cursor = self.connection.cursor()
            for org_data in org_data_list:
                values = list(org_data.values())

                cursor.execute(
                    f"INSERT INTO {table_name} "
                    f"(applicant_no, applicant, corp_no, biz_no) "
                    f"VALUES (%s, %s, %s, %s)"
                    f"ON DUPLICATE KEY UPDATE "
                    f"applicant_no = VALUES(applicant_no)",
                    values
                )
            return self.connection.commit()
        except OperationalError as e:
            print(f"Error: {e}")
            self.connection.rollback()
            return
        finally:
            if cursor:
                cursor.close()
            self.close()

    def get_applicant_no(self, org_type: int) -> list[str]:
        """기관 유형에 따른 출원인 번호 목록을 조회합니다.

        Args:
            org_type (int): 기관 유형 코드
                - 0: 기업
                - 1: 대학
                - 2: 기업과 대학 모두

        Returns:
            list[str]: 출원인 번호 목록
            None: 데이터베이스 조회 실패 시

        Raises:
            OperationalError: 데이터베이스 연결 또는 쿼리 실행 중 오류 발생 시

        Note:
            - 기업 데이터는 tb24_200_corp_applicant 테이블에서 조회
            - 대학 데이터는 tb24_210_univ_applicant 테이블에서 조회
            - org_type이 2인 경우 두 테이블의 데이터를 UNION으로 통합 조회
        """
        cursor = None

        try:
            self.connect()
            cursor = self.connection.cursor()
            if org_type == 0:
                cursor.execute(
                    f"SELECT applicant_no FROM {
                        self.db_name}.tb24_200_corp_applicant"
                )
            elif org_type == 1:
                cursor.execute(
                    f"SELECT applicant_no FROM {
                        self.db_name}.tb24_210_univ_applicant"
                )
            elif org_type == 2:
                cursor.execute(
                    f"SELECT applicant_no FROM {
                        self.db_name}.tb24_200_corp_applicant "
                    f"UNION "
                    f"SELECT applicant_no FROM {
                        self.db_name}.tb24_210_univ_applicant;"
                )
            rows = cursor.fetchall()
            return list(row[0] for row in rows)
        except OperationalError as e:
            print(f"Error: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            self.close()