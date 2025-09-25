# BrandEye - AI Pipeline for Product Detection and Brand Grouping

## Overview
BrandEye is a microservices-based AI pipeline that detects products in retail shelf images and groups them by brand. Built for the Infilect assignment, it provides a complete solution for retail product analysis.

## How It Works

### Pipeline Flow
The system processes images through multiple stages:
1. **Input** → Image upload
2. **Detection** → Find products using YOLO
3. **Grouping** → Group by brand using ResNet18 + OCR
4. **Visualization** → Create annotated images
5. **Output** → JSON response + visualization

### Services
Each stage runs as an independent service:
- **Detection Service** (Port 5001) - Uses YOLO for object detection
- **Grouping Service** (Port 5002) - Uses ResNet18 + DBSCAN for clustering
- **Visualization Service** (Port 5003) - Uses OpenCV for drawing
- **Main Server** (Port 5000) - Orchestrates the pipeline

## Quick Start

### 1. Setup Environment
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Start the System
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

### 3. Access the Application
- **Web Interface**: http://localhost:5000
- **Health Check**: http://localhost:5000/health

## How It Works

### Detection Service
- **Algorithm**: YOLO (You Only Look Once)
- **Fallback**: OpenCV edge detection if YOLO fails
- **Features**: Multiple detection strategies for better coverage

### Grouping Service  
- **Feature Extraction**: ResNet18 (pre-trained CNN)
- **Clustering**: DBSCAN for visual similarity
- **Brand Detection**: EasyOCR for text recognition
- **Process**: Groups products by brand names first, then by visual similarity

### Visualization Service
- **Drawing**: OpenCV for computer graphics
- **Features**: Color-coded boxes, legends, group information
- **Output**: Professional annotated images with detailed legends

## API Usage

### Process Image
```bash
POST /process
Content-Type: multipart/form-data

# Upload image file
curl -X POST -F "image=@shelf_image.jpg" http://localhost:5000/process
```

### Response Format
```json
{
  "success": true,
  "result_image": "/static/results/result_123.jpg",
  "products_count": 8,
  "groups_count": 3,
  "processing_time": 2.45,
  "groups": {
    "0": 3,
    "1": 2, 
    "2": 3
  },
  "detections": [
    {
      "bbox": [100, 200, 300, 400],
      "confidence": 0.85,
      "group_id": 0,
      "brand_name": "Kotex",
      "group_name": "Kotex Products"
    }
  ]
}
```

## Technical Details

### Performance
- **Detection**: 1-2 seconds
- **Grouping**: 3-5 seconds  
- **Visualization**: 0.5-1 second
- **Total**: 5-8 seconds per image

### Scalability
- Each microservice can be scaled independently
- Services communicate via HTTP REST APIs
- Can be deployed on different servers
- Supports horizontal scaling

## File Structure
```
BrandEye/
├── main_server.py              # Main orchestrator
├── start_system.py            # System launcher
├── microservices/
│   ├── detection_service.py    # YOLO-based detection
│   ├── grouping_service.py     # ResNet18 + DBSCAN grouping
│   ├── visualization_service.py # OpenCV visualization
│   ├── start_all_services.py   # Service launcher
│   └── yolov8n.pt             # YOLO model file
├── static/results/            # Output images
├── requirements.txt           # Dependencies
├── README.md                 # This file
├── API_DOCUMENTATION.md      # API reference
├── TECHNICAL_WRITEUP.md      # Technical details
├── SETUP_GUIDE.md           # Setup instructions
└── PROJECT_SUMMARY.md       # Project summary
```

## Troubleshooting

### Common Issues

1. **Services not starting**
   - Check if ports 5001, 5002, 5003 are available
   - Ensure all dependencies are installed

2. **YOLO model not loading**
   - Check internet connection for model download
   - Verify yolov8n.pt file exists

3. **Memory issues**
   - ResNet18 requires ~200MB RAM (optimized for speed)
   - Consider using smaller models for production

### Health Checks
```bash
# Check all services
curl http://localhost:5000/health

# Check individual services
curl http://localhost:5001/health  # Detection
curl http://localhost:5002/health  # Grouping  
curl http://localhost:5003/health  # Visualization
```

## Technologies Used

### Core Libraries
- **Flask**: Web framework
- **OpenCV**: Computer vision library
- **PyTorch**: Deep learning framework
- **scikit-learn**: Machine learning library
- **EasyOCR**: Text recognition library

### Key Concepts
- **Object Detection**: YOLO algorithm
- **Feature Extraction**: Convolutional Neural Networks (ResNet18)
- **Clustering**: DBSCAN algorithm
- **OCR**: Optical Character Recognition
- **Microservices**: Service-oriented architecture

## Future Improvements
- Add more detection models
- Implement brand database
- Add batch processing
- Implement caching
- Add Docker containerization
- Add authentication

## Contact
For questions about this implementation, contact the development team.