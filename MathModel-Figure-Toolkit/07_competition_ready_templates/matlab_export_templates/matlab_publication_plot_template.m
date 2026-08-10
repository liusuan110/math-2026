%% MATLAB 论文图导出模板
% 用途：
%   1. 统一 MATLAB 图的字体、线宽、尺寸
%   2. 优先使用 external-tools/figure-tools/export_fig 高质量导出
%   3. 如果 export_fig 不可用，则回退到 exportgraphics
%
% 赛时建议：
%   - MATLAB 负责仿真和快速探索，但论文图不要直接截图。
%   - 若 MATLAB 图难以调美，可以导出数据给 Python 重画。

clear; clc;

repoRoot = fileparts(fileparts(fileparts(fileparts(mfilename('fullpath')))));
exportFigDir = fullfile(repoRoot, 'external-tools', 'figure-tools', 'export_fig');
if exist(exportFigDir, 'dir')
    addpath(exportFigDir);
end

outDir = fullfile(fileparts(mfilename('fullpath')), 'output');
if ~exist(outDir, 'dir')
    mkdir(outDir);
end

% 示例数据：比赛时替换为模型或仿真输出
t = linspace(0, 12, 300);
y1 = exp(-0.12 * t) .* sin(1.8 * t);
y2 = exp(-0.10 * t) .* sin(1.8 * t + 0.35);

fig = figure('Color', 'w', 'Units', 'centimeters', 'Position', [4, 4, 14, 8]);
plot(t, y1, '-', 'LineWidth', 1.8, 'Color', [0.18, 0.44, 0.62]); hold on;
plot(t, y2, '--', 'LineWidth', 1.8, 'Color', [0.75, 0.22, 0.17]);
xlabel('Time t / s');
ylabel('Response amplitude');
title('Simulation response comparison');
legend({'Baseline scheme', 'Optimized scheme'}, 'Location', 'northeast', 'Box', 'off');
grid on;

set(gca, ...
    'FontName', 'Times New Roman', ...
    'FontSize', 10, ...
    'LineWidth', 0.9, ...
    'GridAlpha', 0.25, ...
    'TickDir', 'out', ...
    'Box', 'off');

baseName = fullfile(outDir, 'matlab_response_comparison');
save_publication_figure(fig, baseName);
fprintf('Saved MATLAB figure to: %s.[png/pdf]\n', baseName);

function save_publication_figure(fig, baseName)
    % 优先使用 export_fig；没有时使用 MATLAB 自带 exportgraphics。
    if exist('export_fig', 'file') == 2
        export_fig(fig, [baseName, '.png'], '-r300', '-transparent');
        export_fig(fig, [baseName, '.pdf'], '-pdf', '-transparent');
    else
        exportgraphics(fig, [baseName, '.png'], 'Resolution', 300);
        exportgraphics(fig, [baseName, '.pdf'], 'ContentType', 'vector');
    end
end

