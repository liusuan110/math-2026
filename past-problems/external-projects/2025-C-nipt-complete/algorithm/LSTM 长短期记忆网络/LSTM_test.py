import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from cycler import cycler
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import matplotlib.font_manager as fm

fm.fontManager.addfont('../../utils/fonts/SourceHanSerifCN-Regular.otf')  # 添加字体
font_name = fm.FontProperties(fname='../../utils/fonts/SourceHanSerifCN-Regular.otf').get_name()
plt.rcParams['font.sans-serif'] = [font_name]
plt.rcParams['font.size'] = 14
plt.rcParams['axes.titlesize'] = 18
plt.rcParams['axes.labelsize'] = 16
plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 14
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'  # 保存后自动裁剪白边
plt.rcParams['lines.linewidth'] = 2
plt.rcParams['lines.markersize'] = 6
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['axes.prop_cycle'] = cycler(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'])
plt.rcParams['axes.unicode_minus'] = False

# --------------------------------------------------
# 步驟 2: 生成帶有噪聲的正弦波數據
# --------------------------------------------------
# 我們創建一個正弦波，並給它加上一些隨機噪聲，讓數據更接近真實世界
time_steps = np.linspace(0, 100, 500) # 生成0到100之間的500個時間點
data = np.sin(time_steps) + np.random.normal(scale=0.1, size=len(time_steps)) # 計算正弦值並加入噪聲

# 數據可視化
plt.figure(figsize=(12, 6))
plt.plot(time_steps, data, label='帶噪聲的正弦波數據')
plt.title('生成的原始數據')
plt.xlabel('時間步')
plt.ylabel('值')
plt.legend()
plt.grid(True)
plt.show()
# --------------------------------------------------
# 步驟 3: 數據預處理 (最關鍵的一步)
# --------------------------------------------------
# 1. 數據縮放
# 感觉没必要，所以我把这部分删了
data=data.reshape(-1, 1)
# 2. 創建時間序列數據集
# 這是為LSTM準備數據的標準方法：使用過去的一段時間序列（X）來預測下一個時間點的值（y）
def create_dataset(dataset, look_back=10):
    X, y = [], []
    for i in range(len(dataset) - look_back - 1):
        # look_back是我們用來預測的時間步長度，也叫“滑動窗口”
        a = dataset[i:(i + look_back), 0]
        X.append(a)
        y.append(dataset[i + look_back, 0])
    return np.array(X), np.array(y)
look_back = 20 # 我們用過去20個時間點的數據來預測下1個點
X, y = create_dataset(data, look_back)

# 3. 劃分訓練集和測試集
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

# 4. 重塑輸入數據以滿足LSTM的要求 [樣本數, 時間步長, 特徵數]
X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))
X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))

# --------------------------------------------------
# 步驟 4: 構建 LSTM 模型
# --------------------------------------------------
model = Sequential()
# 添加一個LSTM層，50個神經元。input_shape告訴模型輸入數據的形狀
model.add(LSTM(units=50, return_sequences=True, input_shape=(look_back, 1)))
model.add(LSTM(units=50))
# 添加一個全連接層作為輸出層，因為我們只預測一個值，所以只有1個神經元
model.add(Dense(units=1))

# 編譯模型：指定優化器和損失函數
model.compile(optimizer='adam', loss='mean_squared_error')

model.summary()
# --------------------------------------------------
# 步驟 5: 訓練模型
# --------------------------------------------------
# validation_split=0.1 會自動從訓練集中分出一部分做驗證，方便我們觀察模型是否過擬合
history = model.fit(X_train, y_train, epochs=25, batch_size=32, validation_split=0.1, verbose=1)

# 可視化訓練過程中的損失變化
plt.figure(figsize=(10, 5))
plt.plot(history.history['loss'], label='訓練損失 (Training Loss)')
plt.plot(history.history['val_loss'], label='驗證損失 (Validation Loss)')
plt.title('模型訓練過程中的損失變化')
plt.xlabel('訓練輪次 (Epoch)')
plt.ylabel('損失 (Loss)')
plt.legend()
plt.grid(True)
plt.show()

# --------------------------------------------------
# 步驟 6: 進行預測並評估模型
# --------------------------------------------------
# 在測試集上進行預測
train_predict = model.predict(X_train)
test_predict = model.predict(X_test)
# --------------------------------------------------
# 步骤 7: 可视化预测结果 (修正版)
# --------------------------------------------------
plt.figure(figsize=(15, 8))
# 绘制原始的完整数据
plt.plot(data, label='原始完整数据', color='grey', alpha=0.6)
# --- 绘制训练集的预测 ---
# 创建一个和原始数据一样大小的NaN数组，用于放置训练集预测值
train_predict_plot = np.empty_like(data)
train_predict_plot[:, :] = np.nan
# 将训练集预测值填充到正确的位置
train_predict_plot[look_back:len(train_predict) + look_back, :] = train_predict
# 绘制
plt.plot(train_predict_plot, label='训练集预测值', color='blue')

# --- 绘制测试集的预测 (这是修正的核心) ---
# 创建一个和原始数据一样大小的NaN数组，用于放置测试集预测值
test_predict_plot = np.empty_like(data)
test_predict_plot[:, :] = np.nan
# 将测试集预测值填充到正确的位置
test_predict_plot[len(train_predict) + look_back:len(train_predict) + look_back + len(test_predict), :] = test_predict
# 绘制
plt.plot(test_predict_plot, label='测试集预测值', color='red')
plt.title('LSTM 对正弦波的预测结果展示 (修正后)', fontsize=16)
plt.xlabel('时间步')
plt.ylabel('值')
plt.legend()
plt.grid(True)
plt.savefig("LSTM_prediction.jpg",dpi=300)
plt.show()