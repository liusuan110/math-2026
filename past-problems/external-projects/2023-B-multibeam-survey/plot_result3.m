% % === 1. 载入布线结果 ===
% T   = readtable('result3_deep_to_shallow.xlsx');  % line_no, x_center, depth
% Lx  = 4 * 1852;      % 东西向 4 nmi
% Ly  = 2 * 1852;      % 南北向 2 nmi
% 
% % === 2. 基础绘图 ===
% 
% figure('Color','w','Position',[100 100 680 320]); hold on; axis equal
% box on; grid on
% % 绘矩形海域
% rectangle('Position',[0 0 Lx Ly],...
%           'EdgeColor',[0.2 0.2 0.2],'LineWidth',1.2);
% 
% % 颜色映射到水深（浅→深）
% cmap = parula(height(T));
% for k = 1:height(T)
%     xk = T.x_center_m_(k);
%     plot([xk xk],[0 Ly],'-','Color',cmap(k,:),...
%          'LineWidth',1.5);
%     % 在条带中心加小圆 & 注记
%     plot(xk,Ly/2,'ko','MarkerSize',4,'MarkerFaceColor',cmap(k,:));
%     text(xk,Ly*0.52,sprintf('#%d',T.line_no(k)),...
%         'HorizontalAlignment','center','FontSize',8);
% end
% 
% % === 3. 细节美化 ===
% colormap(cmap); cb=colorbar;
% cb.Label.String='中心水深 / m';
% xlabel('东西向坐标 x / m');
% ylabel('南北向坐标 y / m');
% % title('多波束测深——由深往潜布线示意图');
% set(gca,'FontName','Times New Roman','FontSize',10);
% exportgraphics(gcf,'figure_lines_layout.pdf','ContentType','vector');

%%
% === 0. 准备 ===
nm  = 1852;                    % 1 海里 = 1852 m
Lx  = 4 * nm;   Ly = 2 * nm;   % 海域原米制尺寸

T  = readtable('stats\result3_lines_info.xlsx');   % 含 x_left(m)、x_right(m)
Ov = readtable('stats\result3_overlap_info.xlsx'); % 含重叠区边界(m)

% === 1. 米 → 海里坐标换算 ===
T.x_left_nm   = T.x_left_m_   / nm;
T.x_right_nm  = T.x_right_m_  / nm;
T.x_center_nm = T.x_center_m_ / nm;

Ov.ov_start_nm = Ov.ov_start_m_ / nm;
Ov.ov_end_nm   = Ov.ov_end_m_   / nm;

Lx_nm = Lx / nm;
Ly_nm = Ly / nm;

% === 2. 绘图 ===
figure('Color','w','Position',[120 120 700 340]); hold on; axis equal
rectangle('Position',[0 0 Lx_nm Ly_nm], ...
          'EdgeColor',[.3 .3 .3],'LineWidth',1.2);

% 颜色映射（按水深米值）
cmap = parula(height(T));

% 绘制中心测线
for k = 1:height(T)
    xc = T.x_center_nm(k);
    plot([xc xc],[0 Ly_nm],'Color',[0 0 0], ...  % 纯黑线
         'LineWidth',0.9,'LineStyle','--');
    % 可改 'LineStyle','--' 获得虚线效果
end

% 条带矩形patch
for k = 1:height(T)
    xl = T.x_left_nm(k);   
    xr = T.x_right_nm(k);
    patch([xl xr xr xl],[0 0 Ly_nm Ly_nm], cmap(k,:), ...
          'EdgeColor','k','FaceAlpha',0.35);
    text((xl+xr)/2, Ly_nm*0.05, sprintf('#%d',T.line_no(k)), ...
        'HorizontalAlignment','center','FontSize',8);
end

% —— 标出重叠率 > 10% 的区段 ——  
idx = Ov.ov_ratio_k_ > 10;                         
for j = find(idx)'
    ovl = Ov.ov_start_nm(j);  ovr = Ov.ov_end_nm(j);
    % patch([ovl ovr ovr ovl],[0 0 Ly_nm Ly_nm], ...
    %       'red','FaceAlpha',0.38,'EdgeColor','none');
    patch([ovl ovr ovr ovl], [0 0 Ly_nm Ly_nm], [0.5 0.5 0.5], 'FaceAlpha', 0.38, 'EdgeColor', 'none');

end

% === 3. 坐标轴与标注 ===
% —— 设置 colormap 与色条 ——
colormap(cmap)                     % 使用先前生成的 cmap
caxis([min(T.depth_m_) max(T.depth_m_)])  % 深度范围
hcb = colorbar('eastoutside');     % 右侧色条
hcb.Label.String = '中心水深 / 米'; % 色条标题
% hcb.TickLabelInterpreter = 'latex';% (可选) LaTeX 格式
% 获取 colorbar 当前刻度（默认递增）
ticks = hcb.Ticks;
% 手动设定新的 label（反向排序）
hcb.TickLabels = arrayfun(@(x) sprintf('%.0f', x), flip(ticks), 'UniformOutput', false);
hcb.FontSize = 9;

xlabel('东西向距离 / 海里');
ylabel('南北向距离 / 海里');
% title('多波束测深条带及重叠区示意（单位：海里）');
title('多波束测深布线示意图');
xlim([0 Lx_nm]); ylim([0 Ly_nm]);
grid off; box on
% exportgraphics(gcf,'strip_overlap_nmi.pdf','ContentType','vector');
