"""
viewer_utils.py — Three.js-based 3D viewers for BVH skeleton and GLB models.

All Three.js files are served locally from Streamlit's static file server
(configured via .streamlit/config.toml: server.enableStaticServing = true).

Files in static/ are available at /app/static/<filename> — no CDN, no internet
required at runtime.

Public API:
    generate_skeleton_viewer_html(bvh_content, width, height) -> str
    generate_model_viewer_html(glb_b64, bvh_content, width, height) -> str
"""

import base64

# Local static paths — served by Streamlit at these URLs
_THREE = "/app/static/three.module.js"
_ORBIT = "/app/static/OrbitControls.js"
_BVH   = "/app/static/BVHLoader.js"
_GLTF  = "/app/static/GLTFLoader.js"
_ESM   = ""  # unused but kept for compat with _build_url_model_viewer import

GLB_SIZE_LIMIT_MB = 15


def _css_common():
    return (
        "*{margin:0;padding:0;box-sizing:border-box;}"
        "body{background:#0d0d14;font-family:'Segoe UI',sans-serif;overflow:hidden;}"
        ".sp{width:36px;height:36px;border:3px solid rgba(120,80,255,.2);"
        "border-top-color:#7850ff;border-radius:50%;animation:spin .8s linear infinite;}"
        "@keyframes spin{to{transform:rotate(360deg)}}"
    )


# ---------------------------------------------------------------------------
# Skeleton Viewer
# ---------------------------------------------------------------------------

