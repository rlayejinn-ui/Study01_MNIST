# 웹 버전 / 데스크톱 버전 분리 설계

- 작성일: 2026-09-22
- 상태: 승인됨 (브레인스토밍에서 부분별 승인 완료)

## 1. 목표

손글씨 숫자 인식 프로그램을 두 버전으로 나눈다.

- **데스크톱 버전** (`desktop_version/`): 기존 PyTorch + tkinter 코드를 그대로 옮긴다.
- **웹 버전** (`web_version/`): 외부 라이브러리 없이 순수 자바스크립트로 추론하고,
  GitHub Pages에 정적 사이트로 배포한다.

두 버전은 **같은 학습 가중치**(`mnist_cnn.pt`, 테스트 정확도 99.28%)를 사용한다.

### 성공 기준

1. `desktop_version/app.py`가 폴더 이동 후에도 더블클릭·명령어 실행 모두 동작한다.
2. 웹 버전이 외부 라이브러리·CDN 없이 동작한다.
3. 같은 28x28 입력에 대해 JS 추론 확률과 PyTorch 확률의 차이가 모든 값에서 1e-4 이하이고,
   예측 숫자가 모두 같다.
4. 웹에서 마우스와 터치 모두로 그려 인식할 수 있다.
5. `main`에 푸시하면 GitHub Actions가 `web_version`을
   https://rlayejinn-ui.github.io/Study01_MNIST/ 로 배포한다.
6. 루트, `desktop_version`, `web_version`에 각각 CLAUDE.md가 있다.

### 범위 밖

- 웹 전용 모델 별도 학습, 브라우저 내 학습
- 번들러·npm·빌드 도구 도입
- 28x28 미리보기 등 데스크톱에 없는 추가 기능

## 2. 폴더 구조

```
Study01_MNIST/
├─ README.md                   전체 소개 (두 버전 안내, 웹 주소)
├─ CLAUDE.md                   공통 규칙 + 폴더별 CLAUDE.md 안내
├─ .gitignore                  폴더 기준 경로로 조정
├─ .github/workflows/pages.yml web_version 배포
├─ docs/superpowers/           설계 문서, 구현 계획
├─ desktop_version/
│  ├─ CLAUDE.md
│  ├─ model.py  train.py  app.py  mnist_cnn.pt   (git mv로 이동)
│  ├─ export_web.py            .pt → web_version/model/ 변환 (신규)
│  ├─ .venv/  data/            git 제외
└─ web_version/
   ├─ CLAUDE.md
   ├─ index.html  style.css
   ├─ js/연산.js  js/모델.js  js/전처리.js  js/화면.js
   ├─ model/weights.json  model/weights.bin
   └─ tests/검사.html  tests/검사.js  tests/기준값.json
```

### 이동 규칙

- 코드 파일은 `git mv`로 옮겨 기록을 유지한다. 내용은 바꾸지 않는다
  (`app.py`는 이미 자기 폴더 기준으로 `.venv`와 가중치를 찾는다).
- Windows 가상환경은 옮기면 일부 실행 파일이 깨지므로 `desktop_version/.venv`를
  **새로 만들고** 루트 `.venv`는 삭제한다.
- `data/`(MNIST 원본)는 `desktop_version/data/`로 옮긴다.

### 데이터 흐름

```
train.py → mnist_cnn.pt → export_web.py → web_version/model/weights.{json,bin}
                                        → web_version/tests/기준값.json
```

재학습 후에는 `export_web.py`를 다시 실행해야 두 버전이 같은 모델을 쓴다.

## 3. 가중치 내보내기 (`desktop_version/export_web.py`)

### 배치정규화 접기

각 `Conv2d → BatchNorm2d` 쌍을 하나의 합성곱으로 합친다.

```
배율 = γ / sqrt(σ² + ε)
W' = W × 배율 (출력 채널별)
b' = (b − μ) × 배율 + β
```

결과 층 목록: `합성곱1 ~ 합성곱4`(각 3x3, 패딩 1), `완전연결1`(3136→128), `완전연결2`(128→10).
내보내기 전, 접은 모델과 원래 모델(평가 모드)의 출력 차이가 1e-5 이하인지 스크립트 안에서 확인하고,
어긋나면 오류로 중단한다.

### 파일 형식

- `weights.bin`: 모든 텐서를 float32 **리틀 엔디언**으로 이어 붙인 이진 파일
- `weights.json`:

```json
{
  "형식_버전": 1,
  "정규화": { "평균": 0.1307, "표준편차": 0.3081 },
  "층": [
    { "이름": "합성곱1", "종류": "합성곱", "가중치": { "모양": [32, 1, 3, 3], "시작": 0, "개수": 288 },
      "편향": { "모양": [32], "시작": 288, "개수": 32 } }
  ]
}
```

(예시는 첫 층만 보인 것이며, 실제 파일에는 6개 층이 같은 형식으로 순서대로 들어간다.
완전연결 층의 `종류`는 `"완전연결"`이다.)

`시작`과 `개수`는 float32 원소 단위다. 텐서 배치 순서는 PyTorch와 같다
(합성곱: `[출력, 입력, 높이, 너비]`, 완전연결: `[출력, 입력]`).

### 기준값

MNIST 테스트 이미지 앞 20장에 대해 정규화된 입력(784개)과 PyTorch softmax 확률(10개),
정답 라벨을 `web_version/tests/기준값.json`에 저장한다.

