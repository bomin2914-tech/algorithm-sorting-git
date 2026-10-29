# ==============================================================================
# Google Cloud Run 배포용 Dockerfile
# 멀티 스테이지 없이 경량 python:3.11-slim 베이스 이미지 사용
# ==============================================================================

FROM python:3.11-slim

# 표준 출력/에러 버퍼링 비활성화 및 바이트코드 생성 방지 (Cloud Run 로깅 최적화)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_HOME=/app

WORKDIR $APP_HOME

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 소스 코드 복사
COPY . .

# Google Cloud Run은 컨테이너가 바인딩해야 할 포트를 PORT 환경 변수로 전달합니다 (기본 8080)
ENV PORT=8080
EXPOSE 8080

# uvicorn 실행 (0.0.0.0 바인딩 필수)
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT} --workers 2"]

