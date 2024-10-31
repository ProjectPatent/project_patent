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
from prometheus_client import start_http_server, Counter, Summary, Gauge, Info
from urllib3.util.ssl_ import create_urllib3_context

class PatentMetrics:
    def __init__(self):
        self.api_requests = Counter(
            'patent_api_requests_total', 
            'Total number of API requests made'
        )
        self.api_errors = Counter(
            'patent_api_errors_total', 
            'Total number of API request errors'
        )
        self.xml_parse_errors = Counter(
            'patent_xml_parse_errors_total', 
            'Total number of XML parsing errors'
        )
        self.successful_downloads = Counter(
            'patent_successful_downloads_total', 
            'Total number of successfully downloaded patents'
        )
        
        self.api_request_duration = Summary(
            'patent_api_request_duration_seconds', 
            'Time spent in API requests'
        )
        self.xml_processing_duration = Summary(
            'patent_xml_processing_duration_seconds', 
            'Time spent processing XML'
        )
        self.db_operation_duration = Summary(
            'patent_db_operation_duration_seconds', 
            'Time spent in database operations'
        )
        
        self.processing_progress = Gauge(
            'patent_processing_progress_percent', 
            'Current progress of patent processing'
        )
        self.active_connections = Gauge(
            'patent_active_connections',
            'Number of active connections'
        )
        self.api_total_duration = Gauge(
            'patent_api_total_duration_seconds',
            'Total time from start to finish of API processing'
        )
        self.memory_usage = Gauge(
            'patent_memory_usage_bytes',
            'Current memory usage'
        )

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

class XMLBuilder:
    def __init__(self):
        self.root = ET.Element("patentCorpData")
        self.items = ET.SubElement(self.root, "items")
        
    async def add_patent_data(self, xml_string: str, applicant_no: str) -> bool:
        try:
            source_root = ET.fromstring(xml_string)
            for source_item in source_root.findall('.//item'):
                new_item = ET.SubElement(self.items, "item")
                
                # applicant_no 추가
                applicant_no_elem = ET.SubElement(new_item, "applicantNo")
                applicant_no_elem.text = applicant_no
                
                fields = [
                    'registerStatus', 'inventionTitle', 'ipcNumber', 
                    'registerNumber', 'registerDate', 'applicationNumber',
                    'applicationDate', 'openNumber', 'openDate',
                    'publicationNumber', 'publicationDate', 'drawing',
                    'applicantName'
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

class AsyncPatentDownloader2:
    def __init__(self):
        # Prometheus 메트릭 서버 시작
        start_http_server(8000, addr='0.0.0.0')
        self.metrics = PatentMetrics()
        
        # 환경변수 로드 및 검증
        load_dotenv()
        self.validate_env()
        
        # 설정값 로드
        self.service_key = os.getenv('KIPRIS_API_KEY')
        self.batch_size = int(os.getenv('BATCH_SIZE'))
        self.base_url = "http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getAdvancedSearch"
        
        # DB 설정
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'db': os.getenv('DB_NAME'),
            'port': int(os.getenv('DB_PORT', 3306))
        }
        
        # 세션 및 연결 풀
        self.session = None
        self.pool = None
        self.start_time = None
        
        # XML 빌더
        self.xml_builder = XMLBuilder()
        
        # 로깅 설정
        self.setup_logging()
        
        # 출력 디렉토리 생성
        os.makedirs('../data', exist_ok=True)

    def validate_env(self):
        required_vars = ['KIPRIS_API_KEY', 'DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME', 'BATCH_SIZE']
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('patent_download.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

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
                    'User-Agent': 'PatentDownloader/1.0'
                }
            )

    async def init_db_pool(self):
        """DB 연결 풀 초기화"""
        if self.pool is None:
            self.pool = await aiomysql.create_pool(
                **self.db_config,
                maxsize=20,
                minsize=5,
                pool_recycle=3600,
                autocommit=True
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

    async def fetch_patent_data(self, applicant_no: str) -> Optional[str]:
        """특허 데이터 조회"""
        with self.metrics.api_request_duration.time():
            if self.session is None or self.session.closed:
                await self.init_session()

            self.metrics.api_requests.inc()
            self.metrics.active_connections.inc()
            
            try:
                params = {
                    'applicant': applicant_no,
                    'ServiceKey': self.service_key
                }
                
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

    async def process_single_applicant(self, applicant_no: str):
        """단일 출원인 처리"""
        try:
            xml_content = await self.fetch_patent_data(applicant_no)
            if not xml_content:
                return
            
            with self.metrics.xml_processing_duration.time():
                if await self.xml_builder.add_patent_data(xml_content, applicant_no):
                    self.metrics.successful_downloads.inc()
                else:
                    self.metrics.xml_parse_errors.inc()
                    
        except Exception as e:
            self.logger.error(f"Error processing {applicant_no}: {e}")

    async def process_batch(self, offset: int, total_count: int) -> bool:
        """배치 처리"""
        applicant_numbers, _ = await self.get_applicant_numbers(offset)
        if not applicant_numbers:
            return False

        # 청크 단위로 분할 처리
        chunk_size = 10
        for i in range(0, len(applicant_numbers), chunk_size):
            chunk = applicant_numbers[i:i + chunk_size]
            tasks = [self.process_single_applicant(no) for no in chunk]
            await asyncio.gather(*tasks)
            
            # 진행률 업데이트
            progress = ((offset + i + len(chunk)) / total_count) * 100
            self.metrics.processing_progress.set(progress)
            
            # 총 소요 시간 업데이트
            if self.start_time:
                current_duration = time.time() - self.start_time
                self.metrics.api_total_duration.set(current_duration)
            
            # 메모리 사용량 모니터링
            import psutil
            process = psutil.Process()
            self.metrics.memory_usage.set(process.memory_info().rss)
            
        return True

    async def process_all(self):
        """전체 처리"""
        try:
            self.start_time = time.time()
            
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
            output_path = f'data/{date_str}_patent_utility_univ.xml'
            self.xml_builder.save(output_path)
            
            # 최종 메트릭 업데이트
            self.metrics.processing_progress.set(100)
            final_duration = time.time() - self.start_time
            self.metrics.api_total_duration.set(final_duration)
            
            self.logger.info(f"All processing completed. Output saved to: {output_path}")
            self.logger.info(f"Total processing time: {final_duration:.2f} seconds")
            
        except KeyboardInterrupt:
            self.logger.info("Processing interrupted by user")
            date_str = datetime.now().strftime('%Y%m%d')
            output_path = f'data/{date_str}_patent_utility_univ_interrupted.xml'
            self.xml_builder.save(output_path)
            
        except Exception as e:
            self.logger.error(f"Processing failed: {e}")
            raise
            
        finally:
            # 리소스 정리
            if self.session and not self.session.closed:
                await self.session.close()
            if self.pool:
                self.pool.close()
                await self.pool.wait_closed()

async def main():
    try:
        downloader = AsyncPatentDownloader2()
        await downloader.process_all()
    except Exception as e:
        logging.error(f"Application failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())