def generate_skeleton_viewer_html(bvh_content: str, width: int = 900, height: int = 550) -> str:
    """
    Render a BVH skeleton using locally-served Three.js.
    No CDN required — files are served from static/ by Streamlit.
    """
    bvh_b64 = base64.b64encode(bvh_content.encode("utf-8")).decode("utf-8")
    HC = height - 54

    html = (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<title>Skeleton Viewer</title>'
        f'<style>{_css_common()}'
        f'#cw{{width:{width}px;height:{HC}px;position:relative;}}'
        f'#bar{{position:absolute;bottom:0;left:0;width:{width}px;height:54px;'
        'display:flex;align-items:center;gap:12px;padding:0 16px;'
        'background:rgba(13,13,20,.93);border-top:1px solid rgba(120,80,255,.3);}}'
        'button{background:rgba(120,80,255,.15);border:1px solid rgba(120,80,255,.5);'
        'color:#c8b8ff;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:13px;}'
        'button:hover{background:rgba(120,80,255,.35);}'
        '#sc{flex:1;accent-color:#7850ff;cursor:pointer;}'
        '#sl{color:#9080c0;font-size:12px;min-width:56px;}'
        '#sp{accent-color:#7850ff;width:70px;cursor:pointer;}'
        '#fi{color:#9080c0;font-size:12px;min-width:80px;text-align:right;}'
        '#ov{position:absolute;inset:0;display:flex;flex-direction:column;'
        'align-items:center;justify-content:center;background:#0d0d14;'
        'color:#8070c0;font-size:14px;gap:12px;}'
        '</style></head><body>'
        '<div id="cw">'
        '<div id="ov"><div class="sp"></div><span>Initialising renderer…</span></div>'
        '</div>'
        '<div id="bar">'
        '<button id="bp">&#9654; Play</button>'
        '<input id="sc" type="range" min="0" max="100" value="0" step="1">'
        '<span id="fi">0 / 0</span>'
        '<span id="sl">Speed: 1x</span>'
        '<input id="sp" type="range" min="0.1" max="3" value="1" step="0.1">'
        '</div>'
        f'<script type="module">\n'
        f'import * as THREE from "{_THREE}";\n'
        f'import {{ OrbitControls }} from "{_ORBIT}";\n'
        f'import {{ BVHLoader }} from "{_BVH}";\n'
        f'const W={width}, H={HC};\n'
        'const renderer = new THREE.WebGLRenderer({antialias:true});\n'
        'renderer.setPixelRatio(devicePixelRatio);\n'
        'renderer.setSize(W, H);\n'
        'document.getElementById("cw").prepend(renderer.domElement);\n'
        'const scene = new THREE.Scene();\n'
        'scene.background = new THREE.Color(0x0d0d14);\n'
        'scene.fog = new THREE.FogExp2(0x0d0d14, 0.04);\n'
        'const grid = new THREE.GridHelper(20, 20, 0x2a1a5e, 0x1a0e3c);\n'
        'grid.position.y = -1; scene.add(grid);\n'
        'scene.add(new THREE.AmbientLight(0x7050cc, 0.6));\n'
        'const dl = new THREE.DirectionalLight(0xffffff, 2);\n'
        'dl.position.set(5,10,5); scene.add(dl);\n'
        'const rl = new THREE.DirectionalLight(0x4040ff, 1.2);\n'
        'rl.position.set(-5,5,-5); scene.add(rl);\n'
        'const cam = new THREE.PerspectiveCamera(45, W/H, 0.01, 200);\n'
        'cam.position.set(0, 1.5, 4);\n'
        'const ctl = new OrbitControls(cam, renderer.domElement);\n'
        'ctl.target.set(0,1,0); ctl.enableDamping = true; ctl.dampingFactor = 0.08; ctl.update();\n'
        f'const bvhText = atob("{bvh_b64}");\n'
        'const bvh = new BVHLoader().parse(bvhText);\n'
        'const root = bvh.skeleton.bones[0];\n'
        'const hr = new THREE.Object3D(); hr.add(root); scene.add(hr);\n'
        'const sh = new THREE.SkeletonHelper(root);\n'
        'sh.material = new THREE.LineBasicMaterial({color:0x9060ff, linewidth:2}); scene.add(sh);\n'
        'const jm = new THREE.MeshStandardMaterial({color:0xcc99ff, emissive:0x6030cc, emissiveIntensity:0.5, roughness:0.3});\n'
        'function addSpheres(b) {\n'
        '  b.add(new THREE.Mesh(new THREE.SphereGeometry(0.025,8,8), jm));\n'
        '  b.children.forEach(c => { if (c.isBone) addSpheres(c); });\n'
        '}\n'
        'bvh.skeleton.bones.forEach(addSpheres);\n'
        'const mixer = new THREE.AnimationMixer(root);\n'
        'const action = mixer.clipAction(bvh.clip); action.play();\n'
        'const dur = bvh.clip.duration;\n'
        'const totalF = Math.max(1, Math.round(dur * 30));\n'
        'let paused = false, speed = 1;\n'
        'const clock = new THREE.Clock();\n'
        'document.getElementById("ov").style.display = "none";\n'
        'const btn = document.getElementById("bp");\n'
        'const sc  = document.getElementById("sc");\n'
        'const fi  = document.getElementById("fi");\n'
        'const spEl= document.getElementById("sp");\n'
        'const sl  = document.getElementById("sl");\n'
        'sc.max = totalF;\n'
        'btn.addEventListener("click", () => {\n'
        '  paused = !paused;\n'
        '  btn.innerHTML = paused ? "&#9654; Play" : "&#9646;&#9646; Pause";\n'
        '});\n'
        'sc.addEventListener("input", () => {\n'
        '  mixer.setTime((parseInt(sc.value) / totalF) * dur);\n'
        '  renderer.render(scene, cam);\n'
        '});\n'
        'spEl.addEventListener("input", () => {\n'
        '  speed = parseFloat(spEl.value);\n'
        '  sl.textContent = "Speed: " + speed.toFixed(1) + "x";\n'
        '  action.timeScale = speed;\n'
        '});\n'
        '(function animate() {\n'
        '  requestAnimationFrame(animate);\n'
        '  const d = clock.getDelta();\n'
        '  if (!paused) {\n'
        '    mixer.update(d * speed);\n'
        '    const cf = Math.round((mixer.time % dur) / dur * totalF);\n'
        '    sc.value = cf;\n'
        '    fi.textContent = cf + " / " + totalF;\n'
        '  }\n'
        '  ctl.update();\n'
        '  renderer.render(scene, cam);\n'
        '})();\n'
        '</script></body></html>'
    )
    return html


