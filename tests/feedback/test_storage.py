"""
피드백 저장소에 대한 테스트를 구현하는 모듈입니다.
"""

import json
import os
import pytest
from pathlib import Path
from typing import Dict, List

from app.feedback.models import (
    Feedback,
    FeedbackType,
    FeedbackSeverity,
    FeedbackStatus
)
from app.feedback.storage import FeedbackStorage

def test_feedback_storage_initialization(temp_storage_dir):
    """FeedbackStorage 초기화 테스트"""
    storage = FeedbackStorage(temp_storage_dir)
    assert isinstance(storage, FeedbackStorage)
    assert storage.storage_dir == Path(temp_storage_dir)
    assert os.path.exists(temp_storage_dir)
    assert len(storage.get_all_feedbacks()) == 0

def test_save_feedback(feedback_storage, sample_feedback):
    """피드백 저장 테스트"""
    # 피드백 저장
    assert feedback_storage.save_feedback(sample_feedback) is True

    # 저장된 파일 확인
    file_path = feedback_storage.storage_dir / f"{sample_feedback.id}.json"
    assert file_path.exists()

    # 파일 내용 확인
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["id"] == sample_feedback.id
        assert data["type"] == sample_feedback.type.value
        assert data["severity"] == sample_feedback.severity.value

def test_get_feedback(feedback_storage, sample_feedback):
    """피드백 조회 테스트"""
    # 피드백 저장
    feedback_storage.save_feedback(sample_feedback)

    # 피드백 조회
    retrieved_feedback = feedback_storage.get_feedback(sample_feedback.id)
    assert retrieved_feedback is not None
    assert retrieved_feedback.id == sample_feedback.id
    assert retrieved_feedback.type == sample_feedback.type
    assert retrieved_feedback.severity == sample_feedback.severity

    # 존재하지 않는 ID로 조회
    assert feedback_storage.get_feedback("non-existent-id") is None

def test_get_all_feedbacks(populated_storage, multiple_feedbacks):
    """모든 피드백 조회 테스트"""
    all_feedbacks = populated_storage.get_all_feedbacks()
    assert len(all_feedbacks) == len(multiple_feedbacks)

    feedback_ids = {f.id for f in all_feedbacks}
    expected_ids = {f["id"] for f in multiple_feedbacks}
    assert feedback_ids == expected_ids

def test_update_feedback(feedback_storage, sample_feedback):
    """피드백 업데이트 테스트"""
    # 피드백 저장
    feedback_storage.save_feedback(sample_feedback)

    # 피드백 수정
    sample_feedback.title = "Updated Title"
    sample_feedback.description = "Updated Description"
    assert feedback_storage.update_feedback(sample_feedback) is True

    # 수정된 피드백 조회
    updated_feedback = feedback_storage.get_feedback(sample_feedback.id)
    assert updated_feedback is not None
    assert updated_feedback.title == "Updated Title"
    assert updated_feedback.description == "Updated Description"

def test_delete_feedback(feedback_storage, sample_feedback):
    """피드백 삭제 테스트"""
    # 피드백 저장
    feedback_storage.save_feedback(sample_feedback)
    file_path = feedback_storage.storage_dir / f"{sample_feedback.id}.json"
    assert file_path.exists()

    # 피드백 삭제
    assert feedback_storage.delete_feedback(sample_feedback.id) is True
    assert not file_path.exists()
    assert feedback_storage.get_feedback(sample_feedback.id) is None

    # 존재하지 않는 ID로 삭제 시도
    assert feedback_storage.delete_feedback("non-existent-id") is False

def test_get_feedbacks_by_plan(populated_storage, multiple_feedbacks):
    """계획별 피드백 조회 테스트"""
    plan_id = multiple_feedbacks[0]["plan_id"]
    feedbacks = populated_storage.get_feedbacks_by_plan(plan_id)

    assert len(feedbacks) == len(multiple_feedbacks)
    assert all(f.plan_id == plan_id for f in feedbacks)

