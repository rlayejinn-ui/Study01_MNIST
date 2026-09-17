"""
MNIST 손글씨 숫자 인식용 CNN 모델 정의 모듈.

학습(train.py)과 추론(draw_app.py)이 동일한 구조를 공유하도록
모델 클래스를 별도 파일로 분리했다.
"""

import torch.nn as nn
import torch.nn.functional as F


class MnistCNN(nn.Module):
    """28x28 흑백 손글씨 숫자 이미지를 0~9로 분류하는 합성곱 신경망."""

    def __init__(self):
        super().__init__()
        # 첫 번째 합성곱: 입력 1채널(흑백) -> 32채널, 3x3 커널
        self.합성곱1 = nn.Conv2d(1, 32, kernel_size=3)
        # 두 번째 합성곱: 32채널 -> 64채널, 3x3 커널
        self.합성곱2 = nn.Conv2d(32, 64, kernel_size=3)
        # 과적합을 막기 위한 드롭아웃
        self.드롭아웃1 = nn.Dropout(0.25)
        self.드롭아웃2 = nn.Dropout(0.5)
        # 완전연결층: 12*12*64 = 9216 차원 -> 128 차원
        self.완전연결1 = nn.Linear(9216, 128)
        # 최종 출력층: 128 차원 -> 10개 숫자(0~9)
        self.완전연결2 = nn.Linear(128, 10)

    def forward(self, 입력):
        """순전파. 입력 형태: (배치, 1, 28, 28) -> 출력: (배치, 10) 로그확률."""
        출력 = F.relu(self.합성곱1(입력))    # (배치, 32, 26, 26)
        출력 = F.relu(self.합성곱2(출력))    # (배치, 64, 24, 24)
        출력 = F.max_pool2d(출력, 2)         # (배치, 64, 12, 12)
        출력 = self.드롭아웃1(출력)
        출력 = output_flatten(출력)          # (배치, 9216)
        출력 = F.relu(self.완전연결1(출력))
        출력 = self.드롭아웃2(출력)
        출력 = self.완전연결2(출력)          # (배치, 10)
        # 로그 소프트맥스를 적용해 로그 확률을 반환 (NLL 손실과 짝을 이룸)
        return F.log_softmax(출력, dim=1)


def output_flatten(텐서):
    """합성곱 출력 텐서를 완전연결층 입력용 2차원 텐서로 펼친다."""
    return 텐서.flatten(1)