# ---------------------------------------------------------------------------
# GLB Model Viewer
# ---------------------------------------------------------------------------

def generate_model_viewer_html(
    glb_b64: str,
    bvh_content: str,
    width: int = 900,
    height: int = 550,
) -> str:
    """Render a GLB model with BVH animation retargeted onto bones."""
    bvh_b64 = base64.b64encode(bvh_content.encode("utf-8")).decode("utf-8")
    HC = height - 54

    html = (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<title>Model Viewer</title>'
        f'<style>{_css_common()}'
        '.sp{border-top-color:#5080ff !important;}'
        f'#cw{{width:{width}px;height:{HC}px;position:relative;}}'
        f'#bar{{position:absolute;bottom:0;left:0;width:{width}px;height:54px;'
        'display:flex;align-items:center;gap:12px;padding:0 16px;'
        'background:rgba(13,13,20,.93);border-top:1px solid rgba(80,120,255,.3);}}'
        'button{background:rgba(80,120,255,.15);border:1px solid rgba(80,120,255,.5);'
        'color:#b8c8ff;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:13px;}'
        'button:hover{background:rgba(80,120,255,.35);}'
        '#sc{flex:1;accent-color:#5080ff;cursor:pointer;}'
        '#sl{color:#8090c0;font-size:12px;min-width:56px;}'
        '#sp2{accent-color:#5080ff;width:70px;cursor:pointer;}'
        '#fi{color:#8090c0;font-size:12px;min-width:80px;text-align:right;}'
        '#warn{position:absolute;top:10px;right:10px;color:#ffcc88;'
        'background:rgba(80,50,0,.85);padding:4px 10px;border-radius:6px;font-size:12px;display:none;}'
        '#ov{position:absolute;inset:0;display:flex;flex-direction:column;'
        'align-items:center;justify-content:center;background:#0d0d14;'
        'color:#8090c0;font-size:14px;gap:12px;}'
        '</style></head><body>'
        '<div id="cw">'
        '<div id="ov"><div class="sp"></div><span>Loading model…</span></div>'
        '<div id="warn">&#9888; Some bones did not match</div>'
        '</div>'
        '<div id="bar">'
        '<button id="bp">&#9654; Play</button>'
        '<input id="sc" type="range" min="0" max="100" value="0" step="1">'
        '<span id="fi">0 / 0</span>'
        '<span id="sl">Speed: 1x</span>'
        '<input id="sp2" type="range" min="0.1" max="3" value="1" step="0.1">'
        '<button id="bb">Bones</button>'
        '</div>'
        f'<script type="module">\n'
        f'import * as THREE from "{_THREE}";\n'
        f'import {{ OrbitControls }} from "{_ORBIT}";\n'
        f'import {{ GLTFLoader }} from "{_GLTF}";\n'
        f'import {{ BVHLoader }} from "{_BVH}";\n'
        f'const W={width}, H={HC};\n'
        'const renderer = new THREE.WebGLRenderer({antialias:true});\n'
        'renderer.setPixelRatio(devicePixelRatio);\n'
        'renderer.setSize(W, H);\n'
        'renderer.shadowMap.enabled = true;\n'
        'document.getElementById("cw").prepend(renderer.domElement);\n'
        'const scene = new THREE.Scene();\n'
        'scene.background = new THREE.Color(0x0d0d14);\n'
        'scene.fog = new THREE.FogExp2(0x0d0d14, 0.035);\n'
        'scene.add(new THREE.GridHelper(20,20,0x1a1a4e,0x0e0e2e));\n'
        'scene.add(new THREE.AmbientLight(0xffffff, 0.7));\n'
        'const dl = new THREE.DirectionalLight(0xffffff, 2.5);\n'
        'dl.position.set(4,10,6); dl.castShadow = true; scene.add(dl);\n'
        'scene.add(Object.assign(new THREE.DirectionalLight(0x8080ff, 1.0), {position: new THREE.Vector3(-6,4,-4)}));\n'
        'const cam = new THREE.PerspectiveCamera(45, W/H, 0.01, 200);\n'
        'cam.position.set(0,1.5,4);\n'
        'const ctl = new OrbitControls(cam, renderer.domElement);\n'
        'ctl.target.set(0,1,0); ctl.enableDamping = true; ctl.dampingFactor = 0.08; ctl.update();\n'
        f'const glbBin = atob("{glb_b64}");\n'
        'const glbBuf = new Uint8Array(glbBin.length);\n'
        'for (let i=0; i<glbBin.length; i++) glbBuf[i] = glbBin.charCodeAt(i);\n'
        f'const bvhResult = new BVHLoader().parse(atob("{bvh_b64}"));\n'
        'const clip = bvhResult.clip;\n'
        'const dur = clip.duration;\n'
        'const totalF = Math.max(1, Math.round(dur * 30));\n'
        'let mixer, action, sklH, playing = false, speed = 1;\n'
        'const clock = new THREE.Clock();\n'
        'new GLTFLoader().parse(glbBuf.buffer, "", gltf => {\n'
        '  const model = gltf.scene; scene.add(model);\n'
        '  model.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });\n'
        '  const bm = {}; model.traverse(o => { bm[o.name] = o; });\n'
        '  let miss = 0;\n'
        '  const tracks = clip.tracks.filter(t => {\n'
        '    const m = t.name.match(/\\[(.+?)\\]/);\n'
        '    if (!m) return false;\n'
        '    const ok = !!bm[m[1]]; if (!ok) miss++; return ok;\n'
        '  });\n'
        '  if (miss) document.getElementById("warn").style.display = "block";\n'
        '  mixer = new THREE.AnimationMixer(model);\n'
        '  action = mixer.clipAction(new THREE.AnimationClip(clip.name, dur, tracks));\n'
        '  action.play();\n'
        '  sklH = new THREE.SkeletonHelper(model); sklH.visible = false; scene.add(sklH);\n'
        '  document.getElementById("ov").style.display = "none";\n'
        '  playing = true;\n'
        '}, err => {\n'
        '  document.getElementById("ov").innerHTML = \'<span style="color:#ff6060">Failed to load model</span>\';\n'
        '});\n'
        'const btn = document.getElementById("bp");\n'
        'const sc  = document.getElementById("sc");\n'
        'const fi  = document.getElementById("fi");\n'
        'const sp2 = document.getElementById("sp2");\n'
        'const sl  = document.getElementById("sl");\n'
        'const bb  = document.getElementById("bb");\n'
        'sc.max = totalF;\n'
        'btn.addEventListener("click", () => { playing = !playing; btn.innerHTML = playing ? "&#9646;&#9646; Pause" : "&#9654; Play"; });\n'
        'sc.addEventListener("input", () => { if (mixer) { mixer.setTime((parseInt(sc.value)/totalF)*dur); renderer.render(scene,cam); } });\n'
        'sp2.addEventListener("input", () => { speed = parseFloat(sp2.value); sl.textContent = "Speed: "+speed.toFixed(1)+"x"; if (action) action.timeScale = speed; });\n'
        'bb.addEventListener("click", () => { if (sklH) sklH.visible = !sklH.visible; });\n'
        '(function animate() {\n'
        '  requestAnimationFrame(animate);\n'
        '  const d = clock.getDelta();\n'
        '  if (mixer && playing) {\n'
        '    mixer.update(d * speed);\n'
        '    const cf = Math.round((mixer.time % dur) / dur * totalF);\n'
        '    sc.value = cf;\n'
        '    fi.textContent = cf + " / " + totalF;\n'
        '  }\n'
        '  ctl.update();\n'
        '  renderer.render(scene, cam);\n'
        '})();\n'
        '</script></body></html>'
    )
    return html
