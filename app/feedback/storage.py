"""
피드백 저장 기능을 구현하는 모듈입니다.
이 모듈은 피드백을 영구적으로 저장하고 관리하는 기능을 제공합니다.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from app.feedback.models import (
    Feedback,
    FeedbackType,
    FeedbackSeverity,
    FeedbackStatus
)

class FeedbackStorage:
    """피드백 저장소 클래스"""

    def __init__(self, storage_dir: Union[str, Path] = "data/feedback"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Feedback] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """저장된 피드백을 캐시로 로드"""
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    feedback = self._dict_to_feedback(data)
                    self._cache[feedback.id] = feedback
            except Exception as e:
                print(f"Error loading feedback from {file_path}: {e}")

    def _dict_to_feedback(self, data: Dict) -> Feedback:
        """딕셔너리를 Feedback 객체로 변환"""
        # datetime 문자열을 datetime 객체로 변환
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])

        # 열거형 문자열을 열거형 객체로 변환
        data["type"] = FeedbackType(data["type"])
        data["severity"] = FeedbackSeverity(data["severity"])
        data["status"] = FeedbackStatus(data["status"])

        return Feedback(**data)

    def _feedback_to_dict(self, feedback: Feedback) -> Dict:
        """Feedback 객체를 딕셔너리로 변환"""
        data = feedback.to_dict()
        return data

    def save_feedback(self, feedback: Feedback) -> bool:
        """피드백 저장"""
        try:
            # 캐시에 저장
            self._cache[feedback.id] = feedback

            # 파일에 저장
            file_path = self.storage_dir / f"{feedback.id}.json"
            data = self._feedback_to_dict(feedback)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Error saving feedback {feedback.id}: {e}")
            return False

    def get_feedback(self, feedback_id: str) -> Optional[Feedback]:
        """피드백 조회"""
        return self._cache.get(feedback_id)

    def get_all_feedbacks(self) -> List[Feedback]:
        """모든 피드백 조회"""
        return list(self._cache.values())

    def update_feedback(self, feedback: Feedback) -> bool:
        """피드백 업데이트"""
        return self.save_feedback(feedback)

    def delete_feedback(self, feedback_id: str) -> bool:
        """피드백 삭제"""
        try:
            # 캐시에서 삭제
            if feedback_id in self._cache:
                del self._cache[feedback_id]

            # 파일 삭제
            file_path = self.storage_dir / f"{feedback_id}.json"
            if file_path.exists():
                file_path.unlink()

            return True
        except Exception as e:
            print(f"Error deleting feedback {feedback_id}: {e}")
            return False

    def get_feedbacks_by_plan(self, plan_id: str) -> List[Feedback]:
        """특정 계획의 모든 피드백 조회"""
        return [
            feedback for feedback in self._cache.values()
            if feedback.plan_id == plan_id
        ]

    def get_feedbacks_by_type(self, type: FeedbackType) -> List[Feedback]:
        """특정 유형의 모든 피드백 조회"""
        return [
            feedback for feedback in self._cache.values()
            if feedback.type == type
        ]

    def get_feedbacks_by_severity(self, severity: FeedbackSeverity) -> List[Feedback]:
        """특정 중요도의 모든 피드백 조회"""
        return [
            feedback for feedback in self._cache.values()
            if feedback.severity == severity
        ]

    def get_feedbacks_by_status(self, status: FeedbackStatus) -> List[Feedback]:
        """특정 상태의 모든 피드백 조회"""
        return [
            feedback for feedback in self._cache.values()
            if feedback.status == status
        ]

    def clear_storage(self) -> bool:
        """모든 피드백 삭제"""
        try:
            # 캐시 초기화
            self._cache.clear()

            # 모든 피드백 파일 삭제
            for file_path in self.storage_dir.glob("*.json"):
                file_path.unlink()

            return True
        except Exception as e:
            print(f"Error clearing storage: {e}")
            return False

    def get_storage_stats(self) -> Dict[str, int]:
        """저장소 통계 조회"""
        return {
            "total_feedbacks": len(self._cache),
            "storage_size": sum(
                os.path.getsize(f)
                for f in self.storage_dir.glob("*.json")
            )
        }
