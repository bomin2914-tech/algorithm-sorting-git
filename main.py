from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, List, Optional, Dict

app = FastAPI(title="Binary Search Tree API")

# ==========================================
# 1. CORS(Cross-Origin Resource Sharing) 설정
# ==========================================
# GAS(Google Apps Script) 웹 앱 및 모든 도메인에서의 접근을 허용합니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 특정 domain으로 제한할 수 있습니다.
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, OPTIONS 등 모든 메서드 허용
    allow_headers=["*"],
)

# ==========================================
# 2. 이진 검색 트리(BST) 클래스 정의
# ==========================================
class Node:
    """이진 검색 트리의 노드 클래스"""
    def __init__(self, key: int, value: Any = None, left: 'Node' = None, right: 'Node' = None):
        self.key = key          # 노드의 키(정렬 및 비교 기준)
        self.value = value      # 노드에 저장할 데이터(기본값은 key와 동일하게 다룸)
        self.left = left        # 왼쪽 자식 노드 참조
        self.right = right      # 오른쪽 자식 노드 참조

    def to_dict(self) -> Dict[str, Any]:
        """시각화 및 JSON 반환을 위해 노드 구조를 사전(dict) 형식으로 변환"""
        return {
            "key": self.key,
            "value": self.value,
            "left": self.left.to_dict() if self.left else None,
            "right": self.right.to_dict() if self.right else None
        }

