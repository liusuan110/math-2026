% 读取数据
T = readtable('stats\validate_diff.csv');
W3d = T.W_3d;
Wan = T.W_analytic;

% 计算误差
abs_diff = abs(Wan - W3d);

% 绘制对数-对数散点图
figure;
loglog(W3d, abs_diff, '.');
% xlabel('W_{total} by 3-D method (m)');
% ylabel('|ΔW|  (m)');
xlabel('三维交点法总宽度 W_{total}', 'FontName', 'SimHei');
ylabel('两方法宽度绝对误差 |ΔW|', 'FontName', 'SimHei');
% title('Analytic vs 3-D  width difference');
title('解析法与三维交点法宽度误差对比', 'FontName', 'SimHei');
grid on;
