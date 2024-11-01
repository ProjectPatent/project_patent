import os
import time
import aiomysql
import aiohttp
import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime
import logging
from typing import Optional, List, Tuple, Dict, Any
from dotenv import load_dotenv
from prometheus_client import start_http_server, Counter, Summary, Gauge
from urllib3.util.ssl_ import create_urllib3_context

from config.config import api_input_params

class DesignMetrics:
    def __init__(self):
        self.api_requests = Counter(
            'design_univ_api_requests_total', 
            'Total number of API requests made'
        )
        self.api_errors = Counter(
            'design_univ_api_errors_total', 
            'Total number of API request errors'
        )
        self.xml_parse_errors = Counter(
            'design_univ_xml_parse_errors_total', 
            'Total number of XML parsing errors'
        )
        self.successful_downloads = Counter(
            'design_univ_successful_downloads_total', 
            'Total number of successfully downloaded designs'
        )
        
        self.api_request_duration = Summary(
            'design_univ_api_request_duration_seconds', 
            'Time spent in API requests'
        )
        self.xml_processing_duration = Summary(
            'design_univ_xml_processing_duration_seconds', 
            'Time spent processing XML'
        )
        self.db_operation_duration = Summary(
            'design_univ_db_operation_duration_seconds', 
            'Time spent in database operations'
        )
        
        self.processing_progress = Gauge(
            'design_univ_processing_progress_percent', 
            'Current progress of design processing'
        )
        self.active_connections = Gauge(
            'design_univ_active_connections', 
            'Number of active connections'
        )

        self.api_total_duration = Gauge(
            'design_univ_api_total_duration_seconds',
            'Total time from start to finish of API processing'
        )

class DesignXMLBuilder:
    def __init__(self):
        self.root = ET.Element("designInfoData")
        self.items = ET.SubElement(self.root, "items")
        
    async def add_design_data(self, xml_string: str, applicant_no: str) -> bool:
        try:
            source_root = ET.fromstring(xml_string)
            for source_item in source_root.findall('.//item'):
                new_item = ET.SubElement(self.items, "item")
                
                # applicant_no 추가
                applicant_no_elem = ET.SubElement(new_item, "applicantNo")
                applicant_no_elem.text = applicant_no
                
                fields = [
                    'articleName',
                    'applicantName',
                    'inventorName',
                    'agentName',
                    'applicationNumber',
                    'applicationDate',
                    'openNumber',
                    'openDate',
                    'registrationNumber',
                    'registrationDate',
                    'publicationNumber',
                    'publicationDate',
                    'applicationStatus',
                    'priorityNumber',
                    'priorityDate'
                ]
                
                for field in fields:
                    elem = source_item.find(field)
                    if elem is not None:
                        field_elem = ET.SubElement(new_item, field)
                        field_elem.text = elem.text
                        
            return True
        except ET.ParseError:
            return False
            
    def save(self, filepath: str):
        tree = ET.ElementTree(self.root)
        ET.indent(tree, space="  ", level=0)
        tree.write(filepath, encoding='utf-8', xml_declaration=True)

class TLSAdapter(aiohttp.TCPConnector):
    """TLS 연결 최적화를 위한 커스텀 어댑터"""
    def __init__(self):
        ssl_context = create_urllib3_context(
            ciphers='ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20'
        )
        super().__init__(
            ssl=ssl_context,
            keepalive_timeout=60,
            limit=100,
            enable_cleanup_closed=True,
            force_close=False,
            limit_per_host=50
        )

