from flask import Flask, request, jsonify
import cv2
import numpy as np
import base64
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

app = Flask(__name__)

# Try to load AI models (optimized for speed)
try:
    import torch
    import torchvision.transforms as transforms
    from torchvision import models
    
    # Load ResNet18 instead of ResNet50 for faster processing
    # Theory: ResNet18 is lighter and faster while still providing good features
    resnet = models.resnet18(pretrained=True)
    resnet.eval()
    
    # Simplified preprocessing pipeline for speed
    preprocess = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize(128),  # Smaller size for faster processing
        transforms.CenterCrop(112),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    print("ResNet18 model loaded successfully (optimized for speed)")
    resnet_available = True
except Exception as e:
    print(f"ResNet not available: {e}")
    resnet_available = False

# Try to load OCR for brand detection
try:
    import easyocr
    ocr_reader = easyocr.Reader(['en'])
    print("EasyOCR loaded successfully")
    ocr_available = True
except Exception as e:
    print(f"EasyOCR not available: {e}")
    ocr_available = False

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'grouping',
        'resnet_available': resnet_available,
        'ocr_available': ocr_available
    })

@app.route('/group', methods=['POST'])
def group_products():
    """Main grouping endpoint - groups products by brand and visual similarity"""
    try:
        data = request.get_json()
        if 'image' not in data or 'detections' not in data:
            return jsonify({'success': False, 'error': 'Missing image or detections data'})
        
        # Decode image
        image_data = data['image']
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        detections = data['detections']
        print(f"Grouping {len(detections)} products")
        
        # Group products
        grouped_detections = group_products_by_similarity(image, detections)
        
        print(f"Grouped into {len(set(d.get('group_id', 0) for d in grouped_detections))} groups")
        
        return jsonify({
            'success': True,
            'grouped_detections': grouped_detections
        })
        
    except Exception as e:
        print(f"Grouping error: {e}")
        return jsonify({'success': False, 'error': str(e)})

def group_products_by_similarity(image, detections):
    """Group products by visual similarity and brand names"""
    if len(detections) < 2:
        # Single product case
        for det in detections:
            det['group_id'] = 0
            det['brand_name'] = 'Unknown Brand'
            det['group_name'] = 'Product Group 1'
        return detections
    
    # Extract features for each product
    features_list = []
    brand_names = []
    
    for i, detection in enumerate(detections):
        bbox = detection['bbox']
        x1, y1, x2, y2 = bbox
        
        # Crop product from image
        product_crop = image[y1:y2, x1:x2]
        
        # Extract visual features
        if resnet_available:
            visual_features = extract_visual_features(product_crop)
        else:
            visual_features = extract_simple_features(product_crop)
        
        # Extract brand name using OCR
        if ocr_available:
            brand_name = extract_brand_name(product_crop)
        else:
            brand_name = 'Unknown Brand'
        
        features_list.append(visual_features)
        brand_names.append(brand_name)
        
        print(f"Product {i+1}: Brand = {brand_name}")
    
    # Group by brand names first
    brand_groups = {}
    unknown_brand_products = []
    
    for i, brand_name in enumerate(brand_names):
        if brand_name == 'Unknown Brand':
            unknown_brand_products.append(i)
        else:
            if brand_name not in brand_groups:
                brand_groups[brand_name] = []
            brand_groups[brand_name].append(i)
    
    # Group unknown brand products by visual similarity
    if unknown_brand_products:
        visual_groups = cluster_by_visual_similarity(features_list, unknown_brand_products)
        for group_id, product_indices in enumerate(visual_groups):
            brand_name = f"Visual Group {group_id + 1}"
            brand_groups[brand_name] = product_indices
    
    # Assign group IDs and names
    group_id = 0
    for brand_name, product_indices in brand_groups.items():
        for idx in product_indices:
            detections[idx]['group_id'] = group_id
            detections[idx]['brand_name'] = brand_name
            detections[idx]['group_name'] = f"{brand_name} Products"
        group_id += 1
    
    return detections

def extract_visual_features(image_crop):
    """Extract visual features using ResNet18"""
    try:
        # Preprocess image for ResNet18
        rgb_image = cv2.cvtColor(image_crop, cv2.COLOR_BGR2RGB)
        input_tensor = preprocess(rgb_image).unsqueeze(0)
        
        # Extract features
        with torch.no_grad():
            features = resnet(input_tensor)
            features = features.squeeze().numpy()
        
        return features
    except Exception as e:
        print(f"ResNet18 feature extraction failed: {e}")
        return extract_simple_features(image_crop)

