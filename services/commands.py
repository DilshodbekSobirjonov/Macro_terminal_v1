# services/commands.py

def handle_command(text, state):
    """
    state = {
        'regime': str,
        'active_trades': list,
        'last_heartbeat': str
    }
    """
    if text == "/status":
        return (
            "🧠 <b>MacroTerminal status</b>\n\n"
            f"Regime: {state['regime']}\n"
            f"Active trades: {len(state['active_trades'])}\n"
            f"Last cycle: {state['last_heartbeat']}"
        )

    if text == "/regime":
        return f"🌍 <b>Market regime:</b> {state['regime']}"

    if text == "/positions":
        if not state["active_trades"]:
            return "📭 No active trades"

        lines = []
        for t in state["active_trades"]:
            lines.append(
                f"{t.pair} | {t.direction} | {t.current_profit:.2f}%"
            )
        return "📊 <b>Active trades</b>\n\n" + "\n".join(lines)

    return None