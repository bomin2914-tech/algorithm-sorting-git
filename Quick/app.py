"""
Google Cloud Run 배포용 알고리즘 시각화 백엔드 서버 (FastAPI)

주요 기능:
1. 셸 정렬(Shell Sort), 퀵 정렬(Quick Sort), 병합 정렬(Merge Sort)을 수행하고
   각 단계의 동작 원리가 담긴 상태 스냅샷(State Snapshot) 히스토리를 반환합니다.
2. CORS(Cross-Origin Resource Sharing)를 완벽 지원하여
   Google Apps Script(GAS) 및 웹 브라우저 클라이언트와의 직접 통신을 지원합니다.
3. 정밀한 입력 유효성 검사 및 명확한 에러 메시지를 제공합니다.
"""

import os
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from sorters import trace_shell_sort, trace_quick_sort, trace_merge_sort

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sort_server")

app = FastAPI(
    title="Sort Algorithm Snapshot Visualizer API",
    description="셸 정렬, 퀵 정렬, 병합 정렬의 상태 스냅샷 히스토리를 제공하는 Cloud Run 백엔드 서비스",
    version="1.0.0"
)

# CORS 설정: GAS 및 외부 웹페이지에서 자유롭게 접근 가능하도록 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 요청 데이터 모델 정의
class SortRequest(BaseModel):
    array: List[int] = Field(
        ...,
        description="정렬할 정수 배열 (시각화 최적화를 위해 3개 이상, 30개 이하 권장)",
        example=[29, 10, 14, 37, 13, 85, 2, 45]
    )

    @field_validator("array")
    @classmethod
    def validate_array_length(cls, v: List[int]) -> List[int]:
        if not v:
            raise ValueError("배열이 비어 있습니다. 최소 1개 이상의 정수를 입력해주세요.")
        if len(v) > 50:
            raise ValueError(f"시각화 애니메이션의 원활한 렌더링을 위해 최대 50개 이하의 배열만 지원합니다. (입력 크기: {len(v)}개)")
        return v


@app.get("/", tags=["기본 정보"])
async def root():
    """서버 가동 상태 및 엔드포인트 안내"""
    return {
        "service": "Sort Algorithm Snapshot Visualizer API",
        "status": "online",
        "supported_algorithms": ["Shell Sort", "Quick Sort", "Merge Sort"],
        "endpoints": {
            "POST /sort": "사용자 지정 배열의 3대 정렬 알고리즘 스냅샷 히스토리 반환",
            "GET /sort/sample": "기본 샘플 데이터에 대한 시각화 히스토리 즉시 반환",
            "GET /health": "서비스 헬스체크"
        }
    }


@app.get("/health", tags=["헬스체크"])
async def health_check():
    """Google Cloud Run 헬스체크용 엔드포인트"""
    return {"status": "healthy"}


@app.post("/sort", tags=["정렬 시각화 데이터 생성"])
async def generate_sort_snapshots(request: SortRequest):
    """
    입력된 배열을 셸 정렬, 퀵 정렬, 병합 정렬로 각각 정렬하면서
    각 단계별 상태 스냅샷을 생성하여 반환합니다.
    """
    try:
        input_data = request.array
        logger.info(f"정렬 요청 수신 - 배열 길이: {len(input_data)}, 데이터: {input_data}")

        # 3가지 알고리즘별 상태 스냅샷 추적 실행
        shell_history = trace_shell_sort(input_data)
        quick_history = trace_quick_sort(input_data)
        merge_history = trace_merge_sort(input_data)

        # 단일 타임라인 동기화를 위한 최대 스텝 수 계산
        max_steps = max(len(shell_history), len(quick_history), len(merge_history))

        response_data = {
            "input_array": input_data,
            "max_steps": max_steps,
            "algorithms": {
                "shell_sort": {
                    "name": "셸 정렬 (Shell Sort)",
                    "time_complexity": {
                        "best": "O(N log N)",
                        "average": "O(N^1.5)",
                        "worst": "O(N^2)"
                    },
                    "space_complexity": "O(1)",
                    "total_steps": len(shell_history),
                    "history": shell_history
                },
                "quick_sort": {
                    "name": "퀵 정렬 (Quick Sort)",
                    "time_complexity": {
                        "best": "O(N log N)",
                        "average": "O(N log N)",
                        "worst": "O(N^2)"
                    },
                    "space_complexity": "O(log N)",
                    "total_steps": len(quick_history),
                    "history": quick_history
                },
                "merge_sort": {
                    "name": "병합 정렬 (Merge Sort)",
                    "time_complexity": {
                        "best": "O(N log N)",
                        "average": "O(N log N)",
                        "worst": "O(N log N)"
                    },
                    "space_complexity": "O(N)",
                    "total_steps": len(merge_history),
                    "history": merge_history
                }
            }
        }

        return response_data

    except ValueError as ve:
        logger.warning(f"유효성 검사 실패: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"입력 데이터 오류: {str(ve)}"
        )
    except Exception as e:
        logger.error(f"정렬 처리 중 예외 발생: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"서버 내부 정렬 처리 오류: {str(e)}"
        )


@app.get("/sort/sample", tags=["정렬 시각화 데이터 생성"])
async def get_sample_snapshots():
    """기본 샘플 배열로 시각화 데이터를 즉시 반환합니다."""
    sample_array = [29, 10, 14, 37, 13, 85, 2, 45, 18, 56]
    return await generate_sort_snapshots(SortRequest(array=sample_array))


if __name__ == "__main__":
    import uvicorn
    # Cloud Run은 환경 변수 PORT를 주입합니다 (기본 8080)
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"서버를 포트 {port}에서 시작합니다.")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)

