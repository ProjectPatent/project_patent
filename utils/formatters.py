def format_corporation_no(corp_no_list: list[str]) -> list[str]:
    """
    법인등록번호를 형식화하는 함수

    Args:
    corp_no_list (list[str]): 13자리 법인등록번호 리스트

    Returns:
    str: '000000-0000000' 형식으로 변환된 기업번호
    """
    formatted_corp_no_list = []
    for corp_no in corp_no_list:
        formatted_corp_no_list.append("-".join([corp_no[:6], corp_no[6:]]))
    return formatted_corp_no_list


def format_biz_no(biz_no_list: list[str]) -> list[str]:
    """
    사업자등록번호를 형식화하는 함수

    Args:
    biz_no_list (list[str]): 10자리 사업자등록번호 리스트

    Returns:
    str: '000-00-00000' 형식으로 변환된 기업번호
    """
    formatted_biz_no_list = []
    for biz_no in biz_no_list:
        formatted_biz_no_list.append(
            "-".join([biz_no[:3], biz_no[3:5], biz_no[5:]])
        )
    return formatted_biz_no_list
