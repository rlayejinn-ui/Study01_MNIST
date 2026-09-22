# CLAUDE.md

이 파일은 Claude Code가 이 저장소에서 작업할 때 참고하는 안내서입니다.

## 프로젝트 개요

마우스로 그린 손글씨 숫자를 CNN으로 인식하는 학습용 프로젝트입니다.
PyTorch로 MNIST를 학습시키고, tkinter GUI에서 실시간으로 숫자를 인식합니다.

## 명령어

```bash
# 학습 (MNIST 자동 다운로드 → mnist_cnn.pt 저장)
.venv\Scripts\python.exe train.py

# 손글씨 인식 GUI 실행 (mnist_cnn.pt 필요)
.venv\Scripts\python.exe app.py
```

**윈도우 콘솔에서 한글이 깨지면** 앞에 인코딩을 지정하세요.

```bash
set PYTHONIOENCODING=utf-8
```

## 파일 구조

| 파일 | 역할 |
| --- | --- |
| `model.py` | `숫자인식CNN` 클래스와 정규화 상수 정의. 학습과 추론이 **반드시 이 한 곳을 공유** |
| `train.py` | 학습 루프, 평가, 가중치 저장 |
| `app.py` | tkinter GUI, 손글씨 전처리, 추론. 더블클릭 시 `.venv`로 자동 재실행 |
| `mnist_cnn.pt` | 학습된 가중치 (`state_dict`만 저장) |
| `data/` | MNIST 원본 데이터 (자동 다운로드, 버전 관리 대상 아님) |

## 코드 작성 규칙

- **모든 코드, 주석, 변수명, 함수명, 클래스명, 화면 문구를 한글로 작성합니다.**
  예: `def 한_에폭_학습(모델, 로더, 최적화기, 장치, 에폭)`, `self.결과_글자`
- 외부 라이브러리 API는 원래 이름을 그대로 씁니다.

## 아키텍처에서 주의할 점

### 모델 구조 변경 시

`model.py`의 `숫자인식CNN`을 바꾸면 기존 `mnist_cnn.pt`와 호환되지 않습니다.
구조를 수정했다면 **반드시 `train.py`를 다시 실행**해 가중치를 새로 만들어야 합니다.

### 손글씨 전처리 (`app.py`의 `전처리`)

그린 그림을 280x280에서 28x28로 그냥 축소하면 인식률이 크게 떨어집니다.
MNIST 제작 방식과 동일한 단계를 거치도록 구현돼 있으니 **이 순서를 유지**하세요.

1. 글씨가 있는 영역만 남기고 여백 잘라내기
2. 가로세로 비율을 유지한 채 긴 변을 20픽셀로 축소
3. 28x28 중앙에 배치한 뒤 **무게중심 기준으로 재정렬**

정규화 상수 `MNIST_평균`, `MNIST_표준편차`는 `model.py`에만 정의하고
`train.py`와 `app.py`가 가져다 씁니다. 값을 따로 적지 마세요.

### 화면과 인식 대상의 이중 관리

tkinter 캔버스에는 화면 표시용으로 그리고, 동시에 같은 내용을 PIL 이미지
(`self.그림`)에도 그립니다. 실제 인식은 PIL 이미지로 수행합니다
(화면 캡처 방식보다 정확하고 창이 가려져도 영향을 받지 않음).
그리기 로직을 수정할 때는 **양쪽이 똑같이 그려지는지** 확인하세요.

## 환경

- Python 3.12 가상환경 `.venv` / PyTorch CPU 빌드 (`torch 2.14.0+cpu`, `torchvision 0.29.0+cpu`)
- 재설치가 필요하면:

```bash
.venv\Scripts\python.exe -m pip install torch torchvision pillow --index-url https://download.pytorch.org/whl/cpu
```

- GPU가 있으면 코드가 자동으로 CUDA를 사용합니다 (`torch.cuda.is_available()`).

## 현재 성능 기준선

5에폭 학습 기준 테스트 정확도 **99.28%** (9,928/10,000).
모델이나 전처리를 수정했다면 이 수치와 비교해 성능이 떨어지지 않았는지 확인하세요.
