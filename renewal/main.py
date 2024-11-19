import asyncio

from dotenv import load_dotenv

load_dotenv()

from api.api_query_generator import APIQueryGenerator
from api.api_fetcher import APIFetcher

def main():
    api_query_generator = APIQueryGenerator()

    asyncio.run(fetch_corp_applicant_no(api_query_generator=api_query_generator))

async def fetch_corp_applicant_no(api_query_generator: APIQueryGenerator):
    requests_list = api_query_generator.generate_applicant_no_fetch_query()
    api_fetcher = APIFetcher('corp', 'applicant_no', requests_list)
    await api_fetcher.start()

if __name__ == "__main__":
    main()
