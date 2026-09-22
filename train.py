# -*- coding: utf-8 -*-
"""
MNIST 손글씨 숫자 인식 CNN 모델 학습 스크립트

실행 방법:
    python train.py

학습이 끝나면 가중치가 mnist_cnn.pt 파일로 저장됩니다.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from model import MNIST_평균, MNIST_표준편차, 숫자인식CNN

# ---------------------------------------------
# 학습 설정값
# ---------------------------------------------
배치_크기 = 128
에폭_수 = 5
학습률 = 1e-3
가중치_파일 = "mnist_cnn.pt"
데이터_경로 = "./data"


def 데이터_로더_만들기():
    """학습용/테스트용 MNIST 데이터 로더를 만듭니다."""
    # 학습 데이터에는 약간의 회전·이동·확대 변형을 주어
    # 사람이 직접 그린 삐뚤빼뚤한 글씨에도 잘 동작하도록 합니다.
    학습_변환 = transforms.Compose([
        transforms.RandomAffine(degrees=10, translate=(0.1, 0.1), scale=(0.9, 1.1)),
        transforms.ToTensor(),
        transforms.Normalize((MNIST_평균,), (MNIST_표준편차,)),
    ])
    테스트_변환 = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((MNIST_평균,), (MNIST_표준편차,)),
    ])

    학습_데이터 = datasets.MNIST(데이터_경로, train=True, download=True, transform=학습_변환)
    테스트_데이터 = datasets.MNIST(데이터_경로, train=False, download=True, transform=테스트_변환)

    학습_로더 = DataLoader(학습_데이터, batch_size=배치_크기, shuffle=True)
    테스트_로더 = DataLoader(테스트_데이터, batch_size=1000, shuffle=False)
    return 학습_로더, 테스트_로더


def 한_에폭_학습(모델, 로더, 최적화기, 장치, 에폭):
    """데이터 전체를 한 번 돌며 모델을 학습합니다."""
    모델.train()
    for 배치_번호, (이미지, 정답) in enumerate(로더):
        이미지, 정답 = 이미지.to(장치), 정답.to(장치)

        최적화기.zero_grad()
        출력 = 모델(이미지)
        손실 = F.cross_entropy(출력, 정답)
        손실.backward()
        최적화기.step()

        if 배치_번호 % 100 == 0:
            진행 = 배치_번호 * len(이미지)
            print(f"[에폭 {에폭}] {진행:5d}/{len(로더.dataset)} 손실: {손실.item():.4f}")


@torch.no_grad()
def 평가(모델, 로더, 장치):
    """테스트 데이터로 정확도를 측정합니다."""
    모델.eval()
    맞은_개수 = 0
    전체_손실 = 0.0
    for 이미지, 정답 in 로더:
        이미지, 정답 = 이미지.to(장치), 정답.to(장치)
        출력 = 모델(이미지)
        전체_손실 += F.cross_entropy(출력, 정답, reduction="sum").item()
        맞은_개수 += (출력.argmax(dim=1) == 정답).sum().item()

    개수 = len(로더.dataset)
    정확도 = 100.0 * 맞은_개수 / 개수
    print(f"테스트 평균 손실: {전체_손실 / 개수:.4f}, 정확도: {맞은_개수}/{개수} ({정확도:.2f}%)")
    return 정확도


def main():
    torch.manual_seed(42)
    장치 = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"사용 장치: {장치}")

    학습_로더, 테스트_로더 = 데이터_로더_만들기()
    모델 = 숫자인식CNN().to(장치)
    최적화기 = torch.optim.Adam(모델.parameters(), lr=학습률)
    # 에폭마다 학습률을 조금씩 줄여 안정적으로 수렴하게 합니다.
    스케줄러 = torch.optim.lr_scheduler.StepLR(최적화기, step_size=1, gamma=0.7)

    for 에폭 in range(1, 에폭_수 + 1):
        한_에폭_학습(모델, 학습_로더, 최적화기, 장치, 에폭)
        평가(모델, 테스트_로더, 장치)
        스케줄러.step()

    # 학습된 가중치 저장
    torch.save(모델.state_dict(), 가중치_파일)
    print(f"가중치를 '{가중치_파일}' 파일로 저장했습니다.")


if __name__ == "__main__":
    main()