def test_get_feedbacks_by_type(populated_storage):
    """유형별 피드백 조회 테스트"""
    # 실행 관련 피드백 조회
    execution_feedbacks = populated_storage.get_feedbacks_by_type(FeedbackType.EXECUTION)
    assert len(execution_feedbacks) == 1
    assert all(f.type == FeedbackType.EXECUTION for f in execution_feedbacks)

    # 성능 관련 피드백 조회
    performance_feedbacks = populated_storage.get_feedbacks_by_type(FeedbackType.PERFORMANCE)
    assert len(performance_feedbacks) == 1
    assert all(f.type == FeedbackType.PERFORMANCE for f in performance_feedbacks)

def test_get_feedbacks_by_severity(populated_storage):
    """중요도별 피드백 조회 테스트"""
    # 중간 중요도 피드백 조회
    medium_feedbacks = populated_storage.get_feedbacks_by_severity(FeedbackSeverity.MEDIUM)
    assert len(medium_feedbacks) == 2
    assert all(f.severity == FeedbackSeverity.MEDIUM for f in medium_feedbacks)

    # 높은 중요도 피드백 조회
    high_feedbacks = populated_storage.get_feedbacks_by_severity(FeedbackSeverity.HIGH)
    assert len(high_feedbacks) == 1
    assert all(f.severity == FeedbackSeverity.HIGH for f in high_feedbacks)

def test_get_feedbacks_by_status(populated_storage):
    """상태별 피드백 조회 테스트"""
    # 새로운 피드백 조회
    new_feedbacks = populated_storage.get_feedbacks_by_status(FeedbackStatus.NEW)
    assert len(new_feedbacks) > 0
    assert all(f.status == FeedbackStatus.NEW for f in new_feedbacks)

def test_clear_storage(populated_storage):
    """저장소 초기화 테스트"""
    # 초기화 전 상태 확인
    initial_count = len(populated_storage.get_all_feedbacks())
    assert initial_count > 0

    # 저장소 초기화
    assert populated_storage.clear_storage() is True
    assert len(populated_storage.get_all_feedbacks()) == 0
    assert len(list(populated_storage.storage_dir.glob("*.json"))) == 0

def test_get_storage_stats(populated_storage, multiple_feedbacks):
    """저장소 통계 조회 테스트"""
    stats = populated_storage.get_storage_stats()

    assert isinstance(stats, dict)
    assert "total_feedbacks" in stats
    assert "storage_size" in stats
    assert stats["total_feedbacks"] == len(multiple_feedbacks)
    assert stats["storage_size"] > 0

def test_storage_persistence(temp_storage_dir, sample_feedback):
    """저장소 영속성 테스트"""
    # 첫 번째 저장소 인스턴스로 피드백 저장
    storage1 = FeedbackStorage(temp_storage_dir)
    storage1.save_feedback(sample_feedback)

    # 두 번째 저장소 인스턴스로 피드백 조회
    storage2 = FeedbackStorage(temp_storage_dir)
    loaded_feedback = storage2.get_feedback(sample_feedback.id)

    assert loaded_feedback is not None
    assert loaded_feedback.id == sample_feedback.id
    assert loaded_feedback.type == sample_feedback.type
    assert loaded_feedback.severity == sample_feedback.severity

def test_invalid_storage_operations(feedback_storage):
    """잘못된 저장소 작업 테스트"""
    # 잘못된 경로에 저장 시도
    invalid_storage = FeedbackStorage("/invalid/path")
    feedback = Feedback(
        id="test-001",
        plan_id="plan-001",
        type=FeedbackType.EXECUTION,
        severity=FeedbackSeverity.MEDIUM,
        title="Test",
        description="Test"
    )

    # 저장 실패 시 False 반환
    assert invalid_storage.save_feedback(feedback) is False
