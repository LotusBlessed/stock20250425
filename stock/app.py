from flask import Flask, render_template
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz  

app = Flask(__name__)
cache_data = {
    "portfolio": [],
    "summary": {},
    "updated_time": "",
}


# ✅ 股票代碼對照表
MY_STOCKS = {
    "0050 元大台灣50": "0050",
    "00929 復華台灣科技優息": "00929",
    "00712 復華富時不動產": "00712",
    "2883 凱基金": "2883",
    "2887 台新金": "2887",
    "2801 彰銀": "2801",
    "1904 正隆": "1904",
    "6154 順發": "6154",
    "1220 台榮": "1220",
    "00905 FT台灣Smart": "00905",
    "4207 環泰": "4207",
    "4744 皇將": "4744",
    "00713 元大台灣高息低波": "00713",
    "6016 康和證": "6016",
    "0056 元大高股息": "0056",
    "6026 福邦證": "6026",
    "2352 佳世達": "2352",
    "8076 伍豐": "8076",
    "2324 仁寶": "2324",
    "2461 光群雷": "2461",
    "1219 福壽": "1219",
    "3071 協禧": "3071",
    "2855 統一證": "2855",
}

# ✅ 持股成本資料
MY_PORTFOLIO = [
    {"名稱": "佳世達", "平均成本": 23.27, "股數": 1000},
    {"名稱": "伍豐", "平均成本": 24.14, "股數": 125},
    {"名稱": "仁寶", "平均成本": 25.72, "股數": 2000},
    {"名稱": "光群雷", "平均成本": 14.47, "股數": 2500},
    {"名稱": "福壽", "平均成本": 13.55, "股數": 2000},
    {"名稱": "正隆", "平均成本": 16.37, "股數": 2000},
    {"名稱": "順發", "平均成本": 15.97, "股數": 1000},
    {"名稱": "台榮", "平均成本": 13.47, "股數": 1000},
    {"名稱": "FT台灣Smart", "平均成本": 10.49, "股數": 1000},
    {"名稱": "環泰", "平均成本": 14.77, "股數": 1000},
    {"名稱": "皇將", "平均成本": 19.93, "股數": 1000},
    {"名稱": "元大台灣50", "平均成本": 161.90, "股數": 1500},
    {"名稱": "復華富時不動產", "平均成本": 8.49, "股數": 3000},
    {"名稱": "元大台灣高息低波", "平均成本": 49.62, "股數": 1000},
    {"名稱": "復華台灣科技優息", "平均成本": 16.65, "股數": 2000},
    {"名稱": "康和證", "平均成本": 11.27, "股數": 1000},
    {"名稱": "元大高股息", "平均成本": 31.62, "股數": 7000},
    {"名稱": "福邦證", "平均成本": 11.96, "股數": 2000},
    {"名稱": "彰銀", "平均成本": 17.72, "股數": 1800},
    {"名稱": "台新金", "平均成本": 15.85, "股數": 1500},
    {"名稱": "凱基金", "平均成本": 15.75, "股數": 1000},
    {"名稱": "統一證", "平均成本": 22.77, "股數": 100},
]

# ✅ 抓價格
def get_stock_price(stock_code):
    try:
        url = f"https://tw.stock.yahoo.com/quote/{stock_code}.TW"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        # 抓成交價格
        price = "N/A"
        for li in soup.find_all("li"):
            spans = li.find_all("span")
            if len(spans) >= 2 and spans[0].text.strip() == "成交":
                price = spans[1].text.strip()
                break

        # 抓漲跌幅
        change_block = soup.find("span", string=lambda s: s and any(x in s for x in ["+", "-", "%"]))
        delta = change_block.text if change_block else "N/A"

        return {
            "價格": float(price.replace(",", "")) if price != "N/A" else None,
            "漲跌": delta
        }

    except Exception as e:
        print(f"[Yahoo爬蟲錯誤] {stock_code}: {e}")
        return {"價格": None, "漲跌": "N/A"}

