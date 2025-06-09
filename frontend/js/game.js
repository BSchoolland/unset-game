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
        
        // New atmospheric elements
        this.dustClouds = [];
        this.moon = null;
        this.moonOrbitAngle = 0;
        this.sunOrbitAngle = 0;
        
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
        this.scene.background = new THREE.Color(0x2a1810); // Dark desert sky

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

        // Lighting - warm desert lighting
        const ambientLight = new THREE.AmbientLight(0x6B4423, 0.3); // Warm ambient
        this.scene.add(ambientLight);

        // Add subtle blue ambient light for nighttime
        const nightAmbientLight = new THREE.AmbientLight(0x4169E1, 0.45); // Blue ambient for night
        this.scene.add(nightAmbientLight);

        this.directionalLight = new THREE.DirectionalLight(0xFFB366, 1.2); // Orange sun
        this.directionalLight.position.set(15, 0, 0); // Position along equator (Y=0)
        this.directionalLight.castShadow = true;
        this.directionalLight.shadow.mapSize.width = 2048;
        this.directionalLight.shadow.mapSize.height = 2048;
        this.scene.add(this.directionalLight);

        // Create visual sun object
        const sunGeometry = new THREE.SphereGeometry(0.2, 16, 8);
        const sunMaterial = new THREE.MeshBasicMaterial({
            color: 0xFFB366,
            emissive: 0xFFB366,
            emissiveIntensity: 1.0
        });
        this.sun = new THREE.Mesh(sunGeometry, sunMaterial);
        this.sun.position.copy(this.directionalLight.position);
        this.scene.add(this.sun);

        // Add secondary light for sci-fi effect
        const blueLight = new THREE.PointLight(0x00BFFF, 0.4, 10);
        blueLight.position.set(-3, 2, 4);
        this.scene.add(blueLight);

        // Create sphere
        this.createSphere();

        // Handle window resize
        window.addEventListener('resize', () => this.onWindowResize());

        // Mouse interaction
        this.setupMouseInteraction();

        // Create starfield
        this.createStarfield();
    }

    createSphere() {
        // Desert planet base with noise
        const geometry = new THREE.SphereGeometry(1, 64, 32);
        
        // Add noise to vertices for rougher surface
        const positions = geometry.attributes.position;
        for (let i = 0; i < positions.count; i++) {
            const vertex = new THREE.Vector3().fromBufferAttribute(positions, i);
            const noise = (Math.random() - 0.5) * 0.02;
            vertex.normalize().multiplyScalar(1 + noise);
            positions.setXYZ(i, vertex.x, vertex.y, vertex.z);
        }
        geometry.computeVertexNormals();
        
        const material = new THREE.MeshPhongMaterial({
            color: 0xD2691E, // Sandy brown
            transparent: false,
            opacity: 1.0,
            roughness: 0.8,
            wireframe: false
        });
        
        this.sphere = new THREE.Mesh(geometry, material);
        this.sphere.receiveShadow = true;
        this.scene.add(this.sphere);

        // Add rocky texture layer
        const textureGeometry = new THREE.SphereGeometry(1.002, 64, 32);
        const rockMaterial = new THREE.MeshPhongMaterial({
            color: 0x8B4513, // Saddle brown for rocks
            transparent: true,
            opacity: 0.4
        });
        const rockLayer = new THREE.Mesh(textureGeometry, rockMaterial);
        this.scene.add(rockLayer);

        // Add mountains/rocks randomly distributed
        for (let i = 0; i < 20; i++) {
            const lat = (Math.random() - 0.5) * 180;
            const lon = (Math.random() - 0.5) * 360;
            const pos = this.latLonToVector3(lat, lon);
            
            const rockGeometry = new THREE.ConeGeometry(0.02 + Math.random() * 0.03, 0.05 + Math.random() * 0.1, 6);
            const rockMaterial = new THREE.MeshPhongMaterial({
                color: new THREE.Color().setHSL(0.08, 0.3 + Math.random() * 0.3, 0.2 + Math.random() * 0.3)
            });
            const rock = new THREE.Mesh(rockGeometry, rockMaterial);
            rock.position.copy(pos.multiplyScalar(1.01 + Math.random() * 0.02));
            
            // Fix rotation: point rocks outward from planet center (local up vector)
            const localUp = rock.position.clone().normalize();
            const quaternion = new THREE.Quaternion();
            quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), localUp);
            rock.setRotationFromQuaternion(quaternion);
            
            rock.castShadow = true;
            this.scene.add(rock);
        }

        // Add wider, shorter mountains
        for (let i = 0; i < 150; i++) {
            const lat = (Math.random() - 0.5) * 180;
            const lon = (Math.random() - 0.5) * 360;
            const pos = this.latLonToVector3(lat, lon);
            
            const mountainGeometry = new THREE.ConeGeometry(0.06 + Math.random() * 0.08, 0.03 + Math.random() * 0.04, 8);
            const mountainMaterial = new THREE.MeshPhongMaterial({
                color: new THREE.Color().setHSL(0.06, 0.4 + Math.random() * 0.2, 0.25 + Math.random() * 0.15)
            });
            const mountain = new THREE.Mesh(mountainGeometry, mountainMaterial);
            mountain.position.copy(pos.multiplyScalar(1.01 + Math.random() * 0.015));
            
            // Fix rotation: point mountains outward from planet center
            const localUp = mountain.position.clone().normalize();
            const quaternion = new THREE.Quaternion();
            quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), localUp);
            mountain.setRotationFromQuaternion(quaternion);
            
            mountain.castShadow = true;
            this.scene.add(mountain);
        }

        // Create dust clouds that move across the planet's surface
        this.createDustClouds();
        
        // Create orbiting forest green moon
        this.createMoon();
    }

    createDustClouds() {
        // Create several dust cloud systems
        for (let i = 0; i < 8; i++) {
            const dustGroup = new THREE.Group();
            
            // Position the dust cloud on the planet surface first
            const lat = (Math.random() - 0.5) * 180;
            const lon = (Math.random() - 0.5) * 360;
            const pos = this.latLonToVector3(lat, lon);
            dustGroup.position.copy(pos.multiplyScalar(1.01)); // Slightly above surface
            
            // Create multiple particles for each dust cloud
            for (let j = 0; j < 20; j++) {
                const dustGeometry = new THREE.PlaneGeometry(0.05 + Math.random() * 0.1, 0.04 + Math.random() * 0.01);
                const dustMaterial = new THREE.MeshBasicMaterial({
                    color: new THREE.Color().setHSL(0.08, 0.4, 0.3 + Math.random() * 0.2), // Much darker sandy dust color
                    transparent: true,
                    opacity: 0.2 + Math.random() * 0.15,
                    side: THREE.DoubleSide
                });
                
                const dustParticle = new THREE.Mesh(dustGeometry, dustMaterial);
                
                // Position particles in a loose cloud formation
                const offsetX = (Math.random() - 0.5) * 0.3;
                const offsetY = (Math.random() - 0.5) * 0.1;
                const offsetZ = (Math.random() - 0.5) * 0.3;
                dustParticle.position.set(offsetX, offsetY, offsetZ);
                
                // Orient each particle to face outward from planet like mountains
                const particleWorldPos = dustGroup.position.clone().add(dustParticle.position);
                const localUp = particleWorldPos.normalize();
                const quaternion = new THREE.Quaternion();
                quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), localUp);
                dustParticle.setRotationFromQuaternion(quaternion);
                
                dustGroup.add(dustParticle);
            }
            
            // Store movement properties - much slower
            dustGroup.userData = {
                orbitSpeed: 0.0001 + Math.random() * 0.0005, // 10x slower movement
                orbitAxis: new THREE.Vector3(
                    (Math.random() - 0.5) * 2,
                    (Math.random() - 0.5) * 2,
                    (Math.random() - 0.5) * 2
                ).normalize(),
                orbitRadius: 1.08
            };
            
            this.dustClouds.push(dustGroup);
            this.scene.add(dustGroup);
        }
    }

    createMoon() {
        // Create forest green moon with texture
        const moonGeometry = new THREE.SphereGeometry(0.15, 32, 16);
        
        // Create canvas texture for forest-like appearance
        const canvas = document.createElement('canvas');
        canvas.width = 256;
        canvas.height = 256;
        const context = canvas.getContext('2d');
        
        // Base forest green color
        context.fillStyle = '#228B22';
        context.fillRect(0, 0, 256, 256);
        
        // Add darker green patches for forest variation
        for (let i = 0; i < 50; i++) {
            const x = Math.random() * 256;
            const y = Math.random() * 256;
            const size = 10 + Math.random() * 20;
            context.fillStyle = `hsl(120, ${40 + Math.random() * 30}%, ${15 + Math.random() * 15}%)`;
            context.beginPath();
            context.arc(x, y, size, 0, 2 * Math.PI);
            context.fill();
        }
        
        // Add lighter green highlights
        for (let i = 0; i < 30; i++) {
            const x = Math.random() * 256;
            const y = Math.random() * 256;
            const size = 5 + Math.random() * 10;
            context.fillStyle = `hsl(120, ${30 + Math.random() * 20}%, ${35 + Math.random() * 10}%)`;
            context.beginPath();
            context.arc(x, y, size, 0, 2 * Math.PI);
            context.fill();
        }
        
        const moonTexture = new THREE.CanvasTexture(canvas);
        const moonMaterial = new THREE.MeshPhongMaterial({
            map: moonTexture,
            color: 0x228B22, // Forest green
            shininess: 30
        });
        
        this.moon = new THREE.Mesh(moonGeometry, moonMaterial);
        this.moon.castShadow = true;
        this.moon.receiveShadow = true;
        
        // Start moon at distance of 5 units from planet center
        this.moon.position.set(5, 0, 0);
        this.scene.add(this.moon);
    }

    createStarfield() {
        // Create a large sphere for the starfield background
        const starfieldGeometry = new THREE.SphereGeometry(500, 64, 32);
        
        // Create high-resolution canvas texture for sharp stars
        const canvas = document.createElement('canvas');
        canvas.width = 2048;
        canvas.height = 1024;
        const context = canvas.getContext('2d');
        
        // Disable smoothing for crisp pixels
        context.imageSmoothingEnabled = false;
        
        // Pure black space background
        context.fillStyle = '#000000';
        context.fillRect(0, 0, canvas.width, canvas.height);
        
        // Add tiny sharp white star points
        context.fillStyle = '#FFFFFF';
        for (let i = 0; i < 5000; i++) {
            const x = Math.floor(Math.random() * canvas.width);
            const y = Math.floor(Math.random() * canvas.height);
            context.fillRect(x, y, 1, 1); // Single pixel stars
        }
        
        const starTexture = new THREE.CanvasTexture(canvas);
        starTexture.magFilter = THREE.NearestFilter; // Sharp pixel filtering
        starTexture.minFilter = THREE.NearestFilter;
        
        const starfieldMaterial = new THREE.MeshBasicMaterial({
            map: starTexture,
            side: THREE.BackSide // Render on inside of sphere
        });
        
        const starfield = new THREE.Mesh(starfieldGeometry, starfieldMaterial);
        this.scene.add(starfield);
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
            
            // Create flat circular icon based on node type
            const type = node.properties.type || 'default';
            const iconRadius = 0.04;
            
            // Create a circular plane geometry for the icon
            const geometry = new THREE.CircleGeometry(iconRadius, 16);
            
            // Create canvas for the icon
            const canvas = document.createElement('canvas');
            canvas.width = 128;
            canvas.height = 128;
            const context = canvas.getContext('2d');
            
            // Draw icon background circle
            context.fillStyle = this.getIconColor(type);
            context.beginPath();
            context.arc(64, 64, 60, 0, 2 * Math.PI);
            context.fill();
            
            // Draw border
            context.strokeStyle = 'white';
            context.lineWidth = 4;
            context.stroke();
            
            // Draw icon symbol
            context.fillStyle = 'white';
            context.font = 'bold 40px Arial';
            context.textAlign = 'center';
            context.textBaseline = 'middle';
            context.fillText(this.getIconSymbol(type), 64, 64);
            
            const texture = new THREE.CanvasTexture(canvas);
            const material = new THREE.MeshBasicMaterial({
                map: texture,
                transparent: true,
                side: THREE.DoubleSide
            });
            
            const mesh = new THREE.Mesh(geometry, material);
            mesh.position.copy(position);
            mesh.position.multiplyScalar(1.02);
            
            // Make icon face outward from planet
            const localUp = mesh.position.clone().normalize();
            const quaternion = new THREE.Quaternion();
            quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), localUp);
            mesh.setRotationFromQuaternion(quaternion);
            
            this.scene.add(mesh);

            // Create floating holographic label (hidden by default)
            const labelGeometry = new THREE.PlaneGeometry(0.15, 0.04);
            const labelCanvas = document.createElement('canvas');
            labelCanvas.width = 256;
            labelCanvas.height = 64;
            const labelContext = labelCanvas.getContext('2d');
            labelContext.fillStyle = 'rgba(0, 150, 255, 0.8)';
            labelContext.fillRect(0, 0, 256, 64);
            labelContext.fillStyle = 'cyan';
            labelContext.font = 'bold 14px monospace';
            labelContext.textAlign = 'center';
            labelContext.fillText(node.name, 128, 40);
            
            const labelTexture = new THREE.CanvasTexture(labelCanvas);
            const labelMaterial = new THREE.MeshBasicMaterial({
                map: labelTexture,
                transparent: true,
                opacity: 0 // Hidden by default
            });
            const label = new THREE.Mesh(labelGeometry, labelMaterial);
            label.position.copy(position);
            label.position.multiplyScalar(1.15);
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

    getIconColor(type) {
        const colors = {
            'city': '#ff6b6b',
            'port': '#4ecdc4',
            'outpost': '#45b7d1',
            'base': '#96ceb4',
            'hub': '#ffeaa7',
            'fort': '#dda0dd',
            'colony': '#98d8c8',
            'default': '#ffffff'
        };
        return colors[type] || colors.default;
    }

    getIconSymbol(type) {
        const symbols = {
            'city': '◈', // Diamond for major settlement
            'port': '⚡', // Lightning for energy/transport hub
            'outpost': '▲', // Triangle for small outpost
            'base': '■', // Square for military base
            'hub': '✦', // Star for connection hub
            'fort': '⬟', // Hexagon for fortification
            'colony': '◯', // Circle for colony
            'default': '●'  // Filled circle for unknown
        };
        return symbols[type] || symbols.default;
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
        
        // Fix rotation: align player to stand upright on planet surface (local up vector)
        const localUp = this.playerObject.position.clone().normalize();
        const quaternion = new THREE.Quaternion();
        quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), localUp);
        this.playerObject.setRotationFromQuaternion(quaternion);
        
        this.playerObject.castShadow = true;
        
        this.scene.add(this.playerObject);
    }

    selectNode(nodeId) {
        // Reset previous selection
        if (this.selectedNode) {
            const prevNodeObj = this.nodeObjects.get(this.selectedNode);
            if (prevNodeObj) {
                // Reset icon back to normal and hide label
                this.updateIconSelection(prevNodeObj, false);
                prevNodeObj.label.material.opacity = 0;
            }
        }

        // Highlight new selection
        this.selectedNode = nodeId;
        const nodeObj = this.nodeObjects.get(nodeId);
        if (nodeObj) {
            // Highlight selected icon and show label
            this.updateIconSelection(nodeObj, true);
            nodeObj.label.material.opacity = 1;
            this.updateSelectedNodeInfo(nodeObj.node);
            
            // Enable/disable buttons based on selection
            const findPathBtn = document.getElementById('find-path-btn');
            const movePlayerBtn = document.getElementById('move-player-btn');
            
            findPathBtn.disabled = !this.currentPlayer;
            movePlayerBtn.disabled = !this.currentPlayer || !this.canMoveToNode(nodeId);
        }
    }

    updateIconSelection(nodeObj, isSelected) {
        const node = nodeObj.node;
        const type = node.properties.type || 'default';
        const iconRadius = 0.04;
        
        // Create canvas for the icon with selection state
        const canvas = document.createElement('canvas');
        canvas.width = 128;
        canvas.height = 128;
        const context = canvas.getContext('2d');
        
        // Draw icon background circle
        context.fillStyle = this.getIconColor(type);
        context.beginPath();
        context.arc(64, 64, 60, 0, 2 * Math.PI);
        context.fill();
        
        // Draw border (thicker and different color if selected)
        if (isSelected) {
            context.strokeStyle = '#ffff00'; // Yellow for selection
            context.lineWidth = 8;
        } else {
            context.strokeStyle = 'white';
            context.lineWidth = 4;
        }
        context.stroke();
        
        // Draw icon symbol
        context.fillStyle = 'white';
        context.font = 'bold 40px Arial';
        context.textAlign = 'center';
        context.textBaseline = 'middle';
        context.fillText(this.getIconSymbol(type), 64, 64);
        
        // Update the texture
        const texture = new THREE.CanvasTexture(canvas);
        nodeObj.mesh.material.map = texture;
        nodeObj.mesh.material.needsUpdate = true;
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
        
        // Animate dust clouds moving across planet surface
        this.dustClouds.forEach(dustGroup => {
            const userData = dustGroup.userData;
            
            // Rotate the dust cloud around the planet
            const rotationMatrix = new THREE.Matrix4();
            rotationMatrix.makeRotationAxis(userData.orbitAxis, userData.orbitSpeed);
            dustGroup.position.applyMatrix4(rotationMatrix);
            
            // Update each particle orientation to stay aligned with planet surface
            dustGroup.children.forEach((particle, index) => {
                const particleWorldPos = dustGroup.position.clone().add(particle.position);
                const localUp = particleWorldPos.normalize();
                const quaternion = new THREE.Quaternion();
                quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), localUp);
                particle.setRotationFromQuaternion(quaternion);
                
                // Add slight rotation to individual particles
                particle.rotation.z += 0.001 + index * 0.0001; // Much slower individual rotation
            });
        });
        
        // Animate moon orbit - much slower
        if (this.moon) {
            this.moonOrbitAngle += 0.0001;
            const orbitRadius = 5;
            this.moon.position.x = Math.cos(this.moonOrbitAngle) * orbitRadius;
            this.moon.position.z = Math.sin(this.moonOrbitAngle) * orbitRadius;
            this.moon.position.y = Math.sin(this.moonOrbitAngle * 0.5) * 0.5; // Slight vertical oscillation
            
            // Make moon rotate on its own axis - also slower
            this.moon.rotation.y += 0.001;
        }
        
        // Animate sun orbit to simulate planet rotation
        if (this.directionalLight && this.sun) {
            this.sunOrbitAngle += 0.0005; // Very slow orbit to simulate day/night cycle
            const sunOrbitRadius = 15;
            this.directionalLight.position.x = Math.cos(this.sunOrbitAngle) * sunOrbitRadius;
            this.directionalLight.position.z = Math.sin(this.sunOrbitAngle) * sunOrbitRadius;
            this.directionalLight.position.y = Math.sin(this.sunOrbitAngle * 0.2) * 3; // Slight vertical movement
            
            // Update visual sun position to match light
            this.sun.position.copy(this.directionalLight.position);
        }
        
        // Planet is now stationary - no rotation
        
        this.renderer.render(this.scene, this.camera);
    }
}

// Initialize the game when the page loads
window.addEventListener('load', () => {
    new SphereGame();
}); 