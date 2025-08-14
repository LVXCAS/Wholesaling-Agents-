# 🤖 AI Data Processor - Real Estate Empire

An intelligent data preprocessing system that uses **Gemini AI** to automatically analyze, clean, and reformat data from ZIP archives for machine learning training.

## ✨ Features

### 🧠 AI-Powered Processing
- **Automatic Format Detection**: Gemini AI analyzes your data structure
- **Smart Data Cleaning**: AI suggests optimal preprocessing steps
- **ML Schema Generation**: Automatically creates ML-ready data formats
- **Quality Assessment**: Comprehensive data quality analysis

### 📁 Multi-Format Support
- **CSV** (.csv) - Comma-separated values
- **Excel** (.xlsx, .xls) - Microsoft Excel files
- **JSON** (.json) - JavaScript Object Notation
- **TSV** (.tsv) - Tab-separated values
- **Text** (.txt) - Plain text files

### 🎯 Processing Modes
1. **Auto Format**: Let AI determine the best ML format
2. **Custom Schema**: Provide your own target ML schema

### 💾 Export Options
- **CSV** - For data analysis and ML training
- **JSON** - For API integration and storage
- **Excel** - For business reporting

## 🚀 Quick Start

### 1. Launch the System
```bash
python launch_data_processor.py
```

This will:
- ✅ Check dependencies
- 🚀 Start the API server
- 🌐 Open the web interface
- 📚 Show usage instructions

### 2. Run the Demo
```bash
python demo_data_processor.py
```

This creates sample real estate data and demonstrates:
- 📦 ZIP file creation
- 🤖 Auto-processing
- 🎯 Schema-based processing
- 💾 Data export

### 3. Use the Web Interface
1. **Upload ZIP File**: Select your data archive
2. **Choose Mode**: Auto-format or custom schema
3. **Process**: Let AI analyze and reformat
4. **Review**: Check results and AI recommendations
5. **Export**: Download processed data

## 📋 API Endpoints

### Upload and Process
```http
POST /api/v1/data-processor/upload-zip
Content-Type: multipart/form-data

file: [ZIP file]
target_schema: [Optional JSON schema]
```

### Auto-Format
```http
POST /api/v1/data-processor/auto-format
Content-Type: multipart/form-data

file: [ZIP file]
```

### Export Data
```http
POST /api/v1/data-processor/export/{format}
Content-Type: application/json

{processed_data}
```

### Validate Schema
```http
POST /api/v1/data-processor/validate-schema
Content-Type: application/json

{schema}
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Frontend  │───▶│   FastAPI Server │───▶│  Gemini AI API  │
│                 │    │                  │    │                 │
│ • File Upload   │    │ • Data Processor │    │ • Analysis      │
│ • Progress UI   │    │ • ZIP Extraction │    │ • Reformatting  │
│ • Results View  │    │ • AI Integration │    │ • Recommendations│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │
         │                       ▼
         │              ┌──────────────────┐
         └─────────────▶│   File Storage   │
                        │                  │
                        │ • Temp Files     │
                        │ • Processed Data │
                        │ • Export Files   │
                        └──────────────────┘
```

## 🎯 ML Schema Format

```json
{
  "fields": {
    "price": {
      "type": "float",
      "required": true,
      "description": "Property sale price"
    },
    "bedrooms": {
      "type": "int",
      "min": 1,
      "max": 10
    },
    "location": {
      "type": "string",
      "enum": ["urban", "suburban", "rural"]
    }
  },
  "target_variable": "price",
  "ml_task": "regression",
  "preprocessing": {
    "handle_missing": "median",
    "scale_features": true,
    "encode_categorical": "onehot"
  }
}
```

## 🔧 Configuration

### Environment Variables
```bash
# Required for AI features
GEMINI_API_KEY=your_gemini_api_key_here

# Optional API configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### Dependencies
```bash
pip install fastapi uvicorn pandas google-generativeai python-multipart openpyxl
```

## 📊 Example Workflow

### 1. Real Estate Data Processing
```python
from app.services.data_processor_service import DataProcessorService

# Initialize processor
processor = DataProcessorService()

# Define ML schema for property price prediction
schema = {
    "fields": {
        "sale_price": {"type": "float", "required": True},
        "bedrooms": {"type": "int"},
        "square_feet": {"type": "int"},
        "location": {"type": "string"}
    },
    "target_variable": "sale_price",
    "ml_task": "regression"
}

# Process ZIP file
result = processor.process_zip_file("data.zip", schema)

# Export for ML training
output_file = processor.export_processed_data(result, "csv")
```

### 2. AI Analysis Results
```json
{
  "gemini_analysis": {
    "mapping_strategy": "Combine property sales and features data",
    "cleaning_steps": [
      "Remove duplicate property IDs",
      "Handle missing square footage with median",
      "Standardize property type categories"
    ],
    "feature_engineering": [
      "Create price_per_sqft feature",
      "Encode neighborhood as categorical",
      "Generate age_of_property from year_built"
    ],
    "recommendations": [
      "Consider log transformation for price",
      "Use cross-validation for model evaluation",
      "Monitor for data drift in production"
    ]
  }
}
```

## 🎨 Frontend Features

### Modern UI Components
- **Drag & Drop Upload**: Intuitive file selection
- **Progress Tracking**: Real-time processing updates
- **Tabbed Results**: Organized data presentation
- **Export Controls**: One-click data download
- **Responsive Design**: Works on all devices

### Interactive Elements
- **Schema Validation**: Real-time JSON validation
- **Sample Schemas**: Pre-built templates
- **Data Preview**: Tabular data display
- **AI Insights**: Formatted recommendations

## 🧪 Testing

### Run Demo
```bash
python demo_data_processor.py
```

### Test API Endpoints
```bash
# Start server
uvicorn app.api.main:app --reload

# Test with curl
curl -X POST "http://localhost:8000/api/v1/data-processor/auto-format" \
     -F "file=@sample_data.zip"
```

### Frontend Testing
1. Open `app/frontend/data-processor.html`
2. Upload sample ZIP file
3. Test both processing modes
4. Verify export functionality

## 🔍 Troubleshooting

### Common Issues

**API Key Not Found**
```bash
export GEMINI_API_KEY=your_key_here
```

**Server Won't Start**
```bash
pip install fastapi uvicorn
python -m uvicorn app.api.main:app --reload
```

**File Upload Fails**
- Check file size limits
- Ensure ZIP contains supported formats
- Verify API server is running

**AI Processing Errors**
- Confirm Gemini API key is valid
- Check internet connection
- Review data format compatibility

## 🚀 Production Deployment

### Docker Setup
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Configuration
```bash
# Production settings
GEMINI_API_KEY=prod_key_here
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

## 📈 Performance

### Benchmarks
- **Small Files** (<10MB): ~5-15 seconds
- **Medium Files** (10-100MB): ~30-60 seconds  
- **Large Files** (100MB+): ~2-5 minutes

### Optimization Tips
- Use specific schemas for faster processing
- Compress data before zipping
- Process files in smaller batches
- Monitor memory usage for large datasets

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

## 📄 License

This project is part of the Real Estate Empire system and follows the same licensing terms.

---

**Built with ❤️ using Gemini AI, FastAPI, and modern web technologies**