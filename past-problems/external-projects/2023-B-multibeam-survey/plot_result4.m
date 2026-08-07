data0=xlsread('stats\附件.xlsx');
y_real=1852*data0(1,2:202);
x_real=1852*data0(2:252,1)';
data=-data0(2:252,2:202);
[X,Y]=meshgrid(x_real,y_real);

hold off

i=1;
k=1;
mid=126;
x0=x_real(mid);%基准点的坐标位置
y(1)=0;%第一条测线边界：和x轴相交（纵坐标）
[~,Index_1(i)] = min(abs(y_real-y(i)));%Index_1返回索引

v=-sqrt(3)*data(mid,1);%第i条测线实际纵坐标
[~,Index(i)] = min(abs(x_real-v));%Index返回附近的点索引
line(i)=v;
while y(i)-sqrt(3)*data(mid,Index_1(i))<4*1852
    y(i+1)=2*line(i)-y(i);
    [~,Index_1(i+1)] = min(abs(y_real-y(i+1)));%Index_1返回索引
    v=-sqrt(3)*data(mid,Index_1(i))+y(i+1);%第i条测线理论纵坐标
    [~,Index(i+1)] = min(abs(y_real-v));%Index返回索引
    line(i+1)=v;
    i=i+1;
end

line=line(1,1:length(line)-1);


y1=ones(length(line),251);
y2=ones(length(line),251);
for i=1:length(line)    
    y1(i,:)=(line(i)+(-1*sqrt(3)*data(:,Index(i))))';%测线上边界
    y2(i,:)=(line(i)-(-1*sqrt(3)*data(:,Index(i))))';%测线下边界    
    plot(x_real,line(i)*ones(1,251),'k')
    hold on
    plot(x_real,y1,'r',x_real,y2,'b');
    hold on
end


%测线的总长度
path_length=length(line)*5


%漏测海区占总待测海域面积的百分比
memory1=[];
for i=2:46
    for j=1:251
        if y2(i,j)>y1(i-1,j)
            memory1=[memory1;y2(i,j)-y1(i-1,j)];
        end
    end
end
for j=1:251
    if y2(1,j)>0
        memory1=[memory1;y2(1,j)];
    end
end
for j=1:251
    if 4*1852-y1(46,j)>0
        memory1=[memory1;4*1852-y1(46,j)];
    end
end
S=sum(memory1)*0.02*1852;
rate=S/(5*4*1852*1852)

% 在重叠区域中，重叠率超过 20% 部分的总长度
memory2=[];
for i=2:46
    for j=1:251
        if (y1(i-1,j)-y2(i,j))>0.2*(y1(i-1,j)-y2(i-1,j))
            memory2=[memory2;0.02*1852];
        end
    end
end
distances=sum(memory2)

%可调整代码以获得所需要的输出图示
h=contour(X',Y',data,50);
axis equal
title('等高线和测线的叠加图')
% % % title('测线分布图')
legend('测线','沿测线扫描形成的条带的上边界','沿测线扫描形成的条带的下边界')
% % % legend('测线')