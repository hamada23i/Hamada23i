#!/usr/bin/env python3
# crypto_trading_bot.py
# Advanced Crypto Trading Bot - GitHub 24/7 Edition

import os
import time
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import logging

# ---------- CONFIGURATION ----------
BOT_TOKEN = os.environ['7279717729:AAE1-IMScN4mMif988PS41HadTDY9cQynsU']
MY_CHAT_ID = os.environ['1924302463']
SYMBOLS = os.environ.get('SYMBOLS', 'BTCUSDT,ETHUSDT,SOLUSDT,ADAUSDT,DOTUSDT').split(',')

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitHubTradingBot:
    def __init__(self):
        self.symbols = SYMBOLS
        self.analysis_count = 0
        self.last_scan = None
        
    def telegram_send(self, text):
        """إرسال رسالة عبر التليجرام"""
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": MY_CHAT_ID,
                "text": text,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info("📤 تم إرسال الرسالة بنجاح")
                return True
            else:
                logger.error(f"❌ فشل إرسال الرسالة: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ خطأ في التليجرام: {e}")
            return False

    def fetch_klines(self, symbol, interval="15m", limit=100):
        """جلب بيانات التداول من Binance"""
        try:
            url = "https://api.binance.com/api/v3/klines"
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            df = pd.DataFrame(data, columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_volume", "trades", "taker_buy_base", 
                "taker_buy_quote", "ignore"
            ])
            
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = df[col].astype(float)
                
            logger.info(f"✅ تم جلب بيانات {symbol}")
            return df
        except Exception as e:
            logger.error(f"❌ خطأ في جلب بيانات {symbol}: {e}")
            return pd.DataFrame()

    def ema(self, series, period):
        """المتوسط المتحرك الأسّي"""
        return series.ewm(span=period, adjust=False).mean()

    def rsi(self, series, period=14):
        """مؤشر القوة النسبية"""
        try:
            delta = series.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
            avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
            rs = avg_gain / (avg_loss + 1e-9)
            return 100 - (100 / (1 + rs))
        except:
            return pd.Series([50] * len(series))

    def analyze_symbol(self, symbol):
        """تحليل عملة مفردة"""
        try:
            df = self.fetch_klines(symbol, "1h", 100)
            if df.empty or len(df) < 20:
                return None
                
            close = df['close']
            current_price = close.iloc[-1]
            
            # المؤشرات الفنية
            ema_20 = self.ema(close, 20).iloc[-1]
            ema_50 = self.ema(close, 50).iloc[-1]
            rsi_14 = self.rsi(close, 14).iloc[-1]
            
            # حساب النقاط
            score = 0
            reasons = []
            
            if ema_20 > ema_50:
                score += 35
                reasons.append("📈 EMA صعودي")
            elif ema_20 > current_price * 0.98:
                score += 20
                reasons.append("🛡️ دعم EMA")
                
            if 40 <= rsi_14 <= 65:
                score += 25
                reasons.append("⚖️ RSI مثالي")
            elif rsi_14 < 40:
                score += 15
                reasons.append("🔻 RSI منخفض")
                
            # تحليل الحجم
            volume = df['volume'].iloc[-1]
            vol_ma20 = df['volume'].rolling(20).mean().iloc[-1]
            if volume > vol_ma20 * 1.2:
                score += 20
                reasons.append("📊 حجم مرتفع")
                
            score = min(score, 100)
            
            # التوصية النهائية
            if score >= 80:
                recommendation = "🟢 شراء قوي"
                risk = "منخفض"
            elif score >= 70:
                recommendation = "🟡 شراء"
                risk = "متوسط"
            elif score >= 60:
                recommendation = "🟠 محايد"
                risk = "متوسط-مرتفع"
            else:
                recommendation = "🔴 تجنب"
                risk = "مرتفع"
                
            return {
                'symbol': symbol,
                'price': current_price,
                'score': score,
                'recommendation': recommendation,
                'risk': risk,
                'reasons': reasons,
                'rsi': round(rsi_14, 2),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحليل {symbol}: {e}")
            return None

    def comprehensive_scan(self):
        """المسح الشامل لجميع العملات"""
        logger.info("🔍 بدء المسح الشامل...")
        self.telegram_send("🔍 <b>بدء المسح الشامل على GitHub...</b>")
        
        opportunities = []
        
        for symbol in self.symbols:
            try:
                result = self.analyze_symbol(symbol)
                if result and result['score'] >= 70:  # فرص بجودة عالية فقط
                    opportunities.append(result)
                    
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.error(f"❌ خطأ في مسح {symbol}: {e}")
                continue
                
        if opportunities:
            # ترتيب الفرص حسب الجودة
            opportunities.sort(key=lambda x: x['score'], reverse=True)
            
            # إرسال أفضل 3 فرص
            for i, opp in enumerate(opportunities[:3]):
                message = self.build_opportunity_message(opp, i+1)
                self.telegram_send(message)
                
            logger.info(f"✅ تم إرسال {len(opportunities[:3])} فرص")
        else:
            self.telegram_send("⚠️ <b>لم يتم العثور على فرص تداول عالية الجودة</b>")
            logger.info("⚠️ لم توجد فرص عالية الجودة")
            
        self.analysis_count += 1
        self.last_scan = datetime.now(timezone.utc).isoformat()

    def build_opportunity_message(self, opportunity, rank):
        """بناء رسالة الفرصة"""
        symbol = opportunity['symbol']
        price = opportunity['price']
        score = opportunity['score']
        
        message = [
            f"🏆 <b>فرصة #{rank} - GitHub Bot</b>",
            f"💰 <b>العملة:</b> #{symbol}",
            f"💵 <b>السعر:</b> {price:.6f}",
            f"📊 <b>التقييم:</b> {score:.1f}/100",
            f"🎯 <b>التوصية:</b> {opportunity['recommendation']}",
            f"⚠️ <b>المخاطرة:</b> {opportunity['risk']}",
            f"📈 <b>الأسباب:</b>",
        ]
        
        # إضافة الأسباب
        for reason in opportunity['reasons']:
            message.append(f"   • {reason}")
            
        message.extend([
            f"🔢 <b>RSI:</b> {opportunity['rsi']}",
            f"⏰ <b>الوقت:</b> {datetime.now(timezone.utc).strftime('%H:%M UTC')}",
            "",
            "📍 <b>تشغيل:</b> GitHub Actions 24/7"
        ])
        
        return "\n".join(message)

    def send_status_report(self):
        """إرسال تقرير حالة البوت"""
        message = [
            "📊 <b>تقرير حالة البوت - GitHub</b>",
            f"🟢 <b>الحالة:</b> نشط ويعمل",
            f"🔍 <b>عدد التحليلات:</b> {self.analysis_count}",
            f"💰 <b>العملات:</b> {len(self.symbols)}",
            f"⏰ <b>آخر مسح:</b> {self.last_scan or 'لم يتم بعد'}",
            f"📍 <b>المكان:</b> GitHub Actions",
            f"🕒 <b>وقت التقرير:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "💡 <b>ملاحظة:</b> البوت يعمل 24/7 مجاناً على GitHub"
        ]
        self.telegram_send("\n".join(message))

    def run_daily_scan(self):
        """تشغيل المسح اليومي"""
        logger.info("🌅 بدء المسح اليومي")
        self.telegram_send("🌅 <b>بدء المسح اليومي على GitHub...</b>")
        self.comprehensive_scan()
        self.send_status_report()

# التشغيل الرئيسي
def main():
    logger.info("🚀 بدء تشغيل البوت على GitHub")
    bot = GitHubTradingBot()
    
    try:
        # إرسال رسالة بدء التشغيل
        bot.telegram_send("🚀 <b>تم تشغيل البوت على GitHub بنجاح!</b>")
        
        # تشغيل المسح
        bot.run_daily_scan()
        
        logger.info("✅ اكتمل تشغيل البوت بنجاح")
        
    except Exception as e:
        error_msg = f"❌ <b>خطأ في البوت:</b> {str(e)}"
        logger.error(error_msg)
        bot.telegram_send(error_msg)

if __name__ == "__main__":
    main()
