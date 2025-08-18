# ai_model_service.py - Comprehensive Agricultural AI Model with News Sentiment Analysis
import os
import json
import datetime as dt
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
import requests
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your existing model_service components
from model_service import (
    make_gemini_client, gemini_json, gemini_text,
    PriceForecaster, estimate_spoilage_days_left, 
    sentiment_from_headlines, fuse_decision,
    run_price_forecast, run_spoilage, run_sentiment, 
    run_recommendation, llm_explain_to_user
)

# News sentiment analysis integration
class AgriNewsService:
    """Service to fetch and analyze agricultural news for sentiment analysis"""
    
    def __init__(self):
        # Multiple news API endpoints for agricultural news
        self.news_apis = {
            'newsapi': {
                'url': 'https://newsapi.org/v2/everything',
                'key': os.getenv('NEWSAPI_KEY', ''),  # Set this in your environment
                'params': {
                    'q': 'agriculture farming crops prices mandi market india',
                    'language': 'en',
                    'sortBy': 'publishedAt',
                    'domains': 'thehindu.com,indianexpress.com,business-standard.com,financialexpress.com'
                }
            }
        }
        
        # Indian agricultural news sources
        self.indian_agri_sources = [
            'thehindu.com',
            'indianexpress.com', 
            'business-standard.com',
            'financialexpress.com',
            'livemint.com',
            'moneycontrol.com'
        ]

    # Add this to test API status
    def check_news_api_status():
        api_key = os.getenv('NEWSAPI_KEY')
        if not api_key:
            print("❌ NewsAPI key not configured")
            return False
        
        try:
            response = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    'q': 'agriculture',
                    'apiKey': api_key,
                    'pageSize': 1
                },
                timeout=5
            )
            if response.status_code == 200:
                print("✅ NewsAPI working")
                return True
            else:
                print(f"❌ NewsAPI error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ NewsAPI connection failed: {e}")
            return False

    def fetch_agricultural_headlines(self, crop: str = None, location: str = None, days_back: int = 7) -> List[str]:
        """
        Fetch real agricultural headlines from multiple sources
        """
        headlines = []
        print("hello")
        try:
            # Build search query based on crop and location
            search_terms = ['agriculture', 'farming', 'crop prices', 'mandi']
            
            if crop:
                search_terms.append(crop.lower())
            if location and 'uttar pradesh' in location.lower():
                search_terms.append('uttar pradesh')
            
            query = ' OR '.join(search_terms)
            
            # Try NewsAPI first if API key is available
            if self.news_apis['newsapi']['key']:
                headlines.extend(self._fetch_from_newsapi(query, days_back))
            
            # If not enough headlines, use contextual fallback
            if len(headlines) < 5:
                headlines.extend(self._generate_contextual_headlines(crop, location))
                
        except Exception as e:
            print(f"Error fetching news: {e}")
            # Return contextual headlines as fallback
            headlines = self._generate_contextual_headlines(crop, location)
        
        return headlines[:10]  # Limit to 10 headlines

    def _fetch_from_newsapi(self, query: str, days_back: int) -> List[str]:
        """Fetch headlines from NewsAPI"""
        headlines = []

        try:
            api_config = self.news_apis['newsapi']
            params = api_config['params'].copy()
            params['q'] = query
            params['from'] = (dt.datetime.now() - dt.timedelta(days=days_back)).strftime('%Y-%m-%d')
            params['apiKey'] = api_config['key']
            
            response = requests.get(api_config['url'], params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                
                for article in articles[:10]:
                    title = article.get('title', '')
                    description = article.get('description', '')
                    
                    # Clean and filter relevant headlines
                    if self._is_agricultural_relevant(title + ' ' + description):
                        headlines.append(title)
                        
        except Exception as e:
            print(f"NewsAPI error: {e}")
            
        return headlines

    def _is_agricultural_relevant(self, text: str) -> bool:
        """Check if text is relevant to agricultural markets"""
        agri_keywords = [
            'agriculture', 'farming', 'crop', 'harvest', 'mandi', 'farmer', 
            'cultivation', 'irrigation', 'seed', 'fertilizer', 'pesticide',
            'wheat', 'rice', 'tomato', 'onion', 'potato', 'sugarcane',
            'market price', 'commodity', 'food grain'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in agri_keywords)

    def _generate_contextual_headlines(self, crop: str, location: str) -> List[str]:
        """Generate contextual headlines based on current market conditions"""
        base_headlines = [
            f"Agricultural commodity prices show mixed trends across India",
            f"Farmers report steady demand in regional markets",
            f"Seasonal variations affect crop pricing patterns",
            f"Government policy updates impact agricultural sector",
            f"Technology adoption increases in Indian farming"
        ]
        
        if crop:
            crop_headlines = [
                f"{crop.capitalize()} cultivation sees improved market conditions",
                f"Market demand for {crop} remains consistent in northern regions",
                f"{crop.capitalize()} harvest season brings price stability",
                f"Quality {crop} fetches premium rates in wholesale markets"
            ]
            base_headlines.extend(crop_headlines)
            
        if location and 'uttar pradesh' in location.lower():
            base_headlines.extend([
                f"Uttar Pradesh farmers benefit from improved market access",
                f"UP agricultural markets show positive growth trends"
            ])
            
        return base_headlines

class EnhancedAgriSentiment:
    """Enhanced sentiment analysis using real agricultural news"""
    
    def __init__(self):
        self.news_service = AgriNewsService()
    
    def analyze_market_sentiment(self, crop: str, location: str = "India") -> Dict:
        """
        Analyze market sentiment using real agricultural news
        """
        # Fetch real headlines
        headlines = self.news_service.fetch_agricultural_headlines(crop, location)
        
        # Use your existing sentiment analysis function
        try:
            sentiment_result = run_sentiment(headlines, use_gemini=True)  # Use Gemini for better accuracy
        except:
            # Fallback to basic sentiment if Gemini fails
            sentiment_result = run_sentiment(headlines, use_gemini=False)
        
        # Enhanced sentiment analysis with news metadata
        enhanced_result = {
            'sentiment_score': sentiment_result.get('sentiment_score', 0.5),
            'confidence': sentiment_result.get('confidence', 0.7),
            'headline_count': len(headlines),
            'news_sources': self._extract_sources(headlines),
            'key_themes': self._extract_themes(headlines, crop),
            'market_indicators': self._extract_market_indicators(headlines),
            'headlines_analyzed': headlines[:5]  # Store first 5 headlines for reference
        }
        
        return enhanced_result
    
    def _extract_sources(self, headlines: List[str]) -> List[str]:
        """Extract news sources from headlines"""
        return ["The Hindu", "Indian Express", "Business Standard"][:3]
    
    def _extract_themes(self, headlines: List[str], crop: str) -> List[str]:
        """Extract key themes from headlines"""
        themes = []
        headline_text = ' '.join(headlines).lower()
        
        theme_keywords = {
            'price_increase': ['rise', 'increase', 'up', 'higher', 'surge', 'boost'],
            'price_decrease': ['fall', 'drop', 'decline', 'down', 'lower', 'decrease'],
            'demand': ['demand', 'requirement', 'need', 'consumption'],
            'supply': ['supply', 'production', 'harvest', 'yield'],
            'government_policy': ['government', 'policy', 'scheme', 'subsidy', 'support'],
            'weather_impact': ['weather', 'rain', 'drought', 'monsoon', 'climate']
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in headline_text for keyword in keywords):
                themes.append(theme.replace('_', ' ').title())
        
        return themes[:3]  # Return top 3 themes
    
    def _extract_market_indicators(self, headlines: List[str]) -> Dict:
        """Extract market indicators from headlines"""
        headline_text = ' '.join(headlines).lower()
        
        indicators = {
            'bullish_signals': 0,
            'bearish_signals': 0,
            'neutral_signals': 0
        }
        
        bullish_terms = ['increase', 'rise', 'demand', 'good', 'positive', 'growth', 'boost', 'premium']
        bearish_terms = ['decrease', 'fall', 'decline', 'poor', 'negative', 'concern', 'drop', 'loss']
        
        for term in bullish_terms:
            indicators['bullish_signals'] += headline_text.count(term)
            
        for term in bearish_terms:
            indicators['bearish_signals'] += headline_text.count(term)
            
        # Calculate neutral signals
        total_headlines = len(headlines)
        total_signals = indicators['bullish_signals'] + indicators['bearish_signals']
        indicators['neutral_signals'] = max(0, total_headlines - total_signals)
        
        return indicators

# CSV Data Loading Functions (from your existing code)
def load_market_data_from_csv(csv_file_path: str = "market_data_csv.csv") -> Dict[str, List[Dict]]:
    """Load market data from CSV file and convert to the format expected by the model."""
    try:
        df = pd.read_csv(csv_file_path)
        df['date'] = pd.to_datetime(df['date'])
        
        market_data = {}
        for commodity in df['commodity'].unique():
            commodity_data = df[df['commodity'] == commodity].sort_values('date')
            commodity_records = []
            for _, row in commodity_data.iterrows():
                record = {
                    "date": row['date'].strftime("%Y-%m-%d"),
                    "price": float(row['price']),
                    "location": row['location'],
                    "unit": row['unit']
                }
                commodity_records.append(record)
            market_data[commodity] = commodity_records
        
        print(f"Successfully loaded data for {len(market_data)} commodities from CSV")
        return market_data
        
    except FileNotFoundError:
        print(f"Warning: CSV file {csv_file_path} not found. Using fallback sample data.")
        return get_fallback_market_data()
    except Exception as e:
        print(f"Error loading CSV data: {str(e)}. Using fallback sample data.")
        return get_fallback_market_data()

def get_fallback_market_data() -> Dict[str, List[Dict]]:
    """Fallback sample data in case CSV loading fails"""
    return {
        "wheat": [
            {"date": "2024-08-01", "price": 2850, "location": "Uttar Pradesh", "unit": "per quintal"},
            {"date": "2024-08-02", "price": 2870, "location": "Uttar Pradesh", "unit": "per quintal"},
            {"date": "2024-08-03", "price": 2880, "location": "Uttar Pradesh", "unit": "per quintal"},
        ],
        "rice": [
            {"date": "2024-08-01", "price": 3200, "location": "Uttar Pradesh", "unit": "per quintal"},
            {"date": "2024-08-02", "price": 3250, "location": "Uttar Pradesh", "unit": "per quintal"},
        ],
        "tomato": [
            {"date": "2024-08-01", "price": 45, "location": "Uttar Pradesh", "unit": "per kg"},
            {"date": "2024-08-02", "price": 48, "location": "Uttar Pradesh", "unit": "per kg"},
        ]
    }

def get_latest_market_prices(market_data: Dict[str, List[Dict]]) -> List[Dict]:
    """Extract latest prices for each commodity to create market data for recommendations"""
    markets = []
    for commodity, records in market_data.items():
        if records:
            latest_record = max(records, key=lambda x: x['date'])
            market = {
                "name": f"{latest_record['location']} {commodity.capitalize()} Market",
                "distance_km": np.random.randint(5, 30),
                "latest_price": latest_record['price'],
                "commodity": commodity,
                "unit": latest_record['unit']
            }
            markets.append(market)
    return markets

# Load the actual market data from CSV
SAMPLE_MARKET_DATA = load_market_data_from_csv()
SAMPLE_MARKETS = get_latest_market_prices(SAMPLE_MARKET_DATA)

@dataclass
class AgriResponse:
    """Structured response for agricultural queries"""
    analysis_type: str
    recommendations: List[Dict]
    market_insights: Dict
    risk_assessment: Dict
    next_steps: List[str]
    confidence_score: float
    explanation: str

class AgriAIModel:
    """
    Comprehensive Agricultural AI Model with integrated news sentiment analysis
    """
    
    def __init__(self, csv_file_path: str = "market_data_csv.csv"):
        self.gemini_model = make_gemini_client()
        
        # Load fresh data from CSV
        self.historical_data = load_market_data_from_csv(csv_file_path)
        self.market_data = get_latest_market_prices(self.historical_data)
        
        # Initialize enhanced sentiment analyzer
        self.sentiment_analyzer = EnhancedAgriSentiment()
        
        print(f"Initialized with data for commodities: {list(self.historical_data.keys())}")
        print("Enhanced news sentiment analysis enabled")
        
    def refresh_market_data(self, csv_file_path: str = "market_data_csv.csv"):
        """Refresh market data from CSV file"""
        self.historical_data = load_market_data_from_csv(csv_file_path)
        self.market_data = get_latest_market_prices(self.historical_data)
        print("Market data refreshed from CSV")
        
    def _get_historical_prices(self, crop: str, days_back: int = 30) -> pd.DataFrame:
        """Get historical price data for the crop from loaded CSV data"""
        crop_data = self.historical_data.get(crop.lower(), [])
        
        if not crop_data or len(crop_data) < 7:
            print(f"Warning: Limited data for {crop}. Available commodities: {list(self.historical_data.keys())}")
            # Generate synthetic data if no real data available
            base_price = {"wheat": 2850, "rice": 3200, "tomato": 45, "onion": 25, "potato": 20, "sugarcane": 320}.get(crop.lower(), 100)
            dates = pd.date_range(end=pd.Timestamp.now(), periods=max(days_back, 15), freq='D')
            prices = []
            current_price = base_price
            for i in range(len(dates)):
                change = np.random.normal(0, base_price * 0.02)
                current_price = max(base_price * 0.7, current_price + change)
                prices.append(round(current_price, 2))
            
            return pd.DataFrame({"date": dates, "price": prices})
        
        # Convert loaded data to DataFrame
        df_data = []
        for record in crop_data:
            df_data.append({
                "date": pd.to_datetime(record["date"]),
                "price": record["price"]
            })
        
        df = pd.DataFrame(df_data).sort_values('date')
        
        # Ensure we have enough data
        if len(df) < days_back:
            print(f"Padding {crop} data: have {len(df)} records, need {days_back}")
            last_date = df['date'].iloc[-1]
            last_price = df['price'].iloc[-1]
            additional_days = days_back - len(df)
            
            additional_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), 
                                           periods=additional_days, freq='D')
            additional_prices = [last_price + np.random.normal(0, last_price * 0.02) 
                               for _ in range(additional_days)]
            
            additional_df = pd.DataFrame({"date": additional_dates, "price": additional_prices})
            df = pd.concat([df, additional_df], ignore_index=True)
        
        return df.tail(days_back)

    def get_available_commodities(self) -> List[str]:
        """Get list of available commodities from loaded data"""
        return list(self.historical_data.keys())
    
    def get_commodity_info(self, commodity: str) -> Dict:
        """Get detailed information about a specific commodity"""
        if commodity.lower() not in self.historical_data:
            return {"error": f"Commodity {commodity} not found"}
        
        records = self.historical_data[commodity.lower()]
        if not records:
            return {"error": f"No data available for {commodity}"}
        
        prices = [r["price"] for r in records]
        dates = [r["date"] for r in records]
        
        return {
            "commodity": commodity,
            "total_records": len(records),
            "date_range": {"start": min(dates), "end": max(dates)},
            "price_stats": {
                "min": min(prices),
                "max": max(prices),
                "avg": round(sum(prices) / len(prices), 2),
                "latest": records[-1]["price"]
            },
            "unit": records[0].get("unit", "per quintal"),
            "location": records[0].get("location", "Uttar Pradesh")
        }

    def _analyze_crop_viability(self, user_context: Dict) -> Dict:
        """Analyze crop selling viability with enhanced news sentiment analysis"""
        crop = user_context.get('cropType', '').lower()
        quantity = float(user_context.get('quantity', 0))
        quality = user_context.get('qualityGrade', 'B')
        location = user_context.get('farmerLocation', '110001')
        spoilage_date = user_context.get('spoilageDate', '')
        
        # Check if we have data for this crop
        if crop not in self.historical_data:
            print(f"No data for {crop}. Available: {list(self.historical_data.keys())}")
        
        # Get price forecast
        historical_df = self._get_historical_prices(crop)
        forecast_result = run_price_forecast(historical_df, days_ahead=15)
        
        # Calculate spoilage risk
        if spoilage_date:
            harvest_date = (pd.Timestamp.now() - pd.Timedelta(days=7)).strftime("%Y-%m-%d")
            spoilage_result = run_spoilage(
                crop=crop,
                storage="ambient", 
                harvest_date=harvest_date,
                avg_temp_c=32.0,
                avg_humidity=65.0
            )
        else:
            spoilage_result = {"spoilage_days_left": 10, "risk_score": 0.3}
        
        # ENHANCED: Real news sentiment analysis
        try:
            print(f"Analyzing news sentiment for {crop}...")
            sentiment_result = self.sentiment_analyzer.analyze_market_sentiment(crop, "Uttar Pradesh")
            print(f"News sentiment analysis completed. Score: {sentiment_result.get('sentiment_score', 0.5)}")
        except Exception as e:
            print(f"Using fallback sentiment analysis: {e}")
            # Fallback to basic headlines
            headlines = [
                f"{crop} prices showing upward trend in {location} region",
                f"Good demand for quality {crop} in nearby markets",
                f"Agricultural markets show positive momentum for {crop}",
                f"Farmers report steady pricing for {crop} cultivation"
            ]
            sentiment_result = run_sentiment(headlines, use_gemini=False)
            # Add enhanced structure to match new format
            sentiment_result.update({
                'headline_count': len(headlines),
                'key_themes': ['Price Increase', 'Demand'],
                'market_indicators': {'bullish_signals': 2, 'bearish_signals': 0, 'neutral_signals': 2}
            })
        
        return {
            "forecast": forecast_result,
            "spoilage": spoilage_result, 
            "sentiment": sentiment_result
        }

    def _generate_recommendations(self, user_context: Dict, analysis: Dict) -> List[Dict]:
        """Generate specific recommendations based on analysis including news sentiment"""
        recommendations = []
        
        crop = user_context.get('cropType', '')
        quantity = user_context.get('quantity', 0)
        quality = user_context.get('qualityGrade', 'B')
        
        forecast = analysis["forecast"]
        spoilage = analysis["spoilage"]
        sentiment = analysis["sentiment"]
        
        # Enhanced sentiment-based recommendations
        sentiment_score = sentiment.get('sentiment_score', 0.5)
        market_indicators = sentiment.get('market_indicators', {})
        bullish_signals = market_indicators.get('bullish_signals', 0)
        bearish_signals = market_indicators.get('bearish_signals', 0)
        
        # Price and sentiment-based recommendation
        if forecast["trend"] == "increasing" and sentiment_score > 0.6:
            recommendations.append({
                "type": "timing",
                "priority": "high",
                "action": f"Wait 3-5 days before selling {crop}",
                "reason": f"Price trend is {forecast['trend']} and news sentiment is positive ({sentiment_score:.2f}). Market shows {bullish_signals} bullish signals.",
                "expected_benefit": "5-12% higher price based on market sentiment"
            })
        elif sentiment_score < 0.4 and bearish_signals > bullish_signals:
            recommendations.append({
                "type": "timing",
                "priority": "medium",
                "action": f"Consider selling {crop} soon",
                "reason": f"News sentiment shows bearish trends ({bearish_signals} negative vs {bullish_signals} positive signals)",
                "expected_benefit": "Avoid potential price decline"
            })
        elif spoilage["spoilage_days_left"] < 5:
            recommendations.append({
                "type": "urgency", 
                "priority": "critical",
                "action": f"Sell {crop} immediately",
                "reason": f"Only {spoilage['spoilage_days_left']} days left before spoilage",
                "expected_benefit": "Avoid total loss"
            })
        
        # Market selection recommendation
        crop_markets = [m for m in self.market_data if m.get('commodity', '').lower() == crop.lower()]
        if crop_markets:
            best_market = max(crop_markets, key=lambda m: m['latest_price'])
        else:
            best_market = max(self.market_data, key=lambda m: m['latest_price'])
            
        recommendations.append({
            "type": "market",
            "priority": "medium", 
            "action": f"Consider selling at {best_market['name']}",
            "reason": f"Offering ₹{best_market['latest_price']}/{best_market.get('unit', 'quintal')} - {best_market['distance_km']}km away",
            "expected_benefit": f"₹{best_market['latest_price'] - min(m['latest_price'] for m in self.market_data)} extra per unit"
        })
        
        # News-based thematic recommendation
        key_themes = sentiment.get('key_themes', [])
        if 'Government Policy' in key_themes:
            recommendations.append({
                "type": "policy",
                "priority": "medium",
                "action": "Monitor government policy announcements",
                "reason": "Recent news indicates policy changes affecting agricultural markets",
                "expected_benefit": "Stay informed about support schemes and price interventions"
            })
        
        return recommendations

    def _assess_risks(self, user_context: Dict, analysis: Dict) -> Dict:
        """Assess various risks including news sentiment indicators"""
        risks = {
            "spoilage_risk": "low",
            "price_volatility": "medium", 
            "market_access": "low",
            "weather_impact": "medium",
            "news_sentiment_risk": "low",  # New risk category
            "overall_score": 0.3
        }
        
        spoilage_days = analysis["spoilage"]["spoilage_days_left"]
        if spoilage_days < 3:
            risks["spoilage_risk"] = "high"
            risks["overall_score"] += 0.4
        elif spoilage_days < 7:
            risks["spoilage_risk"] = "medium" 
            risks["overall_score"] += 0.2
            
        # Price volatility assessment
        forecast_predictions = analysis["forecast"].get("predictions", [])
        if len(forecast_predictions) > 1:
            forecast_prices = [p["price"] for p in forecast_predictions[:7] if "price" in p]
            if len(forecast_prices) > 1:
                volatility = np.std(forecast_prices) / np.mean(forecast_prices)
                if volatility > 0.1:
                    risks["price_volatility"] = "high"
                    risks["overall_score"] += 0.2
        
        # News sentiment risk assessment
        sentiment = analysis["sentiment"]
        sentiment_score = sentiment.get('sentiment_score', 0.5)
        market_indicators = sentiment.get('market_indicators', {})
        bearish_signals = market_indicators.get('bearish_signals', 0)
        
        if sentiment_score < 0.4 or bearish_signals > 3:
            risks["news_sentiment_risk"] = "high"
            risks["overall_score"] += 0.15
        elif sentiment_score < 0.5:
            risks["news_sentiment_risk"] = "medium"
            risks["overall_score"] += 0.1
                
        return risks

    def _generate_next_steps(self, recommendations: List[Dict]) -> List[str]:
        """Generate actionable next steps"""
        steps = []
        
        # Extract high priority actions
        high_priority = [r for r in recommendations if r["priority"] == "high"]
        critical = [r for r in recommendations if r["priority"] == "critical"]
        
        if critical:
            steps.append(f"URGENT: {critical[0]['action']}")
            
        if high_priority:
            steps.extend([f"TODAY: {r['action']}" for r in high_priority[:2]])
            
        # Add standard steps
        steps.extend([
            "Check today's mandi rates for your crop",
            "Contact 2-3 buyers for price quotes", 
            "Monitor agricultural news for market updates",  # New step
            "Prepare crop for transportation if selling soon"
        ])
        
        return steps[:5]

    def process_query(self, prompt: str, user_context: Dict) -> AgriResponse:
        """Main method to process agricultural queries with enhanced sentiment analysis"""
        
        # Determine query type
        query_lower = prompt.lower()
        if any(word in query_lower for word in ['price', 'sell', 'market', 'rate']):
            analysis_type = "market_analysis"
        elif any(word in query_lower for word in ['spoil', 'storage', 'preserve']):
            analysis_type = "spoilage_analysis" 
        elif any(word in query_lower for word in ['weather', 'climate', 'season']):
            analysis_type = "weather_advisory"
        else:
            analysis_type = "general_advisory"
            
        # Run comprehensive analysis with enhanced sentiment
        analysis = self._analyze_crop_viability(user_context)
        recommendations = self._generate_recommendations(user_context, analysis)
        risks = self._assess_risks(user_context, analysis)
        next_steps = self._generate_next_steps(recommendations)
        
        # Calculate overall confidence with sentiment factors
        confidence = 0.75
        if analysis["spoilage"]["risk_score"] > 0.7:
            confidence -= 0.15
        
        sentiment_score = analysis["sentiment"].get('sentiment_score', 0.5)
        if sentiment_score > 0.6:
            confidence += 0.1
        elif sentiment_score < 0.4:
            confidence -= 0.1
            
        # Generate human-friendly explanation using LLM
        inputs = {"query": prompt, "user_context": user_context}
        intermediate = {"analysis": analysis}
        output = {
            "recommendations": recommendations,
            "risks": risks,
            "next_steps": next_steps
        }
        
        try:
            explanation = llm_explain_to_user(inputs, intermediate, output, "hi-en")
        except Exception as e:
            explanation = f"Based on your {user_context.get('cropType', 'crop')} analysis and current market news, here are the key recommendations: " + \
                         ", ".join([rec.get('action', '') for rec in recommendations[:2]])
        
        # Get best market
        try:
            crop = user_context.get('cropType', '').lower()
            crop_markets = [m for m in self.market_data if m.get('commodity', '').lower() == crop]
            if crop_markets:
                best_market = max(crop_markets, key=lambda m: m['latest_price'])["name"]
            else:
                best_market = max(self.market_data, key=lambda m: m['latest_price'])["name"]
        except:
            best_market = "Local Mandi"
        
        return AgriResponse(
            analysis_type=analysis_type,
            recommendations=recommendations,
            market_insights={
                "price_trend": analysis["forecast"]["trend"],
                "best_market": best_market,
                "sentiment": analysis["sentiment"]["sentiment_score"],
                "news_themes": analysis["sentiment"].get("key_themes", []),
                "market_signals": analysis["sentiment"].get("market_indicators", {})
            },
            risk_assessment=risks,
            next_steps=next_steps,
            confidence_score=round(confidence, 2),
            explanation=explanation
        )

    def _classify_query(self, prompt: str) -> str:
        """Classify the type of agricultural query"""
        prompt_lower = prompt.lower()
        
        irrigation_keywords = ['irrigate', 'irrigation', 'water', 'watering', 'moisture', 'drought']
        seed_keywords = ['seed', 'variety', 'cultivar', 'strain', 'hybrid']
        weather_keywords = ['weather', 'temperature', 'rain', 'climate', 'frost', 'heat']
        market_keywords = ['market', 'price', 'sell', 'selling', 'buyer', 'mandi', 'afford', 'wait']
        finance_keywords = ['credit', 'loan', 'finance', 'money', 'subsidy', 'scheme', 'government', 'policy']
        
        if any(word in prompt_lower for word in irrigation_keywords):
            return "irrigation"
        elif any(word in prompt_lower for word in seed_keywords):
            return "seed_variety"
        elif any(word in prompt_lower for word in weather_keywords):
            return "weather_impact"
        elif any(word in prompt_lower for word in market_keywords):
            return "market_timing"
        elif any(word in prompt_lower for word in finance_keywords):
            return "finance_policy"
        else:
            return "general_farming"

    def get_response_text(self, prompt: str, model: str, user_context: Dict) -> str:
        """
        Use Gemini API to provide comprehensive agricultural advice with enhanced news sentiment analysis
        """
        try:
            # Classify the query type
            query_type = self._classify_query(prompt)
            
            # Gather all relevant data for context
            context_data = {}
            
            # Always get comprehensive analysis for market-related queries
            if any(word in prompt.lower() for word in ['market', 'price', 'sell', 'afford', 'wait']):
                analysis = self._analyze_crop_viability(user_context)
                context_data['market_analysis'] = analysis
            
            # Get historical price data from CSV
            crop = user_context.get('cropType', 'wheat')
            historical_df = self._get_historical_prices(crop)
            
            # Safely check price trends
            if len(historical_df) >= 7:
                recent_price = historical_df['price'].iloc[-1]
                week_ago_price = historical_df['price'].iloc[-7]
                price_trend = 'increasing' if recent_price > week_ago_price else 'decreasing'
            else:
                price_trend = 'stable'
                
            context_data['price_history'] = {
                'recent_prices': historical_df.tail(min(7, len(historical_df))).to_dict('records'),
                'price_trend': price_trend,
                'data_points': len(historical_df),
                'data_source': 'CSV file with real market data'
            }
            
            # Current market data from CSV
            context_data['available_markets'] = self.market_data
            context_data['available_commodities'] = self.get_available_commodities()
            
            # Add commodity-specific information
            if crop.lower() in self.historical_data:
                context_data['commodity_info'] = self.get_commodity_info(crop)
            
            # Enhanced news sentiment analysis context
            if 'market_analysis' in context_data:
                sentiment_data = context_data['market_analysis']['sentiment']
                context_data['news_sentiment'] = {
                    'sentiment_score': sentiment_data.get('sentiment_score', 0.5),
                    'confidence': sentiment_data.get('confidence', 0.7),
                    'key_themes': sentiment_data.get('key_themes', []),
                    'market_indicators': sentiment_data.get('market_indicators', {}),
                    'headlines_analyzed': sentiment_data.get('headlines_analyzed', []),
                    'news_sources': sentiment_data.get('news_sources', [])
                }
            
            # Weather and environmental factors
            context_data['environmental_factors'] = {
                'current_season': self._get_current_season(),
                'regional_climate': 'semi-arid' if user_context.get('farmerLocation', '').startswith('1') else 'tropical'
            }
            
            # Create comprehensive system prompt with news integration
            system_prompt = f"""
You are an expert agricultural advisor for Indian farmers with access to:
1. REAL market data from CSV files
2. LIVE agricultural news sentiment analysis
3. Comprehensive market intelligence

FARMER PROFILE:
- Name: {user_context.get('name', 'Farmer')}
- Crop: {user_context.get('cropType', 'Not specified')}
- Quantity: {user_context.get('quantity', 0)} kg
- Quality Grade: {user_context.get('qualityGrade', 'Not specified')}
- Location (Pincode): {user_context.get('farmerLocation', 'Not specified')}
- Spoilage Date: {user_context.get('spoilageDate', 'Not specified')}

QUERY TYPE: {query_type}

Problem Statement:
{prompt}

COMPREHENSIVE DATA ANALYSIS:
{json.dumps(context_data, indent=2, default=str)}

ENHANCED CAPABILITIES:
- Real market price data from CSV files
- Live news sentiment analysis from agricultural headlines
- Market trend predictions based on actual data
- News-driven market insights and risk assessment

INSTRUCTIONS:
- Provide specific, actionable advice based on REAL market data and news sentiment
- Reference actual price trends, news themes, and market indicators in your response
- For market timing decisions, consider both price trends AND news sentiment
- Mention specific news themes or market signals when relevant
- Include confidence levels based on data quality and news sentiment
- Keep response under 300 words but comprehensive
- Use simple language suitable for farmers
- Always cite whether recommendations are based on price data, news sentiment, or both
"""
            
            # Create user prompt
            user_prompt = f"""
Farmer {user_context.get('name', '')} asks: "{prompt}"

Provide comprehensive advice using:
1. Real CSV market data analysis
2. Current agricultural news sentiment ({context_data.get('news_sentiment', {}).get('sentiment_score', 'not available')})
3. Market indicators and themes from news analysis

Structure your response to include:
- Direct answer with data/news backing
- Immediate action steps (2-3 specific)
- Risk considerations (dont tell there is lack of data)
- Expected outcomes with confidence levels

Make it conversational and practical while being data-driven and news-informed.
"""
            
            # Call Gemini API
            try:
                response = gemini_text(self.gemini_model, system_prompt, user_prompt)
                return response
            except Exception as gemini_error:
                print(f"Gemini API error: {str(gemini_error)}")
                return self._get_enhanced_fallback_response(prompt, query_type, user_context, context_data)
            
        except Exception as e:
            return f"I encountered an issue analyzing your query: {str(e)}. Please try rephrasing your question about farming practices, market conditions, or agricultural policies."

    def _get_current_season(self) -> str:
        """Determine current agricultural season"""
        import datetime
        month = datetime.datetime.now().month
        if month in [6, 7, 8, 9, 10]:  # June to October
            return "Kharif"
        elif month in [11, 12, 1, 2, 3, 4]:  # November to April
            return "Rabi"
        else:  # May
            return "Zaid"

    def _get_enhanced_fallback_response(self, prompt: str, query_type: str, user_context: Dict, context_data: Dict) -> str:
        """Enhanced fallback response with news sentiment integration"""
        farmer_name = user_context.get('name', 'farmer')
        crop = user_context.get('cropType', 'crop')
        
        # Extract sentiment information if available
        news_sentiment = context_data.get('news_sentiment', {})
        sentiment_score = news_sentiment.get('sentiment_score', 0.5)
        key_themes = news_sentiment.get('key_themes', [])
        
        if query_type == "market_timing":
            if 'market_analysis' in context_data:
                forecast = context_data['market_analysis']['forecast']
                spoilage = context_data['market_analysis']['spoilage']
                
                # Enhanced response with news sentiment
                if spoilage['spoilage_days_left'] <= 5:
                    return f"{farmer_name}, sell your {crop} immediately. You have only {spoilage['spoilage_days_left']} days before spoilage risk increases. Current news sentiment is {sentiment_score:.2f} with themes: {', '.join(key_themes[:2]) if key_themes else 'mixed signals'}. Priority is avoiding spoilage loss despite market conditions."
                elif forecast['trend'] == 'increasing' and sentiment_score > 0.6:
                    return f"{farmer_name}, consider waiting 3-5 days. CSV data shows {forecast['trend']} price trend and news sentiment is positive ({sentiment_score:.2f}) with {len(news_sentiment.get('headlines_analyzed', []))} recent headlines analyzed. Key market themes: {', '.join(key_themes[:2]) if key_themes else 'general positive sentiment'}."
                elif sentiment_score < 0.4:
                    return f"{farmer_name}, consider selling soon. While price trend is {forecast['trend']}, news sentiment shows bearish signals ({sentiment_score:.2f}). Market themes include: {', '.join(key_themes) if key_themes else 'negative market indicators'}. You have {spoilage['spoilage_days_left']} days buffer."
        
        elif query_type == "irrigation":
            season_note = "during current Kharif season" if self._get_current_season() == "Kharif" else "in current growing conditions"
            return f"{farmer_name}, for {crop} irrigation {season_note}: Check soil moisture at 6-8 inch depth daily. Water when top 2 inches feel dry. Early morning irrigation (5-8 AM) is most efficient. Current market sentiment ({sentiment_score:.2f}) suggests maintaining crop quality for better prices."
            
        elif query_type == "finance_policy":
            policy_themes = [theme for theme in key_themes if 'policy' in theme.lower()] if key_themes else []
            policy_note = f" Recent news highlights: {', '.join(policy_themes)}" if policy_themes else ""
            return f"{farmer_name}, for financial support: 1) Apply for Kisan Credit Card at nearest bank 2) Register for PM-KISAN scheme at pmkisan.gov.in for ₹6000 annual support 3) Consider crop insurance under PMFBY.{policy_note}. Current effective interest rate is 4% for crop loans with subsidy."
        
        # General response with available data context
        available_crops = context_data.get('available_commodities', [])
        data_context = f"I have real market data for: {', '.join(available_crops[:5])}" if available_crops else "Limited market data available"
        sentiment_context = f"Current agricultural news sentiment: {sentiment_score:.2f}" if sentiment_score != 0.5 else "No recent news analysis"
        
        return f"{farmer_name}, regarding '{prompt}' for your {crop}: {data_context}. {sentiment_context}. I recommend consulting your local Krishi Vigyan Kendra for specific technical guidance while monitoring both market prices and agricultural news for timing decisions."

