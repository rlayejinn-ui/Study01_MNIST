# 웹 버전 / 데스크톱 버전 분리 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 기존 PyTorch 데스크톱 앱을 `desktop_version/`으로 옮기고, 같은 가중치로 순수 자바스크립트 추론을 하는 `web_version/`을 새로 만들어 GitHub Pages에 배포한다.

**Architecture:** `desktop_version/export_web.py`가 `mnist_cnn.pt`의 배치정규화를 합성곱에 접어 `web_version/model/weights.bin`(float32) + `weights.json`(목록)으로 내보낸다. 웹은 ES 모듈 4개(연산 → 모델 → 전처리 → 화면)로 나뉘며 외부 라이브러리가 없다. 검사는 브라우저에서 여는 `web_version/tests/검사.html`로 하고, 배포는 GitHub Actions가 `web_version` 폴더만 Pages에 올린다.

**Tech Stack:** Python 3.12 + PyTorch 2.14 CPU (데스크톱·변환), 순수 JavaScript ES 모듈 + Canvas API + Pointer Events (웹), GitHub Actions + GitHub Pages (배포)

**Spec:** `docs/superpowers/specs/2026-09-22-web-desktop-split-design.md`

## Global Constraints

- 모든 코드·주석·변수명·함수명·클래스명·화면 문구는 **한글**로 쓴다. 외부 API(PyTorch, DOM, Canvas 등) 이름만 원래대로 쓴다. 단, GitHub Actions의 job id처럼 문법상 영문만 허용되는 곳은 예외.
- 웹 버전은 **외부 라이브러리·CDN·npm·번들러를 쓰지 않는다.**
- 두 버전은 같은 가중치(`desktop_version/mnist_cnn.pt`)와 같은 정규화 상수(평균 `0.1307`, 표준편차 `0.3081`)를 쓴다.
- JS 추론 확률과 PyTorch 확률의 차이는 모든 값에서 **1e-4 이하**, 예측 숫자는 모두 일치해야 한다.
- 배치정규화를 접은 모델과 원래 모델의 출력 차이는 **1e-5 이하**여야 한다.
- 가중치 파일: `weights.bin`은 float32 리틀 엔디언, `weights.json`의 `시작`/`개수`는 float32 원소 단위, `형식_버전`은 `1`.
- 배포 주소: `https://rlayejinn-ui.github.io/Study01_MNIST/`
- 커밋 메시지는 한글로 쓰고 끝에 `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>` 줄을 붙인다.
- 명령어는 저장소 루트(`C:\학교과제\study01_MNIST`)에서 **Git Bash** 기준으로 적었다. 한글 출력이 깨지지 않도록 Python 실행 앞에 `PYTHONIOENCODING=utf-8`을 붙인다.

## 파일 구조

| 경로 | 상태 | 책임 |
| --- | --- | --- |
| `desktop_version/model.py` | 이동 | `숫자인식CNN`, 정규화 상수 |
| `desktop_version/train.py` | 이동 + 경로 수정 | 학습, `mnist_cnn.pt` 저장 (데이터·가중치 경로를 스크립트 폴더 기준으로) |
| `desktop_version/app.py` | 이동 | tkinter GUI (변경 없음) |
| `desktop_version/mnist_cnn.pt` | 이동 | 학습된 가중치 |
| `desktop_version/검사_전처리.py` | 신규 | 데스크톱 전처리·인식 회귀 검사 |
| `desktop_version/export_web.py` | 신규 | BN 접기, `weights.*`와 `기준값.json` 내보내기 |
| `desktop_version/검사_내보내기.py` | 신규 | 내보낸 파일 형식과 값 검사 |
| `desktop_version/CLAUDE.md` | 이동 + 수정 | 데스크톱 안내 |
| `web_version/js/연산.js` | 신규 | 순수 수치 연산 함수 |
| `web_version/js/모델.js` | 신규 | 가중치 불러오기, 순전파 |
| `web_version/js/전처리.js` | 신규 | 캔버스 → 정규화된 28x28 |
| `web_version/js/화면.js` | 신규 | 그리기, 결과 표시 |
| `web_version/index.html`, `style.css` | 신규 | 화면 뼈대와 모양 |
| `web_version/model/weights.json`, `weights.bin` | 생성 | 내보낸 가중치 |
| `web_version/tests/검사.html`, `검사.js`, `검사도구.js` | 신규 | 브라우저 검사 실행기 |
| `web_version/tests/연산_검사.js`, `모델_검사.js`, `전처리_검사.js` | 신규 | 각 모듈 검사 |
| `web_version/tests/기준값.json` | 생성 | PyTorch 기준 입력·확률 |
| `web_version/개발서버.py` | 신규 | 로컬 확인용 정적 서버 (올바른 MIME, 캐시 끔) |
| `web_version/CLAUDE.md` | 신규 | 웹 안내 |
| `.github/workflows/pages.yml` | 신규 | Pages 배포 |
| `CLAUDE.md`, `README.md`, `.gitignore` | 수정 | 루트 안내·소개·제외 목록 |
| `.claude/launch.json` | 신규 (git 제외) | 브라우저 창에서 개발 서버 실행 |

> 설계 문서 대비 보완: 검사 파일을 실행기(`검사.js`) + 도구(`검사도구.js`) + 모듈별 검사로 나누었고, `개발서버.py`(Windows에서 `.js` MIME이 잘못 잡히는 문제 방지)와 데스크톱 검사 스크립트 2개를 추가했다. `train.py`는 어느 폴더에서 실행해도 `desktop_version/data`와 `desktop_version/mnist_cnn.pt`를 쓰도록 경로만 고친다.

---

### Task 1: 데스크톱 코드를 `desktop_version/`으로 이동

**Files:**
- Move: `model.py`, `train.py`, `app.py`, `mnist_cnn.pt`, `CLAUDE.md` → `desktop_version/`
- Modify: `desktop_version/train.py` (경로 상수 2줄), `desktop_version/CLAUDE.md`, `.gitignore`
- Create: `desktop_version/검사_전처리.py`
- 폴더 이동(비추적): `data/` → `desktop_version/data/`, 루트 `.venv/` 삭제 후 `desktop_version/.venv/` 새로 생성

**Interfaces:**
- Consumes: 없음
- Produces: `desktop_version/.venv/Scripts/python.exe` (torch·torchvision·pillow 설치됨), `desktop_version/mnist_cnn.pt`, `desktop_version/data/MNIST/`

- [ ] **Step 1: 실행 중인 데스크톱 앱 종료** (열려 있으면 `.venv` 삭제가 막힌다)

```bash
powershell -Command "Get-Process pythonw -ErrorAction SilentlyContinue | Stop-Process"
```

- [ ] **Step 2: 회귀 검사 스크립트 작성** — `desktop_version/검사_전처리.py`

```python
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
```

- [ ] **Step 3: 파일 이동** (Step 2의 검사 스크립트는 처음부터 `desktop_version/검사_전처리.py` 경로로 만든다)

```bash
git mv model.py train.py app.py mnist_cnn.pt desktop_version/
git mv CLAUDE.md desktop_version/CLAUDE.md
mv data desktop_version/data
rm -rf __pycache__
```

- [ ] **Step 4: 검사가 실패하는지 확인** (가상환경이 아직 없음)

Run: `ls desktop_version/.venv/Scripts/python.exe`
Expected: `No such file or directory`

- [ ] **Step 5: 새 가상환경 만들기, 루트 가상환경 삭제**

```bash
"$LOCALAPPDATA/Programs/Python/Python312/python.exe" -m venv desktop_version/.venv
desktop_version/.venv/Scripts/python.exe -m pip install --quiet torch torchvision pillow --index-url https://download.pytorch.org/whl/cpu
rm -rf .venv
```

- [ ] **Step 6: `train.py` 경로를 스크립트 폴더 기준으로 수정**

`desktop_version/train.py`에서 `import torch` 위에 `import os`를 추가하고, 설정값 두 줄을 바꾼다.

```python
import os

import torch
```

```python
# 이 파일이 있는 폴더를 기준으로 경로를 잡아, 어느 폴더에서 실행해도 같은 곳을 씁니다.
프로젝트_폴더 = os.path.dirname(os.path.abspath(__file__))
가중치_파일 = os.path.join(프로젝트_폴더, "mnist_cnn.pt")
데이터_경로 = os.path.join(프로젝트_폴더, "data")
```

(기존 `가중치_파일 = "mnist_cnn.pt"`, `데이터_경로 = "./data"` 두 줄을 위 세 줄로 교체.)

- [ ] **Step 7: 회귀 검사 통과 확인**

Run: `cd desktop_version && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe 검사_전처리.py; cd ..`
Expected: `[통과]` 4줄과 `모든 검사 통과`

Run: `PYTHONIOENCODING=utf-8 desktop_version/.venv/Scripts/python.exe -c "import ast,sys; ast.parse(open('desktop_version/train.py',encoding='utf-8').read()); print('train.py 문법 정상')"`
Expected: `train.py 문법 정상`

- [ ] **Step 8: 더블클릭 실행 흉내 확인** (다른 작업 폴더에서 py 런처로 실행)

이 단계는 **PowerShell 도구**로 실행한다.

```powershell
Start-Process -FilePath "$env:LOCALAPPDATA\Programs\Python\Launcher\py.exe" -ArgumentList '"C:\학교과제\study01_MNIST\desktop_version\app.py"' -WorkingDirectory $env:USERPROFILE; Start-Sleep 6; Get-Process | Where-Object { $_.MainWindowTitle -like "*MNIST*" } | Select-Object Id, MainWindowTitle
```
Expected: `손글씨 숫자 인식기 (MNIST CNN)` 창 1개. 확인 후 `Get-Process pythonw | Stop-Process`로 닫는다.

