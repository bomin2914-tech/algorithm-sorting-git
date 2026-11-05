"""
FastAPI 기반 힙 정렬(Heap Sort) vs 도수 정렬(Counting Sort) 시각화 백엔드 서버
파일: main.py
"""

import time
import math
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

app = FastAPI(
    title="Heap Sort vs Counting Sort Visualizer API",
    description="힙 정렬과 도수 정렬의 단계별 히스토그램 스냅샷 및 복잡도 텔레메트리 제공",
    version="1.0.0"
)

# CORS 설정 (GAS 및 웹 클라이언트 직접 통신 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SortRequest(BaseModel):
    array: List[int] = Field(
        ...,
        description="정렬할 정수 배열",
        example=[12, 18, 8, 24, 15, 31, 20, 29, 14, 22, 10, 26, 17, 30, 25, 19]
    )

    @field_validator("array")
    @classmethod
    def validate_array(cls, v: List[int]) -> List[int]:
        if not v:
            raise ValueError("배열이 비어 있습니다.")
        if len(v) > 60:
            raise ValueError(f"시각화 성능을 위해 60개 이하의 배열만 지원합니다. (현재: {len(v)}개)")
        return v


# --------------------------------------------------------------------------
# 1. 힙 정렬 (Heap Sort) 단계별 히스토그램 스냅샷 생성기
# --------------------------------------------------------------------------
def generate_heap_sort_snapshots(arr: List[int]) -> List[Dict[str, Any]]:
    a = list(arr)
    n = len(a)
    snapshots = []
    max_val = max(a) if a else 1
    
    # 이론적 상한 복잡도 추정 (2 * N * log2(N))
    theoretical_ops = max(1, int(2 * n * math.log2(max(2, n))))
    current_ops = 0
    t_start = time.perf_counter()

    def make_snapshot(desc: str, active_indices: Dict[int, str]):
        elapsed = (time.perf_counter() - t_start) * 1000
        progress = min(100.0, round((current_ops / theoretical_ops) * 100, 1))
        
        bars = []
        for idx, val in enumerate(a):
            state = active_indices.get(idx, "default")
            height_pct = max(10, int((val / max_val) * 100)) if max_val > 0 else 10
            bars.append({
                "index": idx,
                "value": val,
                "height_pct": height_pct,
                "state": state  # default, comparing, swap, root, sorted
            })
            
        snapshots.append({
            "step": len(snapshots) + 1,
            "description": desc,
            "bars": bars,
            "elapsed_ms": round(elapsed, 3),
            "current_ops": current_ops,
            "complexity_progress": progress,
            "time_complexity_bound": f"O(N log N) ≈ {theoretical_ops} ops"
        })

    sorted_set = set()
    make_snapshot("힙 정렬 초기 상태 로드", {})

    def heapify(size: int, i: int):
        nonlocal current_ops
        largest = i
        left = 2 * i + 1
        right = 2 * i + 2

        current_ops += 1
        if left < size and a[left] > a[largest]:
            largest = left

        current_ops += 1
        if right < size and a[right] > a[largest]:
            largest = right

        if largest != i:
            current_ops += 1
            a[i], a[largest] = a[largest], a[i]
            
            hl = {idx: "sorted" for idx in sorted_set}
            hl[i] = "swap"
            hl[largest] = "swap"
            make_snapshot(f"노드 {i}(값 {a[i]}) ↔ 노드 {largest}(값 {a[largest]}) 교환(Swap)", hl)
            heapify(size, largest)

    # 1. Build Max Heap
    for i in range(n // 2 - 1, -1, -1):
        heapify(n, i)
        
    make_snapshot("Max-Heap 구축 완료 (루트에 최댓값 위치)", {0: "root"})

    # 2. Extract Elements
    for i in range(n - 1, 0, -1):
        current_ops += 1
        a[0], a[i] = a[i], a[0]
        sorted_set.add(i)
        
        hl = {idx: "sorted" for idx in sorted_set}
        hl[0] = "swap"
        hl[i] = "sorted"
        make_snapshot(f"최댓값 {a[i]}을 인덱스 {i}로 확정 배치", hl)
        
        heapify(i, 0)

    sorted_set.add(0)
    make_snapshot("힙 정렬 완료: 모든 원소 정렬 확정", {i: "sorted" for i in range(n)})
    return snapshots


# --------------------------------------------------------------------------
# 2. 도수 정렬 (Counting Sort) 단계별 히스토그램 스냅샷 생성기
# --------------------------------------------------------------------------
def generate_counting_sort_snapshots(arr: List[int]) -> List[Dict[str, Any]]:
    a = list(arr)
    n = len(a)
    snapshots = []
    
    if not a:
        return []

    min_val = min(a)
    max_val = max(a)
    k = max_val - min_val + 1
    
    # 이론적 상한 복잡도 추정 (2*N + K)
    theoretical_ops = max(1, 2 * n + k)
    current_ops = 0
    t_start = time.perf_counter()

    count = [0] * k
    output = [0] * n
    placed_indices = set()

    def make_snapshot(desc: str, active_output: Dict[int, str], active_bucket: int = -1):
        elapsed = (time.perf_counter() - t_start) * 1000
        progress = min(100.0, round((current_ops / theoretical_ops) * 100, 1))

        bars = []
        for idx, val in enumerate(output):
            state = active_output.get(idx, "default")
            height_pct = max(10, int((val / max_val) * 100)) if (max_val > 0 and val > 0) else 8
            bars.append({
                "index": idx,
                "value": val,
                "height_pct": height_pct,
                "state": state  # default, counting, sorted
            })

        snapshots.append({
            "step": len(snapshots) + 1,
            "description": desc,
            "bars": bars,
            "count_matrix": list(count[:16]),  # 프론트 시각화용 일부 버킷
            "active_bucket": active_bucket,
            "elapsed_ms": round(elapsed, 3),
            "current_ops": current_ops,
            "complexity_progress": progress,
            "time_complexity_bound": f"O(N + K) ≈ {theoretical_ops} ops"
        })

    make_snapshot(f"도수 정렬 초기화: 빈도 버킷 C[0..{k-1}] 생성", {}, -1)

    # 1. 빈도수 계산
    for idx, num in enumerate(a):
        current_ops += 1
        bucket = num - min_val
        count[bucket] += 1
        make_snapshot(f"빈도수 계수: 원소 {num} ➜ 버킷 C[{bucket}]={count[bucket]}", {}, bucket)

    # 2. 누적 합 계산
    for i in range(1, k):
        current_ops += 1
        count[i] += count[i - 1]
    make_snapshot("누적 합(Prefix Sum) 계산 완료", {}, -1)

    # 3. 출력 배열 배치
    for i in range(n - 1, -1, -1):
        current_ops += 1
        val = a[i]
        bucket = val - min_val
        target_idx = count[bucket] - 1
        output[target_idx] = val
        count[bucket] -= 1
        placed_indices.add(target_idx)

        hl = {idx: "sorted" for idx in placed_indices}
        hl[target_idx] = "counting"
        make_snapshot(f"원소 {val} ➜ 출력 배열 B[{target_idx}]에 배치", hl, bucket)

    make_snapshot("도수 정렬 완료: O(N+K) 선형 시간 완료", {i: "sorted" for i in range(n)}, -1)
    return snapshots


# --------------------------------------------------------------------------
# 엔드포인트
# --------------------------------------------------------------------------
@app.get("/health", tags=["시스템"])
async def health_check():
    return {"status": "ok", "service": "heap_vs_counting_visualizer"}


@app.post("/sort", tags=["정렬 시각화"])
async def compare_sort_algorithms(request: SortRequest):
    try:
        input_data = request.array
        heap_snaps = generate_heap_sort_snapshots(input_data)
        counting_snaps = generate_counting_sort_snapshots(input_data)

        max_steps = max(len(heap_snaps), len(counting_snaps))

        return {
            "status": "success",
            "input_array": input_data,
            "array_size": len(input_data),
            "max_steps": max_steps,
            "heap_sort": {
                "name": "힙 정렬 (Heap Sort)",
                "time_complexity": "O(N log N)",
                "space_complexity": "O(1)",
                "total_steps": len(heap_snaps),
                "snapshots": heap_snaps
            },
            "counting_sort": {
                "name": "도수 정렬 (Counting Sort)",
                "time_complexity": "O(N + K)",
                "space_complexity": "O(N + K)",
                "total_steps": len(counting_snaps),
                "snapshots": counting_snaps
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"정렬 데이터 생성 실패: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)

