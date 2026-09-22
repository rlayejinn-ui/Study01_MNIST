# CLAUDE.md — 데스크톱 버전

이 폴더는 PyTorch + tkinter로 만든 손글씨 숫자 인식 **데스크톱 버전**입니다.
저장소 전체 규칙은 루트의 `CLAUDE.md`를 먼저 보세요.

## 명령어 (이 폴더에서 실행)

```bash
# 가상환경 만들기 (처음 한 번)
python -m venv .venv
.venv/Scripts/python.exe -m pip install torch torchvision pillow --index-url https://download.pytorch.org/whl/cpu

# 학습 (MNIST 자동 다운로드 → mnist_cnn.pt 저장)
.venv/Scripts/python.exe train.py

# 웹 버전용 가중치 내보내기 (학습 후 반드시 실행)
.venv/Scripts/python.exe export_web.py

# 손글씨 인식 GUI 실행 (파일 탐색기에서 app.py 더블클릭도 가능)
.venv/Scripts/python.exe app.py

# 검사
.venv/Scripts/python.exe 검사_전처리.py
.venv/Scripts/python.exe 검사_내보내기.py
```

**윈도우 콘솔에서 한글이 깨지면** 먼저 인코딩을 설정하세요: cmd는 `set PYTHONIOENCODING=utf-8`, PowerShell은 `$env:PYTHONIOENCODING="utf-8"`.

## 파일 구조

| 파일 | 역할 |
| --- | --- |
| `model.py` | `숫자인식CNN` 클래스와 정규화 상수. 학습·추론·내보내기가 **반드시 이 한 곳을 공유** |
| `train.py` | 학습 루프, 평가, 가중치 저장 (경로는 이 폴더 기준) |
| `app.py` | tkinter GUI, 손글씨 전처리, 추론. 더블클릭 시 `.venv`로 자동 재실행 |
| `export_web.py` | 배치정규화를 접어 `../web_version/model/`과 `../web_version/tests/기준값.json`으로 내보내기 |
| `검사_전처리.py` | 선을 그려 1·0·7 인식과 빈 그림 처리를 확인 |
| `검사_내보내기.py` | 내보낸 가중치 파일의 형식과 값을 확인 |
| `mnist_cnn.pt` | 학습된 가중치 (`state_dict`만 저장, 저장소에 포함) |
| `data/` | MNIST 원본 데이터 (자동 다운로드, 버전 관리 대상 아님) |
| `.venv/` | 이 폴더 전용 가상환경 (버전 관리 대상 아님) |

## 아키텍처에서 주의할 점

### 모델 구조나 가중치를 바꾼 경우

- `model.py`의 `숫자인식CNN`을 바꾸면 기존 `mnist_cnn.pt`와 호환되지 않으므로 `train.py`를 다시 실행합니다.
- **가중치가 바뀌면 `export_web.py`를 꼭 실행**해 웹 버전도 같은 모델을 쓰게 하고, 결과 파일을 함께 커밋합니다.
- 층 구성을 바꾸면 `export_web.py`의 층 목록과 `../web_version/js/모델.js`의 순전파도 함께 고쳐야 합니다.

### 손글씨 전처리 (`app.py`의 `전처리`)

그린 그림을 280x280에서 28x28로 그냥 축소하면 인식률이 크게 떨어집니다.
MNIST 제작 방식과 같은 순서를 **유지**하세요. 웹 버전 `js/전처리.js`도 같은 순서이므로 **함께 수정**합니다.

1. 글씨가 있는 영역만 남기고 여백 잘라내기
2. 가로세로 비율을 유지한 채 긴 변을 20픽셀로 축소
3. 28x28 중앙에 배치한 뒤 **무게중심 기준으로 재정렬**

정규화 상수 `MNIST_평균`, `MNIST_표준편차`는 `model.py`에만 정의합니다.
웹 버전은 `export_web.py`가 `weights.json`에 적어 준 값을 씁니다.

### 화면과 인식 대상의 이중 관리

tkinter 캔버스에는 화면 표시용으로 그리고, 같은 내용을 PIL 이미지(`self.그림`)에도 그립니다.
실제 인식은 PIL 이미지로 합니다. 그리기 로직을 고칠 때는 **양쪽이 똑같이 그려지는지** 확인하세요.

## 환경

- Python 3.12 가상환경 `.venv` / PyTorch CPU 빌드 (`torch 2.14.0+cpu`, `torchvision 0.29.0+cpu`)
- GPU가 있으면 코드가 자동으로 CUDA를 사용합니다.

## 현재 성능 기준선

5에폭 학습 기준 테스트 정확도 **99.28%** (9,928/10,000).
모델이나 전처리를 수정했다면 이 수치와 비교해 성능이 떨어지지 않았는지 확인하세요.
