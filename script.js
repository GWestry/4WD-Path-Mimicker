document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('drawingCanvas');
    const ctx = canvas.getContext('2d');
    const clearButton = document.getElementById('clearButton');
    const sendButton = document.getElementById('sendBtn');
    let drawing = false;
    let hasDrawn = false;
    let pathPoints = []; // Store the actual drawing path
    
    // Set canvas size
    canvas.width = 800;
    canvas.height = 600;
    
    // Set initial drawing properties
    ctx.lineWidth = 5;
    ctx.lineCap = 'round';
    ctx.strokeStyle = '#000000'; // Black color
    
    // Event listeners for drawing
    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mouseup', stopDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseout', stopDrawing);
    
    // Event listener for clear button (only if present)
    if (clearButton) {
        clearButton.addEventListener('click', clearCanvas);
    }
    
    // Event listener for send button
    sendButton.addEventListener('click', sendPath);
    
    // Add keyboard event listener for 'R' key to reset canvas
    document.addEventListener('keydown', (e) => {
        if (e.key.toLowerCase() === 'r') {
            clearCanvas();
        }
    });
    
    function startDrawing(e) {
        // Only allow drawing if no line has been drawn yet
        if (hasDrawn) {
            console.log("Line already drawn. Press 'R' to reset and draw a new line.");
            return;
        }
        
        drawing = true;
        const x = e.offsetX;
        const y = e.offsetY;
        
        // Start new path and record starting point
        pathPoints = [{x: x, y: y}];
        ctx.beginPath();
        ctx.moveTo(x, y);
        console.log(`Starting drawing at: (${x}, ${y})`);
    }
    
    function stopDrawing() {
        if (drawing) {
            hasDrawn = true;
            console.log(`Line complete with ${pathPoints.length} points. Press 'R' to reset canvas for a new line.`);
            console.log("Path points:", pathPoints);
        }
        drawing = false;
        ctx.closePath();
    }
    
    function draw(e) {
        if (!drawing || hasDrawn) return;
        
        const x = e.offsetX;
        const y = e.offsetY;
        
        // Record this point in our path
        pathPoints.push({x: x, y: y});
        
        // Draw on canvas
        ctx.lineTo(x, y);
        ctx.stroke();
    }
    
    function clearCanvas() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        hasDrawn = false;
        pathPoints = []; // Clear the recorded path
        console.log("Canvas cleared. You can now draw a new line.");
    }
    
    function sendPath() {
        if (!hasDrawn || pathPoints.length < 2) {
            alert("Please draw a path first!");
            return;
        }
        
        // Simplify the path - take every Nth point to avoid too many coordinates
        const simplifiedPath = simplifyPath(pathPoints, 10); // Take every 10th point
        
        console.log(`Sending simplified path with ${simplifiedPath.length} points:`, simplifiedPath);
        
        fetch('http://172.20.10.4:5000/path', { 
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                pathPoints: simplifiedPath, // Send actual drawing coordinates
                imageData: canvas.toDataURL('image/png') // Still send image for backup
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log("Server response:", data);
            alert(data.message);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to send path. See console for details.');
        });
    }
    
    function simplifyPath(points, minDistance = 30) {
        if (points.length <= 2) return points.map(p => [p.x, p.y]);
        
        const simplified = [];
        
        // Always include first point
        simplified.push([points[0].x, points[0].y]);
        let lastPoint = points[0];
        
        // Only add points that are significantly far from the last added point
        for (let i = 1; i < points.length; i++) {
            const currentPoint = points[i];
            const distance = Math.sqrt(
                Math.pow(currentPoint.x - lastPoint.x, 2) + 
                Math.pow(currentPoint.y - lastPoint.y, 2)
            );
            
            // Only add point if it's far enough from the last added point
            if (distance >= minDistance) {
                simplified.push([currentPoint.x, currentPoint.y]);
                lastPoint = currentPoint;
            }
        }
        
        // Always include the last point if it's not already close to the last added point
        const lastDrawn = points[points.length - 1];
        const lastAdded = simplified[simplified.length - 1];
        const finalDistance = Math.sqrt(
            Math.pow(lastDrawn.x - lastAdded[0], 2) + 
            Math.pow(lastDrawn.y - lastAdded[1], 2)
        );
        
        if (finalDistance >= minDistance) {
            simplified.push([lastDrawn.x, lastDrawn.y]);
        }
        
        console.log(`Simplified from ${points.length} to ${simplified.length} points (min distance: ${minDistance}px)`);
        return simplified;
    }
    
    // Remove this function since we're not using coordinates from image anymore
    function moveRobotAlongPath(coordinates) {
        console.log("Robot movement will be handled by server with actual drawing coordinates");
    }
});