/**
 * scenario.js —— 全局仿真状态 + 题目场景预设（问题1 ~ 问题5）
 *
 * 数据结构：
 *  state.params  物理参数（重力、烟幕半径/持续/下沉速度、导弹速度、遮蔽模式）
 *  state.cyl     真目标圆柱（中心 (0,200,0)，半径 7，高 10）
 *  state.missiles 来袭导弹列表（M1/M2/M3）
 *  state.drones   无人机列表（FY1~FY5），每架含航向 θ、速度、干扰弹列表
 */

window.SimState = (function () {
    'use strict';

    // ---------- 固定场景数据（题目给定） ----------
    const MISSILE_DATA = [
        { name: 'M1', pos: [20000, 0, 2000] },
        { name: 'M2', pos: [19000, 600, 2100] },
        { name: 'M3', pos: [18000, -600, 1900] },
    ];

    const DRONE_DATA = [
        { name: 'FY1', pos: [17800, 0, 1800], color: '#e6194b' },
        { name: 'FY2', pos: [12000, 1400, 1400], color: '#3cb44b' },
        { name: 'FY3', pos: [6000, -3000, 700], color: '#4363d8' },
        { name: 'FY4', pos: [11000, 2000, 1800], color: '#f58231' },
        { name: 'FY5', pos: [13000, -2000, 1300], color: '#911eb4' },
    ];

    function makeBomb(tDrop, delay, enabled) {
        return { tDrop: tDrop, delay: delay, enabled: enabled !== false };
    }

    function makeDrone(name, pos, color, opts) {
        opts = opts || {};
        return {
            name: name, pos: pos.slice(), color: color,
            enabled: opts.enabled !== false,
            speed: opts.speed !== undefined ? opts.speed : 100,
            theta: opts.theta !== undefined ? opts.theta : 180,
            bombs: (opts.bombs || [{ tDrop: 15, delay: 2 }]).map(b => makeBomb(b.tDrop, b.delay, b.enabled)),
        };
    }

    // ---------- 场景预设 ----------
    // 问题1：FY1 以 120 m/s 朝向假目标，1.5 s 后投放，间隔 3.6 s 起爆（θ=180° 即 -x 方向指向原点）
    const PRESET_Q1 = {
        params: { g: 9.8, missileSpeed: 300, smokeRadius: 10, activeDuration: 20, descentRate: 3, strict: true, sampleNum: 32 },
        missiles: [0],
        drones: [
            { idx: 0, speed: 120, theta: 180, bombs: [{ tDrop: 1.5, delay: 3.6 }] },
        ],
    };

    // 问题2：FY1 单弹（参数可调，可点"自动优化"）
    const PRESET_Q2 = {
        params: { g: 9.8, missileSpeed: 300, smokeRadius: 10, activeDuration: 20, descentRate: 3, strict: true, sampleNum: 32 },
        missiles: [0],
        drones: [
            { idx: 0, speed: 100, theta: 180, bombs: [{ tDrop: 15, delay: 2 }] },
        ],
    };

    // 问题3：FY1 投放 3 枚干扰弹（投放间隔 ≥1s）
    const PRESET_Q3 = {
        params: { g: 9.8, missileSpeed: 300, smokeRadius: 10, activeDuration: 20, descentRate: 3, strict: true, sampleNum: 32 },
        missiles: [0],
        drones: [
            { idx: 0, speed: 100, theta: 180, bombs: [{ tDrop: 10, delay: 2 }, { tDrop: 20, delay: 2 }, { tDrop: 30, delay: 2 }] },
        ],
    };

    // 问题4：FY1/FY2/FY3 各投放 1 枚
    const PRESET_Q4 = {
        params: { g: 9.8, missileSpeed: 300, smokeRadius: 10, activeDuration: 20, descentRate: 3, strict: true, sampleNum: 32 },
        missiles: [0],
        drones: [
            { idx: 0, speed: 100, theta: 180, bombs: [{ tDrop: 20, delay: 2 }] },
            { idx: 1, speed: 100, theta: 312, bombs: [{ tDrop: 25, delay: 2 }] },
            { idx: 2, speed: 100, theta: 73, bombs: [{ tDrop: 30, delay: 2 }] },
        ],
    };

    // 问题5：5 架无人机 × 至多 3 弹，干扰 3 枚导弹
    const PRESET_Q5 = {
        params: { g: 9.8, missileSpeed: 300, smokeRadius: 10, activeDuration: 20, descentRate: 3, strict: true, sampleNum: 32 },
        missiles: [0, 1, 2],
        drones: [
            { idx: 0, speed: 100, theta: 180, bombs: [{ tDrop: 20, delay: 2 }] },
            { idx: 1, speed: 100, theta: 312, bombs: [{ tDrop: 25, delay: 2 }] },
            { idx: 2, speed: 100, theta: 73, bombs: [{ tDrop: 30, delay: 2 }] },
            { idx: 3, speed: 100, theta: 200, bombs: [{ tDrop: 20, delay: 2 }] },
            { idx: 4, speed: 100, theta: 250, bombs: [{ tDrop: 25, delay: 2 }] },
        ],
    };

    const PRESETS = {
        q1: { label: '问题 1（复现题意）', data: PRESET_Q1 },
        q2: { label: '问题 2（FY1 单弹）', data: PRESET_Q2 },
        q3: { label: '问题 3（FY1 三弹）', data: PRESET_Q3 },
        q4: { label: '问题 4（三机各一弹）', data: PRESET_Q4 },
        q5: { label: '问题 5（五机三弹×三导弹）', data: PRESET_Q5 },
    };

    // ---------- 全局状态 ----------
    function defaultState() {
        return {
            t: 0,
            playing: false,
            speed: 1,
            tMax: 70,
            scenarioKey: 'q1',
            params: {
                g: 9.8,
                missileSpeed: 300,
                smokeRadius: 10,
                activeDuration: 20,
                descentRate: 3,
                strict: true,
                sampleNum: 32,
            },
            cyl: { center: [0, 200, 0], radius: 7, height: 10 },
            fakeTarget: { pos: [0, 0, 0] },
            missiles: MISSILE_DATA.map(m => ({ name: m.name, pos: m.pos.slice(), speed: 300, enabled: true })),
            drones: DRONE_DATA.map(d => makeDrone(d.name, d.pos, d.color, { enabled: false })),
            cameraMode: 'free',   // free | top | missile | smoke
            missileViewIndex: 0,
            missileCamInitialized: false, // 导弹视角相机是否已定位（首次进入或切换导弹时置 false）
            missileLastTarget: null,      // 导弹视角上一帧旋转中心（用于跟随平移）
            droneViewIndex: 0,    // 无人机视角跟随第几架（点击循环切换）
            droneCamInitialized: false,   // 无人机视角相机是否已定位
            droneLastTarget: null,        // 无人机视角上一帧旋转中心（用于跟随平移）
            smokeViewIndex: 0,    // 烟幕视角跟随第几团（点击循环切换）
            smokeCamLabel: '',    // 当前跟随的云团标签（app 每帧更新）
            smokeCamInitialized: false, // 烟幕视角相机是否已定位（首次进入或切换云团时置 false）
            coverage: null,       // computeCoverage 的结果
        };
    }

    let state = defaultState();

    /**
     * 应用预设。注意：必须在原 state 对象上就地修改（保持对象引用不变），
     * 因为 app.js / ui.js 都持有该对象的引用，替换整个对象会导致动画循环
     * 读到过期数据（时间不前进、场景不重建）。
     */
    function applyPreset(key) {
        const p = PRESETS[key];
        if (!p) return state;
        state.scenarioKey = key;
        Object.assign(state.params, p.data.params);
        state.missiles.forEach((m, i) => { m.enabled = p.data.missiles.includes(i); });
        state.drones.forEach((d) => { d.enabled = false; });
        for (const cfg of p.data.drones) {
            const d = state.drones[cfg.idx];
            d.enabled = true;
            d.speed = cfg.speed;
            d.theta = cfg.theta;
            d.bombs = cfg.bombs.map(b => makeBomb(b.tDrop, b.delay, b.enabled));
        }
        state.coverage = null;
        // 切换场景：回到自由视角并重置所有相机定位标志（避免残留视角状态）
        state.cameraMode = 'free';
        state.missileViewIndex = 0;
        state.missileCamInitialized = false;
        state.missileLastTarget = null;
        state.droneViewIndex = 0;
        state.droneCamInitialized = false;
        state.droneLastTarget = null;
        state.smokeViewIndex = 0;
        state.smokeCamInitialized = false;
        return state;
    }

    /** 恢复默认（同样保持对象引用不变） */
    function resetState() {
        const def = defaultState();
        state.scenarioKey = def.scenarioKey;
        Object.assign(state.params, def.params);
        Object.assign(state.cyl, def.cyl);
        Object.assign(state.fakeTarget, def.fakeTarget);
        state.missiles.forEach((m, i) => {
            const dm = def.missiles[i];
            m.name = dm.name; m.pos = dm.pos; m.speed = dm.speed; m.enabled = dm.enabled;
        });
        state.drones.forEach((dr, i) => {
            const dd = def.drones[i];
            dr.name = dd.name; dr.pos = dd.pos; dr.color = dd.color;
            dr.enabled = dd.enabled; dr.speed = dd.speed; dr.theta = dd.theta;
            dr.bombs = dd.bombs.map(b => makeBomb(b.tDrop, b.delay, b.enabled));
        });
        state.t = def.t; state.playing = def.playing; state.speed = def.speed; state.tMax = def.tMax;
        state.cameraMode = def.cameraMode; state.missileViewIndex = def.missileViewIndex;
        state.coverage = null;
        return state;
    }

    function getState() { return state; }

    function setState(s) { state = s; }

    return {
        PRESETS, DRONE_DATA, MISSILE_DATA,
        defaultState, applyPreset, resetState, getState, setState,
        makeBomb, makeDrone,
    };
})();
