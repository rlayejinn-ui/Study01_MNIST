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
.venv/Scripts/python.exe -m pip install torch torchvision pillow --index-url https://download.pytorch.org/whl/cpu
.venv/Scripts/python.exe app.py
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