def extract_simple_features(image_crop):
    """Extract simple features using OpenCV (fallback method)"""
    # Color features
    avg_color = np.mean(image_crop.reshape(-1, 3), axis=0)
    
    # Texture features
    gray = cv2.cvtColor(image_crop, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    texture_score = np.sum(edges) / (image_crop.shape[0] * image_crop.shape[1])
    
    # Combine features
    features = np.concatenate([avg_color, [texture_score]])
    
    return features

def extract_brand_name(image_crop):
    """Extract brand name using OCR"""
    try:
        # Fast OCR attempt
        results = ocr_reader.readtext(image_crop, detail=1, paragraph=False, width_ths=0.7, height_ths=0.7)
        
        # Brand database
        brand_keywords = {
            # Feminine hygiene products
            'Kotex': ['Kotex', 'KOTEX', 'kotex', 'Kotex®', 'Kotex Ultra'],
            'Seni': ['Seni', 'SENI', 'seni', 'Seni®', 'Seni Gentle'],
            'Always': ['Always', 'ALWAYS', 'always', 'Always®', 'Always Ultra'],
            'Tampax': ['Tampax', 'TAMPAX', 'tampax', 'Tampax®', 'Tampax Pearl'],
            'Carefree': ['Carefree', 'CAREFREE', 'carefree', 'Carefree®'],
            'Playtex': ['Playtex', 'PLAYTEX', 'playtex', 'Playtex®'],
            
            # Laundry products
            'Molto': ['Molto', 'MOLTO', 'molto', 'Molto®', 'Molto Ultra'],
            'Downy': ['Downy', 'DOWNY', 'downy', 'Downy®', 'Downy Ultra'],
            'Tide': ['Tide', 'TIDE', 'tide', 'Tide®', 'Tide Ultra'],
            'Ariel': ['Ariel', 'ARIEL', 'ariel', 'Ariel®'],
            'Surf': ['Surf', 'SURF', 'surf', 'Surf®'],
            
            # Baby products
            'Huggies': ['Huggies', 'HUGGIES', 'huggies', 'Huggies®'],
            'Pampers': ['Pampers', 'PAMPERS', 'pampers', 'Pampers®'],
            'MamyPoko': ['MamyPoko', 'MAMYPOKO', 'mamypoko', 'MamyPoko®'],
            
            # Personal care
            'Head & Shoulders': ['Head & Shoulders', 'HEAD & SHOULDERS', 'Head Shoulders'],
            'Pantene': ['Pantene', 'PANTENE', 'pantene', 'Pantene®'],
            'Dove': ['Dove', 'DOVE', 'dove', 'Dove®'],
            'Lux': ['Lux', 'LUX', 'lux', 'Lux®'],
            'Sunsilk': ['Sunsilk', 'SUNSILK', 'sunsilk', 'Sunsilk®'],
            
            # Generic product types
            'Ultra': ['Ultra', 'ULTRA', 'ultra'],
            'Gentle': ['Gentle', 'GENTLE', 'gentle'],
            'Slimguard': ['Slimguard', 'SLIMGUARD', 'slimguard'],
            'Regular': ['Regular', 'REGULAR', 'regular'],
            'Super': ['Super', 'SUPER', 'super']
        }
        
        # Process OCR results
        best_brand = None
        best_confidence = 0
        
        for (bbox, text, confidence) in results:
            if confidence > 0.3:
                text_clean = text.strip().upper()
                
                # Check for exact brand matches
                for brand_name, variations in brand_keywords.items():
                    for variation in variations:
                        if variation.upper() in text_clean:
                            if confidence > best_confidence:
                                best_brand = brand_name
                                best_confidence = confidence
                                break
                
                # Check for partial matches
                if not best_brand:
                    for brand_name, variations in brand_keywords.items():
                        for variation in variations:
                            variation_words = variation.upper().split()
                            text_words = text_clean.split()
                            if any(word in text_words for word in variation_words if len(word) > 3):
                                if confidence > best_confidence:
                                    best_brand = brand_name
                                    best_confidence = confidence
                                    break
        
        # Return best brand found
        if best_brand:
            return best_brand
        
        # If no brand found, try to extract meaningful text
        if results:
            best_result = max(results, key=lambda x: x[2])
            text = best_result[1].strip()
            
            if len(text) > 3:
                return text[:25]
        
        return 'Unknown Brand'
        
    except Exception as e:
        print(f"OCR failed: {e}")
        return 'Unknown Brand'

def enhance_image_for_ocr(image_crop):
    """Enhance image for better OCR results"""
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(image_crop, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Apply adaptive threshold for better text contrast
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # Apply morphological operations to clean up text
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Convert back to BGR for OCR
        enhanced = cv2.cvtColor(cleaned, cv2.COLOR_GRAY2BGR)
        
        return enhanced
        
    except Exception as e:
        print(f"Image enhancement failed: {e}")
        return image_crop

def cluster_by_visual_similarity(features_list, product_indices):
    """Cluster products by visual similarity using DBSCAN"""
    if len(product_indices) < 2:
        return [product_indices]
    
    # Extract features for unknown brand products
    unknown_features = [features_list[i] for i in product_indices]
    
    # Normalize features
    scaler = StandardScaler()
    normalized_features = scaler.fit_transform(unknown_features)
    
    # Apply DBSCAN clustering
    clustering = DBSCAN(eps=0.5, min_samples=2)
    cluster_labels = clustering.fit_predict(normalized_features)
    
    # Group products by cluster labels
    groups = {}
    for i, label in enumerate(cluster_labels):
        if label not in groups:
            groups[label] = []
        groups[label].append(product_indices[i])
    
    return list(groups.values())

if __name__ == '__main__':
    print("Starting Grouping Service on port 5002")
    print("ResNet18 available:", resnet_available)
    print("OCR available:", ocr_available)
    app.run(host='0.0.0.0', port=5002, debug=False)