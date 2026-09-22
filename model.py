# -*- coding: utf-8 -*-
"""손글씨 숫자 인식을 위한 CNN 모델 정의"""

import torch.nn as nn

# MNIST 데이터셋 픽셀의 평균과 표준편차 (정규화에 사용)
MNIST_평균 = 0.1307
MNIST_표준편차 = 0.3081


class 숫자인식CNN(nn.Module):
    """
    28x28 흑백 이미지를 입력받아 0~9 중 어떤 숫자인지 분류하는 합성곱 신경망

    구조:
        [합성곱 → 배치정규화 → ReLU] x2 → 최대풀링   (28x28 → 14x14)
        [합성곱 → 배치정규화 → ReLU] x2 → 최대풀링   (14x14 → 7x7)
        완전연결층 → 드롭아웃 → 출력층(10개)
    """

    def __init__(self):
        super().__init__()
        self.특징추출 = nn.Sequential(
            # 첫 번째 블록: 1채널 → 32채널
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Conv2d(32, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),
            # 두 번째 블록: 32채널 → 64채널
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        self.분류기 = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 7 * 7, 128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, 10),
        )

    def forward(self, x):
        x = self.특징추출(x)
        return self.분류기(x)
