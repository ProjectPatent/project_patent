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
import csv
from datetime import datetime

from dotenv import load_dotenv
from MySQLdb import OperationalError, connect
from tqdm import tqdm

from config.api_config import TABLES


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
        self.db_port = int(os.getenv("MYSQL_PORT"))
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
                database=self.db_name,
                port=self.db_port,
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

    def append_biz_no(
        self,
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
                f"SELECT applicant_no, biz_no FROM {table_metadata[0]}")
            rows = cursor.fetchall()

            biz_no_dict = {}
            for applicant_no, biz_no in rows:
                biz_no_dict[applicant_no] = biz_no

            for data_seq, data in tqdm(
                enumerate(dataset), desc="사업자등록번호 추가 중", unit="rows"
            ):
                applicant_no = dataset[data_seq]["applicant_no"]
                if applicant_no in biz_no_dict:
                    biz_no = biz_no_dict[applicant_no]
                    dataset[data_seq]["biz_no"] = biz_no
                else:
                    dataset[data_seq]["biz_no"] = None

            return dataset
        except OperationalError as e:
            print("Error:", e)
            return None
        finally:
            if cursor:
                cursor.close()
            self.close()

    def insert_data(
        self,
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
                columns = ", ".join(data.keys())
                placeholders = ", ".join(["%s"] * len(data))
                query = f"INSERT INTO {self.db_name}.{table_metadata[0]}({columns}) VALUES({placeholders})"

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

    def upsert_data(
        self,
        org_type: int,
        service_type: int,
        table_to_load: list[str, list[str]],
        dataset: list[dict],
        batch_size: int = 1000,
        ipr_seqs: dict[str, int] = None,
    ):
        cursor = None
        try:
            self.connect()
            cursor = self.connection.cursor()

            current_batch = []
            query = None
            total_processed = 0

            table_name = table_to_load[0]

            # CSV 저장을 위한 디렉토리 생성
            os.makedirs("./var", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            batch_count = 0

            desc_org_type = "기업" if org_type == 0 else "대학"
            desc_service_type = (
                "4권리"
                if service_type == 0
                else "IPC/CPC" if service_type == 1 else "우선권"
            )

            for data in tqdm(
                dataset,
                desc=f"{desc_org_type} {desc_service_type} 데이터 처리 중",
                unit="rows",
            ):
                values = []
                if service_type == 0:
                    for value in data.values():
                        values.append(value)
                    query = f"""
                    INSERT INTO {table_name} (
                        applicant_no, title, applicant, main_ipc, appl_no, ipr_code, appl_date, open_no, 
                        open_date, reg_no, reg_date, pub_no, pub_date, legal_status_desc, img_url, inventor, 
                        agent, int_appl_no, int_appl_date, int_open_no, int_open_date, exam_flag, exam_date, 
                        claim_cnt, abstract, biz_no
                        ) 
                        VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                            %s, %s, %s, %s, %s, %s
                        ) 
                        ON DUPLICATE KEY UPDATE 
                            title = VALUES(title),
                            applicant = VALUES(applicant),
                            main_ipc = VALUES(main_ipc),
                            ipr_code = VALUES(ipr_code),
                            appl_date = VALUES(appl_date),
                            open_no = VALUES(open_no),
                            open_date = VALUES(open_date),
                            reg_no = VALUES(reg_no),
                            reg_date = VALUES(reg_date),
                            pub_no = VALUES(pub_no),
                            pub_date = VALUES(pub_date),
                            int_appl_no = VALUES(int_appl_no),
                            int_appl_date = VALUES(int_appl_date),
                            int_open_no = VALUES(int_open_no),
                            int_open_date = VALUES(int_open_date),
                            legal_status_desc = CASE 
                                WHEN legal_status_desc != VALUES(legal_status_desc) 
                                THEN VALUES(legal_status_desc) 
                                ELSE legal_status_desc 
                                END,
                            exam_flag = VALUES(exam_flag),
                            exam_date = VALUES(exam_date),
                            claim_cnt = VALUES(claim_cnt),
                            abstract = VALUES(abstract),
                            biz_no = VALUES(biz_no),
                            img_url = VALUES(img_url),
                            inventor = VALUES(inventor),
                            agent = VALUES(agent);
                    """

                elif service_type == 1:
                    for value in data.values():
                        values.append(value)
                    # values.append(ipr_seqs[data['appl_no']])
                    values.append(None)
                    ipr_table = (
                        "tb24_300_corp_ipr_reg"
                        if org_type == 0
                        else "tb24_400_univ_ipr_reg"
                    )

                    # VALUES (%s, %s, %s, (SELECT ipr_seq FROM {ipr_table} WHERE appl_no = %s))
                    query = f"""
                    INSERT INTO {table_name} (appl_no, ipc_cpc, ipc_cpc_code, ipr_seq)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        ipr_seq = VALUES(ipr_seq),
                        appl_no = VALUES(appl_no),
                        ipc_cpc = VALUES(ipc_cpc),
                        ipc_cpc_code = VALUES(ipc_cpc_code)
                    """

                elif service_type == 2:
                    for value in data.values():
                        values.append(value)
                    values.append(ipr_seqs[data["appl_no"]])
                    values.pop(-2)

                    # VALUES (%s, %s, %s, (SELECT ipr_seq FROM {ipr_table} WHERE appl_no = %s))
                    query = f"""
                    INSERT INTO {table_name} (applicant_no, priority_date, priority_no, ipr_seq)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        applicant_no = VALUES(applicant_no),
                        priority_no = VALUES(priority_no),
                        priority_date = VALUES(priority_date),
                        ipr_seq = VALUES(ipr_seq)
                    """

                current_batch.append(tuple(values))

                if len(current_batch) >= batch_size:
                    # CSV 파일로 현재 배치 저장
                    batch_count += 1
                    # csv_filename = f'./var/batch_{timestamp}_{batch_count}.csv'
                    # with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                    #     writer = csv.writer(f)
                    #     writer.writerows(current_batch)

                    cursor.executemany(query, current_batch)
                    self.connection.commit()
                    total_processed += len(current_batch)
                    # print(f"{total_processed} rows processed - Saved to {csv_filename}")

                    current_batch = []

            if current_batch:
                # 마지막 배치 저장
                batch_count += 1
                # csv_filename = f'./var/batch_{timestamp}_{batch_count}.csv'
                # with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                #     writer = csv.writer(f)
                #     writer.writerows(current_batch)

                cursor.executemany(query, current_batch)
                self.connection.commit()
                total_processed += len(current_batch)
                # print(f"Total {total_processed} rows processed - Final batch saved to {csv_filename}")

        except OperationalError as e:
            print(f"Error: {e}")
            self.connection.rollback()
        finally:
            if cursor:
                cursor.close()
            self.close()

    def fetch_corp_no(self) -> list[str]:
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
            cursor.execute(
                f"SELECT corp_no FROM {TABLES['COMMON']['BIZ_INFO'][0]}")
            rows = cursor.fetchall()

            return list(row[0] for row in rows)

        except OperationalError as e:
            print(f"법인등록번호 조회 실패: {str(e)}")
            return None
        finally:
            if cursor:
                cursor.close()
            self.close()

    def fetch_biz_no(self) -> list[str]:
        """
        tb24_100_bizinfo 테이블에서 모든 biz_no 값을 조회합니다.

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
            cursor.execute(
                f"SELECT biz_no FROM {TABLES['COMMON']['BIZ_INFO'][0]}")
            rows = cursor.fetchall()

            return list(row[0] for row in rows)

        except OperationalError as e:
            print(f"사업자등록번호 조회 실패: {str(e)}")
            return None
        finally:
            if cursor:
                cursor.close()
            self.close()

    def load_applicant_no(
        self, table_to_load: list[str, list[str]], org_info: tuple[list[dict], str]
    ):
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
                    values,
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

    def get_applicant_no(self, org_type: str) -> list[str]:
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
        table_name = TABLES[org_type.upper()]['APPLICANT'][0]

        try:
            self.connect()
            cursor = self.connection.cursor()
            if org_type in ['corp', 'univ']:
                cursor.execute(
                    f"SELECT applicant_no FROM {table_name}"
                )
            elif org_type == 'all':
                cursor.execute(
                    f"SELECT applicant_no FROM {TABLES['CORP']['APPLICANT'][0]} "
                    f"UNION "
                    f"SELECT applicant_no FROM {TABLES['UNIV']['APPLICANT'][0]}"
                )
            else:
                raise ValueError(f"지원하지 않는 org_type: {org_type}")
            rows = cursor.fetchall()
            return list(row[0] for row in rows)
        except OperationalError as e:
            print(f"Error: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            self.close()

    def get_ipr_seqs(self, org_type: int) -> dict[str, int]:
        cursor = None
        try:
            self.connect()
            cursor = self.connection.cursor()
            if org_type == 0:
                cursor.execute(
                    "SELECT appl_no, ipr_seq FROM tb24_300_corp_ipr_reg")
            elif org_type == 1:
                cursor.execute(
                    "SELECT appl_no, ipr_seq FROM tb24_400_univ_ipr_reg")
            rows = cursor.fetchall()
            return dict(rows)
        except OperationalError as e:
            print(f"Error: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            self.close()