- [ ] **Step 9: `.gitignore` 교체** (가중치 파일은 이제 저장소에 포함하므로 제외 목록에서 뺀다)

```gitignore
# 데스크톱 버전: 내려받은 MNIST 원본 데이터 (train.py 실행 시 자동 생성, 약 64MB)
desktop_version/data/

# 학습 로그
train_log.txt

# 파이썬 캐시
__pycache__/
*.py[cod]

# 가상환경
.venv/
venv/

# 에디터·도구 설정
.vscode/
.idea/
.claude/
```

- [ ] **Step 10: `desktop_version/CLAUDE.md` 수정**

다음 내용으로 전체를 교체한다.

````markdown
# CLAUDE.md — 데스크톱 버전

이 폴더는 PyTorch + tkinter로 만든 손글씨 숫자 인식 **데스크톱 버전**입니다.
저장소 전체 규칙은 루트의 `CLAUDE.md`를 먼저 보세요.

## 명령어 (이 폴더에서 실행)

```bash
# 가상환경 만들기 (처음 한 번)
python -m venv .venv
.venv\Scripts\python.exe -m pip install torch torchvision pillow --index-url https://download.pytorch.org/whl/cpu

# 학습 (MNIST 자동 다운로드 → mnist_cnn.pt 저장)
.venv\Scripts\python.exe train.py

# 웹 버전용 가중치 내보내기 (학습 후 반드시 실행)
.venv\Scripts\python.exe export_web.py

# 손글씨 인식 GUI 실행 (파일 탐색기에서 app.py 더블클릭도 가능)
.venv\Scripts\python.exe app.py

# 검사
.venv\Scripts\python.exe 검사_전처리.py
.venv\Scripts\python.exe 검사_내보내기.py
```

**윈도우 콘솔에서 한글이 깨지면** 먼저 `set PYTHONIOENCODING=utf-8`을 실행하세요.

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
````

- [ ] **Step 11: 상태 확인 후 커밋**

Run: `git status --short`
Expected: `R` 표시로 `desktop_version/`으로 옮겨진 5개 파일, `M .gitignore`, `?? desktop_version/검사_전처리.py`(또는 이미 추가됨). `.venv`, `data`는 목록에 없어야 한다.

```bash
git add .gitignore desktop_version
git commit -m "데스크톱 코드를 desktop_version 폴더로 이동" -m "- 가상환경을 desktop_version/.venv 로 새로 만들고 train.py 경로를 폴더 기준으로 수정
- 전처리 회귀 검사(검사_전처리.py) 추가, 가중치 파일을 저장소에 정식 포함" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: 웹용 가중치 내보내기 (`export_web.py`)

**Files:**
- Create: `desktop_version/검사_내보내기.py`, `desktop_version/export_web.py`
- 생성물: `web_version/model/weights.json`, `web_version/model/weights.bin`, `web_version/tests/기준값.json`

**Interfaces:**
- Consumes: `desktop_version/model.py`의 `숫자인식CNN`, `MNIST_평균`, `MNIST_표준편차`; `desktop_version/mnist_cnn.pt`; `desktop_version/data/`
- Produces:
  - `weights.json`: `{"형식_버전": 1, "정규화": {"평균": 0.1307, "표준편차": 0.3081}, "층": [{"이름", "종류", "가중치": {"모양", "시작", "개수"}, "편향": {"모양", "시작", "개수"}}, ...]}`
  - 층 이름·종류·가중치 모양 (순서대로): `합성곱1` 합성곱 `[32,1,3,3]`, `합성곱2` 합성곱 `[32,32,3,3]`, `합성곱3` 합성곱 `[64,32,3,3]`, `합성곱4` 합성곱 `[64,64,3,3]`, `완전연결1` 완전연결 `[128,3136]`, `완전연결2` 완전연결 `[10,128]`
  - `기준값.json`: `{"입력": number[20][784], "확률": number[20][10], "정답": number[20]}`

- [ ] **Step 1: 검사 스크립트 작성** — `desktop_version/검사_내보내기.py`

```python
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
```

- [ ] **Step 2: 검사가 실패하는지 확인**

Run: `cd desktop_version && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe 검사_내보내기.py; cd ..`
Expected: `[실패] weights.json / weights.bin 파일이 있다` 후 종료 코드 1

- [ ] **Step 3: 내보내기 스크립트 작성** — `desktop_version/export_web.py`

```python
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
```

- [ ] **Step 4: 내보내기 실행**

Run: `cd desktop_version && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe export_web.py; cd ..`
Expected: `배치정규화 접기 확인: 최대 로짓 차이 …e-06` 수준, `weights.bin 저장: float32 467,818개 (1.78 MB)`, `내보내기 완료`

- [ ] **Step 5: 검사 통과 확인**

Run: `cd desktop_version && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe 검사_내보내기.py; cd ..`
Expected: `[통과]` 줄들과 `모든 검사 통과`

- [ ] **Step 6: 커밋**

```bash
git add desktop_version/export_web.py desktop_version/검사_내보내기.py web_version/model web_version/tests/기준값.json
git commit -m "웹용 가중치 내보내기 스크립트와 생성 파일 추가" -m "배치정규화를 합성곱에 접어 weights.bin(float32) + weights.json 으로 내보내고, 웹 검사용 PyTorch 기준값 20장을 함께 저장" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: 브라우저 검사 실행기와 수치 연산 모듈 (`연산.js`)

**Files:**
- Create: `web_version/개발서버.py`, `.claude/launch.json`(git 제외)
- Create: `web_version/tests/검사.html`, `web_version/tests/검사.js`, `web_version/tests/검사도구.js`, `web_version/tests/연산_검사.js`
- Create: `web_version/js/연산.js`

**Interfaces:**
- Consumes: 없음
- Produces:
  - `검사도구.js`: `검사(이름: string, 함수: () => void | string | Promise<void | string>)`, `근사같음(실제: ArrayLike<number>, 기대: ArrayLike<number>, 오차 = 1e-6, 설명 = "")`, `확인(조건: boolean, 메시지: string)`, `모두_실행(목록요소: HTMLElement, 요약요소: HTMLElement): Promise<{통과: number, 실패: number, 실패목록: string[], 메모: string[]}>`. 검사 함수가 문자열을 돌려주면 결과 옆에 메모로 표시한다.
  - `검사.js`: `검사_모듈` 배열의 모듈을 동적으로 불러온 뒤 실행하고 결과를 `window.검사결과`에 넣는다.
  - `연산.js` (모두 새 `Float32Array` 반환, 배열 배치는 PyTorch와 같은 `[채널][높이][너비]`):
    - `합성곱3x3(입력, 입력채널, 높이, 너비, 가중치, 편향, 출력채널)` — 3x3, 패딩 1, 보폭 1, 가중치 배치 `[출력][입력][3][3]`
    - `렐루(입력)`
    - `최대풀링2x2(입력, 채널, 높이, 너비)` → 크기 `채널 × (높이/2) × (너비/2)`
    - `완전연결(입력, 가중치, 편향, 출력수)` — 가중치 배치 `[출력][입력]`
    - `소프트맥스(로짓)`
    - `최댓값_위치(배열): number` — 가장 큰 값의 위치(같으면 앞쪽)
  - 개발 서버 주소: `http://localhost:8000/` (루트가 `web_version`)

- [ ] **Step 1: 개발 서버 작성** — `web_version/개발서버.py`

```python
# -*- coding: utf-8 -*-
"""
웹 버전을 내 컴퓨터에서 확인하기 위한 간단한 정적 파일 서버

실행 방법 (web_version 폴더 기준):
    python 개발서버.py
그다음 브라우저에서 http://localhost:8000 을 엽니다.
검사 페이지: http://localhost:8000/tests/검사.html

index.html 을 파일로 직접 열면(file://) 브라우저 보안 정책 때문에
모듈과 가중치를 불러올 수 없으므로 이 서버로 여세요.
Windows 에서는 .js 의 MIME 형식이 잘못 잡히는 경우가 있어 직접 지정합니다.
"""

import functools
import http.server
import os

포트 = 8000
폴더 = os.path.dirname(os.path.abspath(__file__))


class 처리기(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".bin": "application/octet-stream",
    }

    def end_headers(self):
        # 코드를 고친 뒤 새로고침하면 바로 반영되도록 캐시를 끕니다.
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main():
    서버 = http.server.ThreadingHTTPServer(("127.0.0.1", 포트), functools.partial(처리기, directory=폴더))
    print(f"웹 버전 개발 서버 실행 중: http://localhost:{포트}  (끝내려면 Ctrl+C)")
    서버.serve_forever()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 브라우저 창용 실행 설정** — `.claude/launch.json` (`.gitignore`의 `.claude/`로 제외됨)

```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "웹버전",
      "runtimeExecutable": "C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
      "runtimeArgs": ["web_version/개발서버.py"],
      "port": 8000
    }
  ]
}
```

- [ ] **Step 3: 검사 도구 작성** — `web_version/tests/검사도구.js`

```js
// 외부 라이브러리 없이 쓰는 아주 작은 검사 도구

const 등록된_검사 = [];

/** 검사를 등록합니다. 함수가 문자열을 돌려주면 결과 옆에 메모로 표시합니다. */
export function 검사(이름, 함수) {
  등록된_검사.push({ 이름, 함수 });
}

/** 조건이 거짓이면 실패시킵니다. */
export function 확인(조건, 메시지) {
  if (!조건) throw new Error(메시지);
}

