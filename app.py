# -*- coding: utf-8 -*-
"""
손글씨 숫자 인식 프로그램 (그림판 GUI)

실행 방법:
    python app.py

사용법:
    - 왼쪽 캔버스에 마우스로 숫자(0~9)를 하나 그립니다.
    - 마우스 버튼을 떼면 자동으로 인식 결과가 표시됩니다.
    - [지우기] 버튼 또는 오른쪽 클릭으로 캔버스를 비웁니다.

먼저 train.py 를 실행해 mnist_cnn.pt 가중치 파일을 만들어 두어야 합니다.

파일 탐색기에서 app.py 를 더블클릭해도 실행됩니다.
(PyTorch 가 설치된 .venv 의 Python 으로 자동으로 다시 실행합니다.)
"""

import os
import subprocess
import sys

# 이 파일이 있는 폴더 (더블클릭으로 실행해도 경로가 어긋나지 않도록 기준으로 삼습니다)
프로젝트_폴더 = os.path.dirname(os.path.abspath(__file__))


def 가상환경으로_다시_실행():
    """
    더블클릭하면 PyTorch 가 없는 기본 Python 으로 실행될 수 있습니다.
    그럴 때는 .venv 의 pythonw.exe(콘솔 창 없는 Python)로 이 파일을 다시 실행하고
    지금 프로세스는 끝냅니다.
    """
    가상환경_폴더 = os.path.join(프로젝트_폴더, ".venv")
    if os.path.normcase(sys.prefix) == os.path.normcase(가상환경_폴더):
        return  # 이미 가상환경에서 실행 중
    가상환경_파이썬 = os.path.join(가상환경_폴더, "Scripts", "pythonw.exe")
    if not os.path.exists(가상환경_파이썬):
        return  # 가상환경이 없으면 지금 Python 으로 그대로 시도
    subprocess.Popen([가상환경_파이썬, os.path.abspath(__file__)], cwd=프로젝트_폴더)
    sys.exit(0)


if __name__ == "__main__":
    가상환경으로_다시_실행()

import tkinter as tk

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageDraw

from model import MNIST_평균, MNIST_표준편차, 숫자인식CNN

가중치_파일 = os.path.join(프로젝트_폴더, "mnist_cnn.pt")
캔버스_크기 = 280   # 화면에 보이는 캔버스 크기 (픽셀)
펜_두께 = 18        # 붓 굵기


def 가중치_불러오기():
    """저장된 가중치를 읽어 평가 모드의 모델을 돌려줍니다."""
    if not os.path.exists(가중치_파일):
        raise FileNotFoundError(f"'{가중치_파일}' 파일이 없습니다. 먼저 train.py 를 실행하세요.")
    모델 = 숫자인식CNN()
    모델.load_state_dict(torch.load(가중치_파일, map_location="cpu", weights_only=True))
    모델.eval()
    return 모델


