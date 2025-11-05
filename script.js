document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('drawingCanvas');
    const ctx = canvas.getContext('2d');
    const clearButton = document.getElementById('clearButton');
    const sendButton = document.getElementById('sendBtn');
    let drawing = false;
    let hasDrawn = false;
    let pathPoints = []; // Store drawing path

    // canvas size
    canvas.width = 800;
    canvas.height = 600;

    // pencil properties
    ctx.lineWidth = 5;
    ctx.lineCap = 'round';
    ctx.strokeStyle = '#000000'; 

    // Event listeners for drawing
    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mouseup', stopDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseout', stopDrawing);

    // Event listener for send button
    sendButton.addEventListener('click', sendPath);

    // When R is pressed canvas is reset
    document.addEventListener('keydown', (e) => {
        if (e.key.toLowerCase() === 'r') {
            clearCanvas();
        }
    });

    function startDrawing(e) {
        // drawing can only happen on blank canvas
        if (hasDrawn) {
            console.log("Line already drawn. Press 'R' to reset and draw a new line.");
            return;
        }

        drawing = true;
        const x = e.offsetX;
        const y = e.offsetY;

        // new path start logic
        pathPoints = [{ x: x, y: y }];
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

        // record points
        pathPoints.push({ x: x, y: y });

        // drawing
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

        // path simplification that is easier to handle
        const simplifiedPath = simplifyPath(pathPoints, 10); // every 10th point is used

        console.log(`Sending simplified path with ${simplifiedPath.length} points:`, simplifiedPath);

        fetch('http://172.20.10.2:5000/path', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                pathPoints: simplifiedPath, // send drawing coordinates
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

        // first point is always included
        simplified.push([points[0].x, points[0].y]);
        let lastPoint = points[0];

        // points that are significant are used
        for (let i = 1; i < points.length; i++) {
            const currentPoint = points[i];
            const distance = Math.sqrt(
                Math.pow(currentPoint.x - lastPoint.x, 2) +
                Math.pow(currentPoint.y - lastPoint.y, 2)
            );


            if (distance >= minDistance) {
                simplified.push([currentPoint.x, currentPoint.y]);
                lastPoint = currentPoint;
            }
        }

      
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


// green object detection control
const startDetectionBtn = document.getElementById('startDetectionBtn');
const serverURL = "http://172.20.10.2:5000";

async function startGreenDetection() {
    try {
        console.log("Starting green detection...");
        const res = await fetch(`${serverURL}/detection/start`, {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });
        const data = await res.json();
        console.log("Detection start response:", data);
        alert("Green detection started!");
    } catch (err) {
        console.error("Error starting detection:", err);
        alert("Failed to start detection.");
    }
}
if (startDetectionBtn) startDetectionBtn.addEventListener('click', startGreenDetection);
