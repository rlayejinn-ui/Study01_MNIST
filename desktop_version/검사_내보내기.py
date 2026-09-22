# -*- coding: utf-8 -*-
"""
export_web.py 가 만든 웹용 파일이 올바른지 확인하는 검사

실행 방법 (desktop_version 폴더 기준):
    .venv\\Scripts\\python.exe 검사_내보내기.py

확인하는 것:
    1. weights.json 의 형식 버전, 정규화 상수, 층 이름·모양
    2. weights.bin 크기가 목록과 정확히 맞는지
    3. weights.bin 만으로 순전파한 확률이 원래 모델(평가 모드)과 1e-4 이내인지
    4. 기준값.json 의 확률이 원래 모델과 1e-5 이내인지
"""

import json
import os
import sys

import numpy as np
import torch
import torch.nn.functional as F

from model import MNIST_평균, MNIST_표준편차, 숫자인식CNN

프로젝트_폴더 = os.path.dirname(os.path.abspath(__file__))
웹_폴더 = os.path.join(프로젝트_폴더, "..", "web_version")
목록_파일 = os.path.join(웹_폴더, "model", "weights.json")
이진_파일 = os.path.join(웹_폴더, "model", "weights.bin")
기준값_파일 = os.path.join(웹_폴더, "tests", "기준값.json")

기대_층 = [
    ("합성곱1", "합성곱", [32, 1, 3, 3]),
    ("합성곱2", "합성곱", [32, 32, 3, 3]),
    ("합성곱3", "합성곱", [64, 32, 3, 3]),
    ("합성곱4", "합성곱", [64, 64, 3, 3]),
    ("완전연결1", "완전연결", [128, 3136]),
    ("완전연결2", "완전연결", [10, 128]),
]


def 확인(조건, 메시지):
    if not 조건:
        print(f"[실패] {메시지}")
        sys.exit(1)
    print(f"[통과] {메시지}")


def 텐서_꺼내기(전체, 정보):
    """weights.bin 전체 배열에서 한 텐서를 잘라 원래 모양으로 돌려줍니다."""
    조각 = 전체[정보["시작"]: 정보["시작"] + 정보["개수"]]
    return torch.from_numpy(조각.copy()).reshape(정보["모양"])


def 이진_가중치로_추론(층들, 입력):
    """weights.bin 에서 읽은 (접힌) 가중치만으로 순전파합니다."""
    x = 입력
    x = F.relu(F.conv2d(x, *층들["합성곱1"], padding=1))
    x = F.max_pool2d(F.relu(F.conv2d(x, *층들["합성곱2"], padding=1)), 2)
    x = F.relu(F.conv2d(x, *층들["합성곱3"], padding=1))
    x = F.max_pool2d(F.relu(F.conv2d(x, *층들["합성곱4"], padding=1)), 2)
    x = F.relu(F.linear(x.flatten(1), *층들["완전연결1"]))
    return F.softmax(F.linear(x, *층들["완전연결2"]), dim=1)


def main():
    확인(os.path.exists(목록_파일) and os.path.exists(이진_파일), "weights.json / weights.bin 파일이 있다")
    with open(목록_파일, encoding="utf-8") as 파일:
        목록 = json.load(파일)
    전체 = np.fromfile(이진_파일, dtype="<f4")

    확인(목록["형식_버전"] == 1, "형식_버전이 1이다")
    확인(abs(목록["정규화"]["평균"] - MNIST_평균) < 1e-12
         and abs(목록["정규화"]["표준편차"] - MNIST_표준편차) < 1e-12, "정규화 상수가 model.py 와 같다")
    확인([(층["이름"], 층["종류"], 층["가중치"]["모양"]) for 층 in 목록["층"]] == 기대_층, "층 이름·종류·모양이 기대와 같다")

    끝 = max(max(층["가중치"]["시작"] + 층["가중치"]["개수"], 층["편향"]["시작"] + 층["편향"]["개수"]) for 층 in 목록["층"])
    확인(끝 == len(전체), f"weights.bin 원소 수({len(전체)})가 목록의 끝 위치({끝})와 같다")

    층들 = {층["이름"]: (텐서_꺼내기(전체, 층["가중치"]), 텐서_꺼내기(전체, 층["편향"])) for 층 in 목록["층"]}

    확인(os.path.exists(기준값_파일), "기준값.json 파일이 있다")
    with open(기준값_파일, encoding="utf-8") as 파일:
        기준 = json.load(파일)
    확인(len(기준["입력"]) == 20 and all(len(행) == 784 for 행 in 기준["입력"]), "기준 입력이 20장 x 784 이다")

    모델 = 숫자인식CNN()
    모델.load_state_dict(torch.load(os.path.join(프로젝트_폴더, "mnist_cnn.pt"), map_location="cpu", weights_only=True))
    모델.eval()
    입력 = torch.tensor(기준["입력"], dtype=torch.float32).reshape(-1, 1, 28, 28)
    with torch.no_grad():
        원래_확률 = F.softmax(모델(입력), dim=1)
        이진_확률 = 이진_가중치로_추론(층들, 입력)
    기준_확률 = torch.tensor(기준["확률"], dtype=torch.float32)

    차이1 = (원래_확률 - 기준_확률).abs().max().item()
    확인(차이1 <= 1e-5, f"기준값 확률이 원래 모델과 같다 (최대 차이 {차이1:.2e})")
    차이2 = (원래_확률 - 이진_확률).abs().max().item()
    확인(차이2 <= 1e-4, f"weights.bin 순전파가 원래 모델과 같다 (최대 차이 {차이2:.2e})")
    확인(torch.equal(원래_확률.argmax(1), 이진_확률.argmax(1)), "예측 숫자가 모두 같다")
    print("모든 검사 통과")


if __name__ == "__main__":
    main()
