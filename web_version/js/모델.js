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
  x = 최대풀링2x2(합성곱층(x, 층.합성곱2, 28), 층.합성곱2.모양[0], 28, 28); // 32x14x14
  x = 합성곱층(x, 층.합성곱3, 14);                   // 64x14x14
  x = 최대풀링2x2(합성곱층(x, 층.합성곱4, 14), 층.합성곱4.모양[0], 14, 14); // 64x7x7 → 펼치면 3136
  x = 렐루(완전연결층(x, 층.완전연결1));             // 128
  x = 완전연결층(x, 층.완전연결2);                   // 10 (드롭아웃은 추론에서 쓰지 않음)
  return 소프트맥스(x);
}
