# -*- coding: utf-8 -*-
"""
市场状态分类器 - 用于识别和分类市场状态
"""
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from loguru import logger


class MarketFeatureExtractor:
    """
    市场特征提取器
    从市场数据中提取用于分类市场状态的特征
    """
    
    def __init__(self, lookback_period: int = 60):
        self.lookback_period = lookback_period
    
    def extract(self, price_data: pd.DataFrame) -> Dict[str, float]:
        """
        从价格数据中提取市场特征
        
        Args:
            price_data: 包含价格信息的DataFrame，需要包含'close'列
            
        Returns:
            提取的市场特征字典
        """
        features = {}
        
        # 计算趋势强度
        features['trend_strength'] = self._calculate_trend_strength(price_data)
        
        # 计算波动率
        features['volatility'] = self._calculate_volatility(price_data)
        
        # 计算成交量比率
        features['volume_ratio'] = self._calculate_volume_ratio(price_data)
        
        # 计算ATR比率
        features['atr_ratio'] = self._calculate_atr_ratio(price_data)
        
        # 计算动量指标
        features['momentum'] = self._calculate_momentum(price_data)
        
        return features
    
    def _calculate_trend_strength(self, price_data: pd.DataFrame) -> float:
        """
        计算趋势强度
        使用线性回归斜率来衡量趋势强度
        """
        close_prices = price_data['close'][-self.lookback_period:]
        x = np.arange(len(close_prices))
        y = close_prices.values
        
        # 线性回归
        slope, _ = np.polyfit(x, y, 1)
        
        # 标准化斜率（除以价格范围）
        price_range = y.max() - y.min()
        if price_range == 0:
            return 0.0
        
        normalized_slope = slope / price_range * len(close_prices)
        
        return normalized_slope
    
    def _calculate_volatility(self, price_data: pd.DataFrame) -> float:
        """
        计算波动率
        使用对数收益率的标准差
        """
        close_prices = price_data['close'][-self.lookback_period:]
        returns = np.log(close_prices / close_prices.shift(1)).dropna()
        
        return returns.std() * np.sqrt(252)  # 年化波动率
    
    def _calculate_volume_ratio(self, price_data: pd.DataFrame) -> float:
        """
        计算成交量比率
        最近20天平均成交量与最近60天平均成交量的比值
        """
        if 'volume' not in price_data.columns:
            return 1.0
        
        volume = price_data['volume']
        recent_avg = volume[-20:].mean()
        long_term_avg = volume[-self.lookback_period:].mean()
        
        if long_term_avg == 0:
            return 1.0
        
        return recent_avg / long_term_avg
    
    def _calculate_atr_ratio(self, price_data: pd.DataFrame) -> float:
        """
        计算ATR（平均真实范围）比率
        最近ATR与最近60天平均ATR的比值
        """
        # 计算TR（真实范围）
        tr = pd.DataFrame()
        tr['h-l'] = price_data['high'] - price_data['low']
        tr['h-pc'] = abs(price_data['high'] - price_data['close'].shift(1))
        tr['l-pc'] = abs(price_data['low'] - price_data['close'].shift(1))
        tr['tr'] = tr[['h-l', 'h-pc', 'l-pc']].max(axis=1)
        
        # 计算ATR
        atr = tr['tr'].rolling(window=14).mean()
        
        recent_atr = atr.iloc[-1]
        avg_atr = atr[-self.lookback_period:].mean()
        
        if avg_atr == 0:
            return 1.0
        
        return recent_atr / avg_atr
    
    def _calculate_momentum(self, price_data: pd.DataFrame) -> float:
        """
        计算动量指标
        最近收盘价与20天前收盘价的比值
        """
        close_prices = price_data['close']
        
        if len(close_prices) < 20:
            return 0.0
        
        recent = close_prices.iloc[-1]
        past = close_prices.iloc[-20]
        
        if past == 0:
            return 0.0
        
        return (recent - past) / past


class RuleBasedClassifier:
    """
    基于规则的市场状态分类器
    根据预设规则将市场分为不同状态
    """
    
    def __init__(self):
        # 分类规则参数
        self.trend_threshold = 0.3
        self.volatility_threshold = 0.02
        self.atr_ratio_threshold = 1.2
    
    def classify(self, features: Dict[str, float]) -> str:
        """
        根据特征分类市场状态
        
        Args:
            features: 市场特征字典
            
        Returns:
            市场状态字符串
        """
        trend_strength = features.get('trend_strength', 0)
        volatility = features.get('volatility', 0)
        atr_ratio = features.get('atr_ratio', 1)
        
        # 简单规则分类
        if trend_strength > self.trend_threshold:
            return 'trend_up'
        elif trend_strength < -self.trend_threshold:
            return 'trend_down'
        elif volatility > self.volatility_threshold and atr_ratio > self.atr_ratio_threshold:
            return 'range_high_vol'
        else:
            return 'range_low_vol'
    
    def get_regime_prototypes(self) -> Dict[str, Dict[str, float]]:
        """
        获取各市场状态的典型特征值
        """
        return {
            'trend_up': {
                'trend_strength': 0.5,
                'volatility': 0.15,
                'volume_ratio': 1.2
            },
            'trend_down': {
                'trend_strength': -0.5,
                'volatility': 0.2,
                'volume_ratio': 1.3
            },
            'range_high_vol': {
                'trend_strength': 0.0,
                'volatility': 0.25,
                'volume_ratio': 1.1
            },
            'range_low_vol': {
                'trend_strength': 0.0,
                'volatility': 0.1,
                'volume_ratio': 0.8
            }
        }