/** 두 숫자 배열이 원소마다 허용 오차 안에서 같은지 확인합니다. */
export function 근사같음(실제, 기대, 오차 = 1e-6, 설명 = "") {
  if (실제.length !== 기대.length) {
    throw new Error(`${설명} 길이가 다릅니다: ${실제.length} ≠ ${기대.length}`);
  }
  for (let 위치 = 0; 위치 < 기대.length; 위치++) {
    if (!(Math.abs(실제[위치] - 기대[위치]) <= 오차)) {
      throw new Error(`${설명}[${위치}] 값이 다릅니다: ${실제[위치]} ≠ ${기대[위치]} (허용 오차 ${오차})`);
    }
  }
}

/** 등록된 검사를 차례로 실행하고 결과를 화면에 표시합니다. */
export async function 모두_실행(목록요소, 요약요소) {
  const 결과 = { 통과: 0, 실패: 0, 실패목록: [], 메모: [] };
  for (const { 이름, 함수 } of 등록된_검사) {
    const 항목 = document.createElement("li");
    try {
      const 메모 = await 함수();
      결과.통과++;
      항목.className = "통과";
      항목.textContent = `✅ ${이름}${메모 ? ` — ${메모}` : ""}`;
      if (메모) 결과.메모.push(`${이름}: ${메모}`);
    } catch (오류) {
      결과.실패++;
      결과.실패목록.push(`${이름}: ${오류.message}`);
      항목.className = "실패";
      항목.textContent = `❌ ${이름} — ${오류.message}`;
      console.error(이름, 오류);
    }
    목록요소.appendChild(항목);
  }
  요약요소.textContent = `통과 ${결과.통과}개, 실패 ${결과.실패}개`;
  요약요소.className = 결과.실패 ? "실패" : "통과";
  return 결과;
}
```

- [ ] **Step 4: 검사 실행기 작성** — `web_version/tests/검사.js`

```js
// 검사 모듈을 불러와 모두 실행하고, 결과를 window.검사결과 에 담습니다.
import { 검사, 모두_실행 } from "./검사도구.js";

// 새 검사 파일을 만들면 여기에 추가합니다.
const 검사_모듈 = ["./연산_검사.js"];

for (const 경로 of 검사_모듈) {
  try {
    await import(경로);
  } catch (오류) {
    // 모듈을 불러오지 못한 것도 실패로 보여 줍니다.
    검사(`${경로} 불러오기`, () => {
      throw 오류;
    });
  }
}

