FROM python:3.10-slim

# 安裝 Python 套件
RUN pip install --no-cache-dir flask pandas yfinance

# 預設進入 /app 目錄
WORKDIR /app

# 預設打開 bash，方便你進 container 下指令
CMD ["bash"]