class AsyncDesignDownloaderUniv:
    def __init__(self):
        # Prometheus 메트릭 서버 시작
        self.metrics = DesignMetrics()
        
        # 환경변수 로드 및 검증
        load_dotenv()
        self.validate_env()
        
        # 설정값 로드
        self.service_key = os.getenv('KIPRIS_API_KEY')
        self.batch_size = int(os.getenv('BATCH_SIZE'))
        self.base_url = "http://plus.kipris.or.kr/kipo-api/kipi/designInfoSearchService/getAdvancedSearch"
        
        # DB 설정
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'db': os.getenv('DB_NAME'),
            'port': int(os.getenv('DB_PORT', 3306))
        }
        
        # API 세션 관련
        self.session = None
        self.request_interval = 1.0 / float(self.batch_size)
        self.last_request_time = 0
        
        # XML 빌더
        self.xml_builder = DesignXMLBuilder()
        
        # DB 풀
        self.pool = None
        
        # 로깅 설정
        self.setup_logging()
        
        # 출력 디렉토리 생성
        os.makedirs('../data', exist_ok=True)

    def validate_env(self):
        required_vars = ['KIPRIS_API_KEY', 'DB_HOST', 'DB_USER', 'DB_PASSWORD', 'BATCH_SIZE']
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('design_download.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    async def init_db_pool(self):
        """DB 연결 풀 초기화"""
        if self.pool is None:
            self.pool = await aiomysql.create_pool(**self.db_config)

    async def init_session(self):
        """API 세션 초기화"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=3.05, sock_read=27)
            self.session = aiohttp.ClientSession(
                connector=TLSAdapter(),
                timeout=timeout,
                headers={
                    'Connection': 'keep-alive',
                    'Keep-Alive': 'timeout=60, max=1000',
                    'User-Agent': 'DesignDownloader/1.0'
                }
            )

    async def get_applicant_numbers(self, offset: int = 0) -> Tuple[List[str], int]:
        """출원인 번호 조회"""
        with self.metrics.db_operation_duration.time():
            if self.pool is None:
                await self.init_db_pool()

            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 전체 건수 조회
                    await cursor.execute("""
                        SELECT COUNT(DISTINCT applicant_no) FROM (
                            SELECT applicant_no FROM tb24_210_univ_applicant 
                            WHERE applicant_no IS NOT NULL
                        ) as total
                    """)
                    total_count = (await cursor.fetchone())[0]
                    
                    # 페이징 처리된 조회
                    await cursor.execute("""
                        SELECT applicant_no FROM tb24_210_univ_applicant 
                        WHERE applicant_no IS NOT NULL
                        LIMIT %s OFFSET %s
                    """, (self.batch_size, offset))
                    
                    results = await cursor.fetchall()
                    return [row[0] for row in results], total_count

    async def fetch_design_data(self, applicant_no: str) -> Optional[str]:
        """디자인 데이터 조회"""
        with self.metrics.api_request_duration.time():
            if self.session is None or self.session.closed:
                await self.init_session()

            self.metrics.api_requests.inc()
            self.metrics.active_connections.inc()
            
            try:
                params = {
                    'applicantName': applicant_no,
                    'ServiceKey': self.service_key
                }
                params.update(api_input_params['design'])
                
                async with self.session.get(self.base_url, params=params) as response:
                    if response.status != 200:
                        self.logger.error(f"API request failed for {applicant_no}: {response.status}")
                        self.metrics.api_errors.inc()
                        return None
                        
                    return await response.text()
                    
            except Exception as e:
                self.logger.error(f"API request error for {applicant_no}: {e}")
                self.metrics.api_errors.inc()
                return None
            finally:
                self.metrics.active_connections.dec()

    async def process_batch(self, offset: int, total_count: int) -> bool:
        """배치 처리"""
        applicant_numbers, _ = await self.get_applicant_numbers(offset)
        if not applicant_numbers:
            return False
        
        tasks = []
        for i, applicant_no in enumerate(applicant_numbers):
            progress = ((offset + i) / total_count) * 100
            self.metrics.processing_progress.set(progress)
            
            tasks.append(self.process_single_applicant(applicant_no))
            
        await asyncio.gather(*tasks)
        return True

    async def process_single_applicant(self, applicant_no: str):
        """단일 출원인 처리"""
        try:
            xml_content = await self.fetch_design_data(applicant_no)
            if not xml_content:
                return
            
            with self.metrics.xml_processing_duration.time():
                if await self.xml_builder.add_design_data(xml_content, applicant_no):
                    self.metrics.successful_downloads.inc()
                else:
                    self.metrics.xml_parse_errors.inc()
                    
        except Exception as e:
            self.logger.error(f"Error processing {applicant_no}: {e}")

    async def process_all(self):
        """전체 처리"""
        try:
            # API 처리 시작 시간
            api_start_time = time.time()
            self.logger.info("API processing started")

            await self.init_db_pool()
            await self.init_session()
            
            _, total_count = await self.get_applicant_numbers(0)
            self.logger.info(f"Total records to process: {total_count}")
            
            offset = 0
            batch_no = 1
            
            while True:
                self.logger.info(f"Processing batch {batch_no} (offset: {offset})")
                if not await self.process_batch(offset, total_count):
                    break
                
                offset += self.batch_size
                batch_no += 1
            
            date_str = datetime.now().strftime('%Y%m%d')
            output_path = f'data/{date_str}_design_univ.xml'
            self.xml_builder.save(output_path)
            
            self.metrics.processing_progress.set(100)
            self.logger.info(f"All processing completed. Output saved to: {output_path}")
            
            api_total_duration = time.time() - api_start_time
            self.metrics.api_total_duration.set(api_total_duration)
            
            self.logger.info(
                f"API processing completed in {api_total_duration:.2f} seconds. "
                f"Average rate: {offset/api_total_duration:.2f} requests/second"
            )

        except KeyboardInterrupt:
            self.logger.info("Processing interrupted by user")
            date_str = datetime.now().strftime('%Y%m%d')
            output_path = f'data/{date_str}_design_univ_interrupted.xml'
            self.xml_builder.save(output_path)
            
        except Exception as e:
            self.logger.error(f"Processing failed: {e}")
            raise
            
        finally:
            if self.session and not self.session.closed:
                await self.session.close()
            if self.pool:
                self.pool.close()
                await self.pool.wait_closed()
