import base64

def _css_common():
    return (
        "*{margin:0;padding:0;box-sizing:border-box;}"
        "body{background:#0d0d14;font-family:'Segoe UI',sans-serif;overflow:hidden;}"
        ".sp{width:36px;height:36px;border:3px solid rgba(120,80,255,.2);"
        "border-top-color:#7850ff;border-radius:50%;animation:spin .8s linear infinite;}"
        "@keyframes spin{to{transform:rotate(360deg)}}"
    )

def _import_map():
    # Switched to JSDelivr for higher reliability and faster global speeds
    return """
    <script async src="https://cdn.jsdelivr.net/npm/es-module-shims@1.8.0/dist/es-module-shims.min.js"></script>
    <script type="importmap">
    {
        "imports": {
            "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
            "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"
        }
    }
    </script>
    """

def _error_catcher():
    # Instantly displays any silent browser crashes on the screen
    return """
    <script>
    window.addEventListener('error', function(event) {
        const spinner = document.querySelector('.sp');
        if (spinner) spinner.style.display = 'none';
        const text = document.getElementById('loading-text');
        if (text) text.innerHTML = '<span style="color:#ff6060; padding:10px; text-align:center;"><b>Renderer Crashed:</b><br>' + event.message + '</span>';
    });
    </script>
    """

# ---------------------------------------------------------------------------
# Skeleton Viewer
# ---------------------------------------------------------------------------

