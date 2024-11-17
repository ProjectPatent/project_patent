from dotenv import load_dotenv
from loguru import logger

from api.api_query_generator import APIQueryGenerator
from api.api_fetcher import APIFetcher
from db.mysql_loader import Database

load_dotenv()


def main():
    api_query_generator = APIQueryGenerator()
    requests_list = api_query_generator.generate_ipr_fetch_query(
        org_type='corp', ipr_mode='patuti')
    api_fetcher = APIFetcher(
        org_type='corp', ipr_mode='patuti', requests_list=requests_list)
    print(requests_list)


if __name__ == "__main__":
    main()
    print("main end")
