d=linspace(-800,800,9);   %测线距中心点处的距离 /m
a=(1.5/360)*2*pi;

h=ones(1,9)*70;
h=h-d*tan(a)             %海水深度 /m

w_l=sin(60/360*2*pi).*h/sin((30-1.5)/360*2*pi);
w_r=sin(60/360*2*pi).*h/sin((30+1.5)/360*2*pi);
w=w_l+w_r                 %覆盖宽度 /m

coordinate_l=d-w_l.*cos(a); %每条测线最左端声波的位置 
coordinate_r=d+w_r.*cos(a); %每条测线最右端声波的位置
Overlap_rate=100*(coordinate_r(1:8)-coordinate_l(2:9))./(w(2:9)*cos(a))
%与前一条测线的重叠率 /%