def generate_skeleton_viewer_html(bvh_content: str, face_b64: str = None, video_b64: str = None, width: int = 900, height: int = 550) -> str:
    bvh_b64 = base64.b64encode(bvh_content.encode("utf-8")).decode("utf-8")
    HC = height - 54

    face_js = ""
    if face_b64:
        # Generate JS to load texture and attach to Head
        face_js = (
            f'   const faceImg = new Image(); faceImg.src = "data:image/png;base64,{face_b64}";\n'
            '   const faceTex = new THREE.Texture(faceImg); faceTex.needsUpdate = true;\n'
            '   faceTex.colorSpace = THREE.SRGBColorSpace;\n'
            '   const faceMat = new THREE.MeshBasicMaterial({map: faceTex, transparent: true, side: THREE.DoubleSide});\n'
            '   const faceGeo = new THREE.PlaneGeometry(0.3, 0.3);\n'
            '   const faceMesh = new THREE.Mesh(faceGeo, faceMat);\n'
            # Adjust rotation/position so it faces forward relative to the Head bone
            '   faceMesh.position.set(0, 0.1, 0.05);\n'
            '   let faceHeadBone = null;\n'
            '   bvh.skeleton.bones.forEach(b => { if(b.name === "Head") faceHeadBone = b; });\n'
            '   if (faceHeadBone) { faceHeadBone.add(faceMesh); avatarMeshes.push(faceMesh); }\n'
        )

    html = (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<title>Skeleton Viewer</title>'
        f'<style>{_css_common()}'
        f'#cw{{width:100%;height:{HC}px;position:relative;}}'
        '#vid{position:absolute;top:10px;left:10px;width:240px;height:auto;border-radius:8px;border:1px solid rgba(120,80,255,.4);box-shadow:0 4px 12px rgba(0,0,0,0.5);z-index:50;display:none;}'
        f'#bar{{position:absolute;bottom:0;left:0;width:100%;height:54px;'
        'display:flex;align-items:center;gap:12px;padding:0 16px;'
        'background:rgba(13,13,20,.93);border-top:1px solid rgba(120,80,255,.3);}}'
        'button{background:rgba(120,80,255,.15);border:1px solid rgba(120,80,255,.5);'
        'color:#c8b8ff;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:13px;}'
        'button:hover{background:rgba(120,80,255,.35);}'
        '#sc{flex:1;accent-color:#7850ff;cursor:pointer;}'
        '#sl{color:#9080c0;font-size:12px;min-width:56px;}'
        '#sp{accent-color:#7850ff;width:70px;cursor:pointer;}'
        '#fi{color:#9080c0;font-size:12px;min-width:80px;text-align:right;}'
        '#av{min-width:86px;}'
        '#ov{position:absolute;inset:0;display:flex;flex-direction:column;'
        'align-items:center;justify-content:center;background:#0d0d14;'
        'color:#8070c0;font-size:14px;gap:12px;z-index:100;}'
        '</style>'
        f'{_import_map()}'
        '</head><body>'
        '<div id="cw">'
        + (f'<video id="vid" src="data:video/mp4;base64,{video_b64}" muted playsinline></video>' if video_b64 else '') +
        '<div id="ov"><div class="sp"></div><span id="loading-text">Initialising renderer…</span></div>'
        '</div>'
        '<div id="bar">'
        '<button id="bp">&#9654; Play</button>'
        '<input id="sc" type="range" min="0" max="100" value="0" step="1">'
        '<span id="fi">0 / 0</span>'
        '<span id="sl">Speed: 1x</span>'
        '<input id="sp" type="range" min="0.1" max="3" value="1" step="0.1">'
        '<button id="av">Avatar</button>'
        '</div>'
        f'{_error_catcher()}'
        f'<script type="module">\n'
        f'import * as THREE from "three";\n'
        f'import {{ OrbitControls }} from "three/addons/controls/OrbitControls.js";\n'
        f'import {{ BVHLoader }} from "three/addons/loaders/BVHLoader.js";\n'
        
        # Hardcoded initial dimensions to prevent WebGL 0x0 crash in iframe
        f'const W={width}, H={HC};\n'
        
        'try {\n'
        '   const renderer = new THREE.WebGLRenderer({antialias:true});\n'
        '   renderer.setPixelRatio(window.devicePixelRatio);\n'
        '   renderer.setSize(W, H);\n'
        '   document.getElementById("cw").prepend(renderer.domElement);\n'
        '   const scene = new THREE.Scene();\n'
        '   scene.background = new THREE.Color(0x0d0d14);\n'
        '   scene.fog = new THREE.FogExp2(0x0d0d14, 0.04);\n'
        '   const grid = new THREE.GridHelper(20, 20, 0x2a1a5e, 0x1a0e3c);\n'
        '   grid.position.y = 0.02; scene.add(grid);\n'
        '   scene.add(new THREE.AmbientLight(0x7050cc, 0.6));\n'
        '   const dl = new THREE.DirectionalLight(0xffffff, 2);\n'
        '   dl.position.set(5,10,5); scene.add(dl);\n'
        '   const rl = new THREE.DirectionalLight(0x4040ff, 1.2);\n'
        '   rl.position.set(-5,5,-5); scene.add(rl);\n'
        '   const cam = new THREE.PerspectiveCamera(45, W/H, 0.01, 200);\n'
        '   cam.position.set(0, 1.5, 4);\n'
        '   const ctl = new OrbitControls(cam, renderer.domElement);\n'
        '   ctl.target.set(0,1,0); ctl.enableDamping = true; ctl.dampingFactor = 0.08; ctl.update();\n'
        
        f'   const bvhText = atob("{bvh_b64}");\n'
        '   const bvh = new BVHLoader().parse(bvhText);\n'
        '   const root = bvh.skeleton.bones[0];\n'
        '   const hr = new THREE.Object3D(); hr.add(root); scene.add(hr);\n'
        '   const sh = new THREE.SkeletonHelper(root);\n'
        '   sh.material = new THREE.LineBasicMaterial({color:0x9060ff, linewidth:2}); scene.add(sh);\n'
        '   const jointMeshes = [];\n'
        '   const jm = new THREE.MeshStandardMaterial({color:0xcc99ff, emissive:0x6030cc, emissiveIntensity:0.25, roughness:0.45});\n'
        '   function addSpheres(b) {\n'
        '     const isFinger = b.name.includes("Index") || b.name.includes("Pinky") || b.name.includes("Thumb");\n'
        '     const sphere = new THREE.Mesh(new THREE.SphereGeometry(isFinger ? 0.006 : 0.016,8,8), jm);\n'
        '     b.add(sphere); jointMeshes.push(sphere);\n'
        '     b.children.forEach(c => { if (c.isBone) addSpheres(c); });\n'
        '   }\n'
        '   addSpheres(root);\n'
        '   const avatarMeshes = [];\n'
        '   const skin = new THREE.MeshStandardMaterial({color:0xd8b08d, roughness:0.55, metalness:0.03});\n'
        '   const suit = new THREE.MeshStandardMaterial({color:0x2f6f9f, roughness:0.62, metalness:0.04});\n'
        '   const accent = new THREE.MeshStandardMaterial({color:0x1f2530, roughness:0.7});\n'
        '   const widths = {Spine:.14,Spine1:.18,Spine2:.20,Neck:.07,Head:.11,RightShoulder:.055,LeftShoulder:.055,RightArm:.055,LeftArm:.055,RightForeArm:.045,LeftForeArm:.045,RightHand:.038,LeftHand:.038,RightUpLeg:.075,LeftUpLeg:.075,RightLeg:.062,LeftLeg:.062,RightFoot:.045,LeftFoot:.045,RightToeBase:.028,LeftToeBase:.028,RightIndex1:.006,LeftIndex1:.006,RightPinky1:.005,LeftPinky1:.005,RightThumb1:.006,LeftThumb1:.006};\n'
        '   const skinBones = new Set(["Neck","Head","RightForeArm","LeftForeArm","RightHand","LeftHand"]);\n'
        '   function bodyMat(name){ return skinBones.has(name) ? skin : (name.includes("Foot") || name.includes("Toe") ? accent : suit); }\n'
        '   function addBodyVolume(boneName, geo, mat, pos, scale) {\n'
        '     const bone = bvh.skeleton.bones.find(b => b.name === boneName); if (!bone) return;\n'
        '     const mesh = new THREE.Mesh(geo, mat); mesh.position.set(pos[0], pos[1], pos[2]); mesh.scale.set(scale[0], scale[1], scale[2]);\n'
        '     mesh.castShadow = true; mesh.receiveShadow = true; bone.add(mesh); avatarMeshes.push(mesh);\n'
        '   }\n'
        '   function addCapsule(parent, child){\n'
        '     if (!child.isBone) return;\n'
        '     const v = child.position.clone(); const len = v.length();\n'
        '     if (len < 0.015 || child.name.endsWith("End")) return;\n'
        '     const radius = widths[child.name] || 0.045;\n'
        '     const radial = radius < 0.012 ? 5 : 8;\n'
        '     const rings = radius < 0.012 ? 6 : 14;\n'
        '     const geo = new THREE.CapsuleGeometry(radius, Math.max(0.004, len - radius * 2), radial, rings);\n'
        '     const mesh = new THREE.Mesh(geo, bodyMat(child.name)); mesh.castShadow = true; mesh.receiveShadow = true;\n'
        '     mesh.position.copy(v).multiplyScalar(0.5);\n'
        '     mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0), v.clone().normalize());\n'
        '     parent.add(mesh); avatarMeshes.push(mesh);\n'
        '   }\n'
        '   bvh.skeleton.bones.forEach(b => b.children.forEach(c => addCapsule(b, c)));\n'
        '   addBodyVolume("Hips", new THREE.SphereGeometry(0.18, 24, 14), suit, [0,0.02,0], [1.35,0.65,0.8]);\n'
        '   addBodyVolume("Spine2", new THREE.SphereGeometry(0.18, 24, 14), suit, [0,0.02,0], [1.2,1.05,0.75]);\n'
        '   addBodyVolume("RightFoot", new THREE.BoxGeometry(0.11,0.055,0.24), accent, [0,-0.025,0.08], [1,1,1]);\n'
        '   addBodyVolume("LeftFoot", new THREE.BoxGeometry(0.11,0.055,0.24), accent, [0,-0.025,0.08], [1,1,1]);\n'
        '   const headBone = bvh.skeleton.bones.find(b => b.name === "Head");\n'
        '   if (headBone) {\n'
        '     const headMesh = new THREE.Mesh(new THREE.SphereGeometry(0.12, 24, 18), skin);\n'
        '     headMesh.position.set(0, 0.06, 0.015); headBone.add(headMesh); avatarMeshes.push(headMesh);\n'
        '   }\n'
        '   jointMeshes.forEach(m => m.visible = false);\n'
        f'{face_js}'
        '   const mixer = new THREE.AnimationMixer(root);\n'
        '   const action = mixer.clipAction(bvh.clip); action.play();\n'
        '   const dur = bvh.clip.duration;\n'
        '   const totalF = Math.max(1, Math.round(dur * 30));\n'
        '   let paused = false, speed = 1;\n'
        '   const clock = new THREE.Clock();\n'
        
        # Hide the loading overlay when successful
        '   document.getElementById("ov").style.display = "none";\n'
        
        '   const btn = document.getElementById("bp");\n'
        '   const sc  = document.getElementById("sc");\n'
        '   const fi  = document.getElementById("fi");\n'
        '   const spEl= document.getElementById("sp");\n'
        '   const sl  = document.getElementById("sl");\n'
        '   const av  = document.getElementById("av");\n'
        '   sc.max = totalF;\n'
        '   let avatarVisible = true;\n'
        '   sh.visible = false;\n'
        '   av.addEventListener("click", () => {\n'
        '     avatarVisible = !avatarVisible;\n'
        '     avatarMeshes.forEach(m => m.visible = avatarVisible);\n'
        '     sh.visible = !avatarVisible;\n'
        '     jointMeshes.forEach(m => m.visible = !avatarVisible);\n'
        '     av.textContent = avatarVisible ? "Avatar" : "Skeleton";\n'
        '   });\n'
        '   btn.addEventListener("click", () => {\n'
        '     paused = !paused;\n'
        '     btn.innerHTML = paused ? "&#9654; Play" : "&#9646;&#9646; Pause";\n'
        '   });\n'
        '   sc.addEventListener("input", () => {\n'
        '     mixer.setTime((parseInt(sc.value) / totalF) * dur);\n'
        '     renderer.render(scene, cam);\n'
        '   });\n'
        '   spEl.addEventListener("input", () => {\n'
        '     speed = parseFloat(spEl.value);\n'
        '     sl.textContent = "Speed: " + speed.toFixed(1) + "x";\n'
        '     action.timeScale = speed;\n'
        '   });\n'
        '   (function animate() {\n'
        '     requestAnimationFrame(animate);\n'
        '     const d = clock.getDelta();\n'
        '     const vid = document.getElementById("vid");\n'
        '     if (vid && vid.style.display === "none") vid.style.display = "block";\n'
        '     if (!paused) {\n'
        '       mixer.update(d * speed);\n'
        '       const cf = Math.round((mixer.time % dur) / dur * totalF);\n'
        '       sc.value = cf;\n'
        '       fi.textContent = cf + " / " + totalF;\n'
        '       if (vid) {\n'
        '         vid.currentTime = mixer.time % dur;\n'
        '       }\n'
        '     }\n'
        '     ctl.update();\n'
        '     renderer.render(scene, cam);\n'
        '   })();\n'
        
        '} catch (err) {\n'
        # If Three.js parsing fails, show it in the UI
        '   document.querySelector(".sp").style.display = "none";\n'
        '   document.getElementById("loading-text").innerHTML = "<span style=\'color:#ff6060;\'><b>Error parsing 3D Data:</b><br>" + err.message + "</span>";\n'
        '}\n'
        
        '</script></body></html>'
    )
    return html