window.검사결과 = await 모두_실행(
  document.getElementById("결과목록"),
  document.getElementById("요약"),
);
```

- [ ] **Step 5: 검사 페이지 작성** — `web_version/tests/검사.html`

```html
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>웹 버전 검사</title>
  <style>
    body { font-family: "맑은 고딕", sans-serif; margin: 16px; background: #fff; color: #222; }
    li { margin: 4px 0; word-break: break-all; }
    .통과 { color: #1b6e2a; }
    .실패 { color: #b3261e; }
    #요약 { font-weight: bold; font-size: 1.2em; }
  </style>
</head>
<body>
  <h1>웹 버전 검사</h1>
  <p id="요약">검사 실행 중…</p>
  <ol id="결과목록"></ol>
  <script type="module" src="./검사.js"></script>
</body>
</html>
```

- [ ] **Step 6: 연산 검사 작성** — `web_version/tests/연산_검사.js`

```js
// 연산.js 의 각 함수를 손으로 계산한 작은 예로 확인합니다.
import { 검사, 근사같음, 확인 } from "./검사도구.js";
import { 합성곱3x3, 렐루, 최대풀링2x2, 완전연결, 소프트맥스, 최댓값_위치 } from "../js/연산.js";

검사("연산: 합성곱3x3 — 모든 가중치 1, 패딩 1", () => {
  const 입력 = Float32Array.from([1, 2, 3, 4, 5, 6, 7, 8, 9]);
  const 가중치 = new Float32Array(9).fill(1);
  const 결과 = 합성곱3x3(입력, 1, 3, 3, 가중치, Float32Array.from([0]), 1);
  근사같음(결과, [12, 21, 16, 27, 45, 33, 24, 39, 28], 1e-6, "합성곱");
});

검사("연산: 합성곱3x3 — 여러 입력·출력 채널과 편향", () => {
  // 입력 채널 0 = [1..4], 채널 1 = [10,20,30,40] (각 2x2)
  const 입력 = Float32Array.from([1, 2, 3, 4, 10, 20, 30, 40]);
  // 출력 0: 채널0 가운데 ×1 + 채널1 가운데 ×2, 편향 1  → a + 2b + 1
  // 출력 1: 가중치 모두 0, 편향 -1                     → -1
  const 가중치 = new Float32Array(2 * 2 * 9);
  가중치[0 * 18 + 0 * 9 + 4] = 1;
  가중치[0 * 18 + 1 * 9 + 4] = 2;
  const 결과 = 합성곱3x3(입력, 2, 2, 2, 가중치, Float32Array.from([1, -1]), 2);
  근사같음(결과, [22, 43, 64, 85, -1, -1, -1, -1], 1e-6, "합성곱");
});

검사("연산: 합성곱3x3 — 커널 위치가 PyTorch 와 같은 방향", () => {
  // 커널 왼쪽 위(ky=0, kx=0)만 1 이면 출력(y,x) = 입력(y-1, x-1)
  const 입력 = Float32Array.from([1, 2, 3, 4, 5, 6, 7, 8, 9]);
  const 가중치 = new Float32Array(9);
  가중치[0] = 1;
  const 결과 = 합성곱3x3(입력, 1, 3, 3, 가중치, Float32Array.from([0]), 1);
  근사같음(결과, [0, 0, 0, 0, 1, 2, 0, 4, 5], 1e-6, "합성곱");
});

검사("연산: 렐루", () => {
  근사같음(렐루(Float32Array.from([-1, 0, 2.5])), [0, 0, 2.5], 0, "렐루");
});

검사("연산: 최대풀링2x2 — 채널별로 따로", () => {
  const 채널1 = Array.from({ length: 16 }, (_, 위치) => 위치 + 1);
  const 채널2 = 채널1.map((값) => -값);
  const 결과 = 최대풀링2x2(Float32Array.from([...채널1, ...채널2]), 2, 4, 4);
  근사같음(결과, [6, 8, 14, 16, -1, -3, -9, -11], 0, "풀링");
});

검사("연산: 완전연결", () => {
  const 결과 = 완전연결(Float32Array.from([1, 2]), Float32Array.from([1, 0, 0, 1, 1, 1]), Float32Array.from([0, 0, 1]), 3);
  근사같음(결과, [1, 2, 4], 1e-6, "완전연결");
});

검사("연산: 소프트맥스 — 값과 합", () => {
  const 결과 = 소프트맥스(Float32Array.from([0, Math.log(3)]));
  근사같음(결과, [0.25, 0.75], 1e-6, "소프트맥스");
});

검사("연산: 소프트맥스 — 큰 값에서도 안정", () => {
  const 결과 = 소프트맥스(Float32Array.from([1000, 1000]));
  근사같음(결과, [0.5, 0.5], 1e-6, "소프트맥스");
});

검사("연산: 최댓값_위치", () => {
  확인(최댓값_위치(Float32Array.from([0.1, 0.7, 0.2])) === 1, "가장 큰 값은 1번");
  확인(최댓값_위치([3, 3, 1]) === 0, "같으면 앞쪽");
});
```

- [ ] **Step 7: 서버를 띄우고 검사가 실패하는지 확인**

브라우저 창 도구 `preview_start`(name: `웹버전`)로 서버를 띄운 뒤 `http://localhost:8000/tests/검사.html`로 이동하고, `javascript_tool`로 결과를 읽는다.

```js
await new Promise((끝) => { const 타이머 = setInterval(() => { if (window.검사결과) { clearInterval(타이머); 끝(window.검사결과); } }, 100); })
```
Expected: `실패: 1`, 실패목록에 `./연산_검사.js 불러오기: …` (연산.js 가 아직 없어 불러오기 실패)

- [ ] **Step 8: 연산 모듈 작성** — `web_version/js/연산.js`

```js
// 신경망 추론에 필요한 수치 연산 (외부 라이브러리 없음)
// 모든 배열은 Float32Array 이고 배치 순서는 PyTorch 와 같은 [채널][높이][너비] 입니다.
// 입력은 바꾸지 않고 항상 새 배열을 돌려줍니다.

/**
 * 3x3 합성곱 (패딩 1, 보폭 1 → 출력 크기 = 입력 크기)
 * 가중치 배치: [출력채널][입력채널][3][3]
 */
export function 합성곱3x3(입력, 입력채널, 높이, 너비, 가중치, 편향, 출력채널) {
  const 면적 = 높이 * 너비;
  const 출력 = new Float32Array(출력채널 * 면적);
  for (let 출 = 0; 출 < 출력채널; 출++) {
    const 출력기준 = 출 * 면적;
    출력.fill(편향[출], 출력기준, 출력기준 + 면적);
    for (let 입 = 0; 입 < 입력채널; 입++) {
      const 입력기준 = 입 * 면적;
      const 커널기준 = (출 * 입력채널 + 입) * 9;
      for (let ky = 0; ky < 3; ky++) {
        const dy = ky - 1;
        // 입력 좌표 (y+dy) 가 범위 안에 드는 y 만 계산 (바깥은 0 패딩)
        const y시작 = Math.max(0, -dy);
        const y끝 = Math.min(높이, 높이 - dy);
        for (let kx = 0; kx < 3; kx++) {
          const dx = kx - 1;
          const 값 = 가중치[커널기준 + ky * 3 + kx];
          if (값 === 0) continue;
          const x시작 = Math.max(0, -dx);
          const x끝 = Math.min(너비, 너비 - dx);
          for (let y = y시작; y < y끝; y++) {
            const 입력행 = 입력기준 + (y + dy) * 너비 + dx;
            const 출력행 = 출력기준 + y * 너비;
            for (let x = x시작; x < x끝; x++) {
              출력[출력행 + x] += 값 * 입력[입력행 + x];
            }
          }
        }
      }
    }
  }
  return 출력;
}

/** ReLU: 음수를 0으로 */
export function 렐루(입력) {
  const 출력 = new Float32Array(입력.length);
  for (let 위치 = 0; 위치 < 입력.length; 위치++) {
    출력[위치] = 입력[위치] > 0 ? 입력[위치] : 0;
  }
  return 출력;
}

/** 2x2 최대풀링 (보폭 2) → 크기가 절반이 됩니다 */
export function 최대풀링2x2(입력, 채널, 높이, 너비) {
  const 새높이 = 높이 >> 1;
  const 새너비 = 너비 >> 1;
  const 출력 = new Float32Array(채널 * 새높이 * 새너비);
  for (let 채 = 0; 채 < 채널; 채++) {
    const 입력기준 = 채 * 높이 * 너비;
    const 출력기준 = 채 * 새높이 * 새너비;
    for (let y = 0; y < 새높이; y++) {
      for (let x = 0; x < 새너비; x++) {
        const 왼위 = 입력기준 + 2 * y * 너비 + 2 * x;
        출력[출력기준 + y * 새너비 + x] = Math.max(
          입력[왼위], 입력[왼위 + 1], 입력[왼위 + 너비], 입력[왼위 + 너비 + 1],
        );
      }
    }
  }
  return 출력;
}

/** 완전연결: 출력 = 가중치 · 입력 + 편향, 가중치 배치: [출력][입력] */
export function 완전연결(입력, 가중치, 편향, 출력수) {
  const 입력수 = 입력.length;
  const 출력 = new Float32Array(출력수);
  for (let 출 = 0; 출 < 출력수; 출++) {
    const 행기준 = 출 * 입력수;
    let 합 = 편향[출];
    for (let 입 = 0; 입 < 입력수; 입++) {
      합 += 가중치[행기준 + 입] * 입력[입];
    }
    출력[출] = 합;
  }
  return 출력;
}

/** 소프트맥스: 로짓을 확률로 (가장 큰 값을 빼서 넘침을 막습니다) */
export function 소프트맥스(로짓) {
  let 최대 = -Infinity;
  for (const 값 of 로짓) 최대 = Math.max(최대, 값);
  const 출력 = new Float32Array(로짓.length);
  let 합 = 0;
  for (let 위치 = 0; 위치 < 로짓.length; 위치++) {
    출력[위치] = Math.exp(로짓[위치] - 최대);
    합 += 출력[위치];
  }
  for (let 위치 = 0; 위치 < 출력.length; 위치++) 출력[위치] /= 합;
  return 출력;
}

/** 가장 큰 값의 위치 (같은 값이 여럿이면 앞쪽) */
export function 최댓값_위치(배열) {
  let 최고 = 0;
  for (let 위치 = 1; 위치 < 배열.length; 위치++) {
    if (배열[위치] > 배열[최고]) 최고 = 위치;
  }
  return 최고;
}
```

- [ ] **Step 9: 검사 통과 확인**

검사 페이지를 새로고침(`navigate`로 같은 주소)하고 Step 7의 `javascript_tool` 코드를 다시 실행한다.
Expected: `통과: 9, 실패: 0`

- [ ] **Step 10: 커밋**

```bash
git add web_version/개발서버.py web_version/tests/검사.html web_version/tests/검사.js web_version/tests/검사도구.js web_version/tests/연산_검사.js web_version/js/연산.js
git commit -m "웹 버전 수치 연산 모듈과 브라우저 검사 도구 추가" -m "합성곱3x3·렐루·최대풀링2x2·완전연결·소프트맥스를 순수 JS로 구현하고 손 계산 예로 검사" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: 가중치 불러오기와 순전파 (`모델.js`)

**Files:**
- Create: `web_version/tests/모델_검사.js`, `web_version/js/모델.js`
- Modify: `web_version/tests/검사.js` (`검사_모듈` 배열)

**Interfaces:**
- Consumes: `연산.js`의 6개 함수; `web_version/model/weights.{json,bin}`; `web_version/tests/기준값.json` (Task 2 형식)
- Produces: `모델_불러오기(기준경로: URL | string): Promise<{ 정규화: {평균: number, 표준편차: number}, 추론(입력: Float32Array(784)): Float32Array(10) }>`. `기준경로`는 `/`로 끝나는 `model/` 폴더 주소. 실패 시 원인을 담은 `Error`를 던진다.

- [ ] **Step 1: 모델 검사 작성** — `web_version/tests/모델_검사.js`

```js
// 모델.js 가 PyTorch 와 같은 결과를 내는지 기준값으로 확인합니다.
import { 검사, 근사같음, 확인 } from "./검사도구.js";
import { 모델_불러오기 } from "../js/모델.js";
import { 최댓값_위치 } from "../js/연산.js";

const 모델경로 = new URL("../model/", import.meta.url);
const 모델_약속 = 모델_불러오기(모델경로);

검사("모델: 정규화 상수를 weights.json 에서 읽음", async () => {
  const 모델 = await 모델_약속;
  근사같음([모델.정규화.평균, 모델.정규화.표준편차], [0.1307, 0.3081], 1e-12, "정규화");
});

검사("모델: 기준값 20장이 PyTorch 와 1e-4 이내로 일치", async () => {
  const 모델 = await 모델_약속;
  const 기준 = await (await fetch(new URL("./기준값.json", import.meta.url))).json();
  확인(기준.입력.length === 20, "기준값은 20장");
  let 최대차이 = 0;
  for (let 번호 = 0; 번호 < 기준.입력.length; 번호++) {
    const 확률 = 모델.추론(Float32Array.from(기준.입력[번호]));
    근사같음(확률, 기준.확률[번호], 1e-4, `${번호}번 이미지 확률`);
    확인(최댓값_위치(확률) === 최댓값_위치(기준.확률[번호]), `${번호}번 이미지 예측 숫자가 다릅니다`);
    for (let 위치 = 0; 위치 < 10; 위치++) {
      최대차이 = Math.max(최대차이, Math.abs(확률[위치] - 기준.확률[번호][위치]));
    }
  }
  return `최대 확률 차이 ${최대차이.toExponential(2)}`;
});

검사("모델: 추론 시간", async () => {
  const 모델 = await 모델_약속;
  const 입력 = new Float32Array(784);
  모델.추론(입력); // 첫 실행은 준비 시간이 섞이므로 제외
  const 횟수 = 20;
  const 시작 = performance.now();
  for (let 번 = 0; 번 < 횟수; 번++) 모델.추론(입력);
  return `1회 평균 ${((performance.now() - 시작) / 횟수).toFixed(1)} ms`;
});

검사("모델: 잘못된 입력 크기는 오류", async () => {
  const 모델 = await 모델_약속;
  let 오류남 = false;
  try {
    모델.추론(new Float32Array(10));
  } catch {
    오류남 = true;
  }
  확인(오류남, "784 가 아닌 입력에서 오류가 나야 합니다");
});

검사("모델: 없는 경로면 이유를 알려 주는 오류", async () => {
  let 메시지 = "";
  try {
    await 모델_불러오기(new URL("./없는폴더/", import.meta.url));
  } catch (오류) {
    메시지 = 오류.message;
  }
  확인(메시지.includes("weights.json"), `오류 메시지에 파일 이름이 있어야 합니다: "${메시지}"`);
});
```

- [ ] **Step 2: 실행기에 등록** — `web_version/tests/검사.js`의 배열을 바꾼다.

```js
const 검사_모듈 = ["./연산_검사.js", "./모델_검사.js"];
```

- [ ] **Step 3: 검사가 실패하는지 확인**

검사 페이지를 새로고침하고 Task 3 Step 7의 `javascript_tool` 코드로 결과를 읽는다.
Expected: 연산 9개 통과, `./모델_검사.js 불러오기` 실패 1개

- [ ] **Step 4: 모델 모듈 작성** — `web_version/js/모델.js`

```js
// 가중치를 불러와 손글씨 숫자 인식 CNN 순전파를 수행합니다.
// 층 구성은 desktop_version/model.py 의 숫자인식CNN 과 같고,
// 배치정규화는 export_web.py 가 합성곱에 미리 접어 두었습니다.
import { 합성곱3x3, 렐루, 최대풀링2x2, 완전연결, 소프트맥스 } from "./연산.js";

const 지원_형식_버전 = 1;
const 필요한_층 = ["합성곱1", "합성곱2", "합성곱3", "합성곱4", "완전연결1", "완전연결2"];

async function 받아오기(주소) {
  const 응답 = await fetch(주소);
  if (!응답.ok) throw new Error(`HTTP ${응답.status}`);
  return 응답;
}

/**
 * model/ 폴더의 weights.json 과 weights.bin 을 불러와 모델을 만듭니다.
 * @param {URL|string} 기준경로  "/" 로 끝나는 model 폴더 주소
 */
export async function 모델_불러오기(기준경로) {
  let 목록;
  try {
    목록 = await (await 받아오기(new URL("weights.json", 기준경로))).json();
  } catch (오류) {
    throw new Error(`weights.json 을 불러오지 못했습니다 (${오류.message})`);
  }
  if (목록.형식_버전 !== 지원_형식_버전) {
    throw new Error(`weights.json 형식 버전 ${목록.형식_버전} 은 지원하지 않습니다 (지원: ${지원_형식_버전})`);
  }

  let 전체;
  try {
    // 모든 브라우저는 리틀 엔디언이므로 Float32Array 로 바로 읽어도 됩니다.
    전체 = new Float32Array(await (await 받아오기(new URL("weights.bin", 기준경로))).arrayBuffer());
  } catch (오류) {
    throw new Error(`weights.bin 을 불러오지 못했습니다 (${오류.message})`);
  }

  const 층 = {};
  for (const 항목 of 목록.층) {
    const 자르기 = (정보) => {
      if (정보.시작 + 정보.개수 > 전체.length) {
        throw new Error(`weights.bin 이 목록보다 짧습니다 (${항목.이름})`);
      }
      return 전체.subarray(정보.시작, 정보.시작 + 정보.개수);
    };
    층[항목.이름] = { 모양: 항목.가중치.모양, 가중치: 자르기(항목.가중치), 편향: 자르기(항목.편향) };
  }
  for (const 이름 of 필요한_층) {
    if (!층[이름]) throw new Error(`weights.json 에 '${이름}' 층이 없습니다`);
  }

  return {
    정규화: 목록.정규화,
    추론: (입력) => 순전파(층, 입력),
  };
}

function 합성곱층(입력, 층정보, 크기) {
  const [출력채널, 입력채널] = 층정보.모양;
  return 렐루(합성곱3x3(입력, 입력채널, 크기, 크기, 층정보.가중치, 층정보.편향, 출력채널));
}

function 완전연결층(입력, 층정보) {
  return 완전연결(입력, 층정보.가중치, 층정보.편향, 층정보.모양[0]);
}

/** 1x28x28 정규화 입력 → 0~9 확률 10개 */
function 순전파(층, 입력) {
  if (입력.length !== 28 * 28) {
    throw new Error(`입력은 784 개여야 합니다 (받은 개수: ${입력.length})`);
  }
  let x = 합성곱층(입력, 층.합성곱1, 28);            // 32x28x28
  x = 최대풀링2x2(합성곱층(x, 층.합성곱2, 28), 32, 28, 28); // 32x14x14
  x = 합성곱층(x, 층.합성곱3, 14);                   // 64x14x14
  x = 최대풀링2x2(합성곱층(x, 층.합성곱4, 14), 64, 14, 14); // 64x7x7 → 펼치면 3136
  x = 렐루(완전연결층(x, 층.완전연결1));             // 128
  x = 완전연결층(x, 층.완전연결2);                   // 10 (드롭아웃은 추론에서 쓰지 않음)
  return 소프트맥스(x);
}
```

- [ ] **Step 5: 검사 통과 확인**

검사 페이지를 새로고침하고 결과를 읽는다.
Expected: `통과: 14, 실패: 0`, 메모에 `최대 확률 차이 …e-7` 수준과 `1회 평균 … ms`. 추론 시간 값을 기록해 둔다(보고용).

- [ ] **Step 6: 커밋**

```bash
git add web_version/js/모델.js web_version/tests/모델_검사.js web_version/tests/검사.js
git commit -m "웹 버전 모델 불러오기와 순전파 추가" -m "weights.json/bin 을 읽어 PyTorch 와 같은 순서로 추론하고, 기준값 20장이 1e-4 이내로 일치함을 검사" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: 손글씨 전처리 (`전처리.js`)

**Files:**
- Create: `web_version/tests/전처리_검사.js`, `web_version/js/전처리.js`
- Modify: `web_version/tests/검사.js` (`검사_모듈` 배열)

**Interfaces:**
- Consumes: `모델_불러오기`, `최댓값_위치`
- Produces: `전처리(캔버스: HTMLCanvasElement, 정규화: {평균, 표준편차}): Float32Array(784) | null` — 검은 바탕에 흰 글씨(빨강 채널 기준)인 캔버스를 받는다. 아무것도 없으면 `null`.

- [ ] **Step 1: 전처리 검사 작성** — `web_version/tests/전처리_검사.js`

```js
// 전처리.js 가 데스크톱과 같은 방식으로 그림을 28x28 로 바꾸는지 확인합니다.
// (desktop_version/검사_전처리.py 와 같은 좌표로 그립니다)
import { 검사, 근사같음, 확인 } from "./검사도구.js";
import { 전처리 } from "../js/전처리.js";
import { 모델_불러오기 } from "../js/모델.js";
import { 최댓값_위치 } from "../js/연산.js";

const 정규화 = { 평균: 0.1307, 표준편차: 0.3081 };
const 모델_약속 = 모델_불러오기(new URL("../model/", import.meta.url));

function 새_캔버스() {
  const 캔버스 = document.createElement("canvas");
  캔버스.width = 280;
  캔버스.height = 280;
  const 붓 = 캔버스.getContext("2d", { willReadFrequently: true });
  붓.fillStyle = "#000";
  붓.fillRect(0, 0, 280, 280);
  붓.strokeStyle = "#fff";
  붓.lineWidth = 18;
  붓.lineJoin = "round";
  return { 캔버스, 붓 };
}

검사("전처리: 빈 그림은 null", () => {
  const { 캔버스 } = 새_캔버스();
  확인(전처리(캔버스, 정규화) === null, "빈 그림이면 null 이어야 합니다");
});

검사("전처리: 결과 크기 784, 바탕은 정규화된 0, 무게중심은 가운데", () => {
  const { 캔버스, 붓 } = 새_캔버스();
  붓.fillStyle = "#fff";
  붓.fillRect(20, 30, 60, 90); // 왼쪽 위에 치우친 직사각형
  const 결과 = 전처리(캔버스, 정규화);
  확인(결과 instanceof Float32Array && 결과.length === 784, "Float32Array(784) 여야 합니다");
  근사같음([결과[0]], [(0 - 0.1307) / 0.3081], 1e-6, "바탕 값");
  // 정규화를 되돌려 밝기로 무게중심 계산
  let 합 = 0, 합y = 0, 합x = 0;
  for (let 위치 = 0; 위치 < 784; 위치++) {
    const 밝기 = 결과[위치] * 0.3081 + 0.1307;
    합 += 밝기;
    합y += Math.floor(위치 / 28) * 밝기;
    합x += (위치 % 28) * 밝기;
  }
  확인(Math.abs(합y / 합 - 14) <= 1 && Math.abs(합x / 합 - 14) <= 1,
    `무게중심이 (14,14) 근처여야 합니다: (${(합y / 합).toFixed(2)}, ${(합x / 합).toFixed(2)})`);
});

const 그림_검사 = [
  ["세로선", 1, (붓) => { 붓.beginPath(); 붓.moveTo(140, 40); 붓.lineTo(140, 240); 붓.stroke(); }],
  // PIL 의 ellipse 는 테두리를 상자 안쪽에 그리므로 반지름을 선 굵기의 절반만큼 줄입니다.
  ["타원", 0, (붓) => { 붓.beginPath(); 붓.ellipse(140, 140, 51, 91, 0, 0, Math.PI * 2); 붓.stroke(); }],
  ["꺾은선", 7, (붓) => { 붓.beginPath(); 붓.moveTo(70, 50); 붓.lineTo(210, 50); 붓.lineTo(110, 240); 붓.stroke(); }],
];

for (const [이름, 정답, 그리기] of 그림_검사) {
  검사(`전처리 + 모델: ${이름}을 ${정답}(으)로 인식`, async () => {
    const 모델 = await 모델_약속;
    const { 캔버스, 붓 } = 새_캔버스();
    그리기(붓);
    const 확률 = 모델.추론(전처리(캔버스, 모델.정규화));
    const 결과 = 최댓값_위치(확률);
    확인(결과 === 정답, `${정답} 이어야 하는데 ${결과} (확률 ${(확률[결과] * 100).toFixed(1)}%)`);
    return `확신도 ${(확률[정답] * 100).toFixed(1)}%`;
  });
}
```

- [ ] **Step 2: 실행기에 등록** — `web_version/tests/검사.js`

```js
const 검사_모듈 = ["./연산_검사.js", "./모델_검사.js", "./전처리_검사.js"];
```

- [ ] **Step 3: 검사가 실패하는지 확인**

검사 페이지 새로고침 후 결과 읽기.
Expected: 14개 통과, `./전처리_검사.js 불러오기` 실패 1개

- [ ] **Step 4: 전처리 모듈 작성** — `web_version/js/전처리.js`

```js
// 그림판 캔버스를 MNIST 형식(28x28, 가운데 정렬, 정규화)으로 바꿉니다.
// desktop_version/app.py 의 전처리와 같은 순서이므로 한쪽을 고치면 다른 쪽도 함께 고치세요.
//   1) 글씨가 있는 영역만 잘라내기
//   2) 비율을 유지하며 긴 변을 20픽셀로 줄이기
//   3) 28x28 검은 바탕 가운데에 붙이기
//   4) 밝기 무게중심이 (14, 14)에 오도록 이동
//   5) (값/255 − 평균) / 표준편차 로 정규화

const 크기 = 28;
const 글씨_상자 = 20;

/**
 * @param {HTMLCanvasElement} 캔버스  검은 바탕에 흰 글씨
 * @param {{평균:number, 표준편차:number}} 정규화
 * @returns {Float32Array|null}  784 개 값, 빈 그림이면 null
 */
export function 전처리(캔버스, 정규화) {
  const 너비 = 캔버스.width;
  const 높이 = 캔버스.height;
  const 픽셀 = 캔버스.getContext("2d", { willReadFrequently: true }).getImageData(0, 0, 너비, 높이).data;

  // 1) 글씨가 있는 영역(빨강 채널 > 0)의 경계 상자
  let 왼 = 너비, 위 = 높이, 오른 = -1, 아래 = -1;
  for (let y = 0; y < 높이; y++) {
    for (let x = 0; x < 너비; x++) {
      if (픽셀[(y * 너비 + x) * 4] > 0) {
        if (x < 왼) 왼 = x;
        if (x > 오른) 오른 = x;
        if (y < 위) 위 = y;
        if (y > 아래) 아래 = y;
      }
    }
  }
  if (오른 < 0) return null; // 아무것도 그리지 않음

  // 2) 긴 변을 20픽셀로 (비율 유지)
  const 상자너비 = 오른 - 왼 + 1;
  const 상자높이 = 아래 - 위 + 1;
  const 배율 = 글씨_상자 / Math.max(상자너비, 상자높이);
  const 새너비 = Math.max(1, Math.round(상자너비 * 배율));
  const 새높이 = Math.max(1, Math.round(상자높이 * 배율));

  // 3) 28x28 검은 바탕 가운데에 붙이기
  const 작은캔버스 = document.createElement("canvas");
  작은캔버스.width = 크기;
  작은캔버스.height = 크기;
  const 붓 = 작은캔버스.getContext("2d", { willReadFrequently: true });
  붓.fillStyle = "#000";
  붓.fillRect(0, 0, 크기, 크기);
  붓.imageSmoothingEnabled = true;
  붓.imageSmoothingQuality = "high";
  붓.drawImage(캔버스, 왼, 위, 상자너비, 상자높이,
    Math.floor((크기 - 새너비) / 2), Math.floor((크기 - 새높이) / 2), 새너비, 새높이);
  const 작은픽셀 = 붓.getImageData(0, 0, 크기, 크기).data;
  const 밝기 = new Float32Array(크기 * 크기);
  for (let 위치 = 0; 위치 < 밝기.length; 위치++) 밝기[위치] = 작은픽셀[위치 * 4];

  // 4) 무게중심을 가운데로 (정수 칸 이동)
  let 합 = 0, 합y = 0, 합x = 0;
  for (let y = 0; y < 크기; y++) {
    for (let x = 0; x < 크기; x++) {
      const 값 = 밝기[y * 크기 + x];
      합 += 값;
      합y += y * 값;
      합x += x * 값;
    }
  }
  const 이동x = 합 > 0 ? Math.round(14 - 합x / 합) : 0;
  const 이동y = 합 > 0 ? Math.round(14 - 합y / 합) : 0;

  // 5) 이동하면서 정규화
  const 결과 = new Float32Array(크기 * 크기);
  for (let y = 0; y < 크기; y++) {
    for (let x = 0; x < 크기; x++) {
      const 원래y = y - 이동y;
      const 원래x = x - 이동x;
      const 값 = 원래y >= 0 && 원래y < 크기 && 원래x >= 0 && 원래x < 크기 ? 밝기[원래y * 크기 + 원래x] : 0;
      결과[y * 크기 + x] = (값 / 255 - 정규화.평균) / 정규화.표준편차;
    }
  }
  return 결과;
}
```

- [ ] **Step 5: 검사 통과 확인**

검사 페이지 새로고침 후 결과 읽기.
Expected: `통과: 19, 실패: 0`. 1·0·7 모두 정답. 하나라도 틀리면 확신도와 함께 원인을 조사한다(`superpowers:systematic-debugging`). 억지로 좌표를 바꿔 통과시키지 않는다.

- [ ] **Step 6: 커밋**

```bash
git add web_version/js/전처리.js web_version/tests/전처리_검사.js web_version/tests/검사.js
git commit -m "웹 버전 손글씨 전처리 추가" -m "데스크톱과 같은 순서(자르기→20px 축소→가운데 배치→무게중심 정렬→정규화)로 캔버스를 28x28 입력으로 변환" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: 화면 (`index.html`, `style.css`, `화면.js`)

**Files:**
- Create: `web_version/index.html`, `web_version/style.css`, `web_version/js/화면.js`

**Interfaces:**
- Consumes: `모델_불러오기`, `전처리`, `최댓값_위치`
- Produces: 요소 id — `그림판`(canvas 280x280), `지우기단추`, `결과숫자`, `확신도`, `확률목록`, `상태`. 그림판은 모델이 준비되기 전 `잠김` 클래스를 가진다.

- [ ] **Step 1: 화면 뼈대 작성** — `web_version/index.html`

```html
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>손글씨 숫자 인식기</title>
  <meta name="description" content="검은 칸에 숫자를 그리면 브라우저 안에서 CNN이 0~9를 알아맞힙니다.">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <main class="앱">
    <h1>손글씨 숫자 인식기</h1>
    <p class="설명">검은 칸에 숫자(0~9)를 하나 그리면 손을 뗄 때 자동으로 인식합니다.</p>

    <div class="본문">
      <section class="그리기영역">
        <canvas id="그림판" class="잠김" width="280" height="280" aria-label="숫자를 그리는 칸"></canvas>
        <button id="지우기단추" type="button">지우기</button>
      </section>

      <section class="결과영역" aria-live="polite">
        <h2>인식 결과</h2>
        <div id="결과숫자">?</div>
        <div id="확신도">&nbsp;</div>
        <ol id="확률목록" aria-label="숫자별 확률"></ol>
      </section>
    </div>

    <p id="상태">모델 불러오는 중…</p>
    <p class="꼬리말">추론은 외부 라이브러리 없이 순수 자바스크립트로 이 브라우저 안에서만 이루어집니다.</p>
  </main>

  <script>
    // 파일을 직접 열면(file://) 모듈과 가중치를 불러올 수 없으므로 안내합니다.
    if (location.protocol === "file:") {
      const 상태 = document.getElementById("상태");
      상태.textContent = "파일을 직접 열면 동작하지 않습니다. web_version 폴더에서 'python 개발서버.py' 를 실행한 뒤 http://localhost:8000 으로 여세요.";
      상태.className = "오류";
    }
  </script>
  <script type="module" src="js/화면.js"></script>
</body>
</html>
```

- [ ] **Step 2: 모양 작성** — `web_version/style.css`

```css
/* 색상 토큰 (밝은 화면 / 어두운 화면) */
:root {
  --바탕: #f6f7f9;
  --카드: #ffffff;
  --글자: #1f2328;
  --흐린글자: #5b636e;
  --테두리: #d6dae0;
  --강조: #2e7d32;
  --막대: #90a4ae;
  --오류: #b3261e;
  color-scheme: light dark;
}
@media (prefers-color-scheme: dark) {
  :root {
    --바탕: #16181c;
    --카드: #1f2227;
    --글자: #e6e8eb;
    --흐린글자: #a3aab3;
    --테두리: #3a3f46;
    --강조: #66bb6a;
    --막대: #607d8b;
    --오류: #f28b82;
  }
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--바탕);
  color: var(--글자);
  font-family: "맑은 고딕", "Malgun Gothic", "Apple SD Gothic Neo", system-ui, sans-serif;
  line-height: 1.5;
}

.앱 {
  max-width: 720px;
  margin: 0 auto;
  padding: 24px 16px 40px;
}

h1 { font-size: 1.6rem; margin: 0 0 4px; }
h2 { font-size: 1.05rem; margin: 0; color: var(--흐린글자); font-weight: 600; }
.설명, .꼬리말 { color: var(--흐린글자); margin: 0 0 16px; }
.꼬리말 { font-size: 0.85rem; margin-top: 8px; }

.본문 {
  display: flex;
  gap: 24px;
  align-items: flex-start;
  background: var(--카드);
  border: 1px solid var(--테두리);
  border-radius: 12px;
  padding: 16px;
}

.그리기영역 {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: min(320px, 100%);
  flex-shrink: 0;
}

#그림판 {
  width: 100%;
  aspect-ratio: 1;
  background: #000;
  border-radius: 8px;
  cursor: crosshair;
  touch-action: none; /* 터치로 그릴 때 페이지가 스크롤되지 않게 */
}
#그림판.잠김 { opacity: 0.5; cursor: wait; }

#지우기단추 {
  font: inherit;
  padding: 8px 12px;
  border: 1px solid var(--테두리);
  border-radius: 8px;
  background: var(--바탕);
  color: var(--글자);
  cursor: pointer;
}
#지우기단추:hover { border-color: var(--흐린글자); }

