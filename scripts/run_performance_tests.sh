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
pip install memory_profiler psutil numpy
if [ $? -ne 0 ]; then
    print_error "의존성 설치 실패"
    exit 1
fi
print_success "의존성 설치 완료"

# 성능 테스트 실행
print_header "패턴 매칭 성능 테스트"
pytest tests/feedback/test_performance.py::TestPatternMatcherPerformance -v
if [ $? -ne 0 ]; then
    print_error "패턴 매칭 성능 테스트 실패"
    exit 1
fi
print_success "패턴 매칭 성능 테스트 완료"

print_header "우선순위 관리 성능 테스트"
pytest tests/feedback/test_performance.py::TestPriorityManagerPerformance -v
if [ $? -ne 0 ]; then
    print_error "우선순위 관리 성능 테스트 실패"
    exit 1
fi
print_success "우선순위 관리 성능 테스트 완료"

print_header "결과 추적 성능 테스트"
pytest tests/feedback/test_performance.py::TestResultTrackerPerformance -v
if [ $? -ne 0 ]; then
    print_error "결과 추적 성능 테스트 실패"
    exit 1
fi
print_success "결과 추적 성능 테스트 완료"

print_header "개선사항 제안 성능 테스트"
pytest tests/feedback/test_performance.py::TestSuggesterPerformance -v
if [ $? -ne 0 ]; then
    print_error "개선사항 제안 성능 테스트 실패"
    exit 1
fi
print_success "개선사항 제안 성능 테스트 완료"

# 성능 프로파일링 리포트 생성
print_header "성능 프로파일링 리포트 생성"
python -m memory_profiler tests/feedback/test_performance.py > performance_report.txt
if [ $? -ne 0 ]; then
    print_error "성능 프로파일링 리포트 생성 실패"
    exit 1
fi
print_success "성능 프로파일링 리포트 생성 완료"

# 결과 요약
print_header "성능 테스트 결과 요약"
echo "성능 테스트 결과는 performance_report.txt 파일에서 확인할 수 있습니다."
print_success "모든 성능 테스트가 성공적으로 완료되었습니다."
