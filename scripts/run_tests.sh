#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 함수 정의
print_header() {
    echo -e "\n${YELLOW}=== $1 ===${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# 작업 디렉토리 설정
cd "$(dirname "$0")/.."

# 가상환경 확인
if [ -z "$VIRTUAL_ENV" ]; then
    print_error "가상환경이 활성화되지 않았습니다."
    echo "가상환경을 활성화하고 다시 시도해주세요."
    exit 1
fi

# 의존성 확인
print_header "의존성 확인"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    print_error "의존성 설치 실패"
    exit 1
fi
print_success "의존성 설치 완료"

# 테스트 실행
print_header "단위 테스트 실행"
pytest tests/feedback/test_pattern_matcher.py -v -m "not slow" --cov=app.feedback.pattern_matcher
if [ $? -ne 0 ]; then
    print_error "패턴 매칭 테스트 실패"
    exit 1
fi
print_success "패턴 매칭 테스트 완료"

pytest tests/feedback/test_priority_manager.py -v -m "not slow" --cov=app.feedback.priority_manager
if [ $? -ne 0 ]; then
    print_error "우선순위 관리 테스트 실패"
    exit 1
fi
print_success "우선순위 관리 테스트 완료"

pytest tests/feedback/test_result_tracker.py -v -m "not slow" --cov=app.feedback.result_tracker
if [ $? -ne 0 ]; then
    print_error "결과 추적 테스트 실패"
    exit 1
fi
print_success "결과 추적 테스트 완료"

pytest tests/feedback/test_suggester.py -v -m "not slow" --cov=app.feedback.suggester
if [ $? -ne 0 ]; then
    print_error "개선사항 제안 테스트 실패"
    exit 1
fi
print_success "개선사항 제안 테스트 완료"

# 통합 테스트 실행
print_header "통합 테스트 실행"
pytest tests/feedback -v -m "integration" --cov=app.feedback
if [ $? -ne 0 ]; then
    print_error "통합 테스트 실패"
    exit 1
fi
print_success "통합 테스트 완료"

# 커버리지 리포트 생성
print_header "커버리지 리포트 생성"
coverage html
if [ $? -ne 0 ]; then
    print_error "커버리지 리포트 생성 실패"
    exit 1
fi
print_success "커버리지 리포트 생성 완료"

# 결과 요약
print_header "테스트 결과 요약"
coverage report
print_success "모든 테스트가 성공적으로 완료되었습니다."
