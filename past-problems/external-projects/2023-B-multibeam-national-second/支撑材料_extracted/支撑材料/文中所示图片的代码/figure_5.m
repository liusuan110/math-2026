filename='附件.xlsx';
data=xlsread(filename);
x=1852*data(1,2:202);
y=1852*data(2:252,1);
data=-data(2:252,2:202);
[X,Y]=meshgrid(x,y);

hold off

figure
subplot(1,2,1)
mesh(X,Y,data)
axis equal
title('海底地形图（等比例）')
hold on

subplot(1,2,2)
mesh(X,Y,data)
title('海底地形图（不等比例）')
