import base64

def generate_viewer_html(glb_url, bvh_content, width=800, height=600):
    """
    Generates an HTML string for a Three.js viewer that loads a GLB avatar and applies BVH motion.
    
    Args:
        glb_url (str): URL to the GLB file (can be local path if served, or remote URL).
        bvh_content (str): The raw string content of the BVH file.
        width (int): Width of the viewer in pixels.
        height (int): Height of the viewer in pixels.
    """
    
    # Encode BVH content to Base64 to avoid escaping issues in HTML string
    bvh_b64 = base64.b64encode(bvh_content.encode('utf-8')).decode('utf-8')
    
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>3D Motion Viewer</title>
        <style>
            body {{ margin: 0; overflow: hidden; background-color: #222; }}
            #container {{ width: {width}px; height: {height}px; }}
        </style>
        <!-- Import maps polyfill -->
        <script async src="https://unpkg.com/es-module-shims@1.8.0/dist/es-module-shims.js"></script>
        
        <script type="importmap">
        {{
            "imports": {{
                "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
                "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
            }}
        }}
        </script>
    </head>
    <body>
        <div id="container"></div>
        <script type="module">
            import * as THREE from 'three';
            import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
            import {{ GLTFLoader }} from 'three/addons/loaders/GLTFLoader.js';
            import {{ BVHLoader }} from 'three/addons/loaders/BVHLoader.js';

            // Inputs
            const glbUrl = "{glb_url}";
            const bvhBase64 = "{bvh_b64}";
            
            // Scene Setup
            const container = document.getElementById('container');
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0xa0a0a0);
            scene.fog = new THREE.Fog(0xa0a0a0, 10, 50);

            const grid = new THREE.GridHelper(30, 30, 0x000000, 0x000000);
            grid.material.opacity = 0.2;
            grid.material.transparent = true;
            scene.add(grid);

            // Lighting
            const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 3);
            hemiLight.position.set(0, 20, 0);
            scene.add(hemiLight);

            const dirLight = new THREE.DirectionalLight(0xffffff, 3);
            dirLight.position.set(3, 10, 10);
            dirLight.castShadow = true;
            scene.add(dirLight);

            // Camera
            const camera = new THREE.PerspectiveCamera(45, {width} / {height}, 0.1, 100);
            camera.position.set(0, 2, 5);

            // Renderer
            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setPixelRatio(window.devicePixelRatio);
            renderer.setSize({width}, {height});
            renderer.shadowMap.enabled = true;
            container.appendChild(renderer.domElement);

            // Controls
            const controls = new OrbitControls(camera, renderer.domElement);
            controls.target.set(0, 1, 0);
            controls.update();

            // Globals
            let mixer = null;
            const clock = new THREE.Clock();

            // Load Assets
            const loaderGLB = new GLTFLoader();
            const loaderBVH = new BVHLoader();

            // Helper to parse Base64 BVH
            function parseBVH(b64) {{
                const text = atob(b64);
                return loaderBVH.parse(text);
            }}

            // Main Load Logic
            loaderGLB.load(glbUrl, function(gltf) {{
                const model = gltf.scene;
                scene.add(model);
                
                // Shadow
                model.traverse(function(object) {{
                    if (object.isMesh) object.castShadow = true;
                }});

                // Load BVH and Apply
                try {{
                    const bvhResult = parseBVH(bvhBase64);
                    const clip = bvhResult.clip;
                    const skeleton = bvhResult.skeleton; // The skeleton from BVH
                    
                    // We need to retarget or apply the clip to the GLB model.
                    // If bone names match, we can usually just use the clip on the GLB model's root.
                    
                    // Center the model?
                    // model.position.set(0, 0, 0); // Reset position
                    
                    mixer = new THREE.AnimationMixer(model);
                    
                    // Ensure the clip tracks are compatible with the model's skeleton
                    // Rename tracks if necessary? 
                    // BVHLoader produces tracks named ".bones[Hips].position", etc.
                    // GLTFLoader produces a hierarchy of Object3Ds. 
                    // The names should match the Object3D names.
                    
                    // ReadyPlayerMe bones often have a prefix or specific structure. 
                    // Standard mixamo names usually work.
                    // If names mismatch, we might need a map. 
                    // Assuming names match for now based on config.py.
                    
                    const action = mixer.clipAction(clip);
                    action.play();
                    
                    // Optional: SkeletonHelper to visualize bones
                    // const skeletonHelper = new THREE.SkeletonHelper(model);
                    // scene.add(skeletonHelper);
                    
                }} catch (e) {{
                    console.error("Error parsing/applying BVH:", e);
                }}

            }}, undefined, function(e) {{
                console.error("Error loading GLB:", e);
            }});

            // Animation Loop
            function animate() {{
                requestAnimationFrame(animate);
                
                const delta = clock.getDelta();
                if (mixer) mixer.update(delta);
                
                renderer.render(scene, camera);
            }}

            animate();
            
            // Handle Resize
            window.addEventListener('resize', function() {{
                // Note: In Streamlit iframe, resize might not trigger normally, but good to have
                camera.aspect = {width} / {height};
                camera.updateProjectionMatrix();
                renderer.setSize({width}, {height});
            }});
        </script>
    </body>
    </html>
    """
    return html_template