def 전처리(그림: Image.Image) -> torch.Tensor:
    """
    사용자가 그린 이미지를 MNIST 형식(28x28, 가운데 정렬)으로 변환합니다.

    MNIST 숫자는 20x20 상자 안에 비율을 유지한 채 들어가 있고,
    무게중심이 28x28 이미지의 중앙에 오도록 배치되어 있습니다.
    같은 방식으로 맞춰 주어야 인식률이 높아집니다.
    """
    배열 = np.array(그림, dtype=np.float32)  # 검은 배경(0) + 흰 글씨(255)

    # 1) 글씨가 있는 영역만 잘라내기
    행들 = np.where(배열.max(axis=1) > 0)[0]
    열들 = np.where(배열.max(axis=0) > 0)[0]
    if len(행들) == 0:
        return None  # 아무것도 그리지 않음
    잘린 = 그림.crop((열들[0], 행들[0], 열들[-1] + 1, 행들[-1] + 1))

    # 2) 비율을 유지하며 긴 변을 20픽셀로 줄이기
    가로, 세로 = 잘린.size
    배율 = 20.0 / max(가로, 세로)
    새_가로 = max(1, round(가로 * 배율))
    새_세로 = max(1, round(세로 * 배율))
    작은 = 잘린.resize((새_가로, 새_세로), Image.LANCZOS)

    # 3) 28x28 검은 바탕 가운데에 붙이기
    바탕 = Image.new("L", (28, 28), 0)
    바탕.paste(작은, ((28 - 새_가로) // 2, (28 - 새_세로) // 2))

    # 4) 무게중심이 정중앙(14, 14)에 오도록 이동
    배열 = np.array(바탕, dtype=np.float32)
    전체 = 배열.sum()
    y좌표, x좌표 = np.indices(배열.shape)
    중심_y = (y좌표 * 배열).sum() / 전체
    중심_x = (x좌표 * 배열).sum() / 전체
    이동_x = int(round(14 - 중심_x))
    이동_y = int(round(14 - 중심_y))
    바탕 = 바탕.transform((28, 28), Image.AFFINE, (1, 0, -이동_x, 0, 1, -이동_y))

    # 5) 텐서로 바꾸고 학습 때와 같은 방식으로 정규화
    텐서 = torch.from_numpy(np.array(바탕, dtype=np.float32) / 255.0)
    텐서 = (텐서 - MNIST_평균) / MNIST_표준편차
    return 텐서.unsqueeze(0).unsqueeze(0)  # 모양: (1, 1, 28, 28)


@torch.no_grad()
def 예측(모델, 그림: Image.Image):
    """그림을 인식해 (숫자별 확률 배열)을 돌려줍니다. 빈 그림이면 None."""
    입력 = 전처리(그림)
    if 입력 is None:
        return None
    확률 = F.softmax(모델(입력), dim=1)[0]
    return 확률.numpy()


class 손글씨앱:
    """마우스로 숫자를 그리면 인식 결과를 보여주는 GUI"""

    def __init__(self, 창, 모델):
        self.모델 = 모델
        self.창 = 창
        창.title("손글씨 숫자 인식기 (MNIST CNN)")
        창.resizable(False, False)

        # 화면용 캔버스와 별도로, 모델에 넣을 이미지를 PIL 로 함께 그립니다.
        self.그림 = Image.new("L", (캔버스_크기, 캔버스_크기), 0)
        self.붓 = ImageDraw.Draw(self.그림)
        self.이전_좌표 = None

        # ----- 왼쪽: 그림 그리는 영역 -----
        왼쪽 = tk.Frame(창, padx=10, pady=10)
        왼쪽.grid(row=0, column=0)
        tk.Label(왼쪽, text="여기에 숫자를 그려 주세요", font=("맑은 고딕", 12)).pack()
        self.캔버스 = tk.Canvas(왼쪽, width=캔버스_크기, height=캔버스_크기,
                              bg="black", cursor="cross", highlightthickness=0)
        self.캔버스.pack(pady=5)
        tk.Button(왼쪽, text="지우기", font=("맑은 고딕", 11), width=12,
                  command=self.지우기).pack()

        # ----- 오른쪽: 결과 표시 영역 -----
        오른쪽 = tk.Frame(창, padx=10, pady=10)
        오른쪽.grid(row=0, column=1, sticky="n")
        tk.Label(오른쪽, text="인식 결과", font=("맑은 고딕", 12)).pack()
        self.결과_글자 = tk.Label(오른쪽, text="?", font=("맑은 고딕", 64, "bold"), width=3)
        self.결과_글자.pack()
        self.신뢰도_글자 = tk.Label(오른쪽, text="", font=("맑은 고딕", 11))
        self.신뢰도_글자.pack()

        # 숫자별 확률 막대그래프
        self.막대_캔버스 = tk.Canvas(오른쪽, width=220, height=200, highlightthickness=0)
        self.막대_캔버스.pack(pady=5)
        self.막대그래프_그리기(np.zeros(10))

        # 마우스 이벤트 연결
        self.캔버스.bind("<Button-1>", self.그리기_시작)
        self.캔버스.bind("<B1-Motion>", self.그리는_중)
        self.캔버스.bind("<ButtonRelease-1>", self.그리기_끝)
        self.캔버스.bind("<Button-3>", lambda e: self.지우기())

    def 그리기_시작(self, 이벤트):
        self.이전_좌표 = (이벤트.x, 이벤트.y)
        self.점_찍기(이벤트.x, 이벤트.y)

    def 그리는_중(self, 이벤트):
        x, y = 이벤트.x, 이벤트.y
        if self.이전_좌표:
            px, py = self.이전_좌표
            # 화면 캔버스와 PIL 이미지에 똑같이 선을 그립니다.
            self.캔버스.create_line(px, py, x, y, fill="white", width=펜_두께,
                                   capstyle=tk.ROUND, smooth=True)
            self.붓.line([px, py, x, y], fill=255, width=펜_두께)
        self.점_찍기(x, y)
        self.이전_좌표 = (x, y)

    def 점_찍기(self, x, y):
        반지름 = 펜_두께 // 2
        self.캔버스.create_oval(x - 반지름, y - 반지름, x + 반지름, y + 반지름,
                               fill="white", outline="white")
        self.붓.ellipse([x - 반지름, y - 반지름, x + 반지름, y + 반지름], fill=255)

    def 그리기_끝(self, 이벤트):
        self.이전_좌표 = None
        self.인식하기()

    def 인식하기(self):
        확률 = 예측(self.모델, self.그림)
        if 확률 is None:
            return
        숫자 = int(확률.argmax())
        self.결과_글자.config(text=str(숫자))
        self.신뢰도_글자.config(text=f"확신도: {확률[숫자] * 100:.1f}%")
        self.막대그래프_그리기(확률)

    def 막대그래프_그리기(self, 확률):
        """0~9 각 숫자의 확률을 가로 막대로 그립니다."""
        c = self.막대_캔버스
        c.delete("all")
        최고 = int(확률.argmax()) if 확률.sum() > 0 else -1
        for i, p in enumerate(확률):
            y = 5 + i * 19
            c.create_text(10, y + 7, text=str(i), font=("맑은 고딕", 10))
            c.create_rectangle(25, y, 25 + 150, y + 14, outline="#cccccc")
            색 = "#2e7d32" if i == 최고 else "#90a4ae"
            if p > 0:
                c.create_rectangle(25, y, 25 + 150 * p, y + 14, fill=색, outline="")
            c.create_text(215, y + 7, text=f"{p * 100:.0f}%", anchor="e", font=("맑은 고딕", 9))

    def 지우기(self):
        self.캔버스.delete("all")
        self.붓.rectangle([0, 0, 캔버스_크기, 캔버스_크기], fill=0)
        self.결과_글자.config(text="?")
        self.신뢰도_글자.config(text="")
        self.막대그래프_그리기(np.zeros(10))


def main():
    창 = tk.Tk()
    try:
        모델 = 가중치_불러오기()
    except FileNotFoundError as 오류:
        # 더블클릭 실행 시에는 콘솔 창이 없으므로 오류를 메시지 창으로 알려 줍니다.
        from tkinter import messagebox
        창.withdraw()
        messagebox.showerror("가중치 파일 없음", str(오류))
        return
    손글씨앱(창, 모델)
    창.mainloop()


if __name__ == "__main__":
    main()
