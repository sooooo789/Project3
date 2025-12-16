def check_breaker(isc, breaker_rating):
    if breaker_rating >= isc:
        return "적합", "차단기 정격이 단락전류를 초과함"
    else:
        return "부적합", "차단기 차단용량 부족"
