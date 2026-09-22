// 모델.js 가 PyTorch 와 같은 결과를 내는지 기준값으로 확인합니다.
import { 검사, 근사같음, 확인 } from "./검사도구.js";
import { 모델_불러오기 } from "../js/모델.js";
import { 최댓값_위치 } from "../js/연산.js";

const 모델경로 = new URL("../model/", import.meta.url);
const 모델_약속 = 모델_불러오기(모델경로);
모델_약속.catch(() => {}); // 실패는 아래에서 각 검사가 await 할 때 그대로 보고됩니다

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
