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
