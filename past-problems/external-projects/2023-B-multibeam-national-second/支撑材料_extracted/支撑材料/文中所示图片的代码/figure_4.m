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
x1(1)=0;
x2(1)=get_x(deep(1))+get_w2(deep(1))*cos(a);
while get_x(deep(i))+get_w2(deep(i))*cos(a)<ew        
    syms x
    eqnn=(x2(i)-(get_x(x)-get_w1(x)*cos(a)))/((get_x(x)+get_w2(x)*cos(a))-(get_x(x)-get_w1(x)*cos(a)))==0.1;
    deep(i+1)=eval(solve(eqnn));
    x1(i+1)=get_x(deep(i+1))-get_w1(deep(i+1))*cos(a);
    x2(i+1)=get_x(deep(i+1))+get_w2(deep(i+1))*cos(a);
    i=i+1;
end

for i=1:length(deep)
    x_line(i)=get_x(deep(i));
end
x_line;   %每条侧线距离海域西边边界的距离

bond1=[linspace(0,ew,100)';ones(50,1)*ew;linspace(ew,0,100)'];
bond2=[zeros(100,1)*sn;(linspace(0,1,50)*sn)';ones(100,1)*sn];
plot(bond1,bond2,'k.-',0,0,'m',0,0,'b');
hold on
for i=1:34
    xx1=ones(50)*x1(i);
    xx2=ones(50)*x2(i);
    yy1=linspace(0,1,50)*sn;
    plot(xx1,yy1,'m');
    plot(xx2,yy1,'b');
    hold on
end
title('海域中测线边界的俯视图')
legend('海域边界','每条测线的西边边界','每条测线的东边边界')



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