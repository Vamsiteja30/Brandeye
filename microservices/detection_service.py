from flask import Flask, request, jsonify
import cv2
import numpy as np
import base64

# Initialize Flask app
app = Flask(__name__)

# Try to load YOLO model (state-of-the-art object detection)
try:
    from ultralytics import YOLO
    yolo_model = YOLO("yolov8n.pt")  # YOLOv8 nano version (lightweight)
    print("YOLO model loaded successfully")
    yolo_available = True
except Exception as e:
    print(f"YOLO not available: {e}")
    print("Will use OpenCV edge detection as fallback")
    yolo_available = False

@app.route('/health')
def health_check():
    """Health check endpoint for microservice"""
    return jsonify({
        'status': 'healthy',
        'service': 'detection',
        'yolo_available': yolo_available
    })

@app.route('/detect', methods=['POST'])
def detect_products():
    """Main detection endpoint - finds products in images"""
    try:
        #  Get data from request
        data = request.get_json()
        if 'image' not in data:
            return jsonify({'success': False, 'error': 'No image data provided'})
        
        # Decode base64 image
        image_data = data['image']
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({'success': False, 'error': 'Invalid image format'})
        
        print(f"Processing image of size: {image.shape}")
        
        # Detect products
        detections = []
        
        if yolo_available:
            print("Using YOLO for product detection...")
            detections = detect_with_yolo(image)
        else:
            print("Using OpenCV for product detection...")
            detections = detect_with_opencv(image)
        
        print(f"Detected {len(detections)} products")
        
        return jsonify({
            'success': True,
            'detections': detections,
            'image_shape': image.shape,
            'method_used': 'YOLO' if yolo_available else 'OpenCV'
        })
        
    except Exception as e:
        print(f"Detection error: {e}")
        return jsonify({'success': False, 'error': str(e)})

def detect_with_yolo(image):
    """Detect products using YOLO with multiple strategies for better coverage"""
    detections = []
    
    # First pass: normal confidence
    results = yolo_model.predict(image, conf=0.1, iou=0.3, verbose=False)
    
    for result in results:
        if result.boxes is not None:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                confidence = float(box.conf[0].cpu().numpy())
                
                width = x2 - x1
                height = y2 - y1
                if width > 20 and height > 20:
                    detections.append({
                        'bbox': [x1, y1, x2, y2],
                        'confidence': confidence
                    })
    
    # Second pass: ultra-low confidence if we didn't find much
    if len(detections) < 5:
        print("Few detections found, trying ultra-low confidence...")
        results2 = yolo_model.predict(image, conf=0.05, iou=0.2, verbose=False)
        
        for result in results2:
            if result.boxes is not None:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                    confidence = float(box.conf[0].cpu().numpy())
                    
                    width = x2 - x1
                    height = y2 - y1
                    if width > 15 and height > 15:
                        # Check for overlap with existing detections
                        overlap = False
                        for existing in detections:
                            if calculate_overlap([x1, y1, x2, y2], existing['bbox']) > 0.3:
                                overlap = True
                                break
                        
                        if not overlap:
                            detections.append({
                                'bbox': [x1, y1, x2, y2],
                                'confidence': confidence
                            })
    
    # Third pass: OpenCV backup if still not enough
    if len(detections) < 3:
        print("Using OpenCV backup detection...")
        opencv_detections = detect_with_opencv(image)
        for ocv_det in opencv_detections:
            overlap = False
            for yolo_det in detections:
                if calculate_overlap(ocv_det['bbox'], yolo_det['bbox']) > 0.3:
                    overlap = True
                    break
            if not overlap:
                detections.append(ocv_det)
    
    print(f"Total detections found: {len(detections)}")
    return detections

def calculate_overlap(bbox1, bbox2):
    """Calculate overlap ratio between two bounding boxes"""
    x1_1, y1_1, x2_1, y2_1 = bbox1
    x1_2, y1_2, x2_2, y2_2 = bbox2
    
    # Calculate intersection
    x1_i = max(x1_1, x1_2)
    y1_i = max(y1_1, y1_2)
    x2_i = min(x2_1, x2_2)
    y2_i = min(y2_1, y2_2)
    
    if x2_i <= x1_i or y2_i <= y1_i:
        return 0.0
    
    intersection = (x2_i - x1_i) * (y2_i - y1_i)
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    union = area1 + area2 - intersection
    
    return intersection / union if union > 0 else 0.0

def detect_with_opencv(image):
    """Detect products using OpenCV edge detection with multiple strategies"""
    detections = []
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Multiple edge detection strategies
    edges1 = cv2.Canny(gray, 50, 150)
    edges2 = cv2.Canny(gray, 30, 100)
    
    # Adaptive threshold for better edge detection
    adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    edges3 = cv2.Canny(adaptive, 20, 80)
    
    # Combine all edge images
    combined_edges = cv2.bitwise_or(edges1, cv2.bitwise_or(edges2, edges3))
    
    # Clean up edges
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    combined_edges = cv2.morphologyEx(combined_edges, cv2.MORPH_CLOSE, kernel)
    
    # Find contours
    contours, _ = cv2.findContours(combined_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        
        # Size filtering
        if (w > 25 and h > 25 and
            w < image.shape[1]*0.9 and h < image.shape[0]*0.9):
            
            # Check if contour fills reasonable portion of bounding box
            contour_area = cv2.contourArea(contour)
            bbox_area = w * h
            area_ratio = contour_area / bbox_area if bbox_area > 0 else 0
            
            if area_ratio > 0.3:
                detections.append({
                    'bbox': [x, y, x+w, y+h],
                    'confidence': 0.6
                })
    
    # Template matching for common product shapes
    template_detections = detect_with_template_matching(image)
    detections.extend(template_detections)
    
    print(f"OpenCV detected {len(detections)} products")
    return detections

def detect_with_template_matching(image):
    """Use template matching to detect common product shapes"""
    detections = []
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Create templates for common product shapes
    templates = []
    
    # Tall rectangle (bottles, boxes)
    template1 = np.ones((60, 30), dtype=np.uint8) * 255
    templates.append((template1, 0.4))
    
    # Wide rectangle (packs, boxes)
    template2 = np.ones((40, 80), dtype=np.uint8) * 255
    templates.append((template2, 0.4))
    
    # Square (small products)
    template3 = np.ones((50, 50), dtype=np.uint8) * 255
    templates.append((template3, 0.3))
    
    for template, threshold in templates:
        result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)
        
        h, w = template.shape
        for pt in zip(*locations[::-1]):
            x, y = pt
            # Check for overlap with existing detections
            overlap = False
            for existing in detections:
                if calculate_overlap([x, y, x+w, y+h], existing['bbox']) > 0.3:
                    overlap = True
                    break
            
            if not overlap:
                detections.append({
                    'bbox': [x, y, x+w, y+h],
                    'confidence': 0.5
                })
    
    return detections

if __name__ == '__main__':
    print("Starting Detection Service on port 5001")
    print("YOLO available:", yolo_available)
    app.run(host='0.0.0.0', port=5001, debug=False)