# ✅ 抓 Yahoo 股利資料
def get_dividend_info(stock_code, year="2024"):
    try:
        url = f"https://tw.stock.yahoo.com/quote/{stock_code}.TW/dividend"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        # 每一列資料都是一個 div.table-row
        rows = soup.select("div.table-row")

        for row in rows:
            year_cell = row.select_one("div.D\\(f\\).W\\(88px\\).Ta\\(start\\)")
            if year_cell and year_cell.text.strip() == year:
                # 取出所有欄位中的 span
                span_elements = row.select("span")
                span_texts = [span.text.strip() for span in span_elements]

                # 安全轉換函數
                def to_float(text):
                    return float(text) if text.replace(".", "", 1).isdigit() else 0.0

                cash_div = to_float(span_texts[0]) if len(span_texts) > 0 else 0.0
                stock_div = to_float(span_texts[1]) if len(span_texts) > 1 else 0.0

                return {
                    "現金股利": cash_div,
                    "股票股利": stock_div
                }

        return {"現金股利": 0.0, "股票股利": 0.0}

    except Exception as e:
        print(f"[股利爬蟲錯誤] {stock_code}: {e}")
        return {"現金股利": 0.0, "股票股利": 0.0}

    
from flask import request  # 別忘了加

@app.route("/")
def index():
    global cache_data

    # ✅ 先使用快取資料顯示畫面（優先呈現）
    if cache_data["portfolio"]:
        print("🟢 使用快取資料")
        rendered_page = render_template(
            "index.html",
            portfolio=cache_data["portfolio"],
            updated_time=cache_data["updated_time"],
            summary=cache_data["summary"]
        )
    else:
        # 初次載入空畫面
        print("🔃 初次載入尚無快取，稍後爬蟲中")
        rendered_page = render_template(
            "index.html",
            portfolio=[],
            updated_time="正在載入...",
            summary={"總成本": 0, "現值": 0, "損益": 0, "總現金股利": 0, "總股票股利": 0}
        )

    # ✅ 背後開始更新快取資料（同步阻塞，若要非同步可之後改 threading）
    portfolio_data = []
    for item in MY_PORTFOLIO:
        name = item["名稱"]
        cost = item["平均成本"]
        qty = item["股數"]

        stock_code = None
        for full_name, code in MY_STOCKS.items():
            if name in full_name:
                stock_code = code
                break

        if not stock_code:
            continue

        result = get_stock_price(stock_code)
        now_price = result["價格"]
        change = result["漲跌"]

        current_value = now_price * qty if now_price else 0
        cost_value = cost * qty
        gain = current_value - cost_value
        gain_str = f"{gain:.2f}"
        rate = f"{(gain / cost_value) * 100:.2f}%" if cost_value else "N/A"
        dividend = get_dividend_info(stock_code)
        cash_dividend = dividend["現金股利"]
        stock_dividend = dividend["股票股利"]
        total_cash = round(cash_dividend * qty, 2)
        total_stock = round(stock_dividend * qty, 2)

        portfolio_data.append({
            "名稱": name,
            "代碼": stock_code,
            "即時價格": f"{now_price:.2f}" if now_price else "N/A",
            "漲跌": change,
            "股數": qty,
            "平均成本": cost,
            "總成本": f"{cost_value:.0f}",
            "現值": f"{current_value:.0f}",
            "損益": gain_str,
            "報酬率": rate,
            "現金股利": cash_dividend,
            "股票股利": stock_dividend,
            "總現金股利": total_cash,
            "總股票股利": total_stock
        })

    summary = {
        "總成本": sum(float(p["總成本"]) for p in portfolio_data),
        "現值": sum(float(p["現值"]) for p in portfolio_data),
        "損益": round(sum(float(p["損益"]) for p in portfolio_data), 2),
        "總現金股利": round(sum(float(p["總現金股利"]) for p in portfolio_data), 2),
        "總股票股利": round(sum(float(p["總股票股利"]) for p in portfolio_data), 2)
    }

    taipei_time = datetime.now(pytz.timezone("Asia/Taipei")).strftime("%Y-%m-%d %H:%M:%S")

    # ✅ 快取更新
    cache_data["portfolio"] = portfolio_data
    cache_data["summary"] = summary
    cache_data["updated_time"] = taipei_time

    return rendered_page
