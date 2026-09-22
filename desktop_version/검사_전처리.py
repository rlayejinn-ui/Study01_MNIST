# -*- coding: utf-8 -*-
"""
app.py 의 전처리와 인식이 제대로 동작하는지 확인하는 간단한 검사

실행 방법 (desktop_version 폴더 기준):
    .venv\\Scripts\\python.exe 검사_전처리.py
"""

import sys

from PIL import Image, ImageDraw

from app import 가중치_불러오기, 예측


def 새_그림():
    """앱 캔버스와 같은 280x280 검은 그림과 붓을 만듭니다."""
    그림 = Image.new("L", (280, 280), 0)
    return 그림, ImageDraw.Draw(그림)


def main():
    모델 = 가중치_불러오기()
    실패 = 0

    # (이름, 정답, 그리는 함수)
    검사_목록 = [
        ("세로선", 1, lambda 붓: 붓.line([140, 40, 140, 240], fill=255, width=18)),
        ("타원", 0, lambda 붓: 붓.ellipse([80, 40, 200, 240], outline=255, width=18)),
        ("꺾은선", 7, lambda 붓: 붓.line([70, 50, 210, 50, 110, 240], fill=255, width=18, joint="curve")),
    ]
    for 이름, 정답, 그리기 in 검사_목록:
        그림, 붓 = 새_그림()
        그리기(붓)
        결과 = int(예측(모델, 그림).argmax())
        표시 = "통과" if 결과 == 정답 else "실패"
        print(f"[{표시}] {이름}: 정답 {정답}, 인식 {결과}")
        실패 += 결과 != 정답

    빈_그림, _ = 새_그림()
    if 예측(모델, 빈_그림) is None:
        print("[통과] 빈 그림: 인식하지 않음")
    else:
        print("[실패] 빈 그림: None 이 아님")
        실패 += 1

    if 실패:
        print(f"실패 {실패}건")
        sys.exit(1)
    print("모든 검사 통과")


if __name__ == "__main__":
    main()
