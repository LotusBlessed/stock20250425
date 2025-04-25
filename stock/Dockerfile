# 使用官方 Python 映像
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 複製專案檔案
COPY . .

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 開放 port
EXPOSE 8000

# 啟動 Gunicorn 並綁定 Render 指定的 port
CMD ["sh", "-c", "gunicorn app:app --bind=0.0.0.0:$PORT --timeout 150"]
