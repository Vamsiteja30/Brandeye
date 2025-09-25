# BrandEye AI Pipeline - API Documentation

## Overview
BrandEye is a microservices-based AI pipeline for retail product detection and brand grouping. The system consists of 4 independent services that communicate via REST APIs.

## Architecture
```
Client → Main Server (5000) → Detection Service (5001) → Grouping Service (5002) → Visualization Service (5003)
```

## Services

### 1. Main Server (Port 5000)
**Purpose:** Orchestrates the AI pipeline and serves the web interface

#### Endpoints:

##### `GET /`
- **Description:** Serves the web interface
- **Response:** HTML page with upload form

##### `POST /process`
- **Description:** Main processing endpoint
- **Content-Type:** `multipart/form-data`
- **Input:** Image file
- **Output:**
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

##### `GET /health`
- **Description:** Health check for all services
- **Output:**
```json
{
  "status": "healthy",
  "services": {
    "detection": true,
    "grouping": true,
    "visualization": true
  }
}
```

### 2. Detection Service (Port 5001)
**Purpose:** Detects products in retail shelf images using YOLO

#### Endpoints:

##### `POST /detect`
- **Description:** Detect products in image
- **Input:**
```json
{
  "image": "base64_encoded_image"
}
```
- **Output:**
```json
{
  "success": true,
  "detections": [
    {
      "bbox": [x1, y1, x2, y2],
      "confidence": 0.85
    }
  ],
  "image_shape": [height, width, channels],
  "method_used": "YOLO"
}
```

##### `GET /health`
- **Description:** Service health check
- **Output:**
```json
{
  "status": "healthy",
  "service": "detection",
  "yolo_available": true
}
```

### 3. Grouping Service (Port 5002)
**Purpose:** Groups detected products by brand using AI models

#### Endpoints:

##### `POST /group`
- **Description:** Group products by brand
- **Input:**
```json
{
  "image": "base64_encoded_image",
  "detections": [
    {
      "bbox": [x1, y1, x2, y2],
      "confidence": 0.85
    }
  ]
}
```
- **Output:**
```json
{
  "success": true,
  "grouped_detections": [
    {
      "bbox": [x1, y1, x2, y2],
      "confidence": 0.85,
      "group_id": 0,
      "brand_name": "Kotex",
      "group_name": "Kotex Products"
    }
  ]
}
```

##### `GET /health`
- **Description:** Service health check
- **Output:**
```json
{
  "status": "healthy",
  "service": "grouping",
  "resnet_available": true,
  "ocr_available": true
}
```

### 4. Visualization Service (Port 5003)
**Purpose:** Creates visualizations with bounding boxes and legends

#### Endpoints:

##### `POST /visualize`
- **Description:** Create visualization
- **Input:**
```json
{
  "image": "base64_encoded_image",
  "detections": [
    {
      "bbox": [x1, y1, x2, y2],
      "confidence": 0.85,
      "group_id": 0,
      "brand_name": "Kotex",
      "group_name": "Kotex Products"
    }
  ]
}
```
- **Output:**
```json
{
  "success": true,
  "result_image": "/static/results/result_123.jpg"
}
```

##### `GET /health`
- **Description:** Service health check
- **Output:**
```json
{
  "status": "healthy",
  "service": "visualization"
}
```

## Error Responses
All services return consistent error responses:
```json
{
  "success": false,
  "error": "Error description"
}
```

## Performance Metrics
*Note: Performance metrics are estimates based on typical system performance*
- **Detection:** 1-2 seconds
- **Grouping:** 3-5 seconds
- **Visualization:** 0.5-1 second
- **Total Pipeline:** 5-8 seconds

## Supported Image Formats
- JPEG (.jpg, .jpeg)
- PNG (.png)
- Maximum size: 10MB

## Brand Recognition
The system recognizes 25+ brands including:
- **Feminine Hygiene:** Kotex, Seni, Always, Tampax
- **Laundry:** Molto, Downy, Tide, Ariel
- **Baby Products:** Huggies, Pampers, MamyPoko
- **Personal Care:** Head & Shoulders, Pantene, Dove
