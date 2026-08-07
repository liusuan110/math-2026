a=1.5/360*2*pi;%海底的坡度
b=linspace(0,315,8)/360*2*pi; %测线方向夹角
d=1852*linspace(0,2.1,8);%测量船距海域中心点的距离
normal_vector=[sin(a),0,cos(a)];%坡面法向量

%船的位置
position=zeros(8,8,3);
for i=1:8  %b
    for j=1:8  %d
        
        position(i,j,1)=d(j)*cos(b(i));
        position(i,j,2)=d(j)*sin(b(i));
        position(i,j,3)=120;
    end
end


%两端波束方向向量
v1=ones(3,8);
for i=1:3
    for j=1:8
        if i==1
            v1(i,j)=-sin(b(j));
        elseif i==2
            v1(i,j)=cos(b(j));
        else
            v1(i,j)=-1/sqrt(3);
        end
    end
end
v2=-1*v1;
v2(3,:)=-1/sqrt(3);
v1=v1/vecnorm(v1(:,1));%一边的波束的单位方向向量
v2=v2/vecnorm(v2(:,1));%另一边的波束的单位方向向量


%两端的波束与海底平面的交点
q1=ones(8,8,3);%一边的波束与平面的交点
q2=ones(8,8,3);%另一边的波束与平面的交点
for i=1:8  %角度
    for j=1:8  %模长
        t=dot(normal_vector,-1*squeeze(position(i,j,:)))/dot(normal_vector,v1(:,i));
        q1(i,j,1)=squeeze(position(i,j,1))+t*v1(1,i);
        q1(i,j,2)=squeeze(position(i,j,2))+t*v1(2,i);
        q1(i,j,3)=squeeze(position(i,j,3))+t*v1(3,i);
    end
end
for i=1:8  %角度
    for j=1:8  %模长
        t=dot(normal_vector,-1*squeeze(position(i,j,:)))/dot(normal_vector,v2(:,i));
        q2(i,j,1)=squeeze(position(i,j,1))+t*v2(1,i);
        q2(i,j,2)=squeeze(position(i,j,2))+t*v2(2,i);
        q2(i,j,3)=squeeze(position(i,j,3))+t*v2(3,i);
    end
end

%覆盖宽度
width=ones(8,8);
for i=1:8
    for j=1:8
        width(i,j)=sqrt((q2(i,j,1)-q1(i,j,1))^2+(q2(i,j,2)-q1(i,j,2))^2+(q2(i,j,3)-q1(i,j,3))^2);
    end
end
width
