from typing import Dict, Any
import numpy as np
from datetime import datetime

class BaseStrategy:
    def __init__(self):
        self.name = self.__class__.__name__
        
    async def evaluate(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

class TechnicalAnalysisStrategy(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.indicators = {}
        
    async def evaluate(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        price_data = market_data.get('prices', [])
        if not price_data:
            return {'should_trade': False}
            
        signals = {
            'rsi': self.calculate_rsi(price_data),
            'macd': self.calculate_macd(price_data),
            'bollinger': self.calculate_bollinger_bands(price_data)
        }
        
        return self.generate_trading_signal(signals)
        
    def calculate_rsi(self, prices: list, period: int = 14) -> float:
        if len(prices) < period:
            return 50  # Neutral if not enough data
            
        price_diff = np.diff(prices)
        gains = np.where(price_diff > 0, price_diff, 0)
        losses = np.where(price_diff < 0, -price_diff, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
        
    def calculate_macd(self, prices: list) -> Dict[str, float]:
        if len(prices) < 26:
            return {'macd': 0, 'signal': 0}
            
        exp12 = np.exp(1 - (2 / 13))
        exp26 = np.exp(1 - (2 / 27))
        
        ema12 = np.zeros_like(prices)
        ema26 = np.zeros_like(prices)
        
        for i in range(1, len(prices)):
            ema12[i] = (prices[i] - ema12[i-1]) * exp12 + ema12[i-1]
            ema26[i] = (prices[i] - ema26[i-1]) * exp26 + ema26[i-1]
            
        macd = ema12 - ema26
        signal = np.mean(macd[-9:])  # 9-day EMA of MACD
        
        return {'macd': macd[-1], 'signal': signal}
        
    def calculate_bollinger_bands(self, prices: list, period: int = 20) -> Dict[str, float]:
        if len(prices) < period:
            return {'upper': prices[-1], 'lower': prices[-1], 'middle': prices[-1]}
            
        prices_array = np.array(prices[-period:])
        middle = np.mean(prices_array)
        std = np.std(prices_array)
        
        return {
            'upper': middle + (2 * std),
            'lower': middle - (2 * std),
            'middle': middle
        }
        
    def generate_trading_signal(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        rsi = signals['rsi']
        macd = signals['macd']
        bollinger = signals['bollinger']
        
        # Example trading logic
        should_trade = False
        trade_type = None
        
        if rsi < 30 and macd['macd'] > macd['signal']:
            should_trade = True
            trade_type = 'buy'
        elif rsi > 70 and macd['macd'] < macd['signal']:
            should_trade = True
            trade_type = 'sell'
            
        return {
            'should_trade': should_trade,
            'trade_type': trade_type,
            'signals': signals,
            'timestamp': datetime.now().isoformat()
        }

class SentimentAnalysisStrategy(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.sentiment_threshold = 0.6
        
    async def evaluate(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        sentiment_data = market_data.get('sentiment', {})
        if not sentiment_data:
            return {'should_trade': False}
            
        news_sentiment = sentiment_data.get('news', 0)
        social_sentiment = sentiment_data.get('social', 0)
        
        # Combine different sentiment sources
        overall_sentiment = (news_sentiment * 0.7) + (social_sentiment * 0.3)
        
        should_trade = abs(overall_sentiment) > self.sentiment_threshold
        trade_type = 'buy' if overall_sentiment > 0 else 'sell'
        
        return {
            'should_trade': should_trade,
            'trade_type': trade_type,
            'sentiment_score': overall_sentiment,
            'timestamp': datetime.now().isoformat()
        }
