from flask import Flask, request, jsonify, send_from_directory
import requests
import time
from pathlib import Path

# Initialize Flask app
app = Flask(__name__)

# Define microservice endpoints (following REST API principles)
DETECTION_URL = "http://localhost:5001"
GROUPING_URL = "http://localhost:5002"
VISUALIZATION_URL = "http://localhost:5003"

# Create directory for storing result images
results_dir = Path("static/results")
results_dir.mkdir(parents=True, exist_ok=True)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>BrandEye - AI Pipeline</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 30px; }
            .upload-area { border: 3px dashed #007bff; padding: 40px; text-align: center; margin: 20px 0; border-radius: 10px; background: #f8f9fa; }
            .upload-area:hover { background: #e9ecef; }
            .results { display: none; margin-top: 30px; }
            .image-container { display: flex; gap: 30px; justify-content: center; }
            .image-container img { max-width: 400px; border: 2px solid #ddd; border-radius: 8px; }
            .info { background: #e3f2fd; padding: 20px; border-radius: 8px; margin-top: 20px; }
            .btn { padding: 12px 30px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
            .btn:hover { background: #0056b3; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .success { background: #d4edda; color: #155724; }
            .error { background: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>BrandEye - AI Pipeline</h1>
                <p>Product Detection and Brand Grouping System</p>
                <p><strong>Microservices Architecture:</strong> Detection → Grouping → Visualization</p>
            </div>
            
            <div class="upload-area">
                <input type="file" id="imageInput" accept="image/*" style="margin-bottom: 15px;">
                <p>Select a retail shelf image to analyze</p>
                <p><small>Supports: JPG, PNG, JPEG formats</small></p>
            </div>
            
            <div style="text-align: center;">
                <button onclick="processImage()" class="btn">Analyze Products</button>
            </div>
            
            <div id="status"></div>
            
            <div id="results" class="results">
                <h3>Analysis Results</h3>
                <div class="image-container">
                    <div>
                        <h4>Original Image</h4>
                        <img id="originalImg" alt="Original">
                    </div>
                    <div>
                        <h4>Detected & Grouped Products</h4>
                        <img id="resultImg" alt="Result">
                    </div>
                </div>
                <div id="info" class="info"></div>
            </div>
        </div>

        <script>
            function showStatus(message, type) {
                const status = document.getElementById('status');
                status.innerHTML = '<div class="status ' + type + '">' + message + '</div>';
            }

            function processImage() {
                const fileInput = document.getElementById('imageInput');
                const file = fileInput.files[0];
                
                if (!file) {
                    showStatus('Please select an image file', 'error');
                    return;
                }
                
                showStatus('Processing image through AI pipeline...', 'success');
                
                const formData = new FormData();
                formData.append('image', file);
                
                fetch('/process', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('originalImg').src = URL.createObjectURL(file);
                        document.getElementById('resultImg').src = data.result_image;
                        
                        let groupsInfo = '';
                        if (data.groups) {
                            groupsInfo = Object.entries(data.groups)
                                .map(([groupId, count]) => `Group ${groupId}: ${count} products`)
                                .join('<br>');
                        }
                        
                        document.getElementById('info').innerHTML = 
                            '<strong>Analysis Complete!</strong><br>' +
                            'Products detected: ' + data.products_count + '<br>' +
                            'Brand groups: ' + data.groups_count + '<br>' +
                            'Processing time: ' + data.processing_time + 's<br>' +
                            '<strong>Groups:</strong><br>' + groupsInfo;
                        
                        document.getElementById('results').style.display = 'block';
                        showStatus('Analysis completed successfully!', 'success');
                    } else {
                        showStatus('Error: ' + data.error, 'error');
                    }
                })
                .catch(error => {
                    showStatus('Error processing image: ' + error, 'error');
                });
            }
        </script>
    </body>
    </html>
    '''

@app.route('/process', methods=['POST'])
def process_image():
    """Main processing function - orchestrates the AI pipeline"""
    try:
        # Validate input
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file provided'})
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No image selected'})
        
        start_time = time.time()
        
        # Convert image to base64 for microservices
        image_bytes = file.read()
        import base64
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Call Detection Service
        print("Calling Detection Service...")
        detection_response = requests.post(f"{DETECTION_URL}/detect", 
                                         json={'image': image_b64}, 
                                         timeout=(10, 60))
        
        if detection_response.status_code != 200:
            return jsonify({'success': False, 'error': 'Detection service not responding'})
        
        detection_data = detection_response.json()
        if not detection_data['success']:
            return jsonify({'success': False, 'error': 'Detection failed: ' + detection_data['error']})
        
        detections = detection_data['detections']
        if not detections:
            return jsonify({'success': False, 'error': 'No products detected in image'})
        
        print(f"Found {len(detections)} products")
        
        # Call Grouping Service
        print("Calling Grouping Service...")
        grouping_response = requests.post(f"{GROUPING_URL}/group", 
                                        json={
                                            'image': image_b64,
                                            'detections': detections
                                        }, 
                                        timeout=(30, 180))
        
        if grouping_response.status_code != 200:
            return jsonify({'success': False, 'error': 'Grouping service not responding'})
        
        grouping_data = grouping_response.json()
        if not grouping_data['success']:
            return jsonify({'success': False, 'error': 'Grouping failed: ' + grouping_data['error']})
        
        grouped_detections = grouping_data['grouped_detections']
        print(f"Grouped into {len(set(d.get('group_id', 0) for d in grouped_detections))} groups")
        
        # Call Visualization Service
        print("Calling Visualization Service...")
        visualization_response = requests.post(f"{VISUALIZATION_URL}/visualize", 
                                             json={
                                                 'image': image_b64,
                                                 'detections': grouped_detections
                                             }, 
                                             timeout=(10, 60))
        
        if visualization_response.status_code != 200:
            return jsonify({'success': False, 'error': 'Visualization service not responding'})
        
        visualization_data = visualization_response.json()
        if not visualization_data['success']:
            return jsonify({'success': False, 'error': 'Visualization failed: ' + visualization_data['error']})
        
        # Calculate processing time and prepare response
        processing_time = round(time.time() - start_time, 2)
        
        # Count products in each group
        groups = {}
        for detection in grouped_detections:
            group_id = detection.get('group_id', 0)
            groups[group_id] = groups.get(group_id, 0) + 1
        
        print(f"Processing completed in {processing_time} seconds")
        
        return jsonify({
            'success': True,
            'result_image': visualization_data['result_image'],
            'products_count': len(grouped_detections),
            'groups_count': len(groups),
            'processing_time': processing_time,
            'groups': {str(gid): count for gid, count in groups.items()},
            'detections': grouped_detections
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'error': f'Service communication error: {str(e)}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Check if all microservices are running
        services_status = {}
        
        detection_status = requests.get(f"{DETECTION_URL}/health", timeout=5)
        services_status['detection'] = detection_status.status_code == 200
        
        grouping_status = requests.get(f"{GROUPING_URL}/health", timeout=5)
        services_status['grouping'] = grouping_status.status_code == 200
        
        visualization_status = requests.get(f"{VISUALIZATION_URL}/health", timeout=5)
        services_status['visualization'] = visualization_status.status_code == 200
        
        all_healthy = all(services_status.values())
        
        return jsonify({
            'status': 'healthy' if all_healthy else 'unhealthy',
            'services': services_status
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        })

@app.route('/static/results/<filename>')
def serve_result(filename):
    """Serve result images"""
    return send_from_directory(results_dir, filename)

if __name__ == '__main__':
    print("BrandEye Main Server Starting...")
    print("Make sure all microservices are running:")
    print("- Detection Service: http://localhost:5001")
    print("- Grouping Service: http://localhost:5002") 
    print("- Visualization Service: http://localhost:5003")
    print("\nMain Server: http://localhost:5000")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=False)
