# BrandEye AI Pipeline - Setup & Run Guide

## Prerequisites
- **Python 3.8+** (Tested with Python 3.13)
- **Windows 10/11** (or Linux/Mac with equivalent commands)
- **8GB+ RAM** (for AI models)
- **Internet connection** (for initial model downloads)

## Quick Start (5 minutes)

### Step 1: Download & Extract
```bash
# Extract BrandEye.zip to your desired location
# Navigate to the BrandEye folder
cd BrandEye
```

### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt
```

### Step 4: Start the System
```bash
# Option 1: Automatic startup (Recommended)
python start_system.py

# Option 2: Manual startup
# Terminal 1: Start microservices
cd microservices
python start_all_services.py

# Terminal 2: Start main server
cd ..
python main_server.py
```

### Step 5: Access the Application
- **Open browser:** http://localhost:5000
- **Upload image:** Select a retail shelf image
- **View results:** See detected products with brand grouping

## Detailed Setup Instructions

### System Requirements
- **OS:** Windows 10/11, Linux (Ubuntu 18.04+), macOS (10.14+)
- **Python:** 3.8 or higher
- **RAM:** 8GB minimum, 16GB recommended
- **Storage:** 2GB free space
- **Network:** Internet for initial setup

### Installation Steps

#### 1. Python Installation
```bash
# Check Python version
python --version

# If Python not installed, download from:
# https://www.python.org/downloads/
```

#### 2. Project Setup
```bash
# Clone or extract project
cd BrandEye

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip
```

#### 3. Install Dependencies
```bash
# Install all packages
pip install -r requirements.txt

# This will install:
# - Flask (web framework)
# - OpenCV (computer vision)
# - YOLO (object detection)
# - PyTorch (deep learning)
# - scikit-learn (machine learning)
# - EasyOCR (text recognition)
```

#### 4. Verify Installation
```bash
# Check if all packages installed correctly
python -c "import flask, cv2, ultralytics, torch, sklearn, easyocr; print('All packages installed successfully!')"
```

## Running the Application

### Method 1: Automatic Startup (Recommended)
```bash
# Single command to start everything
python start_system.py

# This will:
# 1. Start Detection Service (Port 5001)
# 2. Start Grouping Service (Port 5002)
# 3. Start Visualization Service (Port 5003)
# 4. Check all services are running
# 5. Provide instructions for main server
```

### Method 2: Manual Startup
```bash
# Terminal 1: Start microservices
cd microservices
python start_all_services.py

# Terminal 2: Start main server
cd ..
python main_server.py
```

### Method 3: Individual Services
```bash
# Terminal 1: Detection Service
cd microservices
python detection_service.py

# Terminal 2: Grouping Service
python grouping_service.py

# Terminal 3: Visualization Service
python visualization_service.py

# Terminal 4: Main Server
cd ..
python main_server.py
```

## Testing the System

### 1. Health Check
```bash
# Check if all services are running
curl http://localhost:5000/health

# Expected response:
{
  "status": "healthy",
  "services": {
    "detection": true,
    "grouping": true,
    "visualization": true
  }
}
```

### 2. Web Interface Test
1. Open browser: http://localhost:5000
2. Upload a retail shelf image
3. Click "Analyze Products"
4. Wait for processing (5-10 seconds)
5. View results with color-coded boxes

### 3. API Test
```bash
# Test detection service
curl -X POST http://localhost:5001/health

# Test grouping service
curl -X POST http://localhost:5002/health

# Test visualization service
curl -X POST http://localhost:5003/health
```

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Error: Address already in use
# Solution: Kill existing processes
# Windows:
taskkill /f /im python.exe
# Linux/Mac:
pkill -f python
```

#### 2. Model Download Issues
```bash
# Error: YOLO model not downloading
# Solution: Check internet connection and try again
# Models will be downloaded automatically on first run
```

#### 3. Memory Issues
```bash
# Error: Out of memory
# Solution: Close other applications, restart system
# Minimum 8GB RAM required
```

#### 4. Package Installation Issues
```bash
# Error: Package installation failed
# Solution: Update pip and try again
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Performance Optimization

#### 1. For Faster Processing
- Use SSD storage
- Increase RAM to 16GB+
- Close unnecessary applications

#### 2. For Better Accuracy
- Use high-quality images
- Ensure good lighting in images
- Use images with clear product labels

## File Structure
```
BrandEye/
├── main_server.py              # Main Flask server
├── start_system.py            # System launcher
├── microservices/
│   ├── detection_service.py    # YOLO detection
│   ├── grouping_service.py     # Brand grouping
│   ├── visualization_service.py # Image visualization
│   ├── start_all_services.py   # Service launcher
│   └── yolov8n.pt             # YOLO model
├── static/results/            # Output images
├── requirements.txt           # Dependencies
├── README.md                 # Project overview
├── API_DOCUMENTATION.md      # API reference
├── TECHNICAL_WRITEUP.md      # Technical details
├── SETUP_GUIDE.md           # This file
└── PROJECT_SUMMARY.md       # Project summary
```

## Support
- **Documentation:** See API_DOCUMENTATION.md and TECHNICAL_WRITEUP.md
- **Issues:** Check troubleshooting section above
- **Contact:** For assignment-specific questions, contact the assignment team

## Next Steps
1. **Test with sample images** to verify functionality
2. **Review API documentation** for integration details
3. **Read technical write-up** for implementation details
4. **Customize** for your specific use case

**The system is now ready for production use!**
