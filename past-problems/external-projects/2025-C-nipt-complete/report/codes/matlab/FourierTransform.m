% 读取音频文件
[audioIn, fs] = audioread('input.wav');

% 进行短时傅里叶变换
window = hamming(1024);
noverlap = 512;
nfft = 1024;
[S, F, T] = spectrogram(audioIn, window, noverlap, nfft, fs);

% 进行谱减法
noiseEstimate = mean(abs(S(:,1:10)), 2);
S_denoised = S - noiseEstimate;

% 进行逆短时傅里叶变换
audioOut = istft(S_denoised, fs, 'Window', window, 'OverlapLength', noverlap);

% 保存去噪后的音频
audiowrite('output.wav', audioOut, fs);