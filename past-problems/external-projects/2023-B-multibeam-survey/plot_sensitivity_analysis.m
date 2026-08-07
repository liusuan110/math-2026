%% ==== 读取 CSV ====
T = readtable('stats\sobol_indices.csv','ReadRowNames',true);

% labels = T.Properties.RowNames;    % {'θ','α','η','D₀'}
labels = {'\theta';'\alpha'; '\eta';'D_{0}'};
S1_Wmid = T.S1_Wmid;
ST_Wmid = T.ST_Wmid;
S1_Lsum = T.S1_Lsum;
ST_Lsum = T.ST_Lsum;

%% ==== 绘制中心条带宽度敏感性 ====
figure('Color','w','Position',[120 120 430 300]);
b = bar([S1_Wmid, ST_Wmid],'grouped','BarWidth',0.7);
% set(b(1),'FaceColor',[0.3 0.6 1]);    % S1 蓝色
% set(b(2),'FaceColor',[1 0.6 0.2]);    % ST 橙色
xticks(1:4); xticklabels(labels);
ylim([0 1]);
ylabel('Sobol index');
title('中心条带宽度 W_{mid} 敏感性');
legend({'一阶 S1','总效应 ST'},'Location','northwest');
grid on; box on;

%% ==== 绘制总测线长度敏感性 ====
figure('Color','w','Position',[600 120 430 300]);
b = bar([S1_Lsum, ST_Lsum],'grouped','BarWidth',0.7);
xticks(1:4); xticklabels(labels);
ylim([0 1]);
ylabel('Sobol index');
title('总测线长度 L_{sum} 敏感性');
legend({'一阶 S1','总效应 ST'},'Location','northwest');
grid on; box on;

%% ==== 可选：保存为 PDF/PNG ====
% exportgraphics(gcf, 'sobol_Lsum_matlab.pdf', 'ContentType', 'vector');