.결과영역 { flex: 1; min-width: 0; text-align: center; }

#결과숫자 {
  font-size: 5rem;
  font-weight: 700;
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
}
#확신도 { color: var(--흐린글자); margin-bottom: 12px; }

#확률목록 { list-style: none; margin: 0; padding: 0; text-align: left; }
#확률목록 li {
  display: grid;
  grid-template-columns: 1.2em 1fr 3em;
  align-items: center;
  gap: 8px;
  margin: 3px 0;
  font-variant-numeric: tabular-nums;
}
.막대틀 {
  height: 14px;
  border: 1px solid var(--테두리);
  border-radius: 4px;
  overflow: hidden;
}
.막대 { height: 100%; width: 0; background: var(--막대); }
li.최고 .막대 { background: var(--강조); }
li.최고 { font-weight: 700; }
.퍼센트 { text-align: right; font-size: 0.85rem; color: var(--흐린글자); }

#상태 { margin: 12px 0 0; color: var(--흐린글자); }
#상태.오류 { color: var(--오류); font-weight: 600; }

/* 좁은 화면: 결과를 캔버스 아래로 */
@media (max-width: 639px) {
  .본문 { flex-direction: column; align-items: stretch; }
  .그리기영역 { width: 100%; max-width: 360px; margin: 0 auto; }
}
```

- [ ] **Step 3: 화면 동작 작성** — `web_version/js/화면.js`

```js
// 그림판 화면: 그리기, 인식 결과 표시, 지우기
import { 모델_불러오기 } from "./모델.js";
import { 전처리 } from "./전처리.js";
import { 최댓값_위치 } from "./연산.js";

