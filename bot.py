from datetime import datetime
import re
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Thay Token Telegram Bot của bạn vào đây
TOKEN = "9125285476:AAGKHXS_l9tCNwg0NlQ3jtZRxTIBkCPFJzA"


async def process_prediction_request(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  text = update.message.text.strip()
  target_date = datetime.now().strftime("%Y-%m-%d")

  # Kiểm tra nếu dùng lệnh dạng /xem 30-10-2026
  if context.args:
    input_str = context.args[0].strip()
  else:
    # Hoặc tự động quét ngày tháng trong tin nhắn thường (VD: 30-10-2026 hoặc 30/10/2026)
    match = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", text)
    if match:
      d, m, y = match.groups()
      target_date = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
      input_str = None
    else:
      input_str = None

  if context.args and len(context.args) > 0:
    input_str = context.args[0].strip()
  if input_str:
    try:
      sep = "-" if "-" in input_str else ("/" if "/" in input_str else None)
      if sep:
        parts = input_str.split(sep)
        if len(parts[0]) == 4:
          target_date = f"{parts[0]}-{parts[1]}-{parts[2]}"
        elif len(parts[2]) == 4:
          target_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
    except Exception:
      pass

  try:
    # Gọi API trực tiếp từ Web App Flask đang chạy ở cổng 5001
    response = requests.get(
        f"http://127.0.0.1:5001/api/results?date={target_date}"
    )
    data = response.json()

    if data and "status" in data:
      ml = data.get("ml_data")
      msg = (
          f"🎯 *PHÂN TÍCH CHỐT SỐ ĐỘC THỦ KỲ QUAY ({data['date']})*\n"
          f"*(Mô hình Random Forest AI - Chắt lọc tối ưu)*\n\n"
          f"👑 *1 CON SỐ ĐỘC THỦ VIP (BEST PICK):*\n⭐ {ml['best']} — Xác"
          f" suất: {ml['best_prob']}%\n\n"
          f"🔥 *2 SỐ NÊN MUA (BẠCH THỦ & SONG THỦ):*\n🔹 Số: {ml['pair1']} —"
          f" Xác suất: {ml['probs'][0]}%\n🔹 Số: {ml['pair2']} — Xác suất:"
          f" {ml['probs'][1]}%\n\n"
          f"📊 *DÀN 4 SỐ CÓ TỶ LỆ RA NHIỀU NHẤT:*\n🔹 Top 1: {ml['set4'][0]} —"
          f" Xác suất: {ml['probs'][0]}%\n🔹 Top 2: {ml['set4'][1]} — Xác"
          f" suất: {ml['probs'][1]}%\n🔹 Top 3: {ml['set4'][2]} — Xác suất:"
          f" {ml['probs'][2]}%\n🔹 Top 4: {ml['set4'][3]} — Xác suất:"
          f" {ml['probs'][3]}%\n\n"
          f"⚠️ *Lưu ý: Dự đoán mang tính chất tham khảo dựa trên thuật toán học"
          f" máy.*\n"
          f"🏢 *Powered by VMAH AI SOLUTIONS*"
      )
    else:
      msg = "⚠️ Không thể kết nối tới dữ liệu phân tích từ Web Server!"
  except Exception as e:
    msg = f"⚠️ Lỗi kết nối tới Flask Server (Hãy đảm bảo Web App đang chạy): {e}"

  await update.message.reply_text(msg, parse_mode="Markdown")


if __name__ == "__main__":
  app = ApplicationBuilder().token(TOKEN).build()

  # Đăng ký lệnh dạng /start, /xem, /date
  app.add_handler(CommandHandler("start", process_prediction_request))
  app.add_handler(CommandHandler("xem", process_prediction_request))
  app.add_handler(CommandHandler("date", process_prediction_request))

  # Đăng ký bắt cả tin nhắn chữ thông thường (bạn chỉ cần gõ: xem 30-10-2026)
  app.add_handler(
      MessageHandler(filters.TEXT & ~filters.COMMAND, process_prediction_request)
  )

  print("🤖 [Telegram Bot] Đã nâng cấp: Hỗ trợ cả lệnh và tin nhắn thường...")
  app.run_polling()