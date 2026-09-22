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
