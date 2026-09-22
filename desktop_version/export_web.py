# -*- coding: utf-8 -*-
"""
학습된 가중치(mnist_cnn.pt)를 웹 버전이 읽을 수 있는 형식으로 내보내는 스크립트

실행 방법 (desktop_version 폴더 기준):
    .venv\\Scripts\\python.exe export_web.py

만드는 파일:
    ../web_version/model/weights.bin    모든 가중치 (float32, 리틀 엔디언)
    ../web_version/model/weights.json   층 이름·모양·위치 목록과 정규화 상수
    ../web_version/tests/기준값.json    웹 추론 검사용 PyTorch 기준 입력·확률

배치정규화는 바로 앞의 합성곱에 미리 합쳐(접어) 내보냅니다.
그래서 웹에서는 합성곱·ReLU·최대풀링·완전연결·소프트맥스만 구현하면 됩니다.
"""

import json
import os
import sys

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import datasets, transforms

from model import MNIST_평균, MNIST_표준편차, 숫자인식CNN

프로젝트_폴더 = os.path.dirname(os.path.abspath(__file__))
가중치_파일 = os.path.join(프로젝트_폴더, "mnist_cnn.pt")
데이터_경로 = os.path.join(프로젝트_폴더, "data")
웹_폴더 = os.path.join(프로젝트_폴더, "..", "web_version")
모델_폴더 = os.path.join(웹_폴더, "model")
검사_폴더 = os.path.join(웹_폴더, "tests")

기준값_개수 = 20       # 기준값으로 저장할 MNIST 테스트 이미지 수
접기_허용_오차 = 1e-5  # 접은 모델과 원래 모델의 허용 차이


def 배치정규화_접기(합성곱: nn.Conv2d, 정규화: nn.BatchNorm2d):
    """
    합성곱 뒤의 배치정규화를 합성곱 하나로 합칩니다 (평가 모드 기준).

        배율 = γ / sqrt(σ² + ε)
        W' = W × 배율 (출력 채널별)
        b' = (b − μ) × 배율 + β
    """
    배율 = 정규화.weight / torch.sqrt(정규화.running_var + 정규화.eps)
    가중치 = 합성곱.weight * 배율.reshape(-1, 1, 1, 1)
    편향 = (합성곱.bias - 정규화.running_mean) * 배율 + 정규화.bias
    return 가중치.detach().contiguous(), 편향.detach().contiguous()


def 층_목록_만들기(모델: 숫자인식CNN):
    """모델에서 (이름, 종류, 가중치, 편향) 6개 층을 순서대로 뽑습니다."""
    특징 = 모델.특징추출   # [합성곱, BN, ReLU, 합성곱, BN, ReLU, 풀링, 합성곱, BN, ReLU, 합성곱, BN, ReLU, 풀링]
    분류 = 모델.분류기     # [펼치기, 완전연결, ReLU, 드롭아웃, 완전연결]
    층들 = []
    for 번호, (합성곱_위치, 정규화_위치) in enumerate([(0, 1), (3, 4), (7, 8), (10, 11)], start=1):
        가중치, 편향 = 배치정규화_접기(특징[합성곱_위치], 특징[정규화_위치])
        층들.append((f"합성곱{번호}", "합성곱", 가중치, 편향))
    층들.append(("완전연결1", "완전연결", 분류[1].weight.detach(), 분류[1].bias.detach()))
    층들.append(("완전연결2", "완전연결", 분류[4].weight.detach(), 분류[4].bias.detach()))
    return 층들


