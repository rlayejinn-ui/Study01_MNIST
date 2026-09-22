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
  확신도.textContent = 확률 ? `확신도: ${(확률[최고] * 100).toFixed(1)}%` : " ";
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
