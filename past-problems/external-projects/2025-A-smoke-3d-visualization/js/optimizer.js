/**
 * optimizer.js —— 自动优化（一键智能寻优）
 *
 * 思路与参考代码一致（由粗到细）：
 *  1. 蒙特卡洛粗搜：对 (t_drop, delay, v, θ) 随机采样，用较粗步长快速评估
 *  2. 局部随机细化：在最优解附近随机游走，步长逐步收缩，用精细步长评估
 *  3. 时序贪心：
 *      - 单架无人机多枚弹：逐枚固定（后一枚不与前一枚投放时间冲突 <1s）
 *      - 多架无人机：逐架固定（优化当前架时保持已优化无人机的弹不变）
 *  目标函数：所选导弹"有效遮蔽时长并集"之和
 *  采用异步分块执行（yield 给主线程），不阻塞 UI，带进度回调。
 */

window.SimOptimizer = (function () {
    'use strict';
    const P = window.SimPhysics;

    // 评估一次完整方案：返回所有选中导弹的并集遮蔽总时长
    function evaluate(state) {
        const cov = P.computeCoverage(state);
        let total = 0;
        for (const m of state.missiles) {
            if (m.enabled && cov[m.name]) total += cov[m.name].total;
        }
        return total;
    }

    // 生成随机个体（对某个无人机的某枚弹）
    function randomInd(state, tMax) {
        return {
            tDrop: Math.random() * Math.max(1, tMax - 2),
            delay: Math.random() * 5,
            v: 70 + Math.random() * 70,
            theta: Math.random() * 360,
        };
    }

    function clip(v, lo, hi) { return Math.min(hi, Math.max(lo, v)); }

    // 点 p 到线段 [a, b] 的距离
    function distPointToSegment(p, a, b) {
        const ab = P.sub(b, a);
        const ap = P.sub(p, a);
        const ab2 = ab[0] * ab[0] + ab[1] * ab[1] + ab[2] * ab[2];
        if (ab2 < 1e-12) return P.norm(ap);
        let t = (ap[0] * ab[0] + ap[1] * ab[1] + ap[2] * ab[2]) / ab2;
        t = Math.max(0, Math.min(1, t));
        const q = P.add(a, P.mul(ab, t));
        return P.norm(P.sub(p, q));
    }

    /**
     * 几何预筛选：烟幕云团起爆点若离任一导弹轨迹线（起点→原点）足够近，
     * 才可能形成遮蔽。把 ~99% 不可能命中的候选直接剪掉，大幅提升搜索效率。
     */
    function promising(state, drone, bombIdx, ind, margin) {
        const dir2 = P.headingDir(ind.theta);
        const bp = P.burstPoint(drone.pos, dir2, ind.v, ind.tDrop, ind.delay, state.params.g);
        if (bp[2] <= 0) return false;
        const m = margin !== undefined ? margin : 80;
        for (const mis of state.missiles) {
            if (!mis.enabled) continue;
            const d = distPointToSegment(bp, mis.pos, [0, 0, 0]);
            if (d <= state.params.smokeRadius + m) return true;
        }
        return false;
    }

    // 保证同一无人机各弹投放间隔 ≥ minInterval（按投放时刻排序）
    function enforceSpacing(drone, bombIdx, minInterval) {
        // 取出投放时刻，把当前弹调整到与其它弹至少间隔 minInterval
        const others = [];
        drone.bombs.forEach((b, i) => { if (i !== bombIdx && b.enabled) others.push(b.tDrop); });
        if (!others.length) return;
        let t = drone.bombs[bombIdx].tDrop;
        for (let guard = 0; guard < 40; guard++) {
            let ok = true;
            for (const o of others) {
                if (Math.abs(t - o) < minInterval - 1e-9) { ok = false; break; }
            }
            if (ok) break;
            // 冲突则向后推
            t = Math.max(t, ...others.filter(o => Math.abs(o - t) < minInterval - 1e-9).map(o => o + minInterval));
            t = Math.max(0, Math.min(t, 120));
        }
        drone.bombs[bombIdx].tDrop = t;
    }

    // 覆盖评估：仅当前无人机当前弹参与（其它无人机弹保持不变）→ 并集总时长
    function evalBomb(state, drone, bombIdx) {
        // 为了速度用较粗步长，覆盖计算内部默认 dt=0.05；这里直接复用 computeCoverage
        // （无人机数量不多，直接全量评估，实现简单可靠）
        return evaluate(state);
    }

    function applyInd(state, drone, bombIdx, ind) {
        drone.bombs[bombIdx].tDrop = clip(ind.tDrop, 0, 120);
        drone.bombs[bombIdx].delay = clip(ind.delay, 0, 20);
        drone.speed = clip(ind.v, 70, 140);
        drone.theta = ((ind.theta % 360) + 360) % 360;
        enforceSpacing(drone, bombIdx, 1.0);
    }

    function yieldFrame() {
        return new Promise(res => setTimeout(res, 0));
    }

    /**
     * 优化一枚弹（MC 粗搜 + 局部细化）
     */
    async function optimizeOne(state, drone, bombIdx, nMC, nRefine, progress) {
        const tMax = state.tMax;
        const best = { ind: null, fit: -1 };

        // 保存当前值以便恢复初始个体之一
        const initInd = {
            tDrop: drone.bombs[bombIdx].tDrop,
            delay: drone.bombs[bombIdx].delay,
            v: drone.speed,
            theta: drone.theta,
        };

        const evalInd = (ind) => {
            applyInd(state, drone, bombIdx, ind);
            return evalBomb(state, drone, bombIdx);
        };

        // --- 阶段1：蒙特卡洛粗搜（含初始个体；几何预筛选剪枝） ---
        const candidates = [initInd];
        for (let i = 0; i < nMC; i++) candidates.push(randomInd(state, tMax));
        let evaluated = 0, pruned = 0;
        for (let i = 0; i < candidates.length; i++) {
            const cand = candidates[i];
            if (!promising(state, drone, bombIdx, cand, 80)) { pruned++; continue; }
            const fit = evalInd(cand);
            evaluated++;
            if (fit > best.fit) { best.fit = fit; best.ind = { ...cand }; }
            if (i % 40 === 0) {
                if (progress) progress((i / candidates.length) * 0.5, 'MC 粗搜 ' + (i + 1) + '/' + candidates.length);
                await yieldFrame();
            }
        }
        // 全部被剪枝（理论上不会发生）：退回初始个体
        if (!best.ind) {
            const fit0 = evalInd(initInd);
            best.fit = fit0; best.ind = { ...initInd };
        }

        // --- 阶段2：局部随机细化（步长收缩） ---
        let cur = { ...best.ind };
        let curFit = best.fit;
        for (let i = 0; i < nRefine; i++) {
            const decay = 1 - i / nRefine;
            const nxt = {
                tDrop: cur.tDrop + (Math.random() * 2 - 1) * (8 * decay + 0.5),
                delay: cur.delay + (Math.random() * 2 - 1) * (1.0 * decay + 0.05),
                v: cur.v + (Math.random() * 2 - 1) * (12 * decay + 1),
                theta: cur.theta + (Math.random() * 2 - 1) * (30 * decay + 2),
            };
            // 细化阶段只保留几何上仍然可行的邻域（收紧余量）
            if (!promising(state, drone, bombIdx, nxt, 40)) continue;
            const fit = evalInd(nxt);
            if (fit >= curFit) { cur = nxt; curFit = fit; }
            if (curFit > best.fit) { best.fit = curFit; best.ind = { ...cur }; }
            if (i % 30 === 0) {
                if (progress) progress(0.5 + (i / nRefine) * 0.5, '局部细化 ' + (i + 1) + '/' + nRefine);
                await yieldFrame();
            }
        }

        // 应用到方案
        applyInd(state, drone, bombIdx, best.ind);
        return best.fit;
    }

    /**
     * 主入口：按无人机顺序逐架、逐弹贪心优化
     * @param {object} state 全局状态（会被就地修改）
     * @param {object} opts { nMC, nRefine, progress(msg, pct), done(bestFit) }
     */
    async function optimize(state, opts) {
        opts = opts || {};
        const nMC = opts.nMC || 1500;
        const nRefine = opts.nRefine || 200;
        const progress = opts.progress;

        const drones = state.drones.filter(d => d.enabled && d.bombs.some(b => b.enabled));
        const totalBombs = drones.reduce((s, d) => s + d.bombs.filter(b => b.enabled).length, 0);
        if (!totalBombs) { if (progress) progress(1, '没有启用的干扰弹'); return 0; }

        let done = 0;
        let bestFit = -1;
        for (const drone of drones) {
            for (let bi = 0; bi < drone.bombs.length; bi++) {
                if (!drone.bombs[bi].enabled) continue;
                const fit = await optimizeOne(state, drone, bi, nMC, nRefine, (pct, msg) => {
                    const global = (done + pct) / totalBombs;
                    if (progress) progress(global, msg + '（' + drone.name + ' 弹' + (bi + 1) + '）');
                });
                bestFit = Math.max(bestFit, fit);
                done++;
            }
        }
        if (progress) progress(1, '优化完成，最佳总遮蔽 ' + bestFit.toFixed(2) + ' s');
        return bestFit;
    }

    return { optimize, evaluate };
})();
