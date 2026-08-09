/**
 * physics.js —— 烟幕干扰弹投放物理模型
 *
 * 严格对照 Q1~Q4 参考代码（Python）实现：
 *  - 导弹：从初始位置以 300 m/s 匀速直线飞向假目标（原点）
 *  - 无人机：等高度匀速直线飞行（速度 70~140 m/s，航向角 θ 在水平面内）
 *  - 干扰弹：无人机飞行 t_drop 后投放，保持无人机水平速度并受重力，经 delay 后起爆
 *  - 烟幕云团：起爆瞬时形成半径 10 m 球体，以 3 m/s 匀速下沉，有效遮蔽 20 s
 *  - 遮蔽判定：导弹 → 圆柱目标上采样点 的视线是否全部被云团"截断"
 *    （strict 模式 = Q1~Q3 的 35 点采样；approx 模式 = Q4/Q5 的圆柱最近点近似）
 */

window.SimPhysics = (function () {
    'use strict';

    // ---------- 基础向量工具 ----------
    function sub(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
    function add(a, b) { return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]; }
    function mul(a, s) { return [a[0] * s, a[1] * s, a[2] * s]; }
    function norm(a) { return Math.hypot(a[0], a[1], a[2]); }
    function dist(a, b) { return norm(sub(a, b)); }

    /**
     * 导弹方向与命中假目标（原点）的时刻
     * @param {number[]} m0 导弹初始位置 [x,y,z]
     * @param {number} speed 导弹速度 (m/s)，默认 300
     * @returns {{dir:number[], tHit:number}}
     */
    function missileDirAndHit(m0, speed) {
        const d = sub([0, 0, 0], m0);
        const L = norm(d) + 1e-12;
        return { dir: mul(d, 1 / L), tHit: L / speed };
    }

    /** 导弹 t 时刻的位置 */
    function missilePosAt(m0, dir, speed, t) {
        return [m0[0] + dir[0] * speed * t, m0[1] + dir[1] * speed * t, m0[2] + dir[2] * speed * t];
    }

    /** 水平面航向角 θ (度) → 单位方向向量 (cosθ, sinθ, 0) */
    function headingDir(thetaDeg) {
        const th = thetaDeg * Math.PI / 180;
        return [Math.cos(th), Math.sin(th), 0];
    }

    /** 无人机 t 时刻位置（等高度直线飞行） */
    function dronePosAt(uav0, dir2, v, t) {
        return [uav0[0] + dir2[0] * v * t, uav0[1] + dir2[1] * v * t, uav0[2]];
    }

    /** 投放点：无人机飞行 t_drop 后投放干扰弹的位置 */
    function releasePoint(uav0, dir2, v, tDrop) {
        return dronePosAt(uav0, dir2, v, tDrop);
    }

    /** 起爆点：投放后干扰弹保持水平速度、受重力下落 delay 秒 */
    function burstPoint(uav0, dir2, v, tDrop, delay, g) {
        const R = releasePoint(uav0, dir2, v, tDrop);
        return [R[0] + dir2[0] * v * delay, R[1] + dir2[1] * v * delay, R[2] - 0.5 * g * delay * delay];
    }

    /** 下落中的干扰弹位置（tRel 为投放后的相对时间） */
    function bombPosDuringFall(R, dir2, v, tRel, g) {
        return [R[0] + dir2[0] * v * tRel, R[1] + dir2[1] * v * tRel, R[2] - 0.5 * g * tRel * tRel];
    }

    /** 烟幕云团中心（t 为绝对时间，tBurst 为起爆时刻） */
    function cloudCenterAt(P, tBurst, t, descent) {
        return [P[0], P[1], P[2] - descent * (t - tBurst)];
    }

    /** 点到线段的最短距离 */
    function distancePointToSegment(P, A, B) {
        const AB = sub(B, A);
        const AP = sub(P, A);
        const ab2 = AB[0] * AB[0] + AB[1] * AB[1] + AB[2] * AB[2];
        if (ab2 <= 1e-16) return dist(P, A);
        let s = (AP[0] * AB[0] + AP[1] * AB[1] + AP[2] * AB[2]) / ab2;
        s = Math.max(0, Math.min(1, s));
        const Q = add(A, mul(AB, s));
        return dist(P, Q);
    }

    /** 圆柱体上离 p 最近的点（Q4/Q5 近似用） */
    function closestPointOnCylinder(p, cyl) {
        const cx = cyl.center[0], cy = cyl.center[1], cz = cyl.center[2];
        const dx = p[0] - cx, dy = p[1] - cy;
        const r = Math.hypot(dx, dy);
        let bx, by;
        if (r > 1e-12) { bx = cx + cyl.radius * dx / r; by = cy + cyl.radius * dy / r; }
        else { bx = cx + cyl.radius; by = cy; }
        const bz = Math.max(cz, Math.min(cz + cyl.height, p[2]));
        return [bx, by, bz];
    }

    /**
     * 严格遮蔽判定（Q1~Q3）：导弹→圆柱上全部采样点（3 个轴心点 + 上下两圈边缘点）的
     * 视线都被烟幕球截断才算遮蔽。
     * @param {number[]} missilePos 导弹位置
     * @param {{center:number[],radius:number,height:number}} cyl 圆柱目标
     * @param {number[]} smokeCenter 云团中心
     * @param {number} R 云团有效半径
     * @param {number} sampleNum 每圈采样数
     */
    function isBlockedStrict(missilePos, cyl, smokeCenter, R, sampleNum) {
        sampleNum = sampleNum || 32;
        const cx = cyl.center[0], cy = cyl.center[1], cz = cyl.center[2];
        const pts = [[cx, cy, cz], [cx, cy, cz + cyl.height], [cx, cy, cz + cyl.height / 2]];
        for (const z of [cz, cz + cyl.height]) {
            for (let k = 0; k < sampleNum; k++) {
                const th = 2 * Math.PI * k / sampleNum;
                pts.push([cx + cyl.radius * Math.cos(th), cy + cyl.radius * Math.sin(th), z]);
            }
        }
        for (const p of pts) {
            if (distancePointToSegment(smokeCenter, missilePos, p) > R) return false;
        }
        return true;
    }

    /**
     * 近似遮蔽判定（Q4/Q5）：只检查导弹 → 圆柱最近点的视线。
     */
    function isBlockedApprox(missilePos, cyl, smokeCenter, R) {
        const tgt = closestPointOnCylinder(missilePos, cyl);
        return distancePointToSegment(smokeCenter, missilePos, tgt) <= R;
    }

    /** 区间合并（并集） */
    function mergeIntervals(list) {
        if (!list.length) return [];
        const arr = list.slice().sort((a, b) => a[0] - b[0]);
        const merged = [arr[0].slice()];
        for (let i = 1; i < arr.length; i++) {
            const last = merged[merged.length - 1];
            if (arr[i][0] <= last[1] + 1e-9) {
                last[1] = Math.max(last[1], arr[i][1]);
            } else {
                merged.push(arr[i].slice());
            }
        }
        return merged;
    }

    function totalLength(intervals) {
        return intervals.reduce((s, iv) => s + (iv[1] - iv[0]), 0);
    }

    /**
     * 单枚干扰弹对单枚导弹的有效遮蔽时段
     * @param {object} bomb   {tDrop, delay}
     * @param {object} drone  {pos:uav0, theta, speed}
     * @param {object} missile {pos:m0, speed}
     * @param {object} params {g, smokeRadius, activeDuration, descentRate, strict, sampleNum, cyl}
     * @param {number} dt 时间步长（默认 0.05，与参考代码一致）
     * @returns {{intervals:number[][], tBurst:number, burstPoint:number[]}}
     */
    function coverageIntervals(bomb, drone, missile, params, dt) {
        dt = dt || 0.05;
        const g = params.g, R = params.smokeRadius, active = params.activeDuration, descent = params.descentRate;
        const cyl = params.cyl;
        const tBurst = bomb.tDrop + bomb.delay;
        const dir2 = headingDir(drone.theta);
        const P = burstPoint(drone.pos, dir2, drone.speed, bomb.tDrop, bomb.delay, g);
        if (P[2] <= 0) return { intervals: [], tBurst: tBurst, burstPoint: P };

        const { dir, tHit } = missileDirAndHit(missile.pos, missile.speed);
        const tStart = Math.max(0, tBurst);
        const tEnd = Math.min(tBurst + active, tHit);
        const intervals = [];
        if (tEnd <= tStart) return { intervals: [], tBurst: tBurst, burstPoint: P };

        const blockedFn = params.strict ? isBlockedStrict : isBlockedApprox;
        let blocked = false, tIn = 0;
        for (let t = tStart; t <= tEnd + 1e-9; t += dt) {
            const mpos = missilePosAt(missile.pos, dir, missile.speed, t);
            const c = cloudCenterAt(P, tBurst, t, descent);
            const cur = blockedFn(mpos, cyl, c, R, params.sampleNum);
            if (cur && !blocked) { tIn = t; }
            else if (!cur && blocked) { intervals.push([tIn, t]); }
            blocked = cur;
        }
        if (blocked) intervals.push([tIn, tEnd]);
        return { intervals: intervals, tBurst: tBurst, burstPoint: P };
    }

    /**
     * 汇总：对每个启用导弹，计算并集遮蔽时段 + 逐弹时段 + 归因
     * @param {object} state 全局状态（见 scenario.js）
     * @returns {object} coverageByMissile
     *   key = 导弹名，value = {
     *     union: number[][], total: number,
     *     parts: [{drone, bombLabel, color, intervals: number[][], burstPoint}],
     *     attributed: [{a, b, labels: string[]}]
     *   }
     */
    function computeCoverage(state) {
        const result = {};
        for (const mis of state.missiles) {
            if (!mis.enabled) continue;
            const parts = [];
            const allIv = [];
            for (const dr of state.drones) {
                if (!dr.enabled) continue;
                dr.bombs.forEach((bomb, bi) => {
                    if (!bomb.enabled) return;
                    const cov = coverageIntervals(bomb, dr, mis, Object.assign({}, state.params, { cyl: state.cyl }), 0.02);
                    if (cov.intervals.length) {
                        parts.push({
                            drone: dr.name,
                            bombIndex: bi,
                            bombLabel: dr.name + '-弹' + (bi + 1),
                            color: dr.color,
                            intervals: cov.intervals,
                            tBurst: cov.tBurst,
                            burstPoint: cov.burstPoint
                        });
                        allIv.push(...cov.intervals);
                    }
                });
            }
            const union = mergeIntervals(allIv);
            // 归因：对每个并集时段，找出哪些弹与之重叠
            const attributed = union.map(iv => {
                const labels = [];
                for (const p of parts) {
                    const hit = p.intervals.some(piv => piv[0] <= iv[1] + 1e-9 && piv[1] >= iv[0] - 1e-9);
                    if (hit) labels.push({ label: p.bombLabel, color: p.color });
                }
                return { a: iv[0], b: iv[1], labels: labels };
            });
            result[mis.name] = {
                union: union,
                total: totalLength(union),
                parts: parts,
                attributed: attributed,
                tHit: missileDirAndHit(mis.pos, mis.speed).tHit
            };
        }
        return result;
    }

    /** t 时刻某导弹是否被遮蔽（并集判断） */
    function isBlockedAt(coverage, t) {
        if (!coverage) return false;
        return coverage.union.some(iv => t >= iv[0] - 1e-9 && t <= iv[1] + 1e-9);
    }

    /** t 时刻正在遮蔽该导弹的干扰弹标签列表 */
    function blockersAt(coverage, t) {
        const list = [];
        if (!coverage) return list;
        for (const p of coverage.parts) {
            if (p.intervals.some(iv => t >= iv[0] - 1e-9 && t <= iv[1] + 1e-9)) {
                list.push(p);
            }
        }
        return list;
    }

    return {
        sub, add, mul, norm, dist,
        missileDirAndHit, missilePosAt, headingDir, dronePosAt,
        releasePoint, burstPoint, bombPosDuringFall, cloudCenterAt,
        distancePointToSegment, closestPointOnCylinder,
        isBlockedStrict, isBlockedApprox,
        mergeIntervals, totalLength,
        coverageIntervals, computeCoverage, isBlockedAt, blockersAt
    };
})();
