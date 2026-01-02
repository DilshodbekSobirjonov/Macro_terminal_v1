from services.telegram import TelegramService
from trades.trade import Trade

tg = TelegramService(
    token="8543769576:AAGmG7nQjuezf5OqHqzAWlZI1GJsP3b_Gyw",
    chat_id="-1003534899420"
)

trade = Trade(
    pair="BTCUSDT",
    direction="LONG",
    entry_price=88899,
    score=5,
    reasons=["CHoCH", "Volume spike", "OI increasing"],
    tp_levels=[3, 6, 10],
    sl_percent=4.5
)

tg.send("🔥 TEST MESSAGE")
