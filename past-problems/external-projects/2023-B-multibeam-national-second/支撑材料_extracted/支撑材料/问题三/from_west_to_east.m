a=(1.5/360)*2*pi;  %坡度
h0=110;  %中央深度
ew=7408;  %海域东西宽度
sn=3704;  %海域南北宽度
deep_east=h0-(ew/2)*tan(a);  %海域东边边界的深度
deep_west=h0+(ew/2)*tan(a);  %海域西边边界的深度

syms hh
eqn=hh+get_w1(hh)*sin(a)==deep_west;
S=eval(solve(eqn));

deep(1)=S;  %第一条测线所处位置的深度
i=1;
while get_x(deep(i))+get_w2(deep(i))*cos(a)<ew  
    deep(i+1)=deep_west-tan(a)*((deep_west-((get_x(deep(i))+get_w2(deep(i))*cos(a))-(get_w(deep(i))*cos(a)*0.1))*tan(a))*sqrt(3)+((get_x(deep(i))+get_w2(deep(i))*cos(a))-(get_w(deep(i))*cos(a)*0.1)));
    i=i+1;
end

for i=1:length(deep)
    x_line(i)=get_x(deep(i));
end
deep     %每条测线处的海域深度
x_line   %每条测线距离海域西边边界的距离






function w1=get_w1(h)       %得到的是深度为h处左边覆盖宽度
w1=sin(60/360*2*pi).*h/sin((30-1.5)/360*2*pi);
end

function w2=get_w2(h)       %得到的是深度为h处右边覆盖宽度
w2=sin(60/360*2*pi).*h/sin((30+1.5)/360*2*pi);
end

function w=get_w(h)        %得到的是深度为h处覆盖宽度
w=get_w1(h)+get_w2(h);
end

function x=get_x(h)         %得到深度为h处距离西边海域边界的距离
x=(110+(7408/2)*tan((1.5/360)*2*pi)-h)/tan(1.5/360*2*pi);
end