const 펜_두께 = 18; // 캔버스 내부 크기 280px 기준 (데스크톱과 같음)

const 그림판 = document.getElementById("그림판");
const 붓 = 그림판.getContext("2d", { willReadFrequently: true });
const 지우기단추 = document.getElementById("지우기단추");
const 결과숫자 = document.getElementById("결과숫자");
const 확신도 = document.getElementById("확신도");
const 확률목록 = document.getElementById("확률목록");
const 상태 = document.getElementById("상태");

let 모델 = null;
let 그리는중 = false;
let 이전점 = null;
const 막대들 = [];

/** 0~9 확률 막대 10줄을 만듭니다. */
function 확률목록_만들기() {
  for (let 숫자 = 0; 숫자 < 10; 숫자++) {
    const 줄 = document.createElement("li");
    const 이름 = document.createElement("span");
    이름.textContent = 숫자;
    const 틀 = document.createElement("div");
    틀.className = "막대틀";
    const 막대 = document.createElement("div");
    막대.className = "막대";
    틀.appendChild(막대);
    const 퍼센트 = document.createElement("span");
    퍼센트.className = "퍼센트";
    퍼센트.textContent = "0%";
    줄.append(이름, 틀, 퍼센트);
    확률목록.appendChild(줄);
    막대들.push({ 줄, 막대, 퍼센트 });
  }
}

