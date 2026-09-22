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
