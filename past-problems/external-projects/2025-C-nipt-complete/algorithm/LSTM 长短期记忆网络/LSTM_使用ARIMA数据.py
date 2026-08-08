import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import seaborn as sns
import matplotlib.font_manager as fm
from cycler import cycler

# -- 图片预设，需要 plt, fm, cycler 库
import matplotlib.font_manager as fm
from cycler import cycler
import os

font_path = "../../utils/fonts/SourceHanSerifCN-Regular.otf"
if os.path.exists(font_path):
    fm.fontManager.addfont(font_path)
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rcParams['font.sans-serif'] = [font_name]
else:
    fallback_fonts = ['STZhongsong', 'SimHei', 'Microsoft YaHei', 'Heiti TC', 'PingFang SC', 'sans-serif']
    plt.rcParams['font.sans-serif'] = fallback_fonts

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


def preprocess_data(data):
    """对原始数据进行归一化处理"""
    data = np.array(data).reshape(-1, 1)
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)
    return scaled_data, scaler


def create_sequences(dataset, look_back: int):
    """为时间序列数据创建输入和输出序列"""
    X, y = [], []
    for i in range(len(dataset) - look_back):
        X.append(dataset[i:(i + look_back), 0])
        y.append(dataset[i + look_back, 0])
    return np.array(X), np.array(y)


def build_lstm_model(input_shape):
    """构建并编译 LSTM 模型。

    input_shape (tuple): 模型的输入形状, 例如 (look_back, 1)。

    Returns:
        tensorflow.keras.models.Sequential: 编译好的 LSTM 模型。
    """
    model = Sequential()
    model.add(LSTM(units=10, return_sequences=True, input_shape=input_shape))
    model.add(Dropout(0.2))
    model.add(LSTM(units=10))
    model.add(Dropout(0.2))
    model.add(Dense(units=1))
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.summary()
    return model


def plot_training_history(history, save_path="LSTM_training_loss.pdf"):
    """
    可视化模型的训练和验证损失。

    Args:
        history (History): model.fit() 返回的 History 对象。
        save_path (str): 图像保存路径。
    """
    train_loss = history.history['loss']
    val_loss = history.history['val_loss']
    epochs = range(1, len(train_loss) + 1)

    loss_df = pd.DataFrame({
        'Epoch': np.concatenate([epochs, epochs]),
        'Loss': np.concatenate([train_loss, val_loss]),
        'Type': ['训练损失 (Training Loss)'] * len(train_loss) + ['验证损失 (Validation Loss)'] * len(val_loss)
    })

    plt.figure(figsize=(10, 5))
    sns.lineplot(data=loss_df, x='Epoch', y='Loss', hue='Type', style='Type', markers=True)
    plt.title('模型训练过程中的损失变化')
    plt.xlabel('训练轮次 (Epoch)')
    plt.ylabel('损失 (Loss)')
    plt.grid(True)
    plt.savefig(save_path, format='pdf')
    plt.show()


def forecast_future(model, scaled_data, look_back, future_steps, scaler):
    """
    使用训练好的模型预测未来 N 步。

    Args:
        model: 训练好的模型。
        scaled_data (np.ndarray): 完整的归一化数据集。
        look_back (int): 时间步长。
        future_steps (int): 要预测的未来步数。
        scaler: 用于逆转换的 scaler 对象。

    Returns:
        np.ndarray: 预测的未来值（已逆转换）。
    """
    last_sequence = scaled_data[-look_back:]
    current_batch = last_sequence.reshape(1, look_back, 1)
    future_predictions = []

    for _ in range(future_steps):
        next_pred = model.predict(current_batch)[0]
        future_predictions.append(next_pred)
        # 移除序列的第一个值，并将新预测值追加到末尾
        current_batch = np.append(current_batch[:, 1:, :], [[next_pred]], axis=1)

    return scaler.inverse_transform(future_predictions)


