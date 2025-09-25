from flask import Flask, request, jsonify
import cv2
import numpy as np
import base64
from sklearn.cluster import KMeans

app = Flask(__name__)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'fast_grouping'
    })

@app.route('/group', methods=['POST'])
def group_products():
    """
    Fast grouping endpoint using color-based clustering
    Theory: Groups products by dominant colors for speed
    """
    try:
        # Step 1: Get data from request
        data = request.get_json()
        if 'image' not in data or 'detections' not in data:
            return jsonify({'success': False, 'error': 'Missing image or detections data'})
        
        # Step 2: Decode image
        image_data = data['image']
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        detections = data['detections']
        print(f"Fast grouping {len(detections)} products")
        
        # Step 3: Group products by color
        grouped_detections = group_by_color(image, detections)
        
        print(f"Grouped into {len(set(d.get('group_id', 0) for d in grouped_detections))} groups")
        
        return jsonify({
            'success': True,
            'grouped_detections': grouped_detections
        })
        
    except Exception as e:
        print(f"Fast grouping error: {e}")
        return jsonify({'success': False, 'error': str(e)})

def group_by_color(image, detections):
    """
    Group products by dominant color using K-means clustering
    Theory: Similar colored products are likely the same brand
    """
    if len(detections) < 2:
        # If only one product, assign to group 0
        for det in detections:
            det['group_id'] = 0
            det['brand_name'] = 'Product'
            det['group_name'] = 'Product Group 1'
        return detections
    
    # Extract dominant colors for each product
    colors = []
    for detection in detections:
        bbox = detection['bbox']
        x1, y1, x2, y2 = bbox
        
        # Crop product from image
        product_crop = image[y1:y2, x1:x2]
        
        # Get dominant color
        dominant_color = get_dominant_color(product_crop)
        colors.append(dominant_color)
    
    # Convert to numpy array
    colors_array = np.array(colors)
    
    # Determine number of clusters (max 5 groups)
    n_clusters = min(5, len(detections))
    
    # Apply K-means clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(colors_array)
    
    # Assign group information
    for i, detection in enumerate(detections):
        group_id = int(cluster_labels[i])
        detection['group_id'] = group_id
        detection['brand_name'] = f'Brand Group {group_id + 1}'
        detection['group_name'] = f'Color Group {group_id + 1}'
    
    return detections

def get_dominant_color(image_crop):
    """
    Get dominant color from image crop
    Theory: Uses K-means to find the most common color
    """
    try:
        # Reshape image to be a list of pixels
        pixels = image_crop.reshape(-1, 3)
        
        # Apply K-means to find dominant colors
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        kmeans.fit(pixels)
        
        # Get the most common color
        labels = kmeans.labels_
        dominant_label = np.bincount(labels).argmax()
        dominant_color = kmeans.cluster_centers_[dominant_label]
        
        return dominant_color
        
    except Exception as e:
        print(f"Color extraction failed: {e}")
        # Return default color if extraction fails
        return np.array([128, 128, 128])  # Gray

if __name__ == '__main__':
    print("Starting Fast Grouping Service on port 5002")
    app.run(host='0.0.0.0', port=5002, debug=False)
