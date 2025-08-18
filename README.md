# Agricultural AI Chatbot

An intelligent agricultural assistant that helps farmers make informed decisions about crop selling, market timing, and agricultural practices using AI-powered analysis and real-time market data.

## Features

### Core Functionality
- **Intelligent Chat Interface**: Text and voice-based interaction with AI agricultural advisor
- **Multi-language Support**: Hindi and English language support with automatic translation
- **Real-time Market Analysis**: Live price forecasting using historical market data
- **News Sentiment Analysis**: Agricultural news sentiment analysis to gauge market conditions
- **Spoilage Risk Assessment**: Calculate crop spoilage timeline based on storage conditions
- **Personalized Recommendations**: Tailored advice based on user context (crop type, quantity, location, quality grade)

### AI Models Integration
- **Google Gemini**: Primary AI model for natural language processing and generation
- **Prophet**: Advanced time series forecasting for price predictions
- **Custom Market Intelligence**: Fusion of multiple data sources for comprehensive analysis

### User Types Supported
- **Farmers (Sellers)**: Crop selling optimization and market timing advice
- **Vendors (Buyers/Sellers)**: Market analysis and trading recommendations
- **General Users**: Agricultural information and guidance

## Tech Stack

### Backend
- **Flask**: Web framework for API endpoints
- **Python 3.8+**: Core programming language
- **Google Generative AI**: Gemini API integration
- **pandas/numpy**: Data processing and analysis
- **Prophet**: Time series forecasting
- **NewsAPI**: Real-time agricultural news integration
- **deep-translator**: Multi-language support

### Frontend
- **React**: Modern web framework with hooks
- **Lucide React**: Icon components
- **MediaRecorder API**: Voice recording functionality
- **Fetch API**: Backend communication

## Installation

### Prerequisites
- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn package manager

### Backend Setup

1. **Clone and setup environment**
```bash
git clone <repository-url>
cd agricultural-ai-chatbot
python -m venv agri_env
source agri_env/bin/activate  # Windows: agri_env\Scripts\activate
```

2. **Install dependencies**
```bash
pip install flask flask-cors google-generativeai pandas numpy
pip install requests deep-translator python-dotenv prophet statsmodels
```

3. **Configure environment variables**
Create `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
NEWSAPI_KEY=your_newsapi_key_here
```

### Frontend Setup

1. **Create React application**
```bash
npx create-react-app frontend
cd frontend
npm install lucide-react
```

2. **Configure proxy**
Add to `package.json`:
```json
"proxy": "http://localhost:5000"
```

3. **Replace App.js** with provided App.jsx content

## Usage

### Starting the Application

1. **Start Backend Server**
```bash
python app.py
```
Server runs on `http://localhost:5000`

2. **Start Frontend**
```bash
cd frontend
npm start
```
Application available at `http://localhost:3000`

### API Endpoints

#### Text Chat
```bash
POST /api/chat
Content-Type: application/json

{
  "prompt": "Should I sell my wheat now?",
  "model": "gemini-1.5-flash",
  "userContext": {
    "name": "Farmer Name",
    "cropType": "wheat",
    "quantity": "100",
    "qualityGrade": "A",
    "farmerLocation": "110001",
    "spoilageDate": "2024-09-15"
  }
}
```

#### Audio Chat
```bash
POST /api/audio-chat
Content-Type: multipart/form-data

Form Data:
- audio: [audio file]
- model: "gemini-1.5-flash"
- userContext: [JSON string]
```

## Configuration

### Market Data Format
CSV file should contain:
- `date`: YYYY-MM-DD format
- `commodity`: Crop name (wheat, rice, tomato)
- `price`: Numeric price value
- `location`: Geographic location
- `unit`: Price unit (per quintal, per kg)

### Supported Crops
- Wheat
- Rice  
- Tomato
- Onion
- Potato
- Sugarcane
- Other common crops (extensible)

### Quality Grades
- A: Premium quality
- B: Good quality  
- C: Average quality
- D: Below average quality

## Features in Detail

### Price Forecasting
- Historical data analysis using Prophet and ExponentialSmoothing
- 15-day price predictions
- Trend analysis (increasing/decreasing/stable)
- Market volatility assessment

### Spoilage Risk Calculation
- Crop-specific shelf life estimation
- Storage condition impact (temperature, humidity)
- Time since harvest consideration
- Risk score calculation (0-1 scale)

### News Sentiment Analysis
- Real-time agricultural news fetching
- Sentiment scoring for market impact
- Key theme extraction
- Market signal identification (bullish/bearish/neutral)

### Decision Fusion Engine
- Multi-factor recommendation system
- Price forecast integration
- Spoilage risk consideration
- Market sentiment analysis
- Storage cost calculations
- Alternative market suggestions

## Customization

### Adding New Crops
1. Update `BASE_SHELF_LIFE` in `model_service.py`
2. Add crop-specific data to CSV files
3. Update market data sources

### Extending AI Models
1. Add new model configurations in backend
2. Update model selection in frontend
3. Implement model-specific API calls

### Language Support
- Modify language detection in `app.py`
- Add new language codes to translation service
- Update UI text for internationalization

## Development

### Project Structure
```
agricultural-ai-chatbot/
├── app.py                    # Flask application
├── ai_model_service.py       # Enhanced AI service with news analysis
├── model_service.py          # Core ML models and forecasting
├── market_data_csv.csv       # Sample market data
├── .env                      # Environment variables
├── requirements.txt          # Python dependencies
└── frontend/
    ├── src/
    │   └── App.jsx          # React main component
    └── package.json         # Node.js dependencies
```
## API Keys Required

### Google Gemini API
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create new project and generate API key
3. Add to `.env` as `GEMINI_API_KEY`

### NewsAPI (Optional)
1. Register at [NewsAPI.org](https://newsapi.org/)
2. Get free API key (1000 requests/day)
3. Add to `.env` as `NEWSAPI_KEY`

## Troubleshooting

### Common Issues
- **CORS errors**: Verify Flask-CORS configuration and proxy settings
- **API key errors**: Check `.env` file location and key validity
- **Audio not working**: Ensure HTTPS/localhost and browser permissions
- **CSV loading fails**: Verify file format and column names
- **Missing dependencies**: Run `pip install -r requirements.txt`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini AI for natural language processing
- NewsAPI for real-time agricultural news
- Prophet library for time series forecasting
- React and Flask communities for frameworks
- Agricultural domain experts for market insights