def plot_predictions(original_data, train_predict, test_predict, future_predictions, look_back, train_size, save_path="LSTM_prediction_new.pdf"):
    """
    将原始数据、训练预测、测试预测和未来预测整合并可视化。

    Args:
        original_data (np.ndarray): 原始数据集。
        train_predict (np.ndarray): 训练集的预测值。
        test_predict (np.ndarray): 测试集的预测值。
        future_predictions (np.ndarray): 未来预测值。
        look_back (int): 时间步长。
        train_size (int): 训练集的大小。
        save_path (str): 图像保存路径。
    """
    # 1. 创建包含所有数据的长格式 DataFrame
    df_original = pd.DataFrame({
        '时间步': np.arange(len(original_data)),
        '值': original_data.flatten(),
        '类别': '原始数据'
    })

    train_predict_index = np.arange(look_back, look_back + train_size)
    df_train_predict = pd.DataFrame({
        '时间步': train_predict_index,
        '值': train_predict.flatten(),
        '类别': '训练集预测值'
    })

    test_predict_index = np.arange(look_back + train_size, len(original_data))
    df_test_predict = pd.DataFrame({
        '时间步': test_predict_index,
        '值': test_predict.flatten(),
        '类别': '测试集预测值'
    })

    future_index = np.arange(len(original_data), len(original_data) + len(future_predictions))
    df_future_predict = pd.DataFrame({
        '时间步': future_index,
        '值': future_predictions.flatten(),
        '类别': '未来预测'
    })

    combined_df = pd.concat([df_original, df_train_predict, df_test_predict, df_future_predict])

    # 2. 使用 Seaborn 绘图
    plt.figure(figsize=(15, 8))
    palette = {"原始数据": "lightgrey", "训练集预测值": "blue", "测试集预测值": "red", "未来预测": "green"}
    hue_order = ["原始数据", "训练集预测值", "测试集预测值", "未来预测"]

    sns.lineplot(
        data=combined_df,
        x='时间步',
        y='值',
        linewidth=2.5,
        hue='类别',
        style='类别',
        hue_order=hue_order,
        palette=palette,
        markers=False
    )

    plt.title('LSTM 模型完整预测结果', fontsize=16)
    plt.xlabel('时间步')
    plt.ylabel('值')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.legend(handlelength=2.5)
    plt.savefig(save_path, format='pdf')
    plt.show()


def main():
    ds = [10930, 10318, 10595, 10972, 7706, 6756, 9092, 10551, 9722, 10913, 11151, 8186, 6422,
          6337, 11649, 11652, 10310, 12043, 7937, 6476, 9662, 9570, 9981, 9331, 9449, 6773, 6304, 9355,
          10477, 10148, 10395, 11261, 8713, 7299, 10424, 10795, 11069, 11602, 11427, 9095, 7707, 10767,
          12136, 12812, 12006, 12528, 10329, 7818, 11719, 11683, 12603, 11495, 13670, 11337, 10232,
          13261, 13230, 15535, 16837, 19598, 14823, 11622, 19391, 18177, 19994, 14723, 15694, 13248,
          9543, 12872, 13101, 15053, 12619, 13749, 10228, 9725, 14729, 12518, 14564, 15085, 14722,
          11999, 9390, 13481, 14795, 15845, 15271, 14686, 11054, 10395]
    original_data = np.array(ds).reshape(-1, 1)

    look_back = 20
    split_ratio = 0.8
    epochs = 50
    batch_size = 16
    future_steps = 10

    # 2. 数据预处理
    scaled_data, scaler = preprocess_data(original_data)

    # 3. 创建时间序列
    X, y = create_sequences(scaled_data, look_back)

    # 4. 划分训练集和测试集
    train_size = int(len(X) * split_ratio)
    X_train, X_test = X[0:train_size], X[train_size:len(X)]
    y_train, y_test = y[0:train_size], y[train_size:len(y)]

    # 5. 重塑输入数据以满足LSTM的要求 [样本数, 时间步长, 特征数]
    X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))
    X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))

    # 6. 构建并训练模型
    model = build_lstm_model(input_shape=(look_back, 1))
    history = model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, validation_data=(X_test, y_test), verbose=1)

    # 7. 可视化训练过程
    plot_training_history(history)

    # 8. 在训练集和测试集上进行预测并逆转换
    train_predict = scaler.inverse_transform(model.predict(X_train))
    test_predict = scaler.inverse_transform(model.predict(X_test))

    # 9. 预测未来
    future_predictions = forecast_future(model, scaled_data, look_back, future_steps, scaler)

    # 10. 可视化所有结果
    plot_predictions(original_data, train_predict, test_predict, future_predictions, look_back, train_size)

    # 11. 打印未来预测值
    print(f"未来 {future_steps} 步的预测值为:")
    print(future_predictions.flatten())


if __name__ == '__main__':
    main()
