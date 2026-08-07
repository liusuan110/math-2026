filename='附件.xlsx';
data=xlsread(filename);
x=1852*data(1,2:202);
y=1852*data(2:252,1);
data=-data(2:252,2:202);
[X,Y]=meshgrid(x,y);

hold off

h=contour(X,Y,data,30);
clabel(h)
title('等深线')
axis equal
