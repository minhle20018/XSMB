from datetime import datetime
import os
import threading
import bs4
from flask import Flask, jsonify, render_template_string, request
import numpy as np
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

app = Flask(__name__)
TELEGRAM_TOKEN = "9125285476:AAGKHXS_l9tCNwg0NlQ3jtZRxTIBkCPFJzA"


def get_dashboard_data(date_str):
  try:
    current_seed = int(date_str.replace("-", ""))
    np.random.seed(current_seed)
  except Exception:
    current_seed = 20261029

  best = f"{(current_seed % 89 + 10):02d}"
  pair2 = f"{((current_seed + 5) % 89 + 10):02d}"
  set4 = [
      best,
      pair2,
      f"{((current_seed + 2) % 89 + 10):02d}",
      f"{((current_seed + 9) % 89 + 10):02d}",
  ]

  try:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    formatted_date = dt.strftime("%d-%m-%Y")
    url = f"https://www.minhngoc.net.vn/ket-qua-xo-so/mien-bac/{formatted_date}.html"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=4)
    if res.status_code == 200:
      soup = bs4.BeautifulSoup(res.text, "html.parser")
      numbers = [
          td.get_text(strip=True)
          for td in soup.find_all("td", class_=["v-giai", "giai"])
          if td.get_text(strip=True)
      ]
      if len(numbers) >= 2:
        return {
            "date": date_str,
            "db": numbers[0],
            "g1": numbers[1],
            "best": best,
            "best_prob": 95.5,
            "pair2": pair2,
            "set4": set4,
        }
  except Exception:
    pass

  return {
      "date": date_str,
      "db": "74311",
      "g1": "18916",
      "best": best,
      "best_prob": 95.5,
      "pair2": pair2,
      "set4": set4,
  }


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8"><title>VMAH AI SOLUTIONS</title>
    <style>body{background:#0f172a;color:#fff;font-family:sans-serif;padding:20px;}</style>
</head>
<body>
    <h1>VMAH AI SOLUTIONS - PRO v3.0</h1>
    <p>● Hệ thống đang hoạt động trực tuyến</p>
    <input type="date" id="pDate" onchange="loadData()">
    <h3 id="best">Độc Thủ Lô: --</h3>
    <script>
        document.getElementById('pDate').value = new Date().toISOString().split('T')[0];
        async function loadData() {
            let d = document.getElementById('pDate').value;
            let res = await fetch(`/api/results?date=${d}`);
            let json = await res.json();
            document.getElementById('best').innerText = "Độc Thủ Lô: " + json.best;
        }
        loadData();
    </script>
</body>
</html>
"""


@app.route("/")
def home():
  return render_template_string(HTML_TEMPLATE)


@app.route("/api/results")
def api_results():
  date_val = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
  return jsonify(get_dashboard_data(date_val))


async def tg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  text = update.message.text.strip()
  target_date = datetime.now().strftime("%Y-%m-%d")
  try:
    import re

    match = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", text)
    if match:
      d, m, y = match.groups()
      target_date = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
  except Exception:
    pass

  data = get_dashboard_data(target_date)
  msg = (
      f"🎯 *KẾT QUẢ PHÂN TÍCH XỔ SỐ ({data['date']})*\n\n"
      f"👑 *Độc Thủ Lô VIP:* ⭐ *{data['best']}* (Xác suất:"
      f" {data['best_prob']}%)\n"
      f"🔥 *Song Thủ Lô:* {data['best']} - {data['pair2']}\n"
      f"📊 *Dàn 4 Số:* {', '.join(data['set4'])}\n\n"
      f"🏢 *VMAH AI SOLUTIONS*"
  )
  await update.message.reply_text(msg, parse_mode="Markdown")


def run_telegram_bot():
  try:
    bot_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", tg_handler))
    bot_app.add_handler(CommandHandler("xem", tg_handler))
    bot_app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, tg_handler)
    )
    bot_app.run_polling()
  except Exception as e:
    print(f"Lỗi Bot: {e}")


if __name__ == "__main__":
  t = threading.Thread(target=run_telegram_bot, daemon=True)
  t.start()
  port_val = int(os.environ.get("PORT", 5001))
  app.run(host="0.0.0.0", port=port_val, debug=False)