def 접은_모델로_추론(층들, 입력):
    """접은 가중치로 로짓을 계산합니다 (원래 모델과 비교용)."""
    (_, _, w1, b1), (_, _, w2, b2), (_, _, w3, b3), (_, _, w4, b4), (_, _, w5, b5), (_, _, w6, b6) = 층들
    x = F.relu(F.conv2d(입력, w1, b1, padding=1))
    x = F.max_pool2d(F.relu(F.conv2d(x, w2, b2, padding=1)), 2)
    x = F.relu(F.conv2d(x, w3, b3, padding=1))
    x = F.max_pool2d(F.relu(F.conv2d(x, w4, b4, padding=1)), 2)
    x = F.relu(F.linear(x.flatten(1), w5, b5))
    return F.linear(x, w6, b6)


def 기준_이미지_불러오기():
    """MNIST 테스트 이미지 앞부분을 학습 때와 같은 정규화로 불러옵니다."""
    변환 = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((MNIST_평균,), (MNIST_표준편차,)),
    ])
    테스트_데이터 = datasets.MNIST(데이터_경로, train=False, download=True, transform=변환)
    이미지들 = torch.stack([테스트_데이터[번호][0] for 번호 in range(기준값_개수)])
    정답들 = [int(테스트_데이터[번호][1]) for 번호 in range(기준값_개수)]
    return 이미지들, 정답들


def 가중치_파일_쓰기(층들):
    """weights.bin 과 weights.json 을 씁니다."""
    조각들 = []
    목록 = []
    위치 = 0

    def 추가(텐서):
        nonlocal 위치
        배열 = 텐서.numpy().astype("<f4").ravel()
        정보 = {"모양": list(텐서.shape), "시작": 위치, "개수": int(배열.size)}
        조각들.append(배열)
        위치 += int(배열.size)
        return 정보

    for 이름, 종류, 가중치, 편향 in 층들:
        목록.append({"이름": 이름, "종류": 종류, "가중치": 추가(가중치), "편향": 추가(편향)})

    os.makedirs(모델_폴더, exist_ok=True)
    np.concatenate(조각들).tofile(os.path.join(모델_폴더, "weights.bin"))
    with open(os.path.join(모델_폴더, "weights.json"), "w", encoding="utf-8") as 파일:
        json.dump({
            "형식_버전": 1,
            "정규화": {"평균": MNIST_평균, "표준편차": MNIST_표준편차},
            "층": 목록,
        }, 파일, ensure_ascii=False, indent=2)
    return 위치


def main():
    모델 = 숫자인식CNN()
    모델.load_state_dict(torch.load(가중치_파일, map_location="cpu", weights_only=True))
    모델.eval()  # 배치정규화를 학습 통계(running_mean/var)로 고정

    층들 = 층_목록_만들기(모델)
    이미지들, 정답들 = 기준_이미지_불러오기()

    # 접은 모델이 원래 모델과 같은 결과를 내는지 먼저 확인합니다.
    with torch.no_grad():
        원래_로짓 = 모델(이미지들)
        접은_로짓 = 접은_모델로_추론(층들, 이미지들)
    차이 = (원래_로짓 - 접은_로짓).abs().max().item()
    print(f"배치정규화 접기 확인: 최대 로짓 차이 {차이:.2e}")
    if 차이 > 접기_허용_오차:
        print(f"오류: 차이가 허용 오차 {접기_허용_오차} 보다 큽니다. 내보내기를 중단합니다.")
        sys.exit(1)

    원소_수 = 가중치_파일_쓰기(층들)
    print(f"weights.bin 저장: float32 {원소_수:,}개 ({원소_수 * 4 / 1024 / 1024:.2f} MB)")

    확률들 = F.softmax(원래_로짓, dim=1)
    os.makedirs(검사_폴더, exist_ok=True)
    with open(os.path.join(검사_폴더, "기준값.json"), "w", encoding="utf-8") as 파일:
        json.dump({
            "입력": 이미지들.reshape(기준값_개수, -1).tolist(),
            "확률": 확률들.tolist(),
            "정답": 정답들,
        }, 파일, ensure_ascii=False)
    print(f"기준값.json 저장: 이미지 {기준값_개수}장")
    print("내보내기 완료")


if __name__ == "__main__":
    main()
