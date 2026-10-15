from flask import Flask, jsonify, request
import time

app = Flask(__name__)

@app.route('/sort', methods=['POST'])
def bubble_sort():
    """
    클라이언트로부터 숫자 배열을 받아 버블 정렬을 수행하고,
    시각화를 위한 모든 단계별 기록(Steps)과 복잡도 정보를 반환합니다.
    """
    start_time = time.time()
    
    # 요청 데이터에서 배열 가져오기 (없으면 기본값 사용)
    data = request.get_json() or {}
    arr = data.get('array', [64, 34, 25, 12, 22, 11, 90, 45])
    
    steps = []
    n = len(arr)
    
    # 초기 상태 기록
    steps.append({
        'array': list(arr),
        'comparing': [],
        'swapped': False,
        'message': '초기 배열 상태입니다.'
    })
    
    # 버블 정렬 알고리즘 수행 및 단계별 상태 저장
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            # 비교 중인 두 원소 인덱스 기록
            steps.append({
                'array': list(arr),
                'comparing': [j, j + 1],
                'swapped': False,
                'message': f'{arr[j]}와 {arr[j+1]}을 비교합니다.'
            })
            
            if arr[j] > arr[j+1]:
                # 원소 교환 (Swap)
                arr[j], arr[j+1] = arr[j+1], arr[j]
                swapped = True
                steps.append({
                    'array': list(arr),
                    'comparing': [j, j + 1],
                    'swapped': True,
                    'message': f'크기가 크므로 교환(Swap)합니다: {arr[j]} <-> {arr[j+1]}'
                })
        
        # 이번 루프에서 교환이 없었다면 이미 정렬 완료된 상태
        if not swapped:
            break
            
    # 최종 완료 상태 기록
    steps.append({
        'array': list(arr),
        'comparing': [],
        'swapped': False,
        'message': '🎉 버블 정렬이 성공적으로 완료되었습니다!'
    })
    
    execution_time = round((time.time() - start_time) * 1000, 2) # 밀리초 단위
    
    return jsonify({
        'status': 'success',
        'execution_time_ms': execution_time,
        'complexity': {
            'time_worst': '$O(N^2)$',
            'time_average': '$O(N^2)$',
            'time_best': '$O(N)$',
            'space': '$O(1)$'
        },
        'steps': steps
    })

if __name__ == '__main__':
    # Cloud Run 환경에서는 PORT 환경 변수를 사용합니다.
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
