# 파이썬 공식 경량화 이미지 사용
FROM python:3.10-slim

# 작업 디렉터리 설정
WORKDIR /app

# 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스코드 복사
COPY . .

# Cloud Run에서 기본 지정하는 PORT 환경 변수 처리 (기본 8080)
ENV PORT=8080

# Uvicorn 서버 실행
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
