"""
마우스로 숫자를 그리면 학습된 CNN이 숫자를 인식해 주는 GUI 프로그램.

실행 방법:
    python draw_app.py

사전 조건: train.py를 먼저 실행해 mnist_cnn.pt 파일이 만들어져 있어야 한다.
"""

import sys
import tkinter as tk
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageDraw

from model import MnistCNN

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ----- 설정 값 -----
현재폴더 = Path(__file__).resolve().parent
가중치경로 = 현재폴더 / "mnist_cnn.pt"
캔버스크기 = 280          # 그림판 한 변의 픽셀 크기 (28의 10배)
붓굵기 = 20               # 마우스로 그릴 때의 선 굵기


def 모델_불러오기(장치):
    """저장된 가중치를 읽어 추론 모드의 모델을 반환한다."""
    if not 가중치경로.exists():
        raise FileNotFoundError(
            f"가중치 파일을 찾을 수 없습니다: {가중치경로}\n"
            f"먼저 'python train.py'를 실행해 학습을 마쳐 주세요."
        )
    모델 = MnistCNN().to(장치)
    모델.load_state_dict(torch.load(가중치경로, map_location=장치))
    모델.eval()  # 드롭아웃을 끄고 추론 모드로 전환
    return 모델


def 손글씨_전처리(원본이미지):
    """
    사용자가 그린 이미지를 MNIST 형식(28x28)에 맞게 변환한다.

    MNIST는 숫자를 20x20 상자에 맞춘 뒤, 무게중심을 기준으로
    28x28 이미지의 한가운데에 배치한 데이터셋이므로 같은 방식을 따른다.
    반환값: (1, 1, 28, 28) 형태의 정규화된 텐서. 그린 내용이 없으면 None.
    """
    배열 = np.array(원본이미지, dtype=np.float32)  # 배경 0, 글씨 255

    # 글씨가 있는 픽셀의 좌표를 찾아 바깥 여백을 잘라낸다
    좌표 = np.argwhere(배열 > 0)
    if 좌표.size == 0:
        return None  # 아무것도 그리지 않은 경우

    위, 왼쪽 = 좌표.min(axis=0)
    아래, 오른쪽 = 좌표.max(axis=0)
    잘린이미지 = 원본이미지.crop((왼쪽, 위, 오른쪽 + 1, 아래 + 1))

    # 가로세로 비율을 유지한 채 긴 변이 20픽셀이 되도록 축소
    너비, 높이 = 잘린이미지.size
    비율 = 20.0 / max(너비, 높이)
    새너비 = max(1, int(round(너비 * 비율)))
    새높이 = max(1, int(round(높이 * 비율)))
    축소이미지 = 잘린이미지.resize((새너비, 새높이), Image.LANCZOS)

    # 28x28 검은 배경 한가운데에 붙인 뒤, 무게중심 기준으로 다시 정렬
    도화지 = Image.new("L", (28, 28), 0)
    도화지.paste(축소이미지, ((28 - 새너비) // 2, (28 - 새높이) // 2))

    배열28 = np.array(도화지, dtype=np.float32)
    총합 = 배열28.sum()
    if 총합 > 0:
        세로중심, 가로중심 = np.array(
            [(np.arange(28) * 배열28.sum(axis=1)).sum(),
             (np.arange(28) * 배열28.sum(axis=0)).sum()]
        ) / 총합
        세로이동 = int(round(13.5 - 세로중심))
        가로이동 = int(round(13.5 - 가로중심))
        배열28 = np.roll(배열28, (세로이동, 가로이동), axis=(0, 1))

    # 0~1 범위로 바꾼 뒤 학습 때와 동일한 평균/표준편차로 정규화
    정규화 = (배열28 / 255.0 - 0.1307) / 0.3081
    return torch.from_numpy(정규화).unsqueeze(0).unsqueeze(0)


class 손글씨인식앱:
    """그림판, 인식 버튼, 확률 막대그래프로 구성된 메인 창."""

    def __init__(self, 루트, 모델, 장치):
        self.루트 = 루트
        self.모델 = 모델
        self.장치 = 장치
        self.이전좌표 = None

        루트.title("손글씨 숫자 인식기 (MNIST CNN)")
        루트.resizable(False, False)

        전체틀 = tk.Frame(루트, padx=12, pady=12)
        전체틀.pack()

        # ----- 왼쪽: 그림판 영역 -----
        왼쪽틀 = tk.Frame(전체틀)
        왼쪽틀.grid(row=0, column=0, padx=(0, 12))

        tk.Label(왼쪽틀, text="아래 검은 칸에 숫자를 크게 하나 그리세요",
                 font=("맑은 고딕", 10)).pack(pady=(0, 6))

        self.캔버스 = tk.Canvas(왼쪽틀, width=캔버스크기, height=캔버스크기,
                               bg="black", cursor="crosshair",
                               highlightthickness=1, highlightbackground="#888")
        self.캔버스.pack()
        self.캔버스.bind("<B1-Motion>", self.그리기)
        self.캔버스.bind("<ButtonRelease-1>", self.붓떼기)

        # 화면의 그림과 똑같은 내용을 담아 둘 PIL 이미지 (실제 인식에 사용)
        self.그림 = Image.new("L", (캔버스크기, 캔버스크기), 0)
        self.그리개 = ImageDraw.Draw(self.그림)

        버튼틀 = tk.Frame(왼쪽틀)
        버튼틀.pack(pady=(10, 0))
        tk.Button(버튼틀, text="인식하기", width=12, command=self.인식하기,
                  font=("맑은 고딕", 10, "bold")).pack(side=tk.LEFT, padx=4)
        tk.Button(버튼틀, text="지우기", width=12, command=self.지우기,
                  font=("맑은 고딕", 10)).pack(side=tk.LEFT, padx=4)

        # ----- 오른쪽: 결과 표시 영역 -----
        오른쪽틀 = tk.Frame(전체틀)
        오른쪽틀.grid(row=0, column=1, sticky="n")

        tk.Label(오른쪽틀, text="인식 결과", font=("맑은 고딕", 11, "bold")).pack()
        self.결과라벨 = tk.Label(오른쪽틀, text="?", font=("맑은 고딕", 64, "bold"),
                               fg="#1a6fd4", width=2)
        self.결과라벨.pack()
        self.확신라벨 = tk.Label(오른쪽틀, text="숫자를 그린 뒤 '인식하기'를 누르세요",
                               font=("맑은 고딕", 9), fg="#555", wraplength=200)
        self.확신라벨.pack(pady=(0, 8))

        # 0~9 각각의 확률을 보여 주는 막대그래프
        self.막대들 = []
        self.확률라벨들 = []
        표틀 = tk.Frame(오른쪽틀)
        표틀.pack()
        for 숫자 in range(10):
            tk.Label(표틀, text=str(숫자), font=("맑은 고딕", 9),
                     width=2).grid(row=숫자, column=0)
            막대 = tk.Canvas(표틀, width=140, height=12, bg="#eee",
                            highlightthickness=0)
            막대.grid(row=숫자, column=1, pady=1)
            라벨 = tk.Label(표틀, text="0.0%", font=("맑은 고딕", 8),
                           width=6, anchor="w")
            라벨.grid(row=숫자, column=2)
            self.막대들.append(막대)
            self.확률라벨들.append(라벨)

        # 키보드 단축키: Enter = 인식, Esc/Delete = 지우기
        루트.bind("<Return>", lambda 이벤트: self.인식하기())
        루트.bind("<Escape>", lambda 이벤트: self.지우기())
        루트.bind("<Delete>", lambda 이벤트: self.지우기())

    def 그리기(self, 이벤트):
        """마우스를 누른 채 움직이면 캔버스와 PIL 이미지에 동시에 선을 긋는다."""
        지금좌표 = (이벤트.x,이벤트.y)
        if self.이전좌표 is None:
            self.이전좌표 = 지금좌표

        self.캔버스.create_line(*self.이전좌표, *지금좌표, fill="white",
                              width=붓굵기, capstyle=tk.ROUND, smooth=True)
        self.그리개.line([self.이전좌표, 지금좌표], fill=255, width=붓굵기, joint="curve")
        # 선의 양 끝을 둥글게 만들어 화면 표시와 실제 이미지를 일치시킨다
        반지름 = 붓굵기 // 2
        for 점x, 점y in (self.이전좌표, 지금좌표):
            self.그리개.ellipse([점x - 반지름, 점y - 반지름,
                               점x + 반지름, 점y + 반지름], fill=255)
        self.이전좌표 = 지금좌표

    def 붓떼기(self, 이벤트):
        """마우스 버튼을 떼면 선의 시작점을 초기화한다."""
        self.이전좌표 = None

    def 지우기(self):
        """그림판과 결과 표시를 모두 초기화한다."""
        self.캔버스.delete("all")
        self.그리개.rectangle([0, 0, 캔버스크기, 캔버스크기], fill=0)
        self.이전좌표 = None
        self.결과라벨.config(text="?")
        self.확신라벨.config(text="숫자를 그린 뒤 '인식하기'를 누르세요")
        for 막대, 라벨 in zip(self.막대들, self.확률라벨들):
            막대.delete("all")
            라벨.config(text="0.0%")

    def 인식하기(self):
        """현재 그림을 전처리해 모델에 넣고, 예측 결과를 화면에 표시한다."""
        입력텐서 = 손글씨_전처리(self.그림)
        if 입력텐서 is None:
            self.확신라벨.config(text="먼저 숫자를 그려 주세요!")
            return

        with torch.no_grad():
            로그확률 = self.모델(입력텐서.to(self.장치))
            확률 = torch.exp(로그확률).squeeze(0).cpu().numpy()

        예측숫자 = int(확률.argmax())
        self.결과라벨.config(text=str(예측숫자))
        self.확신라벨.config(text=f"확신도: {확률[예측숫자] * 100:.1f}%")

        # 각 숫자의 확률을 막대 길이로 표현 (가장 높은 것은 파란색 강조)
        for 숫자, (막대, 라벨) in enumerate(zip(self.막대들, self.확률라벨들)):
            막대.delete("all")
            길이 = max(1, int(확률[숫자] * 140))
            색 = "#1a6fd4" if 숫자 == 예측숫자 else "#b0b8c1"
            막대.create_rectangle(0, 0, 길이, 12, fill=색, width=0)
            라벨.config(text=f"{확률[숫자] * 100:.1f}%")

        print(f"예측: {예측숫자} (확신도 {확률[예측숫자] * 100:.1f}%)")


def main():
    장치 = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"사용 장치: {장치}")
    모델 = 모델_불러오기(장치)
    print("모델을 불러왔습니다. 창에 숫자를 그려 보세요.")

    루트 = tk.Tk()
    손글씨인식앱(루트, 모델, 장치)
    루트.mainloop()


if __name__ == "__main__":
    main()
