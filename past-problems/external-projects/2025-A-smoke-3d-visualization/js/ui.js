/**
 * ui.js —— 界面（左侧参数面板 / 底部时间轴 / 右侧遮蔽看板）
 *
 * 通过 SimUI.init(state, callbacks) 挂载到页面 DOM：
 *  - callbacks.onChange()  任何参数变化（由 app 重新计算并重建 3D 场景）
 *  - callbacks.onSeek(t)   时间跳转
 *  - callbacks.onPlayPause(playing)
 *  - callbacks.onSpeed(v)
 *  - callbacks.onCamera(mode, missileIndex)
 *  - callbacks.onOptimize()
 *  - callbacks.onFit()
 *  - callbacks.onCloudScale(v)
 */

window.SimUI = (function () {
    'use strict';
    const S = window.SimState;

    // ---------- DOM 工具 ----------
    function el(tag, cls, parent, html) {
        const e = document.createElement(tag);
        if (cls) e.className = cls;
        if (html !== undefined) e.innerHTML = html;
        if (parent) parent.appendChild(e);
        return e;
    }

    // ---------- 部件 ----------
    function sliderRow(label, value, min, max, step, oninput, fmt) {
        const row = el('div', 'ctl-row');
        const lab = el('span', 'ctl-label', row, label);
        const wrap = el('div', 'ctl-slider', row);
        const input = el('input', '', wrap);
        input.type = 'range';
        input.min = min; input.max = max; input.step = step; input.value = value;
        const val = el('span', 'ctl-value', row, fmt ? fmt(value) : value.toFixed(1));
        input.addEventListener('input', () => {
            val.textContent = fmt ? fmt(+input.value) : (+input.value).toFixed(1);
            if (oninput) oninput(+input.value);
        });
        return { row, input, val };
    }

    /** 滑动条 + 数字输入框 组合控件：拖动/键入均实时联动（输入框支持小数点） */
    function sliderNumRow(label, value, min, max, step, oninput) {
        const row = el('div', 'ctl-row ctl-slider-num');
        el('span', 'ctl-label', row, label);
        const wrap = el('div', 'ctl-slider', row);
        const slider = el('input', '', wrap);
        slider.type = 'range';
        slider.min = min; slider.max = max; slider.step = step; slider.value = value;
        const num = el('input', 'ctl-num', row);
        num.type = 'text';
        num.inputMode = 'decimal';
        num.value = value;
        const clamp = (v) => Math.min(max, Math.max(min, v));
        slider.addEventListener('input', () => {
            num.value = slider.value;
            if (oninput) oninput(+slider.value);
        });
        // 解析文本为数字：支持 . 与 , 作为小数点，四舍五入到步进精度
        const parse = (s) => {
            const t = s.trim().replace(',', '.');
            if (t === '' || !/^-?\d*\.?\d*$/.test(t) || !isFinite(+t)) return null;
            const r = +(+t).toFixed(6);
            return +((Math.round(r / step) * step).toFixed(6));
        };
        const fromNum = (normalize) => {
            const v = parse(num.value);
            if (v === null) return;
            const c = clamp(v);
            slider.value = c;
            if (normalize) num.value = c;
            if (oninput) oninput(c);
        };
        num.addEventListener('input', () => fromNum(false));   // 键入过程中不清空输入框
        num.addEventListener('change', () => fromNum(true));   // 失焦/回车时规范化
        num.addEventListener('keydown', (e) => {               // 回车即生效
            if (e.key === 'Enter') { num.blur(); }
        });
        return { row, input: num, slider };
    }

    function checkboxRow(label, checked, onchange) {
        const row = el('div', 'ctl-check');
        const lab = el('label', '', row);
        const cb = el('input', '', lab);
        cb.type = 'checkbox'; cb.checked = checked;
        el('span', '', lab, label);
        cb.addEventListener('change', () => { if (onchange) onchange(cb.checked); });
        return { row, cb };
    }

    function numberRow(label, value, min, max, step, onchange) {
        const row = el('div', 'ctl-row');
        el('span', 'ctl-label', row, label);
        const inp = el('input', 'ctl-num', row);
        inp.type = 'text';
        inp.inputMode = 'decimal';
        inp.value = value;
        // 解析文本为数字：支持 . 与 , 作为小数点，四舍五入到步进精度
        const parse = (s) => {
            const t = s.trim().replace(',', '.');
            if (t === '' || !/^-?\d*\.?\d*$/.test(t) || !isFinite(+t)) return null;
            const r = +(+t).toFixed(6);
            return +((Math.round(r / step) * step).toFixed(6));
        };
        const update = (normalize) => {
            const v = parse(inp.value);
            if (v === null) return;
            if (normalize) inp.value = v;
            if (onchange) onchange(v);
        };
        inp.addEventListener('input', () => update(false));   // 键入过程中实时更新，不清空输入框
        inp.addEventListener('change', () => update(true));   // 失焦/回车时规范化
        inp.addEventListener('keydown', (e) => {              // 回车即生效
            if (e.key === 'Enter') { inp.blur(); }
        });
        return { row, input: inp };
    }

    function section(title, parent) {
        const sec = el('div', 'panel-section');
        el('div', 'panel-title', sec, title);
        parent.appendChild(sec);
        return sec;
    }

    // ---------- 全局句柄 ----------
    let _state = null;
    let _cb = null;
    let _panel = null;
    let _dash = null;
    let _timeSlider = null;
    let _timeText = null;
    let _playBtn = null;
    let _optimizing = false;

    // ================= 左侧参数面板 =================
    function buildPanel() {
        const st = _state;
        _panel.innerHTML = '';

        // ---- 场景预设 ----
        const sec0 = section('场景预设', _panel);
        const selRow = el('div', 'ctl-row');
        const sel = el('select', 'ctl-select', selRow);
        for (const key in S.PRESETS) {
            const o = el('option', '', null, S.PRESETS[key].label);
            o.value = key;
            sel.appendChild(o);
        }
        sel.value = st.scenarioKey;
        sel.addEventListener('change', () => {
            S.applyPreset(sel.value);
            _state = S.getState();
            refreshAll();
        });
        _panel.appendChild(selRow);
        const btnRow = el('div', 'ctl-row ctl-btns');
        const btnReset = el('button', 'btn', btnRow, '恢复默认');
        btnReset.addEventListener('click', () => { S.resetState(); _state = S.getState(); refreshAll(); });
        _panel.appendChild(btnRow);

        // ---- 来袭导弹 ----
        const sec1 = section('来袭导弹', _panel);
        st.missiles.forEach((m, i) => {
            const cr = checkboxRow(m.name + '  (' + m.pos.join(', ') + ')', m.enabled, (v) => {
                m.enabled = v;
                afterChange();
            });
            sec1.appendChild(cr.row);
        });
        const spd = numberRow('导弹速度 (m/s)', st.params.missileSpeed, 100, 500, 10, (v) => {
            st.params.missileSpeed = v;
            st.missiles.forEach(m => m.speed = v);
            afterChange();
        });
        sec1.appendChild(spd.row);
        const strict = checkboxRow('严格遮蔽判定（Q1~Q3 采样法）', st.params.strict, (v) => {
            st.params.strict = v;
            afterChange();
        });
        sec1.appendChild(strict.row);

        // ---- 物理参数 ----
        const sec2 = section('物理参数（高级）', _panel);
        const mk = (lab, key, min, max, step, fmt) => {
            const r = sliderRow(lab, st.params[key], min, max, step, (v) => {
                st.params[key] = v;
                afterChange();
            }, fmt);
            sec2.appendChild(r.row);
            return r;
        };
        mk('烟幕半径 (m)', 'smokeRadius', 2, 30, 0.5);
        mk('有效遮蔽时长 (s)', 'activeDuration', 2, 60, 0.5);
        mk('云团下沉速度 (m/s)', 'descentRate', 0, 10, 0.1);
        mk('重力加速度 g', 'g', 9, 11, 0.01);

        // ---- 无人机列表 ----
        const sec3 = section('无人机 & 干扰弹', _panel);
        st.drones.forEach((d, di) => {
            const card = el('div', 'drone-card');
            const head = el('div', 'drone-head');
            const chk = el('input', '', head);
            chk.type = 'checkbox'; chk.checked = d.enabled;
            const name = el('span', 'drone-name', head, d.name);
            name.style.color = d.color;
            el('span', 'drone-pos', head, '(' + d.pos[0] + ',' + d.pos[1] + ',' + d.pos[2] + ')');
            chk.addEventListener('change', () => {
                d.enabled = chk.checked;
                afterChange();
            });
            card.appendChild(head);

            const body = el('div', 'drone-body');
            body.style.display = d.enabled ? '' : 'none';
            const toggleBody = () => { body.style.display = d.enabled ? '' : 'none'; };
            chk.addEventListener('change', toggleBody);

            // 航向角（滑动条 + 数字输入）
            const thRow = sliderNumRow('航向 θ°', d.theta, 0, 360, 0.5, (v) => {
                d.theta = v;
                updateCompass(d, compass);
                afterChange();
            });
            // 简易罗盘指示
            const compass = el('div', 'compass', body);
            updateCompass(d, compass);
            body.appendChild(thRow.row);

            // 速度（滑动条 + 数字输入）
            const spRow = sliderNumRow('速度 (m/s)', d.speed, 70, 140, 1, (v) => {
                d.speed = v;
                afterChange();
            });
            body.appendChild(spRow.row);

            // 干扰弹列表
            const bombHead = el('div', 'bomb-head', body, '干扰弹（每架至多 3 枚，投放间隔 ≥1s）');
            const bombList = el('div', 'bomb-list', body);
            const renderBombs = () => {
                bombList.innerHTML = '';
                d.bombs.forEach((b, bi) => {
                    const brow = el('div', 'bomb-row');
                    el('span', 'bomb-tag', brow, '弹' + (bi + 1)).style.color = d.color;
                    const en = el('input', '', brow);
                    en.type = 'checkbox'; en.checked = b.enabled;
                    en.title = '启用';
                    en.addEventListener('change', () => { b.enabled = en.checked; afterChange(); });
                    const td = numberRow('投放 t (s)', b.tDrop, 0, 120, 0.1, (v) => {
                        b.tDrop = v;
                        afterChange();
                    });
                    td.row.classList.add('bomb-inline');
                    const dl = numberRow('延时 (s)', b.delay, 0, 20, 0.1, (v) => {
                        b.delay = v;
                        afterChange();
                    });
                    dl.row.classList.add('bomb-inline');
                    brow.appendChild(en);
                    brow.appendChild(td.row);
                    brow.appendChild(dl.row);
                    if (d.bombs.length > 1) {
                        const del = el('button', 'btn btn-mini', brow, '×');
                        del.addEventListener('click', () => {
                            d.bombs.splice(bi, 1);
                            renderBombs(); afterChange();
                        });
                    }
                    bombList.appendChild(brow);
                });
            };
            renderBombs();

            const addBtn = el('button', 'btn btn-mini', body, '+ 添加干扰弹');
            addBtn.style.display = d.bombs.length >= 3 ? 'none' : '';
            addBtn.addEventListener('click', () => {
                if (d.bombs.length >= 3) return;
                d.bombs.push(S.makeBomb(30, 2, true));
                renderBombs();
                addBtn.style.display = d.bombs.length >= 3 ? 'none' : '';
                afterChange();
            });
            body.appendChild(bombHead);
            body.appendChild(bombList);
            body.appendChild(addBtn);
            card.appendChild(body);
            sec3.appendChild(card);
        });
    }

    function updateCompass(d, compass) {
        const th = d.theta * Math.PI / 180;
        const x = Math.sin(th) * 50, y = -Math.cos(th) * 50;
        // θ 从 +x（东）起算逆时针；箭头默认朝北，旋转 (90-θ)° 使 θ=0 指向东
        // translate(-50%,-100%)：三角高 46px，-100% 把底边中心精确放到罗盘圆心
        compass.innerHTML =
            '<span class="compass-n">北</span><span class="compass-e">东</span>' +
            '<span class="compass-arrow" style="transform:translate(-50%,-100%) rotate(' + (90 - d.theta) + 'deg)"></span>' +
            '<span class="compass-dot" style="left:' + (50 + x) + '%;top:' + (50 + y) + '%"></span>';
    }

    // ================= 遮蔽看板 =================
    function buildDashboard() {
        _dash.innerHTML = '';
        const st = _state;
        const title = el('div', 'dash-title', _dash, '遮蔽看板');
        const hint = el('div', 'dash-hint', _dash, '横条 = 导弹被烟幕遮蔽的时间区域，颜色对应无人机');
        // 图例
        const legend = el('div', 'dash-legend', _dash);
        st.drones.filter(d => d.enabled).forEach(d => {
            const it = el('span', 'legend-item', legend);
            const chip = el('span', 'legend-chip', it);
            chip.style.background = d.color;
            el('span', '', it, d.name);
        });
        if (!legend.children.length) el('span', '', legend, '（未启用无人机）');

        let any = false;
        for (const m of st.missiles) {
            if (!m.enabled) continue;
            any = true;
            const cov = (st.coverage || {})[m.name];
            const card = el('div', 'dash-card');
            const head = el('div', 'dash-mhead');
            el('span', 'dash-mname', head, m.name);
            const info = el('span', 'dash-minfo', head,
                '命中 t=' + (cov ? cov.tHit.toFixed(1) : '-') + ' s');
            const badge = el('span', 'dash-badge', head, '—');
            badge.id = 'badge-' + m.name;
            head.appendChild(badge);
            card.appendChild(head);

            const stats = el('div', 'dash-stats', card);
            if (cov) {
                el('span', 'dash-total', stats, '总有效遮蔽: ' + cov.total.toFixed(2) + ' s (' +
                    (cov.tHit > 0 ? (100 * cov.total / cov.tHit).toFixed(1) : 0) + '%)');
            } else {
                el('span', 'dash-total', stats, '总有效遮蔽: 0 s');
            }

            // 时间轨道
            const trackWrap = el('div', 'dash-track-wrap', card);
            const ruler = el('div', 'dash-ruler', trackWrap);
            const ticks = 10;
            for (let i = 0; i <= ticks; i++) {
                const t = i * (st.tMax / ticks);
                const tk = el('span', 'dash-tick', ruler, t.toFixed(0) + 's');
                tk.style.left = (i * 100 / ticks) + '%';
            }
            const track = el('div', 'dash-track', trackWrap);
            track.id = 'track-' + m.name;
            const playhead = el('div', 'dash-playhead', trackWrap);
            playhead.id = 'ph-' + m.name;

            // 归因条
            const att = el('div', 'dash-att', card);
            if (cov && cov.attributed.length) {
                cov.attributed.forEach(seg => {
                    const bar = el('div', 'dash-bar');
                    bar.style.left = (seg.a / st.tMax * 100) + '%';
                    bar.style.width = Math.max(0.4, (seg.b - seg.a) / st.tMax * 100) + '%';
                    const colors = seg.labels.map(l => l.color);
                    bar.style.background = colors.length === 1 ? colors[0] :
                        'linear-gradient(90deg,' + colors.map((c, i) => c + ' ' + (i * 100 / colors.length) + '%,' + c + ' ' + ((i + 1) * 100 / colors.length) + '%)').join(',');
                    const labText = seg.labels.map(l => l.label).join('+');
                    bar.textContent = seg.b - seg.a > st.tMax * 0.03 ? labText : '';
                    bar.title = seg.a.toFixed(2) + '–' + seg.b.toFixed(2) + ' s : ' + labText;
                    track.appendChild(bar);
                });
            }
            if (cov && cov.attributed.length) {
                const txt = cov.attributed.map(s =>
                    s.a.toFixed(1) + '–' + s.b.toFixed(1) + 's: ' + s.labels.map(l => l.label).join('+')
                ).join('；');
                el('div', 'dash-att-text', att, txt);
            } else {
                el('div', 'dash-att-text', att, '无遮蔽时段');
            }
            _dash.appendChild(card);
        }
        if (!any) {
            el('div', 'dash-hint', _dash, '请至少启用一枚导弹');
        }
    }

    // ================= 底部时间轴 =================
    function buildTimeline() {
        const st = _state;
        _timeSlider.max = st.tMax;
        _timeSlider.value = st.t;
        _timeText.textContent = 't = ' + st.t.toFixed(2) + ' s / ' + st.tMax.toFixed(1) + ' s';
        _playBtn.textContent = st.playing ? '⏸ 暂停' : '▶ 播放';
    }

    // ================= 刷新 =================
    function refreshAll() {
        const st = _state;
        st.tMax = computeTMax(st);
        st.coverage = window.SimPhysics.computeCoverage(st);
        buildPanel();
        buildDashboard();
        buildTimeline();
        if (_cb.onChange) _cb.onChange();
    }

    function computeTMax(st) {
        let tMax = 70;
        for (const m of st.missiles) {
            if (!m.enabled) continue;
            const { tHit } = window.SimPhysics.missileDirAndHit(m.pos, m.speed);
            tMax = Math.max(tMax, tHit + 1);
        }
        return Math.ceil(tMax);
    }

    // 防抖：滑块拖动时避免高频重建
    let _debounceTimer = null;
    function afterChange() {
        if (_debounceTimer) clearTimeout(_debounceTimer);
        _debounceTimer = setTimeout(() => {
            const st = _state;
            st.tMax = computeTMax(st);
            st.coverage = window.SimPhysics.computeCoverage(st);
            buildDashboard();
            buildTimeline();
            if (_cb.onChange) _cb.onChange();
        }, 60);
    }

    // ================= 对外接口 =================
    function init(state, callbacks, dom) {
        _state = state;
        _cb = callbacks;
        _panel = dom.panel;
        _dash = dom.dashboard;
        _timeSlider = dom.timeSlider;
        _timeText = dom.timeText;
        _playBtn = dom.playBtn;

        // 底部控制按钮事件
        _playBtn.addEventListener('click', () => {
            _state.playing = !_state.playing;
            _playBtn.textContent = _state.playing ? '⏸ 暂停' : '▶ 播放';
            if (_cb.onPlayPause) _cb.onPlayPause(_state.playing);
        });
        _timeSlider.addEventListener('input', () => {
            _state.t = +_timeSlider.value;
            _timeText.textContent = 't = ' + _state.t.toFixed(2) + ' s / ' + _state.tMax.toFixed(1) + ' s';
            updateDashboardAt(_state.t);
            if (_cb.onSeek) _cb.onSeek(_state.t);
        });

        // 速度选择
        const speedSel = dom.speedSel;
        speedSel.addEventListener('change', () => {
            _state.speed = +speedSel.value;
            if (_cb.onSpeed) _cb.onSpeed(_state.speed);
        });

        // 相机模式（自由视角无按钮，仅作为默认/回退模式保留）
        dom.camDrone.addEventListener('click', () => {
            const en = _state.drones.filter(d => d.enabled);
            if (!en.length) { setCam('free'); return; }
            if (_state.cameraMode === 'drone') {
                // 已处于无人机视角：循环切换下一架无人机（重置定位到新无人机）
                const cur = _state.droneViewIndex;
                let nxt = -1;
                for (let i = 1; i <= _state.drones.length; i++) {
                    const idx = (cur + i) % _state.drones.length;
                    if (_state.drones[idx].enabled) { nxt = idx; break; }
                }
                if (nxt === -1 || nxt === cur) { setCam('free'); return; }
                _state.droneViewIndex = nxt;
                _state.droneCamInitialized = false;
                _cb.onCamera('drone', nxt);
                updateCamBtnLabel();
            } else {
                // 进入无人机视角（默认第一架启用无人机）
                const first = _state.drones.findIndex(d => d.enabled);
                _state.droneViewIndex = first >= 0 ? first : 0;
                _state.droneCamInitialized = false;
                setCam('drone');
            }
        });
        dom.camSmoke.addEventListener('click', () => {
            if (_state.cameraMode === 'smoke') {
                // 已处于烟幕视角：循环跟随下一团云（重置相机定位到新云团）
                _state.smokeViewIndex++;
                _state.smokeCamInitialized = false;
                _cb.onCamera('smoke', _state.smokeViewIndex);
                updateCamBtnLabel();
            } else {
                _state.smokeViewIndex = 0;
                _state.smokeCamInitialized = false;
                setCam('smoke');
            }
        });
        dom.camMissile.addEventListener('click', () => {
            const en = _state.missiles.filter(m => m.enabled);
            if (!en.length) { setCam('free'); return; }
            if (_state.cameraMode === 'missile') {
                // 已处于导弹视角：循环切换下一枚导弹；到末尾则退出
                const cur = _state.missileViewIndex;
                let nxt = -1;
                for (let i = 1; i <= _state.missiles.length; i++) {
                    const idx = (cur + i) % _state.missiles.length;
                    if (_state.missiles[idx].enabled) { nxt = idx; break; }
                }
                if (nxt === -1 || nxt === cur) { setCam('free'); return; }
                _state.missileViewIndex = nxt;
                _state.missileCamInitialized = false; // 重新定位到新导弹
                _cb.onCamera('missile', nxt);
                updateCamBtnLabel();
            } else {
                // 进入导弹视角（默认第一枚启用导弹）
                const first = _state.missiles.findIndex(m => m.enabled);
                _state.missileViewIndex = first >= 0 ? first : 0;
                _state.missileCamInitialized = false;
                setCam('missile');
            }
        });

        // 适配视角
        dom.fitBtn.addEventListener('click', () => { if (_cb.onFit) _cb.onFit(); });

        // 自动优化
        dom.optBtn.addEventListener('click', async () => {
            if (_optimizing) return;
            _optimizing = true;
            dom.optBtn.disabled = true;
            dom.optProgressWrap.style.display = 'flex';
            dom.optProgressBar.style.width = '0%';
            dom.optProgressText.textContent = '开始优化…';
            try {
                const fit = await window.SimOptimizer.optimize(_state, {
                    progress: (pct, msg) => {
                        dom.optProgressBar.style.width = Math.round(pct * 100) + '%';
                        dom.optProgressText.textContent = msg;
                    },
                });
                refreshAll();
                dom.optProgressText.textContent = '完成，总遮蔽 ' + fit.toFixed(2) + ' s';
            } finally {
                _optimizing = false;
                dom.optBtn.disabled = false;
                setTimeout(() => { dom.optProgressWrap.style.display = 'none'; }, 2500);
            }
        });

        refreshAll();
    }

    function setCam(mode) {
        _state.cameraMode = mode;
        if (_cb.onCamera) _cb.onCamera(mode, _state.missileViewIndex);
        // 更新按钮高亮
        document.querySelectorAll('.cam-btn').forEach(b => b.classList.remove('active'));
        const map = { free: '.cam-free', drone: '.cam-drone', missile: '.cam-missile', smoke: '.cam-smoke' };
        const s = document.querySelector(map[mode]);
        if (s) s.classList.add('active');
        updateCamBtnLabel();
    }

    function updateCamBtnLabel() {
        const mBtn = document.querySelector('.cam-missile');
        if (mBtn) {
            if (_state.cameraMode === 'missile') {
                const mi = _state.missiles[_state.missileViewIndex];
                mBtn.textContent = '🎯 导弹视角(' + (mi ? mi.name : '?') + ')' + (mi ? '·点击切换' : '');
            } else {
                mBtn.textContent = '🎯 导弹视角';
            }
        }
        const dBtn = document.querySelector('.cam-drone');
        if (dBtn) {
            if (_state.cameraMode === 'drone') {
                const d = _state.drones[_state.droneViewIndex];
                dBtn.textContent = '🚁 无人机视角(' + (d ? d.name : '?') + ')' + (d ? '·点击切换' : '');
            } else {
                dBtn.textContent = '🚁 无人机视角';
            }
        }
        const sBtn = document.querySelector('.cam-smoke');
        if (sBtn) {
            if (_state.cameraMode === 'smoke') {
                sBtn.textContent = '☁ 烟幕视角(' + (_state.smokeCamLabel || '…') + ')·点击切换';
            } else {
                sBtn.textContent = '☁ 烟幕视角';
            }
        }
    }

    /** 时间推进时由 app 调用 */
    function updateTime(t, tMax) {
        _timeSlider.max = tMax;
        _timeSlider.value = t;
        _timeText.textContent = 't = ' + t.toFixed(2) + ' s / ' + tMax.toFixed(1) + ' s';
        updateDashboardAt(t);
    }

    /** 看板 playhead 与状态徽章 */
    function updateDashboardAt(t) {
        const tMax = _state.tMax;
        const pct = tMax > 0 ? (t / tMax * 100) : 0;
        _state.missiles.forEach(m => {
            const ph = document.getElementById('ph-' + m.name);
            if (ph) ph.style.left = pct + '%';
            const badge = document.getElementById('badge-' + m.name);
            if (badge && m.enabled) {
                const cov = (_state.coverage || {})[m.name];
                const blocked = cov ? window.SimPhysics.isBlockedAt(cov, t) : false;
                const blk = window.SimPhysics.blockersAt(cov, t);
                badge.textContent = blocked ? '遮蔽中' : '可见';
                badge.className = 'dash-badge ' + (blocked ? 'on' : 'off');
                badge.title = blocked ? ('被 ' + blk.map(p => p.bombLabel).join('、') + ' 干扰') : '';
            }
        });
    }

    /** 播放状态按钮同步（时间轴到达末尾自动暂停时） */
    function syncPlay(playing) {
        _playBtn.textContent = playing ? '⏸ 暂停' : '▶ 播放';
    }

    return { init, updateTime, syncPlay, setCam };
})();