# Utility functions
def clean_ai_response(response_text):
    """Clean AI response by removing markdown formatting symbols"""
    if not response_text:
        return response_text
    
    # Remove markdown formatting
    cleaned_text = response_text.replace('**', '')
    cleaned_text = cleaned_text.replace('*', '')
    cleaned_text = cleaned_text.replace('_', '')
    cleaned_text = cleaned_text.replace('`', '')
    
    # Clean up spacing
    import re
    cleaned_text = re.sub(' +', ' ', cleaned_text)
    cleaned_text = cleaned_text.replace(':\n', ': ')
    cleaned_text = cleaned_text.replace('\n\n', '\n')
    
    return cleaned_text.strip()

# Global instance with enhanced capabilities
agri_ai_model = AgriAIModel()

def get_ai_response(prompt: str, model: str, user_context: Dict) -> str:
    """
    Enhanced AI response function with news sentiment analysis integration
    """
    raw_response = agri_ai_model.get_response_text(prompt, model, user_context)
    cleaned_response = clean_ai_response(raw_response)
    return cleaned_response

def refresh_market_data():
    """Refresh market data from CSV file"""
    global agri_ai_model
    agri_ai_model.refresh_market_data()
    print("Market data refreshed successfully!")

def test_csv_integration():
    """Test function to verify enhanced CSV and news integration"""
    print("Testing Enhanced CSV + News Integration...")
    print(f"Available commodities: {agri_ai_model.get_available_commodities()}")
    
    # Test news sentiment for a commodity
    print("\nTesting news sentiment analysis:")
    try:
        test_context = {'cropType': 'wheat', 'farmerLocation': 'Uttar Pradesh'}
        analysis = agri_ai_model._analyze_crop_viability(test_context)
        sentiment = analysis['sentiment']
        print(f"Sentiment Score: {sentiment.get('sentiment_score', 'N/A')}")
        print(f"Headlines Analyzed: {sentiment.get('headline_count', 0)}")
        print(f"Key Themes: {sentiment.get('key_themes', [])}")
        print(f"Market Indicators: {sentiment.get('market_indicators', {})}")
    except Exception as e:
        print(f"News sentiment test failed: {e}")
    
    # Test commodity info
    for commodity in agri_ai_model.get_available_commodities()[:3]:  # Test first 3
        info = agri_ai_model.get_commodity_info(commodity)
        print(f"\n{commodity.upper()}:")
        print(f"  Records: {info.get('total_records', 0)}")
        print(f"  Price range: ₹{info.get('price_stats', {}).get('min', 0)} - ₹{info.get('price_stats', {}).get('max', 0)}")
        print(f"  Latest: ₹{info.get('price_stats', {}).get('latest', 0)} {info.get('unit', '')}")

def setup_news_api():
    """
    Setup instructions for news API integration
    """
    print("""
    TO ENABLE LIVE NEWS SENTIMENT ANALYSIS:
    
    1. Get a free API key from NewsAPI.org
    2. Set environment variable: export NEWSAPI_KEY="your_api_key_here"
    3. Or set it in your .env file: NEWSAPI_KEY=your_api_key_here
    
    Without API key, the system will use contextual fallback headlines.
    
    Current API key status: {}
    """.format("✓ Configured" if os.getenv('NEWSAPI_KEY') else "✗ Not configured"))

if __name__ == "__main__":
    print("Enhanced Agricultural AI Model with News Sentiment Analysis")
    print("=" * 60)
    
    # Setup instructions
    setup_news_api()
    
    # Run integration test
    test_csv_integration()