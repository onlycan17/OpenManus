"""
개선사항 적용 결과를 추적하는 모듈입니다.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from functools import lru_cache
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
import numpy as np

from .models import (
    Feedback,
    FeedbackType,
    FeedbackSeverity,
    ImprovementSuggestion,
    ImprovementStatus
)

class ResultTracker:
    """
    개선사항 적용 결과를 추적하는 클래스입니다.
    병렬 처리와 캐싱을 통해 성능을 최적화합니다.
    """

    def __init__(self):
        """ResultTracker 객체를 초기화합니다."""
        self.tracking_window = timedelta(days=30)  # 추적 기간
        self.success_threshold = 0.7  # 성공 판단 임계값
        self.metrics_history: Dict[str, List[Dict]] = defaultdict(list)  # 메트릭 이력
        self.feedback_history: Dict[str, List[Feedback]] = defaultdict(list)  # 피드백 이력

        # 병렬 처리를 위한 설정
        self.max_workers = mp.cpu_count()

    def _generate_cache_key(self, suggestion_id: str, timestamp: datetime) -> str:
        """캐시 키를 생성합니다."""
        return f"{suggestion_id}|{timestamp.isoformat()}"

    def track_implementation(
        self,
        suggestion: ImprovementSuggestion,
        before_metrics: Dict,
        after_metrics: Dict
    ) -> Dict:
        """
        개선사항 구현 전후의 메트릭을 비교하여 결과를 추적합니다.
        병렬 처리를 통해 성능을 최적화합니다.

        Args:
            suggestion: 추적할 개선사항
            before_metrics: 구현 전 메트릭
            after_metrics: 구현 후 메트릭

        Returns:
            Dict: 추적 결과
        """
        # 메트릭 이력 저장
        current_time = datetime.now()
        self.metrics_history[suggestion.id].append({
            "timestamp": current_time,
            "metrics": after_metrics,
            "type": "after_implementation"
        })

        # 공통 메트릭 키 추출
        common_metrics = set(before_metrics.keys()) & set(after_metrics.keys())
        numeric_metrics = {
            metric_name: (before_metrics[metric_name], after_metrics[metric_name])
            for metric_name in common_metrics
            if isinstance(before_metrics[metric_name], (int, float)) and
               isinstance(after_metrics[metric_name], (int, float))
        }

        # 넘파이 배열로 변환하여 계산
        if numeric_metrics:
            before_values = np.array([v[0] for v in numeric_metrics.values()])
            after_values = np.array([v[1] for v in numeric_metrics.values()])

            # 0으로 나누기 방지
            with np.errstate(divide='ignore', invalid='ignore'):
                improvement_rates = np.where(
                    before_values != 0,
                    (after_values - before_values) / np.abs(before_values),
                    np.where(after_values > 0, 1.0, 0.0)
                )

            improvements = {
                name: {
                    "before": float(before_values[i]),
                    "after": float(after_values[i]),
                    "improvement_rate": float(improvement_rates[i])
                }
                for i, name in enumerate(numeric_metrics.keys())
            }
        else:
            improvements = {}

        # 전체 개선 점수 계산
        overall_score = self._calculate_overall_score(improvements)

        return {
            "suggestion_id": suggestion.id,
            "timestamp": current_time.isoformat(),
            "improvements": improvements,
            "overall_score": overall_score,
            "success": overall_score >= self.success_threshold
        }

    @lru_cache(maxsize=128)
    def track_feedback_changes(
        self,
        suggestion: ImprovementSuggestion,
        feedbacks: Tuple[Feedback, ...]  # 캐시를 위해 튜플 사용
    ) -> Dict:
        """
        개선사항 구현 후의 피드백 변화를 추적합니다.
        병렬 처리와 캐싱을 통해 성능을 최적화합니다.

        Args:
            suggestion: 추적할 개선사항
            feedbacks: 관련 피드백 목록 (튜플)

        Returns:
            Dict: 피드백 변화 분석 결과
        """
        # 피드백 이력 저장
        self.feedback_history[suggestion.id].extend(feedbacks)

        # 최근 피드백 필터링
        now = datetime.now()
        recent_feedbacks = tuple(f for f in feedbacks if now - f.created_at <= self.tracking_window)

        if not recent_feedbacks:
            return {
                "total_feedbacks": 0,
                "type_distribution": {},
                "severity_distribution": {},
                "daily_counts": {},
                "trend": {"direction": "stable", "confidence": 0.0}
            }

        # 병렬로 각 분석 작업 실행
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_type = executor.submit(self._analyze_type_distribution, recent_feedbacks)
            future_severity = executor.submit(self._analyze_severity_distribution, recent_feedbacks)
            future_daily = executor.submit(self._analyze_daily_counts, recent_feedbacks)
            future_trend = executor.submit(self._analyze_feedback_trend, recent_feedbacks)

            # 결과 수집
            analysis = {
                "total_feedbacks": len(recent_feedbacks),
                "type_distribution": future_type.result(),
                "severity_distribution": future_severity.result(),
                "daily_counts": future_daily.result(),
                "trend": future_trend.result()
            }

        return analysis

    @lru_cache(maxsize=128)
    def _analyze_type_distribution(self, feedbacks: Tuple[Feedback, ...]) -> Dict[str, int]:
        """피드백 유형 분포를 분석합니다."""
        types = np.array([f.type.value for f in feedbacks])
        unique_types, counts = np.unique(types, return_counts=True)
        return dict(zip(unique_types, counts))

    @lru_cache(maxsize=128)
    def _analyze_severity_distribution(self, feedbacks: Tuple[Feedback, ...]) -> Dict[str, int]:
        """피드백 심각도 분포를 분석합니다."""
        severities = np.array([f.severity.value for f in feedbacks])
        unique_severities, counts = np.unique(severities, return_counts=True)
        return dict(zip(unique_severities, counts))

    @lru_cache(maxsize=128)
    def _analyze_daily_counts(self, feedbacks: Tuple[Feedback, ...]) -> Dict[str, int]:
        """일별 피드백 수를 분석합니다."""
        dates = np.array([f.created_at.date().isoformat() for f in feedbacks])
        unique_dates, counts = np.unique(dates, return_counts=True)
        return dict(zip(unique_dates, counts))

    @lru_cache(maxsize=128)
    def _analyze_feedback_trend(self, feedbacks: Tuple[Feedback, ...]) -> Dict:
        """
        피드백 트렌드를 분석합니다.
        시계열 분석을 통해 추세를 파악합니다.
        """
        if not feedbacks:
            return {"direction": "stable", "confidence": 0.0}

        # 일별 피드백 수 계산
        daily_counts = self._analyze_daily_counts(feedbacks)
        if len(daily_counts) < 2:
            return {"direction": "stable", "confidence": 0.0}

        # 시계열 데이터 생성
        dates = sorted(daily_counts.keys())
        counts = np.array([daily_counts[date] for date in dates])

        # 선형 회귀를 통한 추세 분석
        x = np.arange(len(counts))
        A = np.vstack([x, np.ones(len(x))]).T
        slope, _ = np.linalg.lstsq(A, counts, rcond=None)[0]

        # 추세 방향과 신뢰도 계산
        direction = "decreasing" if slope < -0.1 else "increasing" if slope > 0.1 else "stable"

        # 결정계수(R²) 계산으로 신뢰도 측정
        y_mean = np.mean(counts)
        ss_tot = np.sum((counts - y_mean) ** 2)
        y_pred = slope * x + _
        ss_res = np.sum((counts - y_pred) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

        return {
            "direction": direction,
            "confidence": float(r_squared),
            "slope": float(slope)
        }

    def evaluate_success(
        self,
        suggestion: ImprovementSuggestion,
        implementation_result: Dict,
        feedback_changes: Dict
    ) -> Tuple[bool, float, str]:
        """
        개선사항 구현의 전반적인 성공 여부를 평가합니다.
        넘파이를 사용하여 계산을 최적화합니다.

        Args:
            suggestion: 평가할 개선사항
            implementation_result: 구현 결과
            feedback_changes: 피드백 변화 분석 결과

        Returns:
            Tuple[bool, float, str]: (성공 여부, 신뢰도, 평가 설명)
        """
        # 평가 지표 배열 초기화
        indicators = np.zeros(3, dtype=bool)
        confidences = np.zeros(3)
        reasons = []

        # 구현 결과 평가
        if implementation_result["success"]:
            indicators[0] = True
            confidences[0] = 0.4
            reasons.append("메트릭 개선 목표 달성")

        # 피드백 변화 평가
        if feedback_changes["trend"]["direction"] == "decreasing":
            indicators[1] = True
            confidences[1] = 0.3
            reasons.append("관련 피드백 감소 추세")

        # 심각도 분포 평가
        severity_dist = feedback_changes["severity_distribution"]
        total_feedbacks = sum(severity_dist.values())
        if total_feedbacks > 0:
            high_severity_count = (
                severity_dist.get("CRITICAL", 0) +
                severity_dist.get("HIGH", 0)
            )
            high_severity_ratio = high_severity_count / total_feedbacks

            if high_severity_ratio < 0.2:
                indicators[2] = True
                confidences[2] = 0.3
                reasons.append("높은 심각도의 피드백 비율 감소")

        # 최종 평가
        is_successful = np.sum(indicators) >= 2
        confidence = float(np.sum(confidences))
        confidence = min(confidence, 1.0)

        evaluation_description = (
            "성공" if is_successful else "부분적 성공" if confidence >= 0.5 else "개선 필요"
        )
        evaluation_description += f" (신뢰도: {confidence:.2f})"
        if reasons:
            evaluation_description += f"\n주요 이유: {', '.join(reasons)}"

        return is_successful, confidence, evaluation_description

    @lru_cache(maxsize=128)
    def get_metrics_history(
        self,
        suggestion_id: str,
        metric_name: Optional[str] = None
    ) -> List[Dict]:
        """
        메트릭 이력을 조회합니다.
        캐싱을 통해 조회 성능을 최적화합니다.

        Args:
            suggestion_id: 개선사항 ID
            metric_name: 조회할 메트릭 이름 (None이면 모든 메트릭)

        Returns:
            List[Dict]: 메트릭 이력
        """
        history = self.metrics_history.get(suggestion_id, [])

        if not metric_name:
            return history

        # 특정 메트릭만 필터링
        return [
            {
                "timestamp": entry["timestamp"],
                "metrics": {metric_name: entry["metrics"][metric_name]}
                if metric_name in entry["metrics"] else {},
                "type": entry["type"]
            }
            for entry in history
            if metric_name in entry["metrics"]
        ]

    @lru_cache(maxsize=128)
    def get_feedback_history(
        self,
        suggestion_id: str,
        feedback_type: Optional[FeedbackType] = None
    ) -> List[Feedback]:
        """
        피드백 이력을 조회합니다.
        캐싱을 통해 조회 성능을 최적화합니다.

        Args:
            suggestion_id: 개선사항 ID
            feedback_type: 조회할 피드백 유형 (None이면 모든 유형)

        Returns:
            List[Feedback]: 피드백 이력
        """
        history = self.feedback_history.get(suggestion_id, [])

        if not feedback_type:
            return history

        # 특정 유형만 필터링 (넘파이 사용)
        feedbacks = np.array(history)
        if len(feedbacks) > 0:
            mask = np.array([f.type == feedback_type for f in feedbacks])
            return feedbacks[mask].tolist()
        return []

    def _calculate_overall_score(self, improvements: Dict) -> float:
        """
        전체 개선 점수를 계산합니다.
        넘파이를 사용하여 계산을 최적화합니다.
        """
        if not improvements:
            return 0.0

        # 개선율을 배열로 변환
        improvement_rates = np.array([
            imp["improvement_rate"]
            for imp in improvements.values()
        ])

        # 이상치 제거 (IQR 방법)
        q1, q3 = np.percentile(improvement_rates, [25, 75])
        iqr = q3 - q1
        mask = (improvement_rates >= q1 - 1.5 * iqr) & (improvement_rates <= q3 + 1.5 * iqr)
        valid_rates = improvement_rates[mask]

        if len(valid_rates) == 0:
            return 0.0

        # 최종 점수 계산
        avg_improvement = np.mean(valid_rates)
        return float(np.clip((avg_improvement + 1) / 2, 0.0, 1.0))
