# 🥦 Nutrition Tracker

A comprehensive nutrition tracking application with AI-powered recipe import, built with FastAPI and Streamlit.

## ✨ Features

- **📊 Daily Food Logging** - Track your meals and nutrition intake with ease
- **📖 Recipe Manager** - Create and manage both direct and granular recipes
- **✨ AI Import** - Upload food photos and let AI automatically create recipes
- **🎯 Dual Recipe Types**:
  - **Granular**: Ingredient-level decomposition with editable components
  - **Direct**: Top-level nutrition entry for quick logging
- **📏 Portion Control** - Flexible serving size adjustments with multipliers
- **💾 Local Storage** - SQLite database for reliable local data storage

## 🏗️ Architecture

- **Backend**: FastAPI with SQLAlchemy ORM
- **Frontend**: Streamlit with custom styling
- **Database**: SQLite (local disk)
- **AI**: OpenAI GPT-4o for image analysis

## 📦 Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd Nutrition
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API key:
```
OPENAI_API_KEY=your_api_key_here
```

## 🚀 Running the Application

1. Start the FastAPI backend:
```bash
uvicorn backend.main:app --reload
```

2. In a separate terminal, start the Streamlit frontend:
```bash
streamlit run frontend/Home.py
```

3. Open your browser to `http://localhost:8501`

## 📁 Project Structure

```
Nutrition/
├── backend/
│   ├── main.py           # FastAPI app & endpoints
│   ├── models.py         # SQLAlchemy models
│   ├── schemas.py        # Pydantic schemas
│   ├── database.py       # Database configuration
│   ├── services.py       # Business logic
│   ├── ai_service.py     # AI image analysis
│   └── prompts/
│       └── image_analysis.md
├── frontend/
│   ├── Home.py           # Main daily logger
│   ├── api_client.py     # Backend API client
│   └── pages/
│       ├── Recipe_Manager.py
│       └── AI_Import.py
├── .streamlit/
│   └── config.toml       # Streamlit theme
├── requirements.txt
└── README.md
```

## 🎨 Features in Detail

### Daily Food Logger
- Select date to view meals
- See detailed nutrition breakdown per meal
- View daily totals with beautiful metrics
- Quick nutrition preview before logging

### Recipe Manager
- View all recipes with ingredient breakdowns
- Edit recipes directly (name, serving size, nutrition)
- Delete recipes
- Convert granular recipes to direct (flatten)
- Interactive ingredient tables

### AI Import
- Upload food photos
- AI automatically identifies ingredients and quantities
- Review and edit AI-generated data
- Save as either granular or direct recipe

## 🔧 Technology Stack

- **FastAPI** - Modern, fast web framework
- **Streamlit** - Beautiful data apps
- **SQLAlchemy** - SQL toolkit and ORM
- **Pydantic** - Data validation
- **OpenAI GPT-4o** - Image analysis
- **SQLite** - Embedded database

## 📝 License

MIT

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## 🙏 Acknowledgments

Built with modern Python tools and AI-powered features for accurate nutrition tracking.