class BinarySearchTree:
    """이진 검색 트리 클래스"""
    def __init__(self):
        self.root: Optional[Node] = None  # 트리의 루트 노드

    def search(self, key: int) -> Optional[Any]:
        """
        키를 통한 노드 검색
        시간 복잡도: 평균 O(log N), 최악 O(N)
        """
        ptr = self.root
        trace = []  # 검색 경로 기록 (시각화용)
        while ptr is not None:
            trace.append(ptr.key)
            if key == ptr.key:
                return ptr.value, trace
            elif key < ptr.key:
                ptr = ptr.left
            else:
                ptr = ptr.right
        return None, trace

    def add(self, key: int, value: Any = None) -> bool:
        """
        새로운 노드 삽입
        시간 복잡도: 평균 O(log N), 최악 O(N)
        """
        if value is None:
            value = key

        def _add_node(node: Node, key: int, value: Any) -> Node:
            if node is None:
                return Node(key, value)
            if key == node.key:
                return node  # 중복 키는 허용하지 않음
            elif key < node.key:
                node.left = _add_node(node.left, key, value)
            else:
                node.right = _add_node(node.right, key, value)
            return node

        if self.search(key)[0] is not None:
            return False  # 이미 존재함

        self.root = _add_node(self.root, key, value)
        return True

    def remove(self, key: int) -> bool:
        """
        노드 삭제 (자식이 없거나 1개인 경우, 2개인 경우 처리)
        시간 복잡도: 평균 O(log N), 최악 O(N)
        """
        def _remove_node(node: Node, key: int) -> Optional[Node]:
            if node is None:
                return None
            if key < node.key:
                node.left = _remove_node(node.left, key)
            elif key > node.key:
                node.right = _remove_node(node.right, key)
            else:
                # 삭제할 노드를 찾은 경우
                # 케이스 1 & 2: 자식이 없거나 1개인 경우
                if node.left is None:
                    return node.right
                elif node.right is None:
                    return node.left
                
                # 케이스 3: 자식이 2개인 경우
                # 오른쪽 서브트리에서 가장 작은 노드(최솟값)를 찾아 대체
                temp = self._min_node(node.right)
                node.key = temp.key
                node.value = temp.value
                node.right = _remove_node(node.right, temp.key)
            return node

        if self.search(key)[0] is None:
            return False  # 삭제할 키가 존재하지 않음

        self.root = _remove_node(self.root, key)
        return True

    def _min_node(self, node: Node) -> Node:
        """지정한 서브트리에서 최소 키 노드 찾기"""
        current = node
        while current.left is not None:
            current = current.left
        return current

    def min_key(self) -> Optional[int]:
        """전체 트리에서 최소 키 반환"""
        if self.root is None:
            return None
        return self._min_node(self.root).key

    def max_key(self) -> Optional[int]:
        """전체 트리에서 최대 키 반환"""
        if self.root is None:
            return None
        current = self.root
        while current.right is not None:
            current = current.right
        return current.key

    def dump(() -> List[Dict[str, Any]]:
        """트리의 모든 노드를 중위 순회(In-order Traversal)하여 정렬된 순서로 반환"""
        result = []
        def _inorder(node: Node):
            if node is not None:
                _inorder(node.left)
                result.append({"key": node.key, "value": node.value})
                _inorder(node.right)
        _inorder(self.root)
        return result

# ==========================================
# 3. 요청/응답 모델 및 API 엔드포인트
# ==========================================
class BSTOperationRequest(BaseModel):
    initial_keys: List[int] = [50, 30, 70, 20, 40, 60, 80]  # 초기 트리 구성용 키
    operation: str  # "add", "remove", "search", "dump", "range" 중 하나
    target_key: Optional[int] = None  # 연산 대상 키

@app.get("/")
def health_check():
    """서버 상태 확인용 헬스체크 API"""
    return {"status": "ok", "message": "Binary Search Tree API Service is Running"}

@app.post("/api/bst")
def process_bst_operation(req: BSTOperationRequest):
    """BST 연산 실행 API"""
    bst = BinarySearchTree()
    
    # 1. 초기 데이터로 트리 구축
    for k in req.initial_keys:
        bst.add(k)

    result_data = {
        "operation": req.operation,
        "target_key": req.target_key,
        "success": True,
        "message": "",
        "search_trace": [],
        "min_key": None,
        "max_key": None,
        "dump_data": [],
        "tree_structure": None,
        "complexity": {
            "time_avg": "O(log N)",
            "time_worst": "O(N)",
            "space": "O(N)"
        }
    }

    # 2. 요청된 연산 수행
    if req.operation == "add":
        if req.target_key is None:
            raise HTTPException(status_code=400, detail="target_key가 필요합니다.")
        success = bst.add(req.target_key)
        result_data["success"] = success
        result_data["message"] = f"키 {req.target_key} 삽입 {'성공' if success else '실패(중복 키)'}"

    elif req.operation == "remove":
        if req.target_key is None:
            raise HTTPException(status_code=400, detail="target_key가 필요합니다.")
        success = bst.remove(req.target_key)
        result_data["success"] = success
        result_data["message"] = f"키 {req.target_key} 삭제 {'성공' if success else '실패(존재하지 않음)'}"

    elif req.operation == "search":
        if req.target_key is None:
            raise HTTPException(status_code=400, detail="target_key가 필요합니다.")
        val, trace = bst.search(req.target_key)
        result_data["success"] = (val is not None)
        result_data["search_trace"] = trace
        result_data["message"] = f"키 {req.target_key} 검색 경로: {' -> '.join(map(str, trace))}" if val else f"키 {req.target_key}를 찾을 수 없습니다."

    elif req.operation == "dump":
        result_data["dump_data"] = bst.dump()
        result_data["message"] = f"트리 중위 순회(Dump) 결과: {[item['key'] for item in result_data['dump_data']]}"

    elif req.operation == "range":
        min_k = bst.min_key()
        max_k = bst.max_key()
        result_data["min_key"] = min_k
        result_data["max_key"] = max_k
        result_data["message"] = f"최소 키: {min_k}, 최대 키: {max_k}"

    else:
        raise HTTPException(status_code=400, detail="지원하지 않는 연산입니다.")

    # 3. 최종 트리 구조 및 결과 반환
    result_data["tree_structure"] = bst.root.to_dict() if bst.root else None
    return result_data
