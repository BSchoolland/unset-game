/**
 * Sphere Game - Three.js Frontend
 * Visualizes nodes on a sphere surface with player movement capabilities
 */

class SphereGame {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.sphere = null;
        this.nodes = [];
        this.nodeObjects = new Map(); // Map node ID to Three.js objects
        this.connectionLines = [];
        this.reachableLines = [];
        this.pathLines = [];
        this.player = null;
        this.playerObject = null;
        this.selectedNode = null;
        this.currentPlayer = null;
        this.showConnections = true;
        this.speed = 1.0;
        
        // API base URL
        this.apiUrl = 'http://localhost:8000';
        
        this.init();
    }

    async init() {
        try {
            this.setupThreeJS();
            this.setupEventListeners();
            await this.loadGameData();
            this.hideLoading();
            this.animate();
        } catch (error) {
            console.error('Failed to initialize game:', error);
            this.showStatus('Failed to load game. Make sure the server is running.', 'error');
        }
    }

    setupThreeJS() {
        // Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x000011);

        // Camera
        this.camera = new THREE.PerspectiveCamera(
            75,
            window.innerWidth / window.innerHeight,
            0.1,
            1000
        );
        this.camera.position.set(0, 0, 3);

        // Renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        document.getElementById('container').appendChild(this.renderer.domElement);

        // Controls
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.minDistance = 1.5;
        this.controls.maxDistance = 10;

        // Lighting
        const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
        this.scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(5, 5, 5);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        this.scene.add(directionalLight);

        // Create sphere
        this.createSphere();

        // Handle window resize
        window.addEventListener('resize', () => this.onWindowResize());

        // Mouse interaction
        this.setupMouseInteraction();
    }

    createSphere() {
        const geometry = new THREE.SphereGeometry(1, 64, 32);
        const material = new THREE.MeshPhongMaterial({
            color: 0x2194ce,
            transparent: true,
            opacity: 0.8,
            wireframe: false
        });
        
        this.sphere = new THREE.Mesh(geometry, material);
        this.sphere.receiveShadow = true;
        this.scene.add(this.sphere);

        // Add wireframe overlay
        const wireframeGeometry = new THREE.SphereGeometry(1.001, 32, 16);
        const wireframeMaterial = new THREE.MeshBasicMaterial({
            color: 0x444444,
            wireframe: true,
            transparent: true,
            opacity: 0.3
        });
        const wireframe = new THREE.Mesh(wireframeGeometry, wireframeMaterial);
        this.scene.add(wireframe);
    }

    setupMouseInteraction() {
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();

        this.renderer.domElement.addEventListener('click', (event) => {
            // Calculate mouse position in normalized device coordinates
            mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

            raycaster.setFromCamera(mouse, this.camera);

            // Check for intersections with node objects
            const nodeObjects = Array.from(this.nodeObjects.values()).map(obj => obj.mesh);
            const intersects = raycaster.intersectObjects(nodeObjects);

            if (intersects.length > 0) {
                const clickedObject = intersects[0].object;
                // Find the node ID for this object
                for (const [nodeId, nodeObj] of this.nodeObjects.entries()) {
                    if (nodeObj.mesh === clickedObject) {
                        this.selectNode(nodeId);
                        break;
                    }
                }
            }
        });
    }

    setupEventListeners() {
        // Speed slider
        const speedSlider = document.getElementById('speed-slider');
        const speedValue = document.getElementById('speed-value');
        speedSlider.addEventListener('input', (e) => {
            this.speed = parseFloat(e.target.value);
            speedValue.textContent = this.speed.toFixed(1);
        });

        // Buttons
        document.getElementById('create-player-btn').addEventListener('click', () => this.createPlayer());
        document.getElementById('show-connections-btn').addEventListener('click', () => this.toggleConnections());
        document.getElementById('show-reachable-btn').addEventListener('click', () => this.showReachableNodes());
        document.getElementById('find-path-btn').addEventListener('click', () => this.findPathToSelected());
        document.getElementById('move-player-btn').addEventListener('click', () => this.movePlayerToSelected());
        document.getElementById('reset-view-btn').addEventListener('click', () => this.resetView());
    }

    async loadGameData() {
        try {
            // Load nodes
            const nodesResponse = await fetch(`${this.apiUrl}/nodes`);
            this.nodes = await nodesResponse.json();
            
            // Load network stats
            await this.updateNetworkStats();
            
            // Create visual representations
            this.createNodeObjects();
            this.createConnectionLines();
            
        } catch (error) {
            console.error('Failed to load game data:', error);
            throw error;
        }
    }

    createNodeObjects() {
        // Clear existing node objects
        this.nodeObjects.forEach(nodeObj => {
            this.scene.remove(nodeObj.mesh);
            this.scene.remove(nodeObj.label);
        });
        this.nodeObjects.clear();

        this.nodes.forEach(node => {
            const position = this.latLonToVector3(node.location.latitude, node.location.longitude);
            
            // Create node mesh
            const geometry = new THREE.SphereGeometry(0.03, 16, 8);
            const material = new THREE.MeshPhongMaterial({
                color: this.getNodeColor(node),
                emissive: 0x222222
            });
            const mesh = new THREE.Mesh(geometry, material);
            mesh.position.copy(position);
            mesh.castShadow = true;
            this.scene.add(mesh);

            // Create label
            const labelGeometry = new THREE.PlaneGeometry(0.2, 0.05);
            const canvas = document.createElement('canvas');
            canvas.width = 256;
            canvas.height = 64;
            const context = canvas.getContext('2d');
            context.fillStyle = 'rgba(0, 0, 0, 0.8)';
            context.fillRect(0, 0, 256, 64);
            context.fillStyle = 'white';
            context.font = '16px Arial';
            context.textAlign = 'center';
            context.fillText(node.name, 128, 40);
            
            const texture = new THREE.CanvasTexture(canvas);
            const labelMaterial = new THREE.MeshBasicMaterial({
                map: texture,
                transparent: true
            });
            const label = new THREE.Mesh(labelGeometry, labelMaterial);
            label.position.copy(position);
            label.position.multiplyScalar(1.1);
            label.lookAt(this.camera.position);
            this.scene.add(label);

            this.nodeObjects.set(node.id, { mesh, label, node });
        });
    }

    getNodeColor(node) {
        const type = node.properties.type || 'default';
        const colors = {
            'city': 0xff6b6b,
            'port': 0x4ecdc4,
            'outpost': 0x45b7d1,
            'base': 0x96ceb4,
            'hub': 0xffeaa7,
            'fort': 0xdda0dd,
            'colony': 0x98d8c8,
            'default': 0xffffff
        };
        return colors[type] || colors.default;
    }

    createConnectionLines() {
        // Clear existing lines
        this.connectionLines.forEach(line => this.scene.remove(line));
        this.connectionLines = [];

        if (!this.showConnections) return;

        this.nodes.forEach(node => {
            const startPos = this.latLonToVector3(node.location.latitude, node.location.longitude);
            
            node.connections.forEach(connectionId => {
                const connectedNode = this.nodes.find(n => n.id === connectionId);
                if (connectedNode) {
                    const endPos = this.latLonToVector3(connectedNode.location.latitude, connectedNode.location.longitude);
                    
                    // Create curved line on sphere surface
                    const line = this.createCurvedLine(startPos, endPos, 0x00ff00, 0.6);
                    this.scene.add(line);
                    this.connectionLines.push(line);
                }
            });
        });
    }

    createCurvedLine(start, end, color, opacity) {
        const curve = new THREE.QuadraticBezierCurve3(
            start,
            start.clone().add(end).normalize().multiplyScalar(1.1),
            end
        );
        
        const points = curve.getPoints(20);
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        const material = new THREE.LineBasicMaterial({
            color: color,
            transparent: true,
            opacity: opacity
        });
        
        return new THREE.Line(geometry, material);
    }

    latLonToVector3(lat, lon) {
        const phi = (90 - lat) * (Math.PI / 180);
        const theta = (lon + 180) * (Math.PI / 180);
        
        const x = Math.sin(phi) * Math.cos(theta);
        const y = Math.cos(phi);
        const z = Math.sin(phi) * Math.sin(theta);
        
        return new THREE.Vector3(x, y, z);
    }

    async createPlayer() {
        if (this.nodes.length === 0) {
            this.showStatus('No nodes available to place player', 'error');
            return;
        }

        try {
            const startingNode = this.nodes[0]; // Use first node as starting position
            const response = await fetch(`${this.apiUrl}/players`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: 'Player 1',
                    starting_node_id: startingNode.id,
                    properties: {}
                })
            });

            if (response.ok) {
                this.currentPlayer = await response.json();
                this.createPlayerObject();
                this.updatePlayerStatus();
                this.showStatus('Player created successfully!', 'success');
            } else {
                throw new Error('Failed to create player');
            }
        } catch (error) {
            console.error('Error creating player:', error);
            this.showStatus('Failed to create player', 'error');
        }
    }

    createPlayerObject() {
        if (this.playerObject) {
            this.scene.remove(this.playerObject);
        }

        if (!this.currentPlayer) return;

        const position = this.latLonToVector3(
            this.currentPlayer.location.latitude,
            this.currentPlayer.location.longitude
        );

        const geometry = new THREE.ConeGeometry(0.05, 0.1, 8);
        const material = new THREE.MeshPhongMaterial({
            color: 0xff0000,
            emissive: 0x440000
        });
        
        this.playerObject = new THREE.Mesh(geometry, material);
        this.playerObject.position.copy(position);
        this.playerObject.position.multiplyScalar(1.05);
        this.playerObject.lookAt(new THREE.Vector3(0, 0, 0));
        this.playerObject.castShadow = true;
        
        this.scene.add(this.playerObject);
    }

    selectNode(nodeId) {
        // Reset previous selection
        if (this.selectedNode) {
            const prevNodeObj = this.nodeObjects.get(this.selectedNode);
            if (prevNodeObj) {
                prevNodeObj.mesh.material.emissive.setHex(0x222222);
            }
        }

        // Highlight new selection
        this.selectedNode = nodeId;
        const nodeObj = this.nodeObjects.get(nodeId);
        if (nodeObj) {
            nodeObj.mesh.material.emissive.setHex(0x444444);
            this.updateSelectedNodeInfo(nodeObj.node);
            
            // Enable/disable buttons based on selection
            const findPathBtn = document.getElementById('find-path-btn');
            const movePlayerBtn = document.getElementById('move-player-btn');
            
            findPathBtn.disabled = !this.currentPlayer;
            movePlayerBtn.disabled = !this.currentPlayer || !this.canMoveToNode(nodeId);
        }
    }

    canMoveToNode(nodeId) {
        if (!this.currentPlayer) return false;
        
        const currentNode = this.nodes.find(n => n.id === this.currentPlayer.current_node_id);
        return currentNode && currentNode.connections.includes(nodeId);
    }

    updateSelectedNodeInfo(node) {
        const info = document.getElementById('selected-node-info');
        info.innerHTML = `
            <strong>${node.name}</strong><br>
            Location: ${node.location.latitude.toFixed(2)}, ${node.location.longitude.toFixed(2)}<br>
            Type: ${node.properties.type || 'Unknown'}<br>
            Population: ${node.properties.population || 'Unknown'}<br>
            Connections: ${node.connections.length}
        `;
    }

    updatePlayerStatus() {
        const status = document.getElementById('player-status');
        const createBtn = document.getElementById('create-player-btn');
        
        if (this.currentPlayer) {
            const currentNode = this.nodes.find(n => n.id === this.currentPlayer.current_node_id);
            status.innerHTML = `
                <strong>${this.currentPlayer.name}</strong><br>
                Current Location: ${currentNode ? currentNode.name : 'Unknown'}<br>
                Coordinates: ${this.currentPlayer.location.latitude.toFixed(2)}, ${this.currentPlayer.location.longitude.toFixed(2)}
            `;
            createBtn.style.display = 'none';
        } else {
            status.textContent = 'No player created';
            createBtn.style.display = 'inline-block';
        }
    }

    async updateNetworkStats() {
        try {
            const response = await fetch(`${this.apiUrl}/network/stats`);
            const stats = await response.json();
            
            const statsDiv = document.getElementById('network-stats');
            statsDiv.innerHTML = `
                Nodes: ${stats.total_nodes}<br>
                Connections: ${stats.total_connections}<br>
                Avg Connections: ${stats.average_connections_per_node.toFixed(1)}<br>
                Isolated Nodes: ${stats.isolated_nodes}
            `;
        } catch (error) {
            console.error('Failed to load network stats:', error);
        }
    }

    toggleConnections() {
        this.showConnections = !this.showConnections;
        this.createConnectionLines();
        
        const btn = document.getElementById('show-connections-btn');
        btn.textContent = this.showConnections ? 'Hide Connections' : 'Show Connections';
    }

    async showReachableNodes() {
        if (!this.currentPlayer) {
            this.showStatus('Create a player first', 'error');
            return;
        }

        try {
            const response = await fetch(
                `${this.apiUrl}/players/${this.currentPlayer.id}/reachable?speed=${this.speed}`
            );
            const data = await response.json();
            
            // Clear previous reachable lines
            this.reachableLines.forEach(line => this.scene.remove(line));
            this.reachableLines = [];
            
            // Create lines to reachable nodes
            const currentPos = this.latLonToVector3(
                this.currentPlayer.location.latitude,
                this.currentPlayer.location.longitude
            );
            
            data.reachable_nodes.forEach(item => {
                const nodePos = this.latLonToVector3(
                    item.node.location.latitude,
                    item.node.location.longitude
                );
                
                const line = this.createCurvedLine(currentPos, nodePos, 0xffff00, 0.8);
                this.scene.add(line);
                this.reachableLines.push(line);
            });
            
            this.showStatus(`Found ${data.reachable_nodes.length} reachable nodes`, 'success');
        } catch (error) {
            console.error('Error showing reachable nodes:', error);
            this.showStatus('Failed to get reachable nodes', 'error');
        }
    }

    async findPathToSelected() {
        if (!this.currentPlayer || !this.selectedNode) {
            this.showStatus('Select a target node first', 'error');
            return;
        }

        try {
            const response = await fetch(
                `${this.apiUrl}/players/${this.currentPlayer.id}/path/${this.selectedNode}?speed=${this.speed}`
            );
            
            if (response.ok) {
                const data = await response.json();
                
                // Clear previous path lines
                this.pathLines.forEach(line => this.scene.remove(line));
                this.pathLines = [];
                
                // Create path lines
                for (let i = 0; i < data.node_details.length - 1; i++) {
                    const startNode = data.node_details[i];
                    const endNode = data.node_details[i + 1];
                    
                    const startPos = this.latLonToVector3(startNode.location.latitude, startNode.location.longitude);
                    const endPos = this.latLonToVector3(endNode.location.latitude, endNode.location.longitude);
                    
                    const line = this.createCurvedLine(startPos, endPos, 0xff0000, 1.0);
                    this.scene.add(line);
                    this.pathLines.push(line);
                }
                
                this.showStatus(`Path found! Travel time: ${data.total_time.toFixed(2)} units`, 'success');
            } else {
                this.showStatus('No path found to selected node', 'error');
            }
        } catch (error) {
            console.error('Error finding path:', error);
            this.showStatus('Failed to find path', 'error');
        }
    }

    async movePlayerToSelected() {
        if (!this.currentPlayer || !this.selectedNode) {
            this.showStatus('Select a target node first', 'error');
            return;
        }

        if (!this.canMoveToNode(this.selectedNode)) {
            this.showStatus('Cannot move to selected node (not connected)', 'error');
            return;
        }

        try {
            const response = await fetch(`${this.apiUrl}/players/move`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    player_id: this.currentPlayer.id,
                    target_node_id: this.selectedNode,
                    speed: this.speed
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.currentPlayer = data.player;
                this.createPlayerObject();
                this.updatePlayerStatus();
                
                // Clear path lines after movement
                this.pathLines.forEach(line => this.scene.remove(line));
                this.pathLines = [];
                
                this.showStatus(`Player moved! Travel time: ${data.travel_time.toFixed(2)} units`, 'success');
            } else {
                const error = await response.json();
                this.showStatus(error.detail || 'Failed to move player', 'error');
            }
        } catch (error) {
            console.error('Error moving player:', error);
            this.showStatus('Failed to move player', 'error');
        }
    }

    resetView() {
        this.camera.position.set(0, 0, 3);
        this.controls.reset();
        
        // Clear all highlight lines
        this.reachableLines.forEach(line => this.scene.remove(line));
        this.reachableLines = [];
        this.pathLines.forEach(line => this.scene.remove(line));
        this.pathLines = [];
    }

    showStatus(message, type = 'success') {
        const statusDiv = document.getElementById('status-messages');
        const statusElement = document.createElement('div');
        statusElement.className = `status ${type}`;
        statusElement.textContent = message;
        
        statusDiv.appendChild(statusElement);
        
        // Remove after 5 seconds
        setTimeout(() => {
            if (statusElement.parentNode) {
                statusElement.parentNode.removeChild(statusElement);
            }
        }, 5000);
    }

    hideLoading() {
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('ui').classList.remove('hidden');
        document.getElementById('controls').classList.remove('hidden');
    }

    onWindowResize() {
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        
        this.controls.update();
        
        // Update label orientations to face camera
        this.nodeObjects.forEach(nodeObj => {
            nodeObj.label.lookAt(this.camera.position);
        });
        
        // Rotate sphere slowly
        if (this.sphere) {
            this.sphere.rotation.y += 0.001;
        }
        
        this.renderer.render(this.scene, this.camera);
    }
}

// Initialize the game when the page loads
window.addEventListener('load', () => {
    new SphereGame();
}); 