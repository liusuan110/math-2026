/**
 * app.js —— Three.js 3D 可视化主程序
 *
 *  - 淡蓝色天空背景（渐变）
 *  - 真目标（圆柱体）+ 假目标（原点标记）
 *  - 导弹（红色锥体 + 轨迹 + 视角线）、无人机（四旋翼模型 + 航向箭头）
 *  - 干扰弹（下落小球 → 起爆闪光 → 烟幕云团，云团按物理参数下沉）
 *  - 相机模式：自由 / 俯视 / 导弹视角（放大观察遮蔽）
 *  - 与 SimUI 联动：时间轴、遮蔽看板、参数面板
 */

window.SimApp = (function () {
    'use strict';
    const P = window.SimPhysics;
    const S = window.SimState;

    let renderer, scene, camera, controls, labelRenderer;
    let container;
    let _state = null;
    let dynamicGroup = null;

    let missileObjs = {};
    let droneObjs = {};
    let bombList = [];          // {key, bombMesh, cloudMesh, cloudWire, groundLine, burstRing, phase}
    let flashList = [];         // 命中假目标爆炸闪光
    let sightCones = [];        // 各导弹的视线采样锥（直接挂在 scene 下）
    let samplingDotsBuilt = false; // 目标采样点只构建一次
    let activeCloudObjs = [];   // 当前处于烟幕阶段的云团（供烟幕视角跟随）

    const TMP = new THREE.Vector3();
    // 世界坐标下的真目标中心：问题坐标 (0,200,5) → (x, z, -y)
    const CYL_CENTER = new THREE.Vector3(0, 5, -200);
    const UP = new THREE.Vector3(0, 1, 0);

    /**
     * 坐标映射：问题坐标系 (x, y, z) —— z 为高度（题目约定）
     *            → Three.js 世界坐标系 (x, z, -y) —— y 为高度
     * 这是保向旋转（det=+1），不会产生镜像；方向向量同样适用。
     */
    function toWorld(p) { return [p[0], p[2], -p[1]]; }

    // ================= 场景搭建 =================
    function createScene() {
        scene = new THREE.Scene();

        // 淡蓝天空渐变背景
        const bgCanvas = document.createElement('canvas');
        bgCanvas.width = 4; bgCanvas.height = 256;
        const ctx = bgCanvas.getContext('2d');
        const grad = ctx.createLinearGradient(0, 0, 0, 256);
        grad.addColorStop(0, '#5aa9e8');   // 天顶深蓝
        grad.addColorStop(0.55, '#a9d7f7');
        grad.addColorStop(1, '#eef9ff');   // 地平线浅色
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, 4, 256);
        const bgTex = new THREE.CanvasTexture(bgCanvas);
        scene.background = bgTex;

        camera = new THREE.PerspectiveCamera(60, 1, 1, 200000);
        camera.position.set(24000, 15000, 17500);
        camera.lookAt(8000, 1000, 0);

        controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.08;
        controls.minDistance = 20;
        controls.maxDistance = 90000;
        controls.target.set(8000, 1000, 0);

        // 灯光
        scene.add(new THREE.HemisphereLight(0xbfdfff, 0x9aa8b8, 1.0));
        const dirLight = new THREE.DirectionalLight(0xffffff, 0.9);
        dirLight.position.set(8000, 15000, 6000);
        scene.add(dirLight);

        // 地面 + 网格
        const ground = new THREE.Mesh(
            new THREE.PlaneGeometry(60000, 60000),
            new THREE.MeshLambertMaterial({ color: 0xdff1fa, transparent: true, opacity: 0.55 })
        );
        ground.rotation.x = -Math.PI / 2;
        ground.position.y = 0;
        scene.add(ground);

        const grid = new THREE.GridHelper(30000, 60, 0x8fbcdd, 0xcfe6f5);
        grid.position.y = 0.5;
        grid.material.transparent = true;
        grid.material.opacity = 0.5;
        scene.add(grid);

        // 静态目标
        buildTargets();

        dynamicGroup = new THREE.Group();
        scene.add(dynamicGroup);
    }

    function buildTargets() {
        // 真目标：问题坐标 (0,200,0)~z=10 → 世界坐标 (x, z, -y) = (0, 0~10, -200)
        const cylGeo = new THREE.CylinderGeometry(7, 7, 10, 40);
        const cylMat = new THREE.MeshLambertMaterial({ color: 0xc2ccd6, emissive: 0x334455, emissiveIntensity: 0.35 });
        const cyl = new THREE.Mesh(cylGeo, cylMat);
        cyl.position.set(0, 5, -200);
        scene.add(cyl);
        // 顶部红圈
        const ringGeo = new THREE.TorusGeometry(7.2, 0.6, 8, 40);
        const ringMat = new THREE.MeshLambertMaterial({ color: 0xe64545 });
        const ring = new THREE.Mesh(ringGeo, ringMat);
        ring.rotation.x = Math.PI / 2;
        ring.position.set(0, 10.1, -200);
        scene.add(ring);

        // 放大定位柱（沿世界 Y = 高度，问题坐标 (0,200,0~320)）
        const beaconGeo = new THREE.CylinderGeometry(26, 26, 320, 24, 1, true);
        const beacon = new THREE.Mesh(
            beaconGeo,
            new THREE.MeshBasicMaterial({ color: 0x7fc4f0, transparent: true, opacity: 0.12, side: THREE.DoubleSide, depthWrite: false })
        );
        beacon.position.set(0, 160, -200);
        scene.add(beacon);
        const beaconWire = new THREE.Mesh(
            new THREE.CylinderGeometry(26, 26, 320, 16, 1, true),
            new THREE.MeshBasicMaterial({ color: 0xaedcf7, wireframe: true, transparent: true, opacity: 0.18, depthWrite: false })
        );
        beaconWire.position.copy(beacon.position);
        scene.add(beaconWire);

        // 假目标：问题原点 (0,0,0) → 世界原点
        const fake = new THREE.Mesh(
            new THREE.CylinderGeometry(4, 4, 6, 24),
            new THREE.MeshLambertMaterial({ color: 0xdc3545 })
        );
        fake.position.set(0, 3, 0);
        scene.add(fake);
        const fakeRing = new THREE.Mesh(
            new THREE.RingGeometry(6, 14, 48),
            new THREE.MeshBasicMaterial({ color: 0xdc3545, transparent: true, opacity: 0.45, side: THREE.DoubleSide })
        );
        fakeRing.rotation.x = -Math.PI / 2;
        fakeRing.position.set(0, 0.6, 0);
        scene.add(fakeRing);
        addLabel('假目标(原点)', [0, 10, 0], 'label label-fake');
    }

    /** 目标上/下表面的采样点标记（物理半径 r=7，顶/底 z 与中心点）——需 _state 就绪后调用 */
    function buildSamplingDots() {
        const n = _state.params.sampleNum || 32;
        const cx = 0, cy = 200, cz = 0, R = 7, H = 10;
        const pts = [];
        const push = (p) => pts.push(...toWorld(p));
        push([cx, cy, cz]); push([cx, cy, cz + H]); push([cx, cy, cz + H / 2]);
        for (const z of [cz, cz + H]) {
            for (let k = 0; k < n; k++) {
                const th = 2 * Math.PI * k / n;
                push([cx + R * Math.cos(th), cy + R * Math.sin(th), z]);
            }
        }
        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
        const mat = new THREE.PointsMaterial({ color: 0xffd166, size: 34, sizeAttenuation: true, transparent: true, opacity: 0.95 });
        const dots = new THREE.Points(geo, mat);
        scene.add(dots);
        addLabel('真目标(r7m h10m)', toWorld([0, 200, 335]), 'label label-target');
    }

    function addLabel(text, pos, cls) {
        const div = document.createElement('div');
        div.className = cls || 'label';
        div.textContent = text;
        const obj = new THREE.CSS2DObject(div);
        obj.position.set(pos[0], pos[1], pos[2]);
        scene.add(obj);
        return obj;
    }

    // ================= 动态对象构建 =================
    function disposeObj(obj) {
        obj.traverse((o) => {
            // 嵌套的 CSS2D 标签在父级组被 remove 时不会自动收到 removed 事件，
            // 这里直接摘除其 DOM 元素，避免旧标签残留在屏幕上。
            if (o.isCSS2DObject && o.element && o.element.parentNode) {
                o.element.parentNode.removeChild(o.element);
            }
            if (o.geometry) o.geometry.dispose();
            if (o.material) {
                (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => m.dispose());
            }
        });
    }

    function clearDynamic() {
        // 必须用 remove()（而非 children.pop()）以触发 CSS2DObject 的 removed 事件，
        // 否则旧的 3D 标签 DOM 不会从屏幕上清除。
        while (dynamicGroup.children.length) {
            const c = dynamicGroup.children[0];
            dynamicGroup.remove(c);
            disposeObj(c);
        }
        // 视线采样锥挂在 scene 下，单独清理
        for (const sc of sightCones) {
            scene.remove(sc);
            sc.geometry.dispose();
            sc.material.dispose();
        }
        sightCones = [];
        missileObjs = {};
        droneObjs = {};
        bombList = [];
        flashList = [];
    }

    function buildMissile(m) {
        // 整体方向约定：Group 的 +Y 为导弹头部（速度方向），
        // 之后每帧把 +Y 旋转到速度方向即可让整个模型（头锥/弹体/尾焰）保持正确朝向。
        // 尺寸：总长约 16m（≤ 烟幕球直径 20m，不喧宾夺主），尾焰仅作推进指示。
        const grp = new THREE.Group();

        // 头锥（红色，锥尖朝前 = +Y）
        const noseMat = new THREE.MeshLambertMaterial({ color: 0xff3b30, emissive: 0x661100, emissiveIntensity: 0.4 });
        const nose = new THREE.Mesh(new THREE.ConeGeometry(3, 8, 16), noseMat);
        nose.position.y = 4;            // 头部区间 0~8
        grp.add(nose);

        // 弹体（银灰色圆柱，视觉上衔接头锥与尾部）
        const bodyMat = new THREE.MeshLambertMaterial({ color: 0xd8dee4, emissive: 0x222222, emissiveIntensity: 0.15 });
        const body = new THREE.Mesh(new THREE.CylinderGeometry(2.8, 3.2, 9, 16), bodyMat);
        body.position.y = -2.5;         // 0~-9 段
        grp.add(body);

        // 尾喷口（深色）
        const tailMat = new THREE.MeshLambertMaterial({ color: 0x555a5f });
        const tail = new THREE.Mesh(new THREE.CylinderGeometry(2.2, 2.6, 2, 12), tailMat);
        tail.position.y = -10;
        grp.add(tail);

        // 尾焰（橙色半透明，贴向尾部后方，不超出烟幕尺度）
        const flameMat = new THREE.MeshBasicMaterial({ color: 0xff9f43, transparent: true, opacity: 0.4 });
        const flame = new THREE.Mesh(new THREE.ConeGeometry(1.8, 5, 10), flameMat);
        flame.position.y = -12.5;       // 锥尖默认朝 +Y，尾焰应朝 -Y 方向扩散
        flame.rotation.x = Math.PI;     // 翻转使锥尖指向 -Y（尾焰向后拉长）
        grp.add(flame);

        // 尾焰内核光晕（橙色光球）
        const glow = new THREE.Mesh(
            new THREE.SphereGeometry(3.5, 12, 12),
            new THREE.MeshBasicMaterial({ color: 0xffb14d, transparent: true, opacity: 0.55 })
        );
        glow.position.y = -10.8;
        grp.add(glow);

        grp.userData.nose = nose;

        // 视线采样锥：导弹 → 目标上/下表面采样点的连线（世界坐标，逐帧更新）
        const n = _state.params.sampleNum || 32;
        const sightGeo = new THREE.BufferGeometry();
        const sightArr = new Float32Array(n * 2 * 6); // 2 圈 × n 段 × 2 顶点 × 3 分量
        sightGeo.setAttribute('position', new THREE.BufferAttribute(sightArr, 3));
        const sightMat = new THREE.LineBasicMaterial({ color: 0x7fce8c, transparent: true, opacity: 0.55 });
        const sightCone = new THREE.LineSegments(sightGeo, sightMat);
        sightCone.frustumCulled = false;
        sightCone.visible = true;
        scene.add(sightCone);
        sightCones.push(sightCone);
        grp.userData.sightGeo = sightGeo;
        grp.userData.sightArr = sightArr;
        grp.userData.sightCone = sightCone;
        grp.userData.sightMat = sightMat;

        // 完整轨迹（淡）
        const { dir, tHit } = P.missileDirAndHit(m.pos, m.speed);
        const pts = [];
        for (let i = 0; i <= 120; i++) {
            const t = tHit * i / 120;
            const p = P.missilePosAt(m.pos, dir, m.speed, t);
            const w = toWorld(p);
            pts.push(new THREE.Vector3(w[0], w[1], w[2]));
        }
        const trail = new THREE.Line(
            new THREE.BufferGeometry().setFromPoints(pts),
            new THREE.LineBasicMaterial({ color: 0xff6b5e, transparent: true, opacity: 0.28 })
        );
        grp.add(trail);

        // 近期路径（亮，实时更新）
        const seg = new THREE.Line(
            new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]),
            new THREE.LineBasicMaterial({ color: 0xff8f3d, transparent: true, opacity: 0.85 })
        );
        seg.frustumCulled = false;
        grp.add(seg);

        const label = addLabelToGrp(m.name + ' · ' + m.pos.join(','), grp, [0, 260, 0], 'label label-missile');
        grp.userData.dir = dir;
        grp.userData.tHit = tHit;
        grp.userData.seg = seg;
        grp.userData.labelEl = label.element;
        dynamicGroup.add(grp);
        missileObjs[m.name] = grp;
    }

    function addLabelToGrp(text, grp, offset, cls) {
        const div = document.createElement('div');
        div.className = cls || 'label';
        div.textContent = text;
        const obj = new THREE.CSS2DObject(div);
        obj.position.set(offset[0], offset[1], offset[2]);
        grp.add(obj);
        return obj;
    }

    function buildDrone(d) {
        const grp = new THREE.Group();
        const color = new THREE.Color(d.color);
        // 机体
        const body = new THREE.Mesh(
            new THREE.BoxGeometry(12, 4, 12),
            new THREE.MeshLambertMaterial({ color: color })
        );
        grp.add(body);
        // 四旋翼
        const rotorMat = new THREE.MeshBasicMaterial({ color: 0x444444, transparent: true, opacity: 0.7 });
        const rotorGroup = new THREE.Group();
        const armOff = 12;
        for (const [ax, ay] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) {
            const arm = new THREE.Mesh(
                new THREE.CylinderGeometry(0.8, 0.8, armOff * 1.4, 6),
                new THREE.MeshLambertMaterial({ color: 0x666666 })
            );
            arm.rotation.z = Math.PI / 2;
            arm.position.set(ax * armOff * 0.7, 0, ay * armOff * 0.7);
            arm.rotation.z = Math.atan2(ay, ax) - Math.PI / 2;
            grp.add(arm);
            const rotor = new THREE.Mesh(new THREE.CylinderGeometry(6, 6, 0.4, 20), rotorMat);
            rotor.position.set(ax * armOff, 2.2, ay * armOff);
            rotorGroup.add(rotor);
        }
        grp.add(rotorGroup);
        grp.userData.rotorGroup = rotorGroup;

        // 航向箭头（实时方向）
        const arrowMat = new THREE.LineBasicMaterial({ color: color });
        const arrow = new THREE.Line(
            new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]),
            arrowMat
        );
        arrow.frustumCulled = false;
        grp.add(arrow);

        // 到地面的垂线
        const dropLine = new THREE.Line(
            new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]),
            new THREE.LineBasicMaterial({ color: color, transparent: true, opacity: 0.25 })
        );
        dropLine.frustumCulled = false;
        grp.add(dropLine);

        // 飞行路径（虚线）
        const end = Math.max(...d.bombs.filter(b => b.enabled).map(b => b.tDrop), 1) + 5;
        const dir2 = P.headingDir(d.theta);
        const p0 = toWorld(d.pos);
        const p1 = toWorld([d.pos[0] + dir2[0] * d.speed * end, d.pos[1] + dir2[1] * d.speed * end, d.pos[2]]);
        const pathPts = [new THREE.Vector3(p0[0], p0[1], p0[2]), new THREE.Vector3(p1[0], p1[1], p1[2])];
        const path = new THREE.Line(
            new THREE.BufferGeometry().setFromPoints(pathPts),
            new THREE.LineDashedMaterial({ color: color, dashSize: 400, gapSize: 300, transparent: true, opacity: 0.5 })
        );
        path.computeLineDistances();
        grp.add(path);

        const label = addLabelToGrp(d.name, grp, [0, 28, 0], 'label label-drone');
        grp.userData.labelEl = label.element;
        grp.userData.dir2 = dir2;
        grp.userData.arrow = arrow;
        grp.userData.dropLine = dropLine;

        dynamicGroup.add(grp);
        droneObjs[d.name] = grp;
    }

    function buildBomb(d, bi) {
        const bomb = d.bombs[bi];
        const key = d.name + '-' + bi;
        const color = new THREE.Color(d.color);

        // 下落中的干扰弹
        const bombMesh = new THREE.Mesh(
            new THREE.SphereGeometry(2.2, 12, 12),
            new THREE.MeshLambertMaterial({ color: 0x333333 })
        );
        bombMesh.visible = false;
        dynamicGroup.add(bombMesh);

        // 烟幕云团：真实比例（半径 = 物理半径，不缩放；完整球体，透明度提高便于观察）
        const R = _state.params.smokeRadius;
        const cloudMat = new THREE.MeshLambertMaterial({
            color: 0xd8e6f2, transparent: true, opacity: 0.55, depthWrite: false, side: THREE.DoubleSide,
        });
        const cloudMesh = new THREE.Mesh(new THREE.SphereGeometry(R, 32, 32), cloudMat);
        cloudMesh.visible = false;
        dynamicGroup.add(cloudMesh);

        // 云团线框（完整球体轮廓）
        const wireMat = new THREE.MeshBasicMaterial({
            color: color, wireframe: true, transparent: true, opacity: 0.3, depthWrite: false,
        });
        const cloudWire = new THREE.Mesh(new THREE.SphereGeometry(R, 20, 20), wireMat);
        cloudWire.visible = false;
        dynamicGroup.add(cloudWire);

        // 起爆闪光环
        const ring = new THREE.Mesh(
            new THREE.TorusGeometry(10, 1.2, 8, 40),
            new THREE.MeshBasicMaterial({ color: 0xffd166, transparent: true, opacity: 0.9 })
        );
        ring.rotation.x = Math.PI / 2;
        ring.visible = false;
        dynamicGroup.add(ring);

        // 云团到地面投影线
        const glMat = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.2 });
        const groundLine = new THREE.Line(
            new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]),
            glMat
        );
        groundLine.frustumCulled = false;
        groundLine.visible = false;
        dynamicGroup.add(groundLine);

        const entry = {
            key: key,
            droneName: d.name,
            bombIndex: bi,
            color: color,
            tDrop: bomb.tDrop,
            delay: bomb.delay,
            tBurst: bomb.tDrop + bomb.delay,
            dir2: P.headingDir(d.theta),
            v: d.speed,
            release: P.releasePoint(d.pos, P.headingDir(d.theta), d.speed, bomb.tDrop),
            burst: P.burstPoint(d.pos, P.headingDir(d.theta), d.speed, bomb.tDrop, bomb.delay, _state.params.g),
            bombMesh: bombMesh,
            cloudMesh: cloudMesh,
            cloudWire: cloudWire,
            ring: ring,
            groundLine: groundLine,
        };
        bombList.push(entry);
    }

    function rebuildDynamic() {
        clearDynamic();
        // 目标采样点标记（静态，只构建一次；需 _state 就绪）
        if (!samplingDotsBuilt) {
            buildSamplingDots();
            samplingDotsBuilt = true;
        }
        for (const m of _state.missiles) {
            if (m.enabled) buildMissile(m);
        }
        for (const d of _state.drones) {
            if (!d.enabled) continue;
            buildDrone(d);
            d.bombs.forEach((b, bi) => { if (b.enabled) buildBomb(d, bi); });
        }
    }

    /**
     * 更新某导弹的视线采样锥：导弹 → 目标上/下表面采样点（各 n 条连线）
     * 与 Q1 严格遮蔽判定的采样点完全一致（上/下两圈边缘点）。
     */
    function updateSightCone(g, mp) {
        const sc = g.userData.sightCone;
        if (!sc) return;
        const cyl = _state.cyl;
        const n = _state.params.sampleNum || 32;
        const arr = g.userData.sightArr;
        const cx = cyl.center[0], cy = cyl.center[1], cz = cyl.center[2];
        const R = cyl.radius, H = cyl.height;
        const wm = toWorld(mp);
        let idx = 0;
        for (const z of [cz, cz + H]) {
            for (let k = 0; k < n; k++) {
                const th = 2 * Math.PI * k / n;
                const tgt = toWorld([cx + R * Math.cos(th), cy + R * Math.sin(th), z]);
                arr[idx++] = wm[0]; arr[idx++] = wm[1]; arr[idx++] = wm[2];
                arr[idx++] = tgt[0]; arr[idx++] = tgt[1]; arr[idx++] = tgt[2];
            }
        }
        g.userData.sightGeo.attributes.position.needsUpdate = true;
    }

    // ================= 帧更新 =================
    function updateLine2(line, a, b) {
        const pos = line.geometry.attributes.position;
        pos.setXYZ(0, a[0], a[1], a[2]);
        pos.setXYZ(1, b[0], b[1], b[2]);
        pos.needsUpdate = true;
    }

    function updateObjects(dt) {
        const t = _state.t;
        const params = _state.params;

        // ---- 导弹 ----
        for (const name in missileObjs) {
            const m = _state.missiles.find(x => x.name === name);
            if (!m || !m.enabled) { missileObjs[name].visible = false; if (missileObjs[name].userData.sightCone) missileObjs[name].userData.sightCone.visible = false; continue; }
            const g = missileObjs[name];
            const { dir, tHit } = g.userData;
            if (t >= tHit) {
                // 命中假目标：停留在原点 + 闪光
                g.position.set(0, 0, 0);
                g.visible = false;
                if (g.userData.sightCone) g.userData.sightCone.visible = false;
                if (flashList.every(f => f.name !== name)) {
                    flashList.push({ name: name, tStart: tHit });
                }
                continue;
            }
            g.visible = true;
            const p = P.missilePosAt(m.pos, dir, m.speed, t);
            const w = toWorld(p);
            g.position.set(w[0], w[1], w[2]);
            // 整个模型（头锥+弹体+尾焰）+Y 指向速度方向（世界坐标：dir 映射为 (dx, dz, -dy)）
            TMP.set(dir[0], dir[2], -dir[1]);
            g.quaternion.setFromUnitVectors(UP, TMP.clone().normalize());
            // 视线采样锥（导弹→目标上/下表面采样点连线）
            updateSightCone(g, p);
            if (g.userData.sightCone) g.userData.sightCone.visible = true;
            // 近期路径
            const t0 = Math.max(0, t - 5);
            const pa = toWorld(P.missilePosAt(m.pos, dir, m.speed, t0));
            updateLine2(g.userData.seg, pa, w);
            // 标签：状态文字“可见/遮蔽中”用蓝色（对应真目标颜色），其余保持原样
            const dist = P.dist(p, [0, 200, 0]);
            const cov = (_state.coverage || {})[m.name];
            const blocked = cov ? P.isBlockedAt(cov, t) : false;
            g.userData.labelEl.innerHTML = m.name + '  <span class="label-status">' + (blocked ? '🛡遮蔽中' : '可见') + '</span>  ' + Math.round(dist) + 'm';
            // 遮蔽时头锥变亮、视线锥变红
            g.userData.nose.material.emissive.setHex(blocked ? 0xff2200 : 0x661100);
            g.userData.nose.material.emissiveIntensity = blocked ? 0.8 : 0.4;
            if (g.userData.sightMat) {
                g.userData.sightMat.color.setHex(blocked ? 0xff3b30 : 0x7fce8c);
                g.userData.sightMat.opacity = blocked ? 0.95 : 0.55;
            }
        }

        // ---- 爆炸闪光（复用每个闪光的环） ----
        for (let i = flashList.length - 1; i >= 0; i--) {
            const f = flashList[i];
            const age = t - f.tStart;
            if (!f.ring) {
                f.ring = new THREE.Mesh(
                    new THREE.RingGeometry(10, 50, 40),
                    new THREE.MeshBasicMaterial({ color: 0xff7043, transparent: true, side: THREE.DoubleSide })
                );
                f.ring.rotation.x = -Math.PI / 2;
                f.ring.position.set(0, 0, 1.2);
                scene.add(f.ring);
            }
            const r = Math.max(1, age * 220);
            f.ring.scale.setScalar(r / 30);
            f.ring.material.opacity = Math.max(0, 1 - age / 6);
            if (age > 6) {
                scene.remove(f.ring);
                f.ring.material.dispose();
                f.ring.geometry.dispose();
                flashList.splice(i, 1);
            }
        }

        // ---- 无人机 ----
        for (const name in droneObjs) {
            const d = _state.drones.find(x => x.name === name);
            if (!d || !d.enabled) { droneObjs[name].visible = false; continue; }
            const g = droneObjs[name];
            const { dir2 } = g.userData;
            const p = P.dronePosAt(d.pos, dir2, d.speed, t);
            const w = toWorld(p);
            g.position.set(w[0], w[1], w[2]);
            g.userData.rotorGroup.children.forEach(r => { r.rotation.y += dt * 30; });
            // 航向箭头（dir2 在问题 xy 平面 → 世界 xz 平面）
            const a2 = P.add(p, P.mul(dir2, d.speed * 3));
            const wa2 = toWorld(a2);
            updateLine2(g.userData.arrow, w, wa2);
            updateLine2(g.userData.dropLine, w, [w[0], 0, w[2]]);
            g.userData.labelEl.textContent = d.name + '  ' + Math.round(d.speed) + 'm/s';
        }

        // ---- 干扰弹 / 烟幕 ----
        const activeClouds = [];
        for (const b of bombList) {
            const rel = t - b.tDrop;
            const life = t - b.tBurst;
            if (t < b.tDrop) {
                setBombVisible(b, 'idle');
            } else if (life < 0) {
                // 下落中
                setBombVisible(b, 'fall');
                const p = toWorld(P.bombPosDuringFall(b.release, b.dir2, b.v, rel, params.g));
                b.bombMesh.position.set(p[0], p[1], p[2]);
            } else if (life <= params.activeDuration) {
                // 烟幕云团：真实比例完整球体（不缩放）
                setBombVisible(b, 'cloud');
                const c = toWorld(P.cloudCenterAt(b.burst, b.tBurst, t, params.descentRate));
                b.cloudMesh.position.set(c[0], c[1], c[2]);
                b.cloudWire.position.set(c[0], c[1], c[2]);
                // 渐隐
                const remain = params.activeDuration - life;
                let op = 0.55;
                if (remain < 1.5) op = 0.55 * (remain / 1.5);
                b.cloudMesh.material.opacity = op;
                b.cloudWire.material.opacity = 0.3 * (remain / 1.5);
                // 起爆闪光环
                if (life < 2) {
                    b.ring.visible = true;
                    const r = 10 + life * 60;
                    b.ring.scale.setScalar(r / 10);
                    b.ring.material.opacity = 0.9 * (1 - life / 2);
                    b.ring.position.set(c[0], c[1], c[2]);
                } else {
                    b.ring.visible = false;
                }
                // 地面投影（世界坐标 y=0 即地面）
                b.groundLine.visible = true;
                updateLine2(b.groundLine, c, [c[0], 0, c[2]]);
                activeClouds.push(b);
            } else {
                setBombVisible(b, 'idle');
            }
        }

        // ---- 云团遮蔽高亮 ----
        for (const b of activeClouds) {
            let boosting = false;
            for (const m of _state.missiles) {
                if (!m.enabled) continue;
                const cov = (_state.coverage || {})[m.name];
                if (!cov) continue;
                for (const part of cov.parts) {
                    if (part.drone !== b.droneName || part.bombIndex !== b.bombIndex) continue;
                    if (part.intervals.some(iv => t >= iv[0] - 1e-9 && t <= iv[1] + 1e-9)) { boosting = true; break; }
                }
                if (boosting) break;
            }
            b.cloudMesh.material.opacity = boosting ? Math.max(b.cloudMesh.material.opacity, 0.55) : b.cloudMesh.material.opacity;
            b.cloudWire.material.opacity = boosting ? 0.45 : b.cloudWire.material.opacity;
        }

        // 记录当前活跃云团（供烟幕视角跟随）
        activeCloudObjs = activeClouds;
    }

    function setBombVisible(b, phase) {
        b.bombMesh.visible = phase === 'fall';
        b.cloudMesh.visible = phase === 'cloud';
        b.cloudWire.visible = phase === 'cloud';
        b.groundLine.visible = phase === 'cloud';
        if (phase !== 'cloud') b.ring.visible = false;
    }

    // ================= 相机模式 =================
    function setCameraMode(mode, idx) {
        _state.cameraMode = mode;
        if (mode === 'free') {
            controls.enabled = true;
            camera.fov = 60;
            camera.updateProjectionMatrix();
        } else if (mode === 'drone') {
            // 无人机视角：启用轨道控制，旋转中心锁定所选无人机位置（随其飞行平移），可自由转动/缩放
            controls.enabled = true;
            camera.fov = 35;
            camera.updateProjectionMatrix();
        } else if (mode === 'missile') {
            // 导弹视角：启用轨道控制，旋转中心锁定导弹位置（随导弹移动），可自由转动/缩放
            controls.enabled = true;
            camera.fov = 25;   // 放大观察
            camera.updateProjectionMatrix();
        } else if (mode === 'smoke') {
            // 烟幕视角：启用轨道控制，旋转中心锁定云团中心，可自由转动/缩放
            controls.enabled = true;
            camera.fov = 35;
            camera.updateProjectionMatrix();
            if (activeCloudObjs.length) {
                const idx = (_state.smokeViewIndex % activeCloudObjs.length + activeCloudObjs.length) % activeCloudObjs.length;
                const b = activeCloudObjs[idx];
                const c = b.cloudMesh.position;
                // 首次进入：把相机放到云团附近
                if (!_state.smokeCamInitialized) {
                    camera.position.set(c.x + 160, c.y + 120, c.z + 160);
                    controls.target.set(c.x, c.y, c.z);
                    _state.smokeCamInitialized = true;
                }
            }
            controls.update();
        }
    }

    /** 当前跟随无人机的世界位置与航向（世界 xz 平面方向） */
    function droneWorldState() {
        const d = _state.drones[_state.droneViewIndex];
        if (!d || !d.enabled) return null;
        const dir2 = P.headingDir(d.theta);
        const p = P.dronePosAt(d.pos, dir2, d.speed, _state.t);
        const w = toWorld(p);
        return { w: w, dirW: [dir2[0], 0, -dir2[1]] };
    }

    /**
     * 无人机视角：旋转中心（controls.target）锁定所选无人机位置并随其飞行平移，
     * 相机与 target 同步平移保持相对视角（用户可自由转动/缩放，转动中心始终是无人机）。
     */
    function updateDroneCamera() {
        const ds = droneWorldState();
        if (!ds) {
            // 无启用无人机：回退自由视角
            if (_state.cameraMode === 'drone') {
                _state.cameraMode = 'free';
                controls.enabled = true;
                camera.fov = 60;
                camera.updateProjectionMatrix();
                if (window.SimUI && window.SimUI.setCam) window.SimUI.setCam('free');
            }
            return;
        }
        const { w, dirW } = ds;
        if (!_state.droneCamInitialized) {
            // 首次进入 / 切换无人机：把相机放到无人机后方偏上
            camera.position.set(
                w[0] - dirW[0] * 90 + 25,
                w[1] + 55,
                w[2] - dirW[2] * 90 + 25
            );
            _state.droneCamInitialized = true;
            _state.droneLastTarget = w.slice();
        } else if (_state.droneLastTarget) {
            // 跟随平移：相机与旋转中心同步移动无人机的位移，保持用户视角相对位置
            const last = _state.droneLastTarget;
            camera.position.x += w[0] - last[0];
            camera.position.y += w[1] - last[1];
            camera.position.z += w[2] - last[2];
            _state.droneLastTarget = w.slice();
        }
        controls.target.set(w[0], w[1], w[2]);
        controls.update();
    }

    /** 当前跟随导弹的世界位置与速度方向 */
    function missileWorldState() {
        const mi = _state.missiles[_state.missileViewIndex];
        if (!mi || !mi.enabled) return null;
        const g = missileObjs[mi.name];
        const { dir, tHit } = g ? g.userData : P.missileDirAndHit(mi.pos, mi.speed);
        const tp = Math.min(_state.t, tHit);
        const mp = P.missilePosAt(mi.pos, dir, mi.speed, tp);
        return { w: toWorld(mp), dirW: [dir[0], dir[2], -dir[1]] };
    }

    /**
     * 导弹视角：旋转中心（controls.target）锁定当前导弹位置并随导弹平移，
     * 相机与 target 同步平移保持相对视角（用户可自由转动/缩放，转动中心始终是导弹）。
     */
    function updateMissileCamera() {
        const ms = missileWorldState();
        if (!ms) return;
        const { w, dirW } = ms;
        if (!_state.missileCamInitialized) {
            // 首次进入 / 切换导弹：把相机放到导弹后方偏上
            camera.position.set(
                w[0] - dirW[0] * 60 + 15,
                w[1] - dirW[1] * 60 + 25,
                w[2] - dirW[2] * 60 + 15
            );
            _state.missileCamInitialized = true;
            _state.missileLastTarget = w.slice();
        } else if (_state.missileLastTarget) {
            // 跟随平移：相机与旋转中心同步移动导弹的位移，保持用户视角相对位置
            const last = _state.missileLastTarget;
            camera.position.x += w[0] - last[0];
            camera.position.y += w[1] - last[1];
            camera.position.z += w[2] - last[2];
            _state.missileLastTarget = w.slice();
        }
        controls.target.set(w[0], w[1], w[2]);
        controls.update();
    }

    /**
     * 烟幕视角：旋转中心（controls.target）锁定所选烟幕云团中心（云团匀速下沉，
     * 每帧同步更新 target），用户可自由旋转 / 缩放 / 平移观察。
     */
    function updateSmokeCamera() {
        if (!activeCloudObjs.length) {
            // 没有活跃云团（未起爆 / 已消散）：自动回到自由视角
            if (_state.cameraMode === 'smoke') {
                _state.cameraMode = 'free';
                controls.enabled = true;
                camera.fov = 60;
                camera.updateProjectionMatrix();
                if (window.SimUI && window.SimUI.setCam) window.SimUI.setCam('free');
            }
            return;
        }
        const idx = _state.smokeViewIndex % activeCloudObjs.length;
        const b = activeCloudObjs[idx];
        const c = b.cloudMesh.position;
        _state.smokeCamLabel = b.droneName + '-弹' + (b.bombIndex + 1);
        // 旋转中心始终锁定云团中心（跟随下沉）；相机位置不动，由用户自由控制
        controls.target.set(c.x, c.y, c.z);
        controls.update();
    }

    function fitView() {
        const pts = [];
        for (const m of _state.missiles) if (m.enabled) pts.push(toWorld(m.pos));
        pts.push([0, 0, 0], toWorld([0, 200, 10]));
        for (const d of _state.drones) if (d.enabled) pts.push(toWorld(d.pos));
        let cx = 0, cy = 0, cz = 0;
        for (const p of pts) { cx += p[0]; cy += p[1]; cz += p[2]; }
        cx /= pts.length; cy /= pts.length; cz /= pts.length;
        let R = 0;
        for (const p of pts) R = Math.max(R, P.dist(p, [cx, cy, cz]));
        R = Math.max(R, 5000);
        camera.position.set(cx + R * 1.5, cy + R * 0.9, cz + R * 1.2);
        controls.target.set(cx, cy, cz);
        camera.lookAt(cx, cy, cz);
        controls.update();
        if (_state.cameraMode !== 'free') setCameraMode('free');
    }

    // ================= 主循环 =================
    function animate(now) {
        requestAnimationFrame(animate);
        const dt = Math.min(0.1, (now - _last) / 1000 || 0.016);
        _last = now;
        if (_state.playing) {
            _state.t += dt * _state.speed;
            if (_state.t >= _state.tMax) {
                _state.t = _state.tMax;
                _state.playing = false;
                window.SimUI.syncPlay(false);
            }
            window.SimUI.updateTime(_state.t, _state.tMax);
        }

        updateObjects(dt);

        if (_state.cameraMode === 'missile') {
            updateMissileCamera();
        } else if (_state.cameraMode === 'drone') {
            updateDroneCamera();
        } else if (_state.cameraMode === 'smoke') {
            updateSmokeCamera();
        }
        controls.update();

        renderer.render(scene, camera);
        labelRenderer.render(scene, camera);
    }

    // ================= 对外接口 =================
    function create(domContainer) {
        container = domContainer;
        renderer = new THREE.WebGLRenderer({ antialias: true, logarithmicDepthBuffer: true });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.setSize(container.clientWidth, container.clientHeight);
        container.appendChild(renderer.domElement);

        labelRenderer = new THREE.CSS2DRenderer();
        labelRenderer.setSize(container.clientWidth, container.clientHeight);
        labelRenderer.domElement.style.position = 'absolute';
        labelRenderer.domElement.style.top = '0';
        labelRenderer.domElement.style.pointerEvents = 'none';
        container.appendChild(labelRenderer.domElement);

        window.addEventListener('resize', onResize);
        createScene();
        return {
            rebuild: rebuildDynamic,
            setCameraMode: setCameraMode,
            fitView: fitView,
            start: () => { _last = performance.now(); requestAnimationFrame(animate); },
        };
    }

    function onResize() {
        const w = container.clientWidth, h = container.clientHeight;
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
        labelRenderer.setSize(w, h);
    }

    function setState(state) { _state = state; }

    let _last = 0;

    // 轻量自检接口（调试/测试用，不影响运行）
    window.__simInspect = {
        missileConeCount: () => sightCones.length,
        missileConeSegments: () => sightCones.length ? sightCones[0].geometry.attributes.position.count / 2 : 0,
        samplingDotCount: () => {
            let n = 0;
            scene.traverse(o => { if (o.isPoints) n += o.geometry.attributes.position.count; });
            return n;
        },
        smokeSphereRadius: () => {
            let r = null;
            for (const b of bombList) {
                if (b.cloudMesh && b.cloudMesh.geometry) {
                    r = b.cloudMesh.geometry.parameters.radius;
                    break;
                }
            }
            return r;
        },
    };

    return { create, setState };
})();
