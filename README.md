# 손글씨 숫자 인식기 (MNIST + PyTorch)

마우스로 숫자를 그리면 CNN 모델이 0~9 중 어떤 숫자인지 알아맞히는 프로그램입니다.

## 구성 파일

| 파일 | 설명 |
| --- | --- |
| `model.py` | CNN 모델 구조 정의 (학습·추론이 공유) |
| `train.py` | MNIST 데이터로 학습하고 `mnist_cnn.pt` 저장 |
| `app.py` | 마우스로 숫자를 그려 인식하는 GUI 프로그램 |
| `mnist_cnn.pt` | 학습된 가중치 파일 (테스트 정확도 99.28%) |
| `data/` | 자동으로 내려받은 MNIST 데이터셋 (저장소에는 포함하지 않음) |

## 설치

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install torch torchvision pillow --index-url https://download.pytorch.org/whl/cpu
```

## 사용 방법

1. 학습 (가중치 파일 생성 — 저장소에 이미 `mnist_cnn.pt`가 있으므로 생략 가능)

```bash
.venv\Scripts\python.exe train.py
```

2. 손글씨 인식 프로그램 실행

```bash
.venv\Scripts\python.exe app.py
```

Windows 파일 탐색기에서 `app.py`를 **더블클릭**해도 실행됩니다.
(`.venv`의 Python으로 자동으로 다시 실행되며, 콘솔 창 없이 그림판 창만 뜹니다.)

## 사용 팁

- 검은 칸에 숫자 하나를 그리고 마우스 버튼을 떼면 **자동으로 인식**합니다.
- `[지우기]` 버튼 또는 **오른쪽 클릭**: 캔버스 지우기
- 오른쪽 막대그래프에서 0~9 각각의 확률을 확인할 수 있습니다.

## 모델 구조

`[합성곱(1→32) → 배치정규화 → ReLU] x2 → 맥스풀링 → [합성곱(32→64) → 배치정규화 → ReLU] x2 → 맥스풀링 → 완전연결(3136→128) → 드롭아웃 → 완전연결(128→10)`

손실 함수는 교차 엔트로피, 옵티마이저는 Adam(학습률 0.001, 에폭마다 0.7배 감소)을 사용합니다.
학습 데이터에는 회전·이동·확대 변형을 주어 직접 그린 글씨에도 잘 동작하도록 했습니다.