function 결과_표시(확률) {
  const 최고 = 확률 ? 최댓값_위치(확률) : -1;
  결과숫자.textContent = 확률 ? String(최고) : "?";
  확신도.textContent = 확률 ? `확신도: ${(확률[최고] * 100).toFixed(1)}%` : "\u00a0";
  막대들.forEach(({ 줄, 막대, 퍼센트 }, 숫자) => {
    const 값 = 확률 ? 확률[숫자] : 0;
    막대.style.width = `${값 * 100}%`;
    퍼센트.textContent = `${Math.round(값 * 100)}%`;
    줄.classList.toggle("최고", 숫자 === 최고);
  });
}

function 그림판_지우기() {
  붓.fillStyle = "#000";
  붓.fillRect(0, 0, 그림판.width, 그림판.height);
  결과_표시(null);
}

/** 화면 좌표를 캔버스 내부 좌표(280x280)로 바꿉니다. */
function 캔버스_좌표(이벤트) {
  const 사각 = 그림판.getBoundingClientRect();
  return {
    x: ((이벤트.clientX - 사각.left) * 그림판.width) / 사각.width,
    y: ((이벤트.clientY - 사각.top) * 그림판.height) / 사각.height,
  };
}

function 선긋기(시작, 끝) {
  붓.strokeStyle = "#fff";
  붓.lineWidth = 펜_두께;
  붓.lineCap = "round";
  붓.lineJoin = "round";
  붓.beginPath();
  붓.moveTo(시작.x, 시작.y);
  붓.lineTo(끝.x, 끝.y);
  붓.stroke();
}

function 인식하기() {
  const 입력 = 전처리(그림판, 모델.정규화);
  if (!입력) return; // 빈 그림
  결과_표시(모델.추론(입력));
}

// 마우스·터치·펜을 Pointer Events 하나로 처리합니다.
그림판.addEventListener("pointerdown", (이벤트) => {
  if (!모델) return;
  if (이벤트.button === 2) {
    그림판_지우기(); // 오른쪽 클릭으로 지우기
    return;
  }
  이벤트.preventDefault();
  그림판.setPointerCapture(이벤트.pointerId);
  그리는중 = true;
  이전점 = 캔버스_좌표(이벤트);
  선긋기(이전점, 이전점); // 점 하나 찍기
});

그림판.addEventListener("pointermove", (이벤트) => {
  if (!그리는중) return;
  const 현재점 = 캔버스_좌표(이벤트);
  선긋기(이전점, 현재점);
  이전점 = 현재점;
});

function 그리기_끝() {
  if (!그리는중) return;
  그리는중 = false;
  이전점 = null;
  인식하기();
}
그림판.addEventListener("pointerup", 그리기_끝);
그림판.addEventListener("pointercancel", 그리기_끝);
그림판.addEventListener("contextmenu", (이벤트) => 이벤트.preventDefault());
지우기단추.addEventListener("click", 그림판_지우기);

async function 시작() {
  확률목록_만들기();
  그림판_지우기();
  try {
    모델 = await 모델_불러오기(new URL("../model/", import.meta.url));
    그림판.classList.remove("잠김");
    상태.textContent = "준비 완료 — 숫자를 그려 보세요.";
  } catch (오류) {
    상태.textContent = `모델을 불러오지 못했습니다: ${오류.message}`;
    상태.className = "오류";
    console.error(오류);
  }
}

시작();
```

- [ ] **Step 4: 브라우저에서 직접 그려 확인** (데스크톱 크기)

`navigate`로 `http://localhost:8000/`을 연다. 확인 항목:
1. `read_page`/`get_page_text`로 `상태`가 `준비 완료 — 숫자를 그려 보세요.`인지 확인
2. `computer` `screenshot`으로 캔버스 위치를 찾은 뒤 `left_click_drag`로 캔버스 가운데에 위→아래 세로선을 긋는다
3. `find`/`get_page_text`로 `결과숫자`가 `1`인지, 확률 막대가 채워졌는지 확인
4. `지우기` 단추를 눌러 `결과숫자`가 `?`로 돌아오는지 확인
5. `read_console_messages`(onlyErrors)로 오류가 없는지 확인

Expected: 세 가지 모두 기대대로, 콘솔 오류 없음

- [ ] **Step 5: 좁은 화면 확인**

`resize_window` preset `mobile` → 새로고침 → `screenshot`. `javascript_tool`로 가로 스크롤이 없는지 확인:

```js
({ 문서폭: document.documentElement.scrollWidth, 화면폭: innerWidth, 결과가_아래: document.querySelector(".결과영역").getBoundingClientRect().top > document.getElementById("그림판").getBoundingClientRect().bottom })
```
Expected: `문서폭 <= 화면폭`, `결과가_아래: true`. 확인 후 `resize_window` preset `desktop`으로 되돌린다.

- [ ] **Step 6: 전체 검사 회귀 확인**

`http://localhost:8000/tests/검사.html` 결과 읽기.
Expected: `통과: 19, 실패: 0`

- [ ] **Step 7: 커밋**

