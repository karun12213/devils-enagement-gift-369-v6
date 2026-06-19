# main.py
import asyncio
import logging
import os
import random

# ==========================================
# 1. CONFIGURATION
# ==========================================
TRADING_MODE = os.environ.get("TRADING_MODE", "LIVE")
META_API_TOKEN = os.environ.get("META_API_TOKEN", "")
MT4_ACCOUNT_ID = os.environ.get("MT4_ACCOUNT_ID", "")
MT4_SYMBOL = "USOIL"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==========================================
# 2. HUMAN EMOTION & PRICE ACTION ENGINE
# ==========================================
class EmotionEngine:
    def __init__(self):
        self.consecutive_losses = 0
        self.fear_level = 50
        self.greed_level = 50

    def update_emotions(self, trade_history):
        recent_losses = sum(1 for trade in trade_history[-5:] if trade.get('profit', 0) < 0)
        self.consecutive_losses = recent_losses
        # Fear rises after losses, greed blinding them after wins
        self.fear_level = min(100, 50 + (self.consecutive_losses * 15))
        self.greed_level = max(0, 100 - self.fear_level)

class LoserBotOrchestrator:
    def __init__(self):
        self.emotion = EmotionEngine()
        self.trade_history = []

    def get_trade_decision(self, current_price, historical_prices):
        self.emotion.update_emotions(self.trade_history)
        
        action = ""
        reason = ""
        
        # Calculate recent volatility (High - Low of recent candles)
        recent_high = max(historical_prices)
        recent_low = min(historical_prices)
        volatility = max(0.05, recent_high - recent_low) # Minimum 5 cents
        
        # Priority 1: Revenge Trading (Blind tilt)
        if self.emotion.consecutive_losses >= 1:
            action = random.choice(["BUY", "SELL"])
            reason = "REVENGE - Tilted! Ignoring logic, doubling down randomly!"
            # In tilt, humans set random tight stops based on anger
            sl_distance = random.uniform(0.05, 0.15)
            
        # Priority 2: Price Action FOMO / Panic (Buying tops, Selling bottoms)
        elif current_price >= recent_high * 0.999:
            action = "BUY"
            reason = "FOMO - Price is breaking out! Must buy the exact top before it's too late!"
            # Human sets SL based on current volatile spike
            sl_distance = random.uniform(0.08, 0.20)
            
        elif current_price <= recent_low * 1.001:
            action = "SELL"
            reason = "PANIC - Price is crashing! Get out before it hits zero!"
            sl_distance = random.uniform(0.08, 0.20)
            
        # Priority 3: Bad Price Action (Fakeouts)
        else:
            action = random.choice(["BUY", "SELL"])
            reason = "FAKEOUT - Thought it was a breakout, trapped by noise."
            # Human tries to use a "logical" volatility-based SL
            sl_distance = volatility * random.uniform(0.5, 1.0)
            sl_distance = max(0.05, min(sl_distance, 0.30)) # Clamp between 5 and 30 cents

        # GUARANTEED LOSS RISK REWARD: TP is strictly 3 times the SL distance
        tp_distance = sl_distance * 3
        
        if action == "BUY":
            sl = current_price - sl_distance
            tp = current_price + tp_distance
        else:
            sl = current_price + sl_distance
            tp = current_price - tp_distance
            
        return {"action": action, "sl": sl, "tp": tp, "reason": reason}

    def record_trade_result(self, profit):
        self.trade_history.append({"profit": profit})
        if len(self.trade_history) > 20:
            self.trade_history.pop(0)


# ==========================================
# 3. LIVE RAILWAY ENGINE (MetaApi)
# ==========================================
async def run_live_bot():
    logger.info("Initializing Live Human-Like Loser Bot for USOIL on Railway...")
    orchestrator = LoserBotOrchestrator()
    
    try:
        from metaapi_cloud_sdk import MetaApi
    except Exception as e:
        logger.error(f"Failed to load MetaApi SDK: {e}")
        return

    if not META_API_TOKEN or not MT4_ACCOUNT_ID:
        logger.error("Missing META_API_TOKEN or MT4_ACCOUNT_ID environment variables!")
        return

    api = MetaApi(token=META_API_TOKEN)
    
    while True: 
        try:
            account = await api.metatrader_account_api.get_account(MT4_ACCOUNT_ID)
            logger.info(f"Connected to MT4 Account: {account.id}")
            
            await account.wait_deployed()
            await account.wait_connected()
            
            connection = account.get_rpc_connection()
            await connection.connect()
            await connection.wait_synchronized()
            
            logger.info(f"Synchronized. Bot is now simulating a panicking human trader on {MT4_SYMBOL}...")
            
            while True: 
                try:
                    account_info = await connection.get_account_information()
                    current_balance = account_info['balance']
                    
                    positions = await connection.get_positions()
                    
                    if len(positions) > 0:
                        # Simulate human anxiously watching the open trade
                        logger.info("Human bot is anxiously watching the open trade hit stop loss...")
                        await asyncio.sleep(2) 
                        continue

                    price_data = await connection.get_symbol_price(MT4_SYMBOL, keep_subscription=True)
                    current_price = price_data['bid']
                    
                    # Simulate human looking at the chart history
                    historical_prices = [current_price * (1 + random.uniform(-0.005, 0.005)) for _ in range(20)]
                    
                    decision = orchestrator.get_trade_decision(current_price, historical_prices)
                    
                    lots = 0.01
                    sl = decision.get("sl")
                    tp = decision.get("tp")
                    
                    # SIMULATE HUMAN EXECUTION DELAY (Hesitation before clicking)
                    hesitation_time = random.uniform(1.0, 3.5)
                    logger.warning(f"AGENT EMOTION: {decision['reason']}")
                    logger.warning(f"Staring at the chart for {hesitation_time:.1f} seconds before clicking...")
                    await asyncio.sleep(hesitation_time)
                    
                    # Re-fetch price right before execution to simulate live click
                    price_data = await connection.get_symbol_price(MT4_SYMBOL, keep_subscription=True)
                    current_price = price_data['bid']
                    
                    # Recalculate SL/TP based on the new clicked price
                    sl_dist = abs(decision["sl"] - current_price)
                    tp_dist = sl_dist * 3
                    
                    if decision["action"] == "BUY":
                        sl = current_price - sl_dist
                        tp = current_price + tp_dist
                        logger.warning(f"CLICKED BUY! Balance: ${current_balance}. Lots: {lots}. Entry: {current_price}. SL: {sl}. TP: {tp}")
                        await connection.create_market_buy_order(MT4_SYMBOL, lots, sl, tp)
                    elif decision["action"] == "SELL":
                        sl = current_price + sl_dist
                        tp = current_price - tp_dist
                        logger.warning(f"CLICKED SELL! Balance: ${current_balance}. Lots: {lots}. Entry: {current_price}. SL: {sl}. TP: {tp}")
                        await connection.create_market_sell_order(MT4_SYMBOL, lots, sl, tp)
                        
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error in trading loop (likely margin call/broker rejection, retrying): {e}")
                    await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Connection lost: {e}. Retrying in 30 seconds...")
            await asyncio.sleep(30)


# ==========================================
# 4. ENTRY POINT
# ==========================================
if __name__ == "__main__":
    if TRADING_MODE == "BACKTEST":
        print("Backtest mode is not supported in this Railway deployment file.")
    else:
        asyncio.run(run_live_bot())