## 4. 웹 버전 구조

순수 ES 모듈(`<script type="module">`)로 작성하고, 각 파일은 한 가지 일만 맡는다.
코드·주석·함수명·변수명은 한글로 쓴다.

| 파일 | 역할 | 의존 |
| --- | --- | --- |
| `js/연산.js` | `합성곱3x3`, `렐루`, `최대풀링2x2`, `완전연결`, `소프트맥스`. `Float32Array`를 받아 새 `Float32Array`를 돌려주는 순수 함수 | 없음 |
| `js/모델.js` | `모델_불러오기(기준경로)` → `{ 추론(입력784) → 확률10 }` | 연산.js |
| `js/전처리.js` | `전처리(캔버스)` → 정규화된 `Float32Array(784)` 또는 빈 그림이면 `null` | Canvas API |
| `js/화면.js` | 그리기(Pointer Events), 결과·확신도·확률 막대 표시, 지우기, 불러오기 상태 | 위 모듈 |

### 순전파 순서 (데스크톱 `숫자인식CNN`과 동일)

```
입력 1x28x28
→ 합성곱1 → 렐루 → 합성곱2 → 렐루 → 최대풀링   (32x14x14)
→ 합성곱3 → 렐루 → 합성곱4 → 렐루 → 최대풀링   (64x7x7)
→ 펼치기(3136) → 완전연결1 → 렐루 → 완전연결2 → 소프트맥스
```

드롭아웃은 추론에서 쓰지 않는다.

### 전처리 (데스크톱 `app.py`의 `전처리`와 같은 순서)

1. 캔버스 픽셀에서 글씨가 있는 영역(밝기 > 0)의 경계 상자 구하기
2. 비율을 유지하며 긴 변을 20픽셀로 축소 (`imageSmoothingQuality = "high"`)
3. 28x28 검은 바탕 가운데에 배치
4. 밝기 가중 무게중심을 (14, 14)로 정수 이동
5. `(값/255 − 0.1307) / 0.3081`로 정규화 (상수는 `weights.json`에서 읽음)

PIL LANCZOS와 브라우저 축소는 픽셀값이 조금 다르므로, 전처리는 값 일치가 아니라
인식 결과 일치로 검증한다.

### 화면

- 데스크톱과 같은 배치: 왼쪽 검은 캔버스, 오른쪽 결과(큰 숫자, 확신도, 0~9 확률 막대), [지우기] 버튼
- 좁은 화면(폭 640px 미만)에서는 결과를 캔버스 아래로 배치
- 마우스·터치·펜을 Pointer Events로 통일, 캔버스에 `touch-action: none`으로 스크롤 방지
- 손을 떼면 자동 인식, 오른쪽 클릭으로도 지우기
- 펜 굵기는 캔버스 크기에 비례 (데스크톱 280px 기준 18px 비율)

### 오류 처리

- 모델 불러오는 동안 "모델 불러오는 중…" 표시, 그리기 비활성
- 불러오기 실패 시 화면에 오류 표시. `file://`로 열었으면 로컬 서버 실행 방법을 안내
- 빈 캔버스는 인식하지 않음

## 5. 검증

Node.js가 없으므로 브라우저 검사 페이지(`tests/검사.html`)를 로컬 서버
(`python -m http.server`)로 열어 확인한다. 페이지는 각 검사의 통과/실패와 요약을 표시한다.

1. **연산 단위 검사**: 손으로 계산한 작은 입력으로 각 연산의 결과 확인
2. **모델 일치 검사**: 기준값 20장의 JS 확률이 PyTorch와 1e-4 이내, 예측 숫자 모두 일치
3. **전처리 검사**: 캔버스에 1, 0, 7을 그려 넣어 올바르게 인식 (데스크톱 검사와 같은 좌표)
4. **추론 시간**: 1회 추론 시간을 측정해 표시
5. **실제 화면**: 브라우저 창에서 직접 그려 보고, 모바일 크기에서도 확인

데스크톱은 `export_web.py`의 내부 일치 확인과, 이동 후 `app.py` 실행 확인으로 검증한다.

## 6. 배포

`.github/workflows/pages.yml`:

- 실행 조건: `main` 푸시 중 `web_version/**` 또는 워크플로 파일 변경 시, 수동 실행(`workflow_dispatch`)
- 단계: `actions/checkout` → `actions/configure-pages` → `actions/upload-pages-artifact`(path: `web_version`) → `actions/deploy-pages`
- 권한: `pages: write`, `id-token: write`, `contents: read`

저장소 Pages 설정을 "GitHub Actions" 방식으로 바꾸는 일은 `gh api`로 하며, 실행 직전에 사용자 확인을 받는다.
`tests/` 폴더도 함께 배포되어 배포된 사이트에서 검사 페이지를 열 수 있다.

## 7. CLAUDE.md

- **루트**: 프로젝트 개요, 두 폴더 안내, 공통 규칙(모든 코드·주석·이름 한글,
  두 버전이 같은 모델과 정규화 상수를 공유, 재학습 후 `export_web.py` 실행)
- **desktop_version**: 기존 CLAUDE.md 내용 이전 + 웹 내보내기 절차
- **web_version**: 외부 라이브러리 금지, 모듈 구조와 의존 방향, 가중치 형식,
  로컬 실행·검사 방법, 배포 방식, 전처리를 데스크톱과 함께 수정해야 한다는 주의
