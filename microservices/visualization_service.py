from flask import Flask, request, jsonify, send_from_directory
import cv2
import numpy as np
import base64
import time
from pathlib import Path

app = Flask(__name__)

# Create results directory
project_root = Path(__file__).parent.parent
results_dir = project_root / "static" / "results"
results_dir.mkdir(parents=True, exist_ok=True)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'visualization'
    })

@app.route('/visualize', methods=['POST'])
def visualize_results():
    """Main visualization endpoint - creates visual representations of results"""
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
        print(f"Visualizing {len(detections)} products")
        
        # Create visualization
        result_image = create_visualization(image, detections)
        
        # Save result image
        timestamp = int(time.time())
        result_filename = f"result_{timestamp}.jpg"
        result_path = results_dir / result_filename
        cv2.imwrite(str(result_path), result_image)
        
        print(f"Visualization saved: {result_filename}")
        
        return jsonify({
            'success': True,
            'result_image': f'/static/results/{result_filename}'
        })
        
    except Exception as e:
        print(f"Visualization error: {e}")
        return jsonify({'success': False, 'error': str(e)})

def create_visualization(image, detections):
    """Create visualization with bounding boxes and legend"""
    # Create a copy of the original image
    result_image = image.copy()
    height, width = result_image.shape[:2]
    
    # Define colors for different groups (BGR format for OpenCV)
    group_colors = [
        (0, 0, 255),    # Red
        (0, 255, 0),    # Green
        (255, 0, 0),    # Blue
        (0, 255, 255),  # Yellow
        (255, 0, 255),  # Magenta
        (255, 255, 0),  # Cyan
        (0, 165, 255),  # Orange
        (128, 0, 128)   # Purple
    ]
    
    # Draw bounding boxes for each detection
    for i, detection in enumerate(detections):
        bbox = detection['bbox']
        x1, y1, x2, y2 = bbox
        
        # Get group color
        group_id = detection.get('group_id', 0)
        color = group_colors[group_id % len(group_colors)]
        
        # Draw bounding box
        cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 3)
        
        # Draw product information with brand name
        brand_name = detection.get('brand_name', 'Unknown')
        confidence = detection.get('confidence', 0)
        
        # Create label with brand name and confidence
        label = f"#{i+1} {brand_name[:12]} ({confidence:.2f})"
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
        
        # Draw label background
        cv2.rectangle(result_image, (x1, y1-35), (x1 + label_size[0] + 10, y1), color, -1)
        cv2.putText(result_image, label, (x1 + 5, y1-12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        # Draw group ID in corner
        group_id = detection.get('group_id', 0)
        group_label = f"G{group_id}"
        cv2.putText(result_image, group_label, (x2-25, y1+20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    # Create legend
    legend = create_legend(detections, group_colors, width, height)
    
    # Add legend to image
    result_image = add_legend_to_image(result_image, legend)
    
    return result_image

def create_legend(detections, group_colors, image_width, image_height):
    """Create legend showing group information"""
    # Count products in each group
    groups = {}
    for detection in detections:
        group_id = detection.get('group_id', 0)
        group_name = detection.get('group_name', f'Group {group_id}')
        brand_name = detection.get('brand_name', 'Unknown')
        
        if group_id not in groups:
            groups[group_id] = {
                'name': group_name,
                'brand': brand_name,
                'count': 0,
                'color': group_colors[group_id % len(group_colors)]
            }
        groups[group_id]['count'] += 1
    
    return groups

def add_legend_to_image(image, legend):
    """Add legend to the image"""
    height, width = image.shape[:2]
    
    # Calculate legend dimensions
    legend_width = min(400, width // 3)
    legend_height = 100 + len(legend) * 40
    legend_x = width - legend_width - 20
    legend_y = 20
    
    # Create semi-transparent background for legend
    overlay = image.copy()
    cv2.rectangle(overlay, (legend_x, legend_y), 
                 (legend_x + legend_width, legend_y + legend_height), 
                 (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)
    
    # Draw legend border
    cv2.rectangle(image, (legend_x, legend_y), 
                 (legend_x + legend_width, legend_y + legend_height), 
                 (255, 255, 255), 2)
    
    # Add title
    total_products = sum(g['count'] for g in legend.values())
    total_groups = len(legend)
    title = f"BrandEye AI Analysis: {total_products} Products, {total_groups} Brand Groups"
    cv2.putText(image, title, (legend_x + 10, legend_y + 25), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Add separator line
    cv2.line(image, (legend_x + 10, legend_y + 35), 
            (legend_x + legend_width - 10, legend_y + 35), (150, 150, 150), 1)
    
    # Add group information
    y_offset = 50
    for group_id, group_info in legend.items():
        color = group_info['color']
        name = group_info['name']
        count = group_info['count']
        brand = group_info['brand']
        
        # Draw color indicator
        cv2.rectangle(image, (legend_x + 15, legend_y + y_offset - 8), 
                     (legend_x + 35, legend_y + y_offset + 8), color, -1)
        cv2.rectangle(image, (legend_x + 15, legend_y + y_offset - 8), 
                     (legend_x + 35, legend_y + y_offset + 8), (255, 255, 255), 1)
        
        # Draw group text with brand name and count
        group_text = f"{brand} - {count} products"
        cv2.putText(image, group_text, (legend_x + 45, legend_y + y_offset + 3), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        
        y_offset += 30
    
    return image

@app.route('/static/results/<filename>')
def serve_result(filename):
    """Serve result images"""
    return send_from_directory(results_dir, filename)

if __name__ == '__main__':
    print("Starting Visualization Service on port 5003")
    app.run(host='0.0.0.0', port=5003, debug=False)