```bash
git add web_version/index.html web_version/style.css web_version/js/화면.js
git commit -m "웹 버전 그림판 화면 추가" -m "마우스·터치로 그리면 자동 인식, 확신도와 0~9 확률 막대 표시, 좁은 화면 배치와 어두운 화면 지원" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: 안내 문서 (CLAUDE.md 3개, README)

**Files:**
- Create: `web_version/CLAUDE.md`, `CLAUDE.md`(루트)
- Modify: `README.md`

**Interfaces:**
- Consumes: 앞 작업들의 파일 이름·명령어
- Produces: 없음

- [ ] **Step 1: 웹 버전 안내 작성** — `web_version/CLAUDE.md`

````markdown
# CLAUDE.md — 웹 버전

이 폴더는 **외부 라이브러리 없이 순수 자바스크립트로 추론**하는 손글씨 숫자 인식 웹 버전입니다.
GitHub Pages에 정적 사이트로 배포됩니다: https://rlayejinn-ui.github.io/Study01_MNIST/
저장소 전체 규칙은 루트의 `CLAUDE.md`를 먼저 보세요.

## 절대 규칙

- **외부 라이브러리·CDN·npm·번들러를 쓰지 않습니다.** 브라우저 기본 기능(ES 모듈, Canvas, Pointer Events, fetch)만 씁니다.
- 빌드 단계가 없습니다. 이 폴더 그대로가 배포 결과물입니다.
- 코드·주석·함수명·변수명·CSS 클래스·요소 id는 한글로 씁니다.

## 로컬에서 실행

`index.html`을 더블클릭(file://)하면 브라우저 보안 정책 때문에 동작하지 않습니다. 개발 서버로 여세요.

```bash
python 개발서버.py
```

- 앱: http://localhost:8000
- 검사: http://localhost:8000/tests/검사.html (모든 항목이 ✅ 여야 합니다)

## 모듈 구조 (의존 방향: 위 → 아래)

| 파일 | 역할 |
| --- | --- |
| `js/화면.js` | 그리기(Pointer Events), 결과·확률 막대 표시, 지우기, 불러오기 상태 |
| `js/전처리.js` | `전처리(캔버스, 정규화)` → `Float32Array(784)` 또는 `null` |
| `js/모델.js` | `모델_불러오기(model폴더주소)` → `{ 정규화, 추론(입력784) → 확률10 }` |
| `js/연산.js` | 합성곱3x3·렐루·최대풀링2x2·완전연결·소프트맥스·최댓값_위치 (순수 함수) |

`연산.js`는 DOM을 쓰지 않는 순수 함수만 둡니다. 화면 코드가 아래 모듈로 새지 않게 하세요.

## 가중치 (`model/`)

- `weights.bin`: float32 리틀 엔디언, `weights.json`: 층별 `모양`·`시작`·`개수`(float32 원소 단위)와 정규화 상수
- **직접 고치지 마세요.** `desktop_version/export_web.py`가 `mnist_cnn.pt`에서 만듭니다.
- 배치정규화는 이미 합성곱에 접혀 있으므로 웹에는 배치정규화 코드가 없습니다.
- 층 구성이 바뀌면 `js/모델.js`의 `순전파`와 `필요한_층`을 함께 고칩니다.

## 전처리

`js/전처리.js`는 `desktop_version/app.py`의 `전처리`와 **같은 순서**입니다
(자르기 → 긴 변 20px 축소 → 28x28 가운데 배치 → 무게중심 정렬 → 정규화). 한쪽을 고치면 다른 쪽도 고치세요.
브라우저 축소와 PIL LANCZOS는 픽셀값이 조금 다르므로 전처리는 **인식 결과**로 검사합니다.

## 검사

- `tests/검사.html`이 `tests/검사.js`의 `검사_모듈` 목록을 불러와 실행하고, 결과를 화면과 `window.검사결과`에 남깁니다.
- 새 검사 파일은 `검사도구.js`의 `검사`, `확인`, `근사같음`을 쓰고 `검사_모듈`에 추가합니다.
- `tests/기준값.json`은 `export_web.py`가 만든 PyTorch 기준값입니다. JS 확률은 이 값과 **1e-4 이내**여야 합니다.

## 배포

`main`에 푸시할 때 `web_version/**`이 바뀌면 `.github/workflows/pages.yml`이 이 폴더를 GitHub Pages로 배포합니다.
Actions 탭에서 수동 실행(`workflow_dispatch`)도 됩니다. 모든 경로는 상대 경로로 써야 `/Study01_MNIST/` 아래에서 동작합니다.
````

- [ ] **Step 2: 루트 안내 작성** — `CLAUDE.md`

````markdown
# CLAUDE.md

이 파일은 Claude Code가 이 저장소에서 작업할 때 참고하는 안내서입니다.

## 프로젝트 개요

마우스(또는 손가락)로 그린 손글씨 숫자를 CNN으로 인식하는 학습용 프로젝트입니다.
같은 학습 가중치를 쓰는 두 버전으로 나뉩니다.

| 폴더 | 내용 | 안내 |
| --- | --- | --- |
| `desktop_version/` | PyTorch 학습 + tkinter 데스크톱 앱, 웹용 가중치 내보내기 | `desktop_version/CLAUDE.md` |
| `web_version/` | 순수 자바스크립트 추론 웹 앱 (GitHub Pages 배포) | `web_version/CLAUDE.md` |

작업할 폴더의 CLAUDE.md를 꼭 함께 읽으세요.

## 공통 규칙

- **모든 코드, 주석, 변수명, 함수명, 클래스명, 화면 문구를 한글로 작성합니다.**
  외부 라이브러리·브라우저 API 이름과, 문법상 영문만 되는 곳(GitHub Actions job id 등)만 예외입니다.
- 두 버전은 **같은 모델**을 씁니다. 가중치의 원본은 `desktop_version/mnist_cnn.pt` 하나입니다.
- 재학습하거나 모델을 바꾸면 `desktop_version/export_web.py`를 실행하고 `web_version/model/`,
  `web_version/tests/기준값.json`을 함께 커밋합니다.
- 전처리 순서와 정규화 상수(0.1307 / 0.3081)는 두 버전이 같아야 합니다. 한쪽을 고치면 다른 쪽도 고칩니다.

## 흐름

```
desktop_version/train.py → mnist_cnn.pt → export_web.py → web_version/model/weights.{json,bin}
                                                        → web_version/tests/기준값.json
```

## 배포

`.github/workflows/pages.yml`이 `main` 푸시 시 `web_version/`을 https://rlayejinn-ui.github.io/Study01_MNIST/ 로 배포합니다.

## 문서

설계 문서와 구현 계획은 `docs/superpowers/` 아래에 있습니다.
````

- [ ] **Step 3: README 교체** — `README.md`

````markdown
# 손글씨 숫자 인식기 (MNIST + PyTorch)

마우스나 손가락으로 숫자를 그리면 CNN 모델이 0~9 중 어떤 숫자인지 알아맞히는 프로그램입니다.
같은 학습 가중치(테스트 정확도 99.28%)를 쓰는 **데스크톱 버전**과 **웹 버전**이 있습니다.

## 🌐 웹 버전 — 바로 써 보기

**https://rlayejinn-ui.github.io/Study01_MNIST/**

- 설치 없이 브라우저에서 동작하며, 휴대폰 터치로도 그릴 수 있습니다.
- 외부 라이브러리 없이 순수 자바스크립트로 이 브라우저 안에서 추론합니다.
- 자세한 내용: [`web_version/`](web_version/)

로컬에서 실행하려면:

```bash
cd web_version
python 개발서버.py
```

그다음 http://localhost:8000 을 엽니다. (`index.html`을 더블클릭하면 브라우저 보안 정책 때문에 동작하지 않습니다.)

## 🖥️ 데스크톱 버전

PyTorch로 학습하고 tkinter 창에서 인식합니다. 자세한 내용: [`desktop_version/`](desktop_version/)

```bash
cd desktop_version
python -m venv .venv
.venv\Scripts\python.exe -m pip install torch torchvision pillow --index-url https://download.pytorch.org/whl/cpu
.venv\Scripts\python.exe app.py
```

Windows 파일 탐색기에서 `desktop_version/app.py`를 **더블클릭**해도 실행됩니다.

다시 학습하려면 `train.py`를 실행한 뒤, 웹 버전도 새 모델을 쓰도록 `export_web.py`를 실행합니다.

## 구성

```
desktop_version/   model.py · train.py · app.py · export_web.py · mnist_cnn.pt
web_version/       index.html · style.css · js/(연산·모델·전처리·화면) · model/ · tests/
```

## 모델 구조

`[합성곱(1→32) → 배치정규화 → ReLU] → [합성곱(32→32) → 배치정규화 → ReLU] → 맥스풀링 → [합성곱(32→64) → 배치정규화 → ReLU] → [합성곱(64→64) → 배치정규화 → ReLU] → 맥스풀링 → 완전연결(3136→128) → 드롭아웃 → 완전연결(128→10)`

손실 함수는 교차 엔트로피, 옵티마이저는 Adam(학습률 0.001, 에폭마다 0.7배 감소)입니다.
학습 데이터에 회전·이동·확대 변형을 주어 직접 그린 글씨에도 잘 동작하도록 했습니다.
웹 버전은 배치정규화를 합성곱에 미리 합친 가중치를 씁니다(결과는 같습니다).
````

- [ ] **Step 4: 문서 속 명령과 파일 이름 확인**

Run: `ls desktop_version/export_web.py desktop_version/검사_전처리.py desktop_version/검사_내보내기.py web_version/개발서버.py web_version/js/연산.js web_version/js/모델.js web_version/js/전처리.js web_version/js/화면.js web_version/tests/검사.html`
Expected: 모두 존재 (오류 없음)

- [ ] **Step 5: 커밋**

```bash
git add CLAUDE.md README.md web_version/CLAUDE.md
git commit -m "루트·웹 버전 CLAUDE.md와 README 작성" -m "두 버전의 역할과 공통 규칙, 웹 버전 모듈 구조·검사·배포 방법을 정리" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 8: GitHub Pages 배포

**Files:**
- Create: `.github/workflows/pages.yml`

**Interfaces:**
- Consumes: `web_version/` 전체
- Produces: https://rlayejinn-ui.github.io/Study01_MNIST/

- [ ] **Step 1: 워크플로 작성** — `.github/workflows/pages.yml`

(액션 주 버전은 계획 작성일에 `gh api repos/<액션>/releases/latest`로 확인한 최신 값이다.)

```yaml
# 웹 버전(web_version 폴더)을 GitHub Pages 로 배포합니다.
name: 웹 버전 배포 (GitHub Pages)

on:
  push:
    branches: [main]
    paths:
      - "web_version/**"
      - ".github/workflows/pages.yml"
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

# 배포가 겹치면 마지막 것만 남깁니다.
concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  deploy:
    name: 배포
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: 저장소 가져오기
        uses: actions/checkout@v7
      - name: Pages 설정
        uses: actions/configure-pages@v6
      - name: web_version 폴더 올리기
        uses: actions/upload-pages-artifact@v5
        with:
          path: web_version
      - name: 배포
        id: deployment
        uses: actions/deploy-pages@v5
```

- [ ] **Step 2: 커밋**

```bash
git add .github/workflows/pages.yml
git commit -m "웹 버전 GitHub Pages 배포 워크플로 추가" -m "main 푸시 시 web_version 폴더만 Pages 로 배포" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

- [ ] **Step 3: 사용자 확인 후 Pages 켜기** (⚠️ 공개 설정 변경 — 실행 직전에 사용자에게 묻고 "예"를 받은 뒤에만)

```bash
"/c/Program Files/GitHub CLI/gh.exe" api -X POST repos/rlayejinn-ui/Study01_MNIST/pages -f build_type=workflow \
  || "/c/Program Files/GitHub CLI/gh.exe" api -X PUT repos/rlayejinn-ui/Study01_MNIST/pages -f build_type=workflow
"/c/Program Files/GitHub CLI/gh.exe" api repos/rlayejinn-ui/Study01_MNIST/pages --jq '{build_type, html_url}'
```
Expected: `{"build_type":"workflow","html_url":"https://rlayejinn-ui.github.io/Study01_MNIST/"}`

- [ ] **Step 4: 푸시** (공개 저장소에 올리는 일이므로 Step 3과 함께 사용자 확인을 받는다)

```bash
git push origin main
```

- [ ] **Step 5: 배포 완료 대기**

```bash
"/c/Program Files/GitHub CLI/gh.exe" run list --workflow pages.yml --limit 1
"/c/Program Files/GitHub CLI/gh.exe" run watch "$("/c/Program Files/GitHub CLI/gh.exe" run list --workflow pages.yml --limit 1 --json databaseId --jq '.[0].databaseId')" --exit-status
```
Expected: 실행 결과 `completed success`. 실패하면 `gh run view --log-failed`로 원인을 확인한다.

- [ ] **Step 6: 배포된 사이트 확인**

브라우저 창에서 `https://rlayejinn-ui.github.io/Study01_MNIST/tests/검사.html`을 열고 Task 3 Step 7의 코드로 결과를 읽는다.
Expected: `통과: 19, 실패: 0`

그다음 `https://rlayejinn-ui.github.io/Study01_MNIST/`을 열어 `상태`가 `준비 완료`이고, 세로선을 그리면 `1`이 나오는지 확인한다.