class MarketRegimeClassifier:
    """
    基于规则+轻量ML的市场状态分类器
    """
    
    def __init__(self, config=None):
        self.config = config or {
            'lookback_window': 60,  # 60个交易日
            'regimes': ['trend_up', 'trend_down', 'range_high_vol', 'range_low_vol']
        }
        
        # 特征计算器
        self.feature_extractor = MarketFeatureExtractor(
            lookback_period=self.config['lookback_window']
        )
        
        # 简单的规则分类器（避免复杂ML引入的不稳定性）
        self.rule_based_classifier = RuleBasedClassifier()
        
        # 市场状态典型特征
        self.regime_prototypes = self.rule_based_classifier.get_regime_prototypes()
    
    def classify_current_market(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """
        分类当前市场状态
        
        Args:
            price_data: 包含价格信息的DataFrame
            
        Returns:
            包含市场状态、置信度和特征的字典
        """
        # 提取特征
        features = self.feature_extractor.extract(price_data)
        
        # 使用规则分类
        regime = self.rule_based_classifier.classify(features)
        
        # 添加置信度计算
        confidence = self._calculate_confidence(features, regime)
        
        return {
            'regime': regime,
            'confidence': confidence,
            'features': features,
            'timestamp': price_data.index[-1] if hasattr(price_data, 'index') else pd.Timestamp.now()
        }
    
    def classify_market_regimes(self, price_data: pd.DataFrame) -> pd.Series:
        """
        对历史数据进行市场状态分类
        
        Args:
            price_data: 包含价格信息的DataFrame
            
        Returns:
            包含每个时间点市场状态的Series
        """
        regimes = []
        timestamps = []
        
        # 滚动窗口分类
        lookback = self.config['lookback_window']
        for i in range(lookback, len(price_data) + 1):
            window_data = price_data.iloc[i-lookback:i]
            classification = self.classify_current_market(window_data)
            regimes.append(classification['regime'])
            timestamps.append(window_data.index[-1])
        
        return pd.Series(regimes, index=timestamps, name='market_regime')
    
    def _calculate_confidence(self, features: Dict[str, float], regime: str) -> float:
        """
        计算分类置信度（基于特征与典型值的距离）
        """
        # 获取该市场状态的典型特征值
        typical_features = self.regime_prototypes.get(regime, {})
        
        if not typical_features:
            return 0.7  # 默认置信度
        
        # 计算特征相似度
        similarity_scores = []
        for feature_name in ['trend_strength', 'volatility', 'volume_ratio']:
            if feature_name in features and feature_name in typical_features:
                actual = features[feature_name]
                typical = typical_features[feature_name]
                # 计算归一化距离
                distance = abs(actual - typical) / (abs(typical) + 1e-8)
                similarity = max(0, 1 - distance)
                similarity_scores.append(similarity)
        
        return np.mean(similarity_scores) if similarity_scores else 0.5
    
    def detect_regime_changes(self, regimes: pd.Series) -> List[Dict[str, Any]]:
        """
        检测市场状态转换
        
        Args:
            regimes: 包含市场状态的Series
            
        Returns:
            状态转换列表，包含转换时间、前状态和后状态
        """
        changes = []
        
        prev_regime = regimes.iloc[0]
        for timestamp, current_regime in regimes.iloc[1:].items():
            if current_regime != prev_regime:
                changes.append({
                    'timestamp': timestamp,
                    'previous_regime': prev_regime,
                    'new_regime': current_regime
                })
                prev_regime = current_regime
        
        return changes
    
    def generate_regime_report(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """
        生成市场状态报告
        
        Args:
            price_data: 包含价格信息的DataFrame
            
        Returns:
            市场状态报告
        """
        # 分类历史市场状态
        regimes = self.classify_market_regimes(price_data)
        
        # 检测状态转换
        regime_changes = self.detect_regime_changes(regimes)
        
        # 计算各状态持续时间
        regime_durations = self._calculate_regime_durations(regimes)
        
        # 计算当前市场状态
        current_regime_info = self.classify_current_market(price_data)
        
        return {
            'current_regime': current_regime_info,
            'regime_history': regimes,
            'regime_changes': regime_changes,
            'regime_statistics': {
                'distribution': regimes.value_counts(normalize=True).to_dict(),
                'durations': regime_durations
            }
        }
    
    def _calculate_regime_durations(self, regimes: pd.Series) -> Dict[str, Dict[str, float]]:
        """
        计算各市场状态的持续时间统计
        """
        durations = {regime: [] for regime in self.config['regimes']}
        
        current_regime = regimes.iloc[0]
        start_time = regimes.index[0]
        
        for timestamp, regime in regimes.iloc[1:].items():
            if regime != current_regime:
                # 计算持续时间（天数）
                duration = (timestamp - start_time).days
                durations[current_regime].append(duration)
                
                # 更新当前状态
                current_regime = regime
                start_time = timestamp
        
        # 处理最后一个状态
        duration = (regimes.index[-1] - start_time).days
        durations[current_regime].append(duration)
        
        # 计算统计信息
        regime_stats = {}
        for regime, regime_durs in durations.items():
            if regime_durs:
                regime_stats[regime] = {
                    'mean': np.mean(regime_durs),
                    'median': np.median(regime_durs),
                    'min': np.min(regime_durs),
                    'max': np.max(regime_durs),
                    'count': len(regime_durs)
                }
            else:
                regime_stats[regime] = {
                    'mean': 0,
                    'median': 0,
                    'min': 0,
                    'max': 0,
                    'count': 0
                }
        
        return regime_stats
