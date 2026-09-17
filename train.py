"""
MNIST 손글씨 숫자 데이터로 CNN을 학습시키고,
학습된 가중치를 mnist_cnn.pt 파일로 저장하는 스크립트.

실행 방법:
    python train.py
"""

import sys
import time
from pathlib import Path

import torch
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from model import MnistCNN

# 윈도우 콘솔에서도 한글이 깨지지 않도록 출력 인코딩을 UTF-8로 설정
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ----- 하이퍼파라미터 -----
배치크기 = 128          # 한 번에 학습에 사용할 이미지 개수
테스트배치크기 = 1000   # 평가 시 한 번에 처리할 이미지 개수
학습횟수 = 5            # 전체 데이터를 반복 학습할 횟수(에폭)
학습률 = 1.0            # Adadelta 옵티마이저 학습률
감마 = 0.7              # 에폭마다 학습률을 줄이는 비율

# 저장 경로 (스크립트와 같은 폴더)
현재폴더 = Path(__file__).resolve().parent
가중치경로 = 현재폴더 / "mnist_cnn.pt"
데이터폴더 = 현재폴더 / "data"


def 데이터로더_준비():
    """MNIST 데이터셋을 내려받고 학습/테스트용 데이터로더를 만든다."""
    # 텐서 변환 후 MNIST 전체 평균(0.1307)과 표준편차(0.3081)로 정규화
    변환 = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,)),
    ])

    학습데이터 = datasets.MNIST(데이터폴더, train=True, download=True, transform=변환)
    테스트데이터 = datasets.MNIST(데이터폴더, train=False, download=True, transform=변환)

    학습로더 = DataLoader(학습데이터, batch_size=배치크기, shuffle=True)
    테스트로더 = DataLoader(테스트데이터, batch_size=테스트배치크기, shuffle=False)
    return 학습로더, 테스트로더


def 한_에폭_학습(모델, 장치, 학습로더, 옵티마이저, 에폭):
    """한 에폭(전체 학습 데이터 1회 순회) 동안 모델을 학습시킨다."""
    모델.train()  # 드롭아웃 등을 학습 모드로 전환
    누적손실 = 0.0

    for 배치번호, (이미지, 정답) in enumerate(학습로더):
        이미지, 정답 = 이미지.to(장치), 정답.to(장치)

        옵티마이저.zero_grad()            # 이전 배치의 기울기 초기화
        예측 = 모델(이미지)               # 순전파
        손실 = F.nll_loss(예측, 정답)     # 음의 로그우도 손실
        손실.backward()                   # 역전파로 기울기 계산
        옵티마이저.step()                 # 가중치 갱신

        누적손실 += 손실.item()
        if 배치번호 % 100 == 0:
            진행률 = 100.0 * 배치번호 / len(학습로더)
            print(f"  [에폭 {에폭}] {배치번호:>4}/{len(학습로더)} 배치 "
                  f"({진행률:5.1f}%)  손실: {손실.item():.4f}")

    return 누적손실 / len(학습로더)


def 성능_평가(모델, 장치, 테스트로더):
    """테스트 데이터로 평균 손실과 정확도를 계산한다."""
    모델.eval()  # 드롭아웃을 끄고 평가 모드로 전환
    총손실 = 0.0
    맞힌개수 = 0

    with torch.no_grad():  # 평가 시에는 기울기를 계산하지 않음
        for 이미지, 정답 in 테스트로더:
            이미지, 정답 = 이미지.to(장치), 정답.to(장치)
            예측 = 모델(이미지)
            총손실 += F.nll_loss(예측, 정답, reduction="sum").item()
            예측숫자 = 예측.argmax(dim=1)
            맞힌개수 += (예측숫자 == 정답).sum().item()

    전체개수 = len(테스트로더.dataset)
    평균손실 = 총손실 / 전체개수
    정확도 = 100.0 * 맞힌개수 / 전체개수
    return 평균손실, 정확도, 맞힌개수, 전체개수


def main():
    # GPU가 있으면 GPU를, 없으면 CPU를 사용
    장치 = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"사용 장치: {장치}")

    torch.manual_seed(1)  # 결과 재현을 위한 난수 고정

    print("MNIST 데이터셋을 준비합니다...")
    학습로더, 테스트로더 = 데이터로더_준비()
    print(f"학습 이미지 {len(학습로더.dataset):,}장, 테스트 이미지 {len(테스트로더.dataset):,}장\n")

    모델 = MnistCNN().to(장치)
    옵티마이저 = optim.Adadelta(모델.parameters(), lr=학습률)
    # 에폭마다 학습률에 감마를 곱해 점점 줄인다
    스케줄러 = optim.lr_scheduler.StepLR(옵티마이저, step_size=1, gamma=감마)

    시작시각 = time.time()
    for 에폭 in range(1, 학습횟수 + 1):
        print(f"===== 에폭 {에폭}/{학습횟수} =====")
        평균학습손실 = 한_에폭_학습(모델, 장치, 학습로더, 옵티마이저, 에폭)
        평균손실, 정확도, 맞힌개수, 전체개수 = 성능_평가(모델, 장치, 테스트로더)
        스케줄러.step()
        print(f"  -> 학습 평균 손실: {평균학습손실:.4f} | "
              f"테스트 손실: {평균손실:.4f} | "
              f"정확도: {맞힌개수:,}/{전체개수:,} ({정확도:.2f}%)\n")

    걸린시간 = time.time() - 시작시각
    print(f"학습 완료! 총 소요 시간: {걸린시간/60:.1f}분")

    # 학습된 가중치만 저장 (구조는 model.py의 MnistCNN이 담당)
    torch.save(모델.state_dict(), 가중치경로)
    print(f"가중치를 저장했습니다: {가중치경로}")


if __name__ == "__main__":
